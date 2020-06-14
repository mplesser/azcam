import os
import glob
import shutil

import numpy
import matplotlib.pyplot as plt

import azcam
from azcam.console import api
import azcam.testers
from azcam.testers.testerbase import TesterBase


class Ptc(TesterBase):
    """
    Photon Transfer Curve acquisition and analysis.
    """

    def __init__(self):

        super().__init__("ptc")

        self.exposure_type = "flat"  # not reset as system dependent
        self.ext_analyze = -1  # extension to analyze if not entire image

        self.exposure_levels = []
        self.use_ref_diode = 0

        self.marker1 = "b."
        self.marker2 = "r."
        self.style1 = ""  # 'b.'
        self.style2 = ""  # 'r.'
        self.wavelength = -1  # wavelength of acquisition

        self.gain_range = []  # [min,max] for gain plotting

        self.system_gain = []  # for scaling from DN to electrons

        self.flush_before_exposure = 0  # number of extra flush before each exposure

        self.bad_chans = []
        self.overscan_correct = 1  # flag for overscan correct

        self.log_plot = 0

        self.fit_line = 0  # flat True to fit line to curve
        self.fit_min = 1000  # min DN for line fit
        self.fit_max = 50000
        self.fullwell_spec = -1  # FW spec in electrons
        self.min_fullwell = -1
        self.minfits = []
        self.maxfits = []

        self.data_file = "ptc.txt"
        self.report_file = "ptc"

        self.poly_coeffs = []
        self.slope = -1  # slope to PTC fit

        self.resample = 1  # number of pixels to reample (1D value) for pixel crosstalk

        self.fit_min = 0
        self.fit_max = 0
        self.means = []
        self.sdevs = []
        self.gains = []
        self.noises = []
        self.num_chans = -1
        # if no exposure_levels...
        self.exposure_times = []
        self.max_exposure = 1.0
        self.log_exposures = 1
        self.include_dark_current = 0

        self.analysis_folder = ""

    def acquire(self):
        """
        Acquire a bias image and a series of flats for a Photon Transfer Curve (PTC).
        ExposureTimes is a list of exposure times for each pair.
        """

        azcam.log("Acquiring PTC sequence")

        # save pars to be changed
        impars = {}
        api.save_imagepars(impars)

        # create new subfolder
        currentfolder, newfolder = azcam.utils.make_file_folder("ptc")
        api.set_par("imagefolder", newfolder)

        # clear device
        api.tests()

        # set wavelength
        if self.wavelength > 0:
            wave = int(self.wavelength)
            wave1 = api.get_wavelength()
            wave1 = int(wave1)
            if wave1 != wave:
                azcam.log(f"Setting wavelength to {wave} nm")
                api.set_wavelength(wave)
                wave1 = api.get_wavelength()
                wave1 = int(wave1)
            azcam.log(f"Current wavelength is {wave1} nm")

        api.set_par("imageroot", "ptc.")  # for automatic data analysis
        api.set_par("imageincludesequencenumber", 1)  # use sequence numbers
        api.set_par("imageautoname", 0)  # manually set name
        api.set_par("imageautoincrementsequencenumber", 1)  # inc sequence numbers
        api.set_par("imagetest", 0)  # turn off TestImage

        # bias image
        api.set_par("imagetype", "zero")
        filename = os.path.basename(api.get_image_filename())
        azcam.log("Taking PTC bias: %s" % filename)

        # measure the reference diode current with shutter closed
        if self.use_ref_diode:
            dc = api.get_current(0, 0)
            api.set_keyword("REFCUR", dc, "Reference diode current (A)", "float", "instrument")

        api.expose(0, "zero", "PTC bias")

        # determine ExposureTimes
        if azcam.testers.detcal.valid and len(self.exposure_levels) > 0:
            azcam.log("Using exposure_levels")
            if self.wavelength == -1:
                wave = api.get_wavelength()
                wave = int(wave)
            else:
                wave = self.wavelength

            meanelectrons = azcam.testers.detcal.mean_electrons
            self.exposure_times = numpy.array(self.exposure_levels) / meanelectrons[wave]

        elif len(self.exposure_times) > 0:
            azcam.log("Using ExposureTimes")

        elif self.number_images_acquire > 0:
            azcam.log("Using number_images_acquire")
            self.exposure_times = []
            MinExposure = float(self.max_exposure) / self.number_images_acquire
            ExposureInc = (self.max_exposure - MinExposure) / max(
                (self.number_images_acquire - 1), 1
            )
            exptime = MinExposure
            for _ in range(self.number_images_acquire):
                self.exposure_times.append(exptime)
                exptime = exptime + ExposureInc
        else:
            raise azcam.AzcamError("could not determine exposure times")

        # loop through pairs
        api.set_par("imagetype", self.exposure_type)
        number_pairs = len(self.exposure_times)

        for pair, ExposureTime in enumerate(self.exposure_times):

            filename = os.path.basename(api.get_image_filename())
            azcam.log(
                "Taking PTC pair %d of %d for %.3f secs" % (pair + 1, number_pairs, ExposureTime)
            )

            # measure the reference diode current
            if self.use_ref_diode:
                dc = api.get_current(0, 1)
                api.set_keyword("REFCUR", dc, "Reference diode current (A)", "float", "instrument")

            # make exposure
            if self.flush_before_exposure:
                api.tests()
            api.expose(ExposureTime, self.exposure_type, "PTC frame 1")
            filename = os.path.basename(api.get_image_filename())

            # measure the reference diode current
            if self.use_ref_diode:
                dc = api.get_current(0, 1)
                api.set_keyword("REFCUR", dc, "Reference diode current (A)", "float", "instrument")

            api.expose(ExposureTime, self.exposure_type, "PTC frame 2")

        # close
        try:
            api.delete_keyword("REFCUR", "instrument")
        except Exception:
            pass
        api.restore_imagepars(impars, currentfolder)
        azcam.log("PTC sequence finished")

        return

    def analyze(self):
        """
        Analyze an exisiting series of flats and create a Photon Transfer Curve (PTC) table.
        """

        azcam.log("Analyzing PTC sequence")

        rootname = "ptc."
        self.analysis_folder = ""

        subfolder = "analysis"
        startingfolder = azcam.utils.curdir()

        self.minfits = []
        self.maxfits = []

        if self.overscan_correct or self.resample > 1:
            # create analysis subfolder
            startingfolder, subfolder = azcam.utils.make_file_folder(subfolder)

            # copy all image files to analysis folder
            azcam.log("Making copy of image files for analysis")
            for filename in glob.glob(os.path.join(startingfolder, "ptc*.fits")):
                shutil.copy(filename, subfolder)

            azcam.utils.curdir(subfolder)  # move for analysis folder - assume it already exists
        currentfolder = azcam.utils.curdir()
        self.analysis_folder = currentfolder  # save for other tasks

        firstfile, starting_seq_num = azcam.utils.find_file_in_sequence(rootname)
        seq_num = starting_seq_num

        self.NumExt, self.first_ext, self.last_ext = azcam.fits.get_extensions(firstfile)

        # get ROI
        self.roi = azcam.utils.get_image_roi()

        # Overscan correct all images
        if self.overscan_correct:
            nextfile = os.path.join(currentfolder, rootname + "%04d" % seq_num) + ".fits"
            loop = 0
            azcam.log("Overscan correcting images")
            while os.path.exists(nextfile):
                azcam.log("Overscan correct image: %s" % os.path.basename(nextfile))
                azcam.fits.colbias(nextfile)
                seq_num = seq_num + 1
                nextfile = os.path.join(currentfolder, rootname + "%04d" % seq_num) + ".fits"
                loop += 1

        if self.resample > 1:
            seq_num = starting_seq_num
            nextfile = os.path.join(currentfolder, rootname + "%04d" % seq_num) + ".fits"
            loop = 0
            azcam.log(f"Resampling images: {self.resample}x{self.resample} pixels")
            while os.path.exists(nextfile):
                azcam.log("Resampling image: %s" % os.path.basename(nextfile))
                azcam.fits.resample(nextfile, 2)
                seq_num = seq_num + 1
                nextfile = os.path.join(currentfolder, rootname + "%04d" % seq_num) + ".fits"
                loop += 1

        # bias image used for gain calc
        zerofilename = rootname + "%04d" % starting_seq_num
        zerofilename = os.path.join(currentfolder, zerofilename) + ".fits"
        zerofilename = azcam.utils.make_image_filename(zerofilename)

        # start with overscan corrected pair
        seq_num = starting_seq_num
        nextfile = os.path.join(currentfolder, rootname + "%04d" % seq_num) + ".fits"
        self.exposure_times = []
        while os.path.exists(nextfile):
            if azcam.utils.check_keyboard(0) == "q":
                break
            seq_num = seq_num + 1
            flat1filename = rootname + "%04d" % seq_num
            flat1filename = os.path.join(currentfolder, flat1filename) + ".fits"
            seq_num = seq_num + 1
            flat2filename = rootname + "%04d" % seq_num
            flat2filename = os.path.join(currentfolder, flat2filename) + ".fits"
            ExposureTime = float(azcam.fits.get_keyword(flat1filename, "EXPTIME"))
            self.exposure_times.append(ExposureTime)

            gain, noise, mean, sdev = azcam.testers.gain.measure_gain(
                zerofilename, flat1filename, flat2filename
            )
            s = "Exposure Time: %-8.3f Mean: %.0f  File: %s" % (
                ExposureTime,
                mean[0],
                os.path.basename(flat1filename),
            )
            azcam.log(s)

            for chan in range(self.first_ext, self.last_ext):
                s = "Chan: %2d Mean: %-8.0f Gain: %-5.2f Noise: %-5.1f" % (
                    chan,
                    mean[chan - 1],
                    gain[chan - 1],
                    noise[chan - 1],
                )
                azcam.log(s)
            self.means.append([float(x) for x in mean])
            self.gains.append([float(x) for x in gain])
            self.sdevs.append([float(x) for x in sdev])
            self.noises.append([float(x) for x in noise])

            nextfile = os.path.join(currentfolder, rootname + "%04d" % (seq_num + 1)) + ".fits"

        self.num_chans = len(self.means[0])
        self.num_points = len(self.means)

        # find indices for line fit
        if self.fit_line:

            # find fit limit indices
            minfit = minfit1 = 0
            maxfit = maxfit1 = len(self.means) - 1
            for ext in range(self.first_ext, self.last_ext):
                chan = ext - 1
                if chan in self.bad_chans:
                    continue
                if self.fit_min != -1:
                    for x, m in enumerate(self.means):
                        if m[chan] > self.fit_min:
                            minfit1 = x
                            break
                if self.fit_max != -1:
                    for x, m in enumerate(self.means):
                        if m[chan] > self.fit_max:
                            maxfit1 = x + 1
                            break
                if minfit1 > minfit:
                    minfit = minfit1
                if maxfit1 < maxfit:
                    maxfit = maxfit1

                self.minfits.append(minfit)
                self.maxfits.append(maxfit)

        azcam.log(f"Grade = {self.grade}")

        # move to starting folder for data/reports
        azcam.utils.curdir(startingfolder)

        # now plot
        if self.create_plots and len(self.means) > 2:
            self.plot(self.log_plot)

        self.dataset = {
            "data_file": self.data_file,
            "grade": self.grade,
            "NumExt": self.NumExt,
            "fullwell_spec": self.fullwell_spec,
            "poly_coeffs": numpy.array(self.poly_coeffs).tolist(),
            "exposure_times": self.exposure_times,
            "means": self.means,
            "sdevs": self.sdevs,
            "gains": self.gains,
        }

        # write output files
        self.write_datafile()
        if self.create_reports:
            self.report()

        # finish
        self.valid = True

        return

    def _make_table(self):
        """
        Rearranges data by image extension.
        Makes a new table of the PTC data from Analyze.
        Must run analyze() first.
        """

        self.means_bychan = []
        self.sdevs_bychan = []
        self.gains_bychan = []
        self.NOISES = []
        for c in range(self.num_chans):
            mm = []
            ss = []
            gg = []
            nn = []
            for p in range(self.num_points):  # was -1
                mm.append(self.means[p][c])
                ss.append(self.sdevs[p][c])
                gg.append(self.gains[p][c])
                nn.append(self.noises[p][c])
            self.means_bychan.append(mm)
            self.sdevs_bychan.append(ss)
            self.gains_bychan.append(gg)
            self.NOISES.append(nn)

        return

    def plot(self, logplot=0):
        """
        Plot a Photon Transfer Curve from ptc.means, ptc.sdevs, ptc.gains.
        This version makes one plot with multiple line types and colors (not subplots).
        If logplot is True, plot is noise vs signal on log plot.
        If logplot is False, plot is variance vs signal on linear plot.
        """

        # rearrange data
        self._make_table()

        # single channel mode
        if self.ext_analyze != -1:
            self.num_chans = 1

        # setup plot pars
        #  get subplot pars with figure(1).subplotpars.left...
        ptop = 0.92
        pbottom = 0.22
        pleft = 0.18
        pright = 0.95
        wspace = None
        hspace = None
        marksize = 5
        large_font = 18
        MediumFont = 16
        small_font = 14
        plotstyle = azcam.plot.style_dot

        # setup PTC plot
        fig_ptc = plt.figure()
        fignum_ptc = fig_ptc.number
        azcam.plot.move_window(fignum_ptc)
        fig_ptc.suptitle("Photon Transfer Curve", fontsize=large_font)
        fig_ptc.subplots_adjust(
            left=pleft, bottom=pbottom, right=pright, top=ptop, wspace=wspace, hspace=hspace,
        )
        fig_ptc = plt.subplot(1, 1, 1)
        fig_ptc.grid(1)

        plt.xlabel("Mean Signal [DN]", fontsize=MediumFont)
        if logplot:
            plt.ylabel("Noise [DN]", fontsize=MediumFont)
        else:
            plt.ylabel(r"$\rm{Variance\ [DN^2]}$", fontsize=MediumFont)
        ax = plt.gca()
        for label in ax.yaxis.get_ticklabels():
            label.set_fontsize(small_font)
        for label in ax.xaxis.get_ticklabels():
            label.set_rotation(45)
            label.set_fontsize(small_font)

        # setup gain plot
        fig_gain = plt.figure()
        fignum_gain = fig_gain.number
        azcam.plot.move_window(fignum_gain)
        fig_gain.suptitle("System Gain", fontsize=large_font)
        fig_gain.subplots_adjust(
            left=pleft, bottom=pbottom, right=pright, top=ptop, wspace=wspace, hspace=hspace,
        )
        fig_gain = plt.subplot(1, 1, 1)
        fig_gain.grid(1)
        plt.ylabel(r"$\rm{Gain\ [e^{-}/DN]}$", fontsize=MediumFont)
        plt.xlabel("Mean Signal [DN]", fontsize=MediumFont)
        ax = plt.gca()
        for label in ax.xaxis.get_ticklabels():
            label.set_rotation(45)
            label.set_fontsize(small_font)
        for label in ax.yaxis.get_ticklabels():
            label.set_fontsize(small_font)

        # make plots
        for chan in range(self.num_chans):

            # single channel mode
            if self.ext_analyze != -1:
                chan = self.ext_analyze

            # get data into arrays for plotting
            sdev = []
            var = []
            mm = []
            m = self.means_bychan[chan]
            s = self.sdevs_bychan[chan]
            g = self.gains_bychan[chan]
            gmedian = sorted(g)[int(len(g) / 2)]
            for i in range(self.num_points):
                sdev.append(s[i])
                mm.append(max(m))
                var.append(s[i] * s[i])

            # ptc plot
            plt.figure(fignum_ptc)
            if logplot:
                if self.style1 == "":
                    plt.loglog(
                        m, sdev, plotstyle[chan % self.num_chans], markersize=marksize,
                    )
                else:
                    plt.loglog(
                        m, sdev, self.style1, markersize=marksize,
                    )
                plt.ylim(1)
                plt.xlim(1)
            else:
                if self.style1 == "":
                    plt.plot(
                        m, var, plotstyle[chan % self.num_chans], markersize=marksize,
                    )
                else:
                    plt.plot(
                        m, var, self.style1, markersize=marksize,
                    )
                plt.ylim(0)
                plt.xlim(0, 65000)

            # plot full well line
            if self.min_fullwell != -1:
                ax = plt.gca()
                plt.plot(
                    [self.min_fullwell, self.min_fullwell], ax.get_ylim(), "r--", linewidth=0.7,
                )

            # line fit
            if self.fit_line:
                xx = m[self.minfits[chan] : self.maxfits[chan]]
                if self.log_plot:
                    yy = sdev[self.minfits[chan] : self.maxfits[chan]]
                    fitorder = 2
                else:
                    yy = var[self.minfits[chan] : self.maxfits[chan]]
                    fitorder = 1
                try:
                    polycoeffs = numpy.polyfit(xx, yy, fitorder)
                    yfit = numpy.polyval(polycoeffs, xx)
                    if self.log_plot:
                        plt.loglog(xx, yfit, "b--", linewidth=1)
                    else:
                        plt.plot(xx, yfit, "b--", linewidth=1)
                    self.slope = 1.0 / polycoeffs[0]
                    s = f"Gain = {self.slope:0.2f} [e/DN]"
                    plt.annotate(
                        s,
                        xy=(0.04, 0.9 - 0.07 * chan),
                        xycoords="axes fraction",
                        bbox=dict(boxstyle="round,pad=0.1", fc="lightyellow", alpha=1.0),
                    )
                except numpy.linalg.LinAlgError:
                    azcam.log(f"Could not fit line to channel {chan} PTC data within limits")

            # gain plot
            plt.figure(fignum_gain)
            if self.style2 == "":
                plt.plot(
                    m, g, plotstyle[chan % self.num_chans], markersize=marksize,
                )
            else:
                plt.plot(
                    m, g, self.style2, markersize=marksize,
                )

            # set axes
            if self.gain_range != []:
                plt.ylim(self.gain_range[0], self.gain_range[1])
            else:
                gmin = max(0, gmedian / 2.0)
                gmax = gmedian * 2.0
                plt.ylim(gmin, gmax)

            plt.xlim(0, 65000)

            # one pass only for single channel mode
            if self.ext_analyze != -1:
                break

        # save plots
        plt.show()
        azcam.plot.save_figure(fignum_ptc, "ptc.png")
        azcam.plot.save_figure(fignum_gain, "gain.png")

        return

    def report(self):
        """
        Write report file.
        """

        PTCPLOT = "ptc.png"
        GAINPLOT = "gain.png"

        lines = ["# PTC Analysis", ""]

        if self.grade != "UNDEFINED":
            s = f"PTC grade = {self.grade}"
            lines.append(s)
            lines.append("")

        lines.append(f"![Photon Transfer Curve]({os.path.abspath(PTCPLOT)})  ")
        lines.append("*Photon Transfer Curve.*")
        lines.append("")

        lines.append(f"![Photon Transfer Gain Plot]({os.path.abspath(GAINPLOT)})  ")
        lines.append("*Photon Transfer Gain Plot.*")
        lines.append("")

        # Make report files
        self.write_report(self.report_file, lines)

        return
