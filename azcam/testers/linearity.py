import glob
import os
import shutil

import numpy

import azcam
import azcam.utils
import azcam.fits
import azcam.console.plot
from azcam.testers.basetester import Tester


class Linearity(Tester):
    """
    Linearity acquisition and analysis.
    Fit is normally 10% to 90% of estimated saturation.
    Mean residual is mean of absolute residuals in fitted range.
    """

    def __init__(self):
        super().__init__("linearity")

        self.exposure_type = "flat"

        self.number_images_acquire = -1  # number of images to acquire
        self.max_exposure = -1

        self.exposure_times = []  # list of exposure times
        self.exposure_levels = []  # listy of exposure levels [electrons/pixel]

        self.mean_gain = 1.0  # mean system gain e/DN

        self.large_font = 18
        self.small_font = 14
        self.roi = []
        self.rootname = "linearity."

        self.wavelength = -1  # wavelength of acquisition

        self.use_ptc_data = 0  # skips every other image file

        self.overscan_correct = 0  # flag for overscan_correct
        self.zero_correct = 1  # flag to use debiased residuals

        self.fullwell_estimate = -1  # estimate of saturation in DN
        self.fit_min = 0.10  # percentage of estimated full well for linearity fit
        self.fit_max = 0.90
        self.fitmin_dn = -1  # calculated fit min in DN
        self.fitmax_dn = -1
        self.fit_all_data = 1

        self.fit_order = 3
        """fit order for overscan correction"""

        self.max_allowed_linearity = -1  # max residual for linearity
        self.plot_specifications = 1  # True to plot max_allowed_linearity
        self.use_weights = 1

        self.poly_coeffs = []  # slope and intercept for each channel fit

        self.y_fits = []
        self.residuals = []
        self.mean_residuals = numpy.array([])

        self.plot_fit = 1
        self.plot_residuals = 1
        self.plot_limits = []  # linearity plot limits in %

        self.bad_chans = []  # list of bad channels to ignore

        self.data_file = "linearity.txt"
        self.report_file = "linearity"
        self.linearity_plot = "linearity.png"

        self.max_residual = 0.0

    def acquire(self, NumberExposures="prompt", max_exposure="prompt"):
        """
        Acquire a series of flats at increasing exposure levels to determine lnearity.
        Assumes that filename, timing code, and binning are already set as desired.
        NumberExposures is the number of exposure levels in sequence
        max_exposure is the maximum exposure time in seconds.
        """

        azcam.log("Acquiring Linearity sequence")

        # save pars to be changed
        impars = {}
        azcam.db.parameters.save_imagepars(impars)

        # create new subfolder
        currentfolder, newfolder = azcam.console.utils.make_file_folder("linearity")
        azcam.log(f"Linearity folder is {newfolder}")
        azcam.db.parameters.set_par("imagefolder", newfolder)

        # clear device
        imname = azcam.db.tools["exposure"].get_filename()
        azcam.db.tools["exposure"].test(0)
        bin1 = int(azcam.fits.get_keyword(imname, "CCDBIN1"))
        bin2 = int(azcam.fits.get_keyword(imname, "CCDBIN2"))
        binning = bin1 * bin2

        azcam.db.parameters.set_par(
            "imageroot", "linearity."
        )  # for automatic data analysis
        azcam.db.parameters.set_par(
            "imageincludesequencenumber", 1
        )  # use sequence numbers
        azcam.db.parameters.set_par("imageautoname", 0)  # manually set name
        azcam.db.parameters.set_par(
            "imageautoincrementsequencenumber", 1
        )  # inc sequence numbers
        azcam.db.parameters.set_par("imagetest", 0)  # turn off TestImage

        # bias image
        azcam.log(
            "Taking Linearity bias: %s"
            % os.path.basename(azcam.db.tools["exposure"].get_filename())
        )
        azcam.db.tools["exposure"].expose(0, "zero", "Linearity bias")

        azcam.db.parameters.set_par("imagetype", self.exposure_type)

        # Try exposure_level to get ExposureTime
        if len(self.exposure_levels) > 0:
            detcal = azcam.db.tools["detcal"]
            if not azcam.db.tools["detcal"].valid:
                azcam.log("Detector not calibrated, cannot use exposure_level")
            else:
                meancounts = azcam.db.tools["detcal"].mean_counts[self.wavelength]

                if self.wavelength == -1:
                    wave = azcam.db.tools["instrument"].get_wavelength()
                    wave = int(wave)

                else:
                    wave = self.wavelength

                self.exposure_times = (
                    numpy.array(self.exposure_levels) / meancounts / binning
                ) * (
                    azcam.db.tools["gain"].system_gain[0]
                    / azcam.db.tools["detcal"].system_gain[0]
                )

        elif self.number_images_acquire != -1:  # max exposure time specified
            self.exposure_times = []  # reset
            MinExposure = float(self.max_exposure) / self.number_images_acquire
            ExposureInc = (self.max_exposure - MinExposure) / max(
                (self.number_images_acquire - 1), 1
            )
            exptime = MinExposure
            for _ in range(self.number_images_acquire):
                self.exposure_times.append(exptime)
                exptime = exptime + ExposureInc

        else:
            NumberExposures = len(
                self.exposure_times
            )  # ExposureTimes directly specified

        # loop through exposures
        NumberExposures = len(self.exposure_times)
        azcam.log("Exposure times will be:", self.exposure_times)
        for exp, exptime in enumerate(self.exposure_times):
            azcam.log(
                "Taking linearity %d of %d image for %.3f seconds: %s"
                % (
                    exp + 1,
                    NumberExposures,
                    exptime,
                    os.path.basename(azcam.db.tools["exposure"].get_filename()),
                )
            )
            azcam.db.tools["exposure"].expose(
                exptime, self.exposure_type, "Linearity flat"
            )

        # finish
        azcam.db.parameters.restore_imagepars(impars)
        azcam.utils.curdir(currentfolder)
        azcam.log("Linearity sequence finished")

        return

    def analyze(self):
        """
        Analyze a series of flats which have already been taken for linearity.
        """

        azcam.log("Analyzing linearity sequence")

        subfolder = "analysis"
        startingfolder = azcam.utils.curdir()

        if self.use_ptc_data:
            rootname = "ptc."
        else:
            rootname = self.rootname

        if self.overscan_correct or self.zero_correct:
            # create analysis subfolder
            startingfolder, subfolder = azcam.console.utils.make_file_folder(subfolder)

            # copy all image files to analysis folder
            azcam.log("Making copy of image files for analysis")
            for filename in glob.glob(os.path.join(startingfolder, "*.fits")):
                shutil.copy(filename, subfolder)

            azcam.utils.curdir(
                subfolder
            )  # move for analysis folder - assume it already exists

        else:
            pass

        currentfolder = azcam.utils.curdir()

        _, StartingSequence = azcam.console.utils.find_file_in_sequence(rootname)

        # Overscan correct all images
        SequenceNumber = StartingSequence
        if self.overscan_correct:
            nextfile = (
                os.path.join(currentfolder, rootname + "%04d" % SequenceNumber)
                + ".fits"
            )
            loop = 0
            filelist = []
            azcam.log("Overscan correct images")
            while os.path.exists(nextfile):
                filelist.append(nextfile)

                # Overscan correct each image
                azcam.log("Overscan correct image: %s" % os.path.basename(nextfile))
                azcam.fits.colbias(nextfile, fit_order=self.fit_order)

                SequenceNumber = SequenceNumber + 1
                nextfile = (
                    os.path.join(currentfolder, rootname + "%04d" % SequenceNumber)
                    + ".fits"
                )
                loop += 1

        # "debias" correct with residuals after colbias
        SequenceNumber = StartingSequence
        if self.zero_correct:
            if self.overscan_correct:
                debiased = azcam.db.tools["bias"].debiased_filename
            else:
                debiased = azcam.db.tools["bias"].superbias_filename
            biassub = "biassub.fits"

            nextfile = (
                os.path.join(currentfolder, rootname + "%04d" % SequenceNumber)
                + ".fits"
            )
            loop = 0
            while os.path.exists(nextfile):
                azcam.fits.sub(nextfile, debiased, biassub)
                os.remove(nextfile)
                os.rename(biassub, nextfile)

                SequenceNumber = SequenceNumber + 1
                nextfile = (
                    os.path.join(currentfolder, rootname + "%04d" % SequenceNumber)
                    + ".fits"
                )
                loop += 1

        self.roi = azcam.console.utils.get_image_roi()

        zerofilename = rootname + "%04d" % StartingSequence
        zerofilename = azcam.utils.make_image_filename(zerofilename)
        nextfile = zerofilename

        self.NumExt, self.first_ext, self.last_ext = azcam.fits.get_extensions(
            zerofilename
        )

        # read data from image files
        self.exptimes = []  # list of exposure times
        self.means = []  # list of list of means - [ExpTime][Channel] CORRECT!!!
        SequenceNumber = StartingSequence + 1
        while os.path.exists(nextfile):
            flatfilename = rootname + "%04d" % SequenceNumber
            flatfilename = azcam.utils.make_image_filename(flatfilename)
            # flatfilename=os.path.join(currentfolder,flatfilename)+'.fits'

            exptime = float(azcam.fits.get_keyword(flatfilename, "EXPTIME"))

            self.exptimes.append(exptime)
            fmean = azcam.fits.mean(flatfilename, self.roi[0])
            mean = []
            for ext in range(self.first_ext, self.last_ext):
                chan = ext - 1
                x = fmean[chan]
                mean.append(x)
            self.means.append(mean)  # list of all extensions for each exposure time

            SequenceNumber = SequenceNumber + 1
            if self.use_ptc_data:
                SequenceNumber = SequenceNumber + 1
            nextfile = (
                os.path.join(currentfolder, rootname + "%04d" % SequenceNumber)
                + ".fits"
            )

        # find fit limits for linearity
        self.fitmin_dn = self.fit_min * self.fullwell_estimate
        self.fitmax_dn = self.fit_max * self.fullwell_estimate
        if self.fit_all_data:
            minfit = 0
            maxfit = len(self.means) - 1
        else:
            for ext in range(self.first_ext, self.last_ext):
                chan = ext - 1
                if chan == -1:
                    chan = 0
                minfit = minfit1 = 0
                maxfit = maxfit1 = len(self.means) - 1
                m1 = self.means[minfit][chan]
                m2 = self.means[maxfit][chan]
                if chan in self.bad_chans:
                    continue
                if self.fitmin_dn > 0:
                    for x, m in enumerate(self.means):
                        if m[chan] > self.fitmin_dn:
                            minfit1 = x
                            m1 = m[chan]
                            break
                if self.fitmax_dn > 0:
                    for x, m in enumerate(self.means):
                        if m[chan] > self.fitmax_dn:
                            maxfit1 = x  # was x+1
                            m2 = m[chan - 1]  # was chan
                            break
                # azcam.log(minfit1,maxfit1,m1,m2)
                maxfit1 = min(maxfit1, len(self.means) - 1)
                if minfit1 > minfit:
                    minfit = minfit1
                if maxfit1 < maxfit:
                    maxfit = maxfit1
                azcam.log(
                    f"Fit limits for chan {chan} are: {m1:.0f}:{m2:.0f} DN ({self.exptimes[minfit1]:.1f}:{self.exptimes[maxfit1]:.1f} secs)"
                )

        # find residuals for linearity (first and last point)
        self._fit_linearity(minfit, maxfit)  # residuals[chan][exp]

        # make final grade
        """
        maxdev=0.0
        for ext in range(self.first_ext,self.last_ext):
            chan=ext-1
            if chan in self.bad_chans:
                continue
            for i,r in enumerate(self.residuals[chan]):
                if i<minfit or i> maxfit:
                    continue
                if abs(r)>maxdev:
                    maxdev=abs(r)
        self.max_residual=maxdev
        """
        azcam.log(f"Largest non-linearity residual is {100. * self.max_residual:0.1f}%")

        # calculate mean linearity
        for ext in range(self.first_ext, self.last_ext):
            # for ext in range(0, self.last_ext - 1):
            ext = ext - 1
            self.mean_residuals = numpy.array(
                [abs(x) for x in self.residuals[ext][minfit:maxfit]]
            ).mean()

        if self.max_allowed_linearity != -1:
            if self.max_residual < self.max_allowed_linearity * 100.0:
                self.grade = "PASS"
            else:
                self.grade = "FAIL"
            azcam.log(f"Grade = {self.grade}")

        if not self.grade_sensor or self.max_allowed_linearity == -1:
            self.grade = "UNDEFINED"

        # plot
        self.plot(minfit, maxfit, minfit, maxfit)

        # define dataset
        self.dataset = {
            "data_file": self.data_file,
            "NumExt": self.NumExt,
            "max_residual": self.max_residual,
            "fit_min": self.fitmin_dn,
            "fit_max": self.fitmax_dn,
            "poly_coeffs": numpy.array(self.poly_coeffs).tolist(),
            "exptimes": self.exptimes,
            "means": numpy.array(self.means).tolist(),
            "residuals": numpy.array(self.residuals).tolist(),
            "mean_residuals": self.mean_residuals.tolist(),
        }
        if self.max_allowed_linearity != -1:
            self.dataset["grade"] = (self.grade,)
            self.dataset["max_allowed_linearity"] = self.max_allowed_linearity

        # set absolute filenames
        self.linearity_plot = os.path.abspath(self.linearity_plot)

        # write data
        self.write_datafile()
        if self.create_reports:
            self.report()

        # move to starting folder for data/reports
        # azcam.utils.curdir(startingfolder)
        self._copy_data_files()

        self.valid = True

        return

    def _fit_linearity(self, fit_min=-1, fit_max=-1):
        """
        Calculate residuals from linearity data.
        """

        if fit_min == -1:
            fit_min = 0

        xdata = self.exptimes
        num_points = len(xdata)

        if fit_max == -1:
            fit_max = num_points

        # make least squares lineary fit through fit_min to fit_max points
        exptimes = xdata[fit_min:fit_max]

        yfits = []
        polys = []
        for ext in range(self.first_ext, self.last_ext):  # extensions
            chan = ext - 1  # now an index into array, not ext number
            ydata = []
            for i in range(
                fit_min, fit_max
            ):  # means list of extensions per each exp times
                means = self.means[i]
                ydata.append(means[chan])  # ydata is list of means for each exension

            # generate line y values
            if self.use_weights:
                weights = 1.0 / numpy.array(ydata)  # 1./variance
                try:
                    polycoeffs = numpy.polyfit(
                        exptimes, ydata, 1, w=weights
                    )  # [slope,intercept]
                except Exception:
                    polycoeffs = numpy.polyfit(exptimes, ydata, 1, w=weights)
            else:
                polycoeffs = numpy.polyfit(exptimes, ydata, 1)  # [slope,intercept]
            polys.append(list(polycoeffs))  # to list for JSON
            yfit = numpy.polyval(polycoeffs, xdata)  # all data, not xxdata

            yfits.append(yfit)  # yfits[ext][ExpTime]
        self.poly_coeffs = polys
        self.y_fits = yfits

        # calculate residuals for all points
        residuals = []
        for ext in range(self.first_ext, self.last_ext):  # extensions
            chan = ext - 1
            r = []
            for i in range(num_points):  # exp times
                r1 = self.means[i][chan] - yfits[chan][i]  # count difference
                r1 = r1 / yfits[chan][i]  # residual
                r.append(r1)
            residuals.append(r)  # residuals[ext][ExpTime]
        self.residuals = residuals

        # find max_residual
        maxdev = 0.0
        for ext in range(self.first_ext, self.last_ext):
            chan = ext - 1
            if chan in self.bad_chans:
                continue
            for i, r in enumerate(self.residuals[chan]):
                if i < fit_min or i > fit_max:
                    continue
                if abs(r) > maxdev:
                    maxdev = abs(r)
        self.max_residual = maxdev

        return

    def plot(self, MinPoint=0, MaxPoint=-1, MinSpec=-1, MaxSpec=-1):
        """
        Plot linearity and residuals curve(s).
        Min and Max Points are limits for plot (as point numbers).
        Min and Max Spec are x-limits to plot specifications ( as point numbers).

        """

        plotstyle = azcam.console.plot.style_dot

        fig = azcam.console.plot.plt.figure()
        fignum = fig.number
        azcam.console.plot.move_window(fignum)

        # ax1 is linearity
        if self.plot_residuals:
            linplotnum = 211
        else:
            linplotnum = 111
        ax1 = azcam.console.plot.plt.subplot(linplotnum)
        s = "Linearity"
        azcam.console.plot.plt.title(s, fontsize=self.large_font)
        azcam.console.plot.plt.ylabel("Mean [DN]", fontsize=self.small_font)

        # ax2 is residuals
        if self.plot_residuals:
            ax2 = azcam.console.plot.plt.subplot(212)
            azcam.console.plot.plt.subplots_adjust(left=0.20, hspace=0.6)
            s = "Linearity Residuals"
            azcam.console.plot.plt.title(s, fontsize=self.large_font)

        nps = len(plotstyle)

        for chan, _ in enumerate(range(self.first_ext, self.last_ext)):
            if chan in self.bad_chans:
                continue

            # plot linearity
            # azcam.console.plot.plt.subplot(linplotnum)
            m = []
            for means in self.means:  # exp times
                m.append(means[chan])
            ax1.plot(
                self.exptimes[MinPoint : MaxPoint + 1], m[MinPoint : MaxPoint + 1], "k+"
            )
            azcam.console.plot.plt.xlabel(
                "Exposure Time [secs]", fontsize=self.small_font
            )
            # azcam.console.plot.plt.ylim(0)
            ax1.grid(1)

            # plot fit
            if self.plot_fit:
                ax1.plot(
                    self.exptimes[MinPoint : MaxPoint + 1],
                    self.y_fits[chan][MinPoint : MaxPoint + 1],
                    "r-",
                )

            # plot residuals
            if self.plot_residuals:
                # azcam.console.plot.plt.subplot(212)
                residuals = self.residuals[chan]
                ax2.plot(
                    self.exptimes[MinPoint : MaxPoint + 1],
                    100.0 * numpy.array(residuals[MinPoint : MaxPoint + 1]),
                    plotstyle[chan % nps],
                )
                azcam.console.plot.plt.xlabel(
                    "Exposure Time [secs]", fontsize=self.small_font
                )
                azcam.console.plot.plt.ylabel("Residual [%]", fontsize=self.small_font)
                if self.plot_limits != []:
                    azcam.console.plot.plt.ylim(
                        self.plot_limits[0], self.plot_limits[1]
                    )
                ax2.grid(1)

        # plot specs (one time) on residuals axis
        if self.plot_specifications:
            upper = 100.0 * self.max_allowed_linearity
            lower = -100.0 * self.max_allowed_linearity
            if MinSpec != -1:
                left = self.exptimes[MinSpec]
            else:
                left = self.exptimes[MinPoint]
            if MaxSpec != -1:
                right = self.exptimes[MaxSpec]
            else:
                right = self.exptimes[MaxPoint + 1]
            if self.plot_residuals:
                ax2.plot([left, right], [upper, upper], "b--", linewidth=0.7)
                ax2.plot([left, right], [lower, lower], "b--", linewidth=0.7)

        # show and save plot
        azcam.console.plot.plt.show()
        azcam.console.plot.save_figure(fignum, self.linearity_plot)

        return

    def report(self):
        """
        Write report file.
        """

        lines = []

        lines.append("# Linearity Analysis")

        if self.grade != "UNDEFINED":
            s = f"Linearity grade = {self.grade}  "
            lines.append(s)

        lines.append(f"Max residual value [%]:   {100. * self.max_residual:0.1f}  ")
        if self.grade != "UNDEFINED":
            lines.append(
                f"Max allowed residual [%]: {100.0 * self.max_allowed_linearity:0.1f}  "
            )
        lines.append(f"Minimum fit limit [DN]: {self.fitmin_dn}  ")
        lines.append(f"Maximum fit limit [DN]: {self.fitmax_dn}  ")
        lines.append(f"Mean residuals [%]: {100. * self.mean_residuals:.1f}  ")
        lines.append("")

        lines.append(
            f"![Linearity and residuals Plot]({os.path.abspath(self.linearity_plot)})  "
        )
        lines.append("*Linearity and residuals Plot.*  ")

        # Make report files
        self.write_report(self.report_file, lines)

        return

    def _copy_data_files(self, folder=""):
        """
        Copy data files to proper report folder.
        """

        files = [
            "linearity.txt",
            "linearity.md",
            "linearity.pdf",
            "linearity.png",
        ]

        # destination folder
        if folder == "":
            fldr = os.path.abspath("../")
        else:
            fldr = os.path.abspath(folder)

        if os.path.exists(fldr):
            azcam.log("Existing linearity folder: %s" % fldr)
        else:
            azcam.log("Creating new linearity folder: %s" % fldr)
            os.mkdir(fldr)

        for f in files:
            try:
                shutil.copy(f, fldr)
            except Exception as message:
                azcam.log(message)

        return
