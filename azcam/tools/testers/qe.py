import glob
import os
import shutil

import numpy

import azcam
from azcam.image import Image
from azcam.tools.testers.basetester import Tester


class Qe(Tester):
    """
    Quantum Efficiency (QE) acquisition and analysis.
    """

    def __init__(self):

        super().__init__("qe")

        self.diode_cal_file = "diode_cal.txt"
        self.diode_qe_file = "diode_qe.txt"
        self.diode_cal_folder = ""

        self.flux_cal_folder = ""
        self.flux_cal_file = "flux_cal.txt"

        self.window_trans = {}  # dictionary of {wave:trans}
        self.throughputs = []  # effective throughput, usually only window
        self.qe_specs = {}  # QE specifications for PASS/FAIL {wavelength:spec}
        self.grades = {}  # QE grade {wavelength:grade}

        self.exposure_levels = {}  # Exposure levels {wave:level} [e/pix]
        self.exposure_times = {}  # Exposure times {wave:seconds]  (when no exposure_levels)
        self.means = []  # mean counts
        self.qe = {}  # QE values
        self.wavelengths = []  # Wavelengths for QE measurements
        self.fluxes = []  # photons/sec/mm^2 at reference
        self.use_edge_mask = 0  # use defects mask
        self.flush_before_exposure = 0  # number of extra flush before each exposure

        self.exptime_offset = 0.0

        self.include_dark_images = 0  # include dark images in acquire & analysis

        self.overscan_correct = 1
        self.zero_correct = 0

        self.system_gain = []

        self.fit_order = 3  # order of overscan correction fit

        self.diode_area = 613.0  # diode area in mm^2
        self.diode_wavelength = []
        self.sphere_current = []
        self.diode_power = []
        self.diode_current = []
        self.diode_qe = {}

        self.use_powermeter = 1

        self.cal_scale = 1.0  # geometric scaling from reference to sensor
        self.pixel_area = 0.015 * 0.015  # unbinned pixel area in mm^2
        self.mean_temp = -999  # Mean temperature of data
        self.binning = 1
        self.global_scale = 1.0  # scale factor

        self.plot_limits = []  # min and max of plot
        self.plot_title = ""  # title for QE plot

        self.data_file = "qe.txt"
        self.report_file = "qe"

        self.qeroi = []  # special ROI for qe [row1,row2,col1,col2]

    def acquire(self):
        """
        Acquire a series of flats for QE measurement.
        Assumes timing code and binning is set as desired.
        """

        azcam.log("Acquiring QE sequence")

        exposure, instrument = azcam.utils.get_tools(["exposure", "instrument"])

        # save pars to be changed
        impars = {}
        azcam.utils.save_imagepars(impars)

        # create new subfolder
        currentfolder, subfolder = azcam.utils.make_file_folder("qe")
        azcam.log(f"QE folder is {subfolder}")
        azcam.db.parameters.set_par("imagefolder", subfolder)

        bin1 = azcam.db.parameters.get_par("colbin")
        bin2 = azcam.db.parameters.get_par("rowbin")
        if 0:
            binning = bin1 * bin2
        else:
            binning = 1

        # Get exposure times
        if len(self.exposure_times) > 0:
            azcam.log("Using exposure_times")
        else:
            raise azcam.AzcamError("Could not determine exposure times")

        azcam.db.parameters.set_par("imageroot", "qe.")  # for automatic data analysis
        azcam.db.parameters.set_par(
            "imageincludesequencenumber", 1
        )  # use sequence numbers
        azcam.db.parameters.set_par("imagesequencenumber", 1)  # start at sequence number 1
        azcam.db.parameters.set_par("imageautoname", 0)  # manually set name
        azcam.db.parameters.set_par(
            "imageautoincrementsequencenumber", 1
        )  # inc sequence numbers
        azcam.db.parameters.set_par("imagetest", 0)  # turn off TestImage

        # binning
        exposure.roi_reset()  # use entire device
        # exposure.set_roi(-1, -1, -1, -1, self.binning, self.binning)

        # take bias image
        azcam.db.parameters.set_par("imageroot", "qe.")
        azcam.log("Taking bias image %s..." % os.path.basename(exposure.get_filename()))

        # clear device
        exposure.test(0)

        exposure.expose(0, "zero", "QE bias")

        waves = self.exposure_times.keys()
        for wave in waves:
            wave = int(0.5 + float(wave))  # make sure wave is an integer

            etime = self.exposure_times[wave]
            title = f"{wave} nm QE flat for {etime} secs"
            azcam.log(f"Setting wavelength to {wave}")
            instrument.set_wavelength(wave)

            azcam.log(
                "Taking %d nm QE image for %.3f seconds: %s..."
                % (
                    wave,
                    etime,
                    os.path.basename(exposure.get_filename()),
                )
            )

            # make sure at proper wavelength
            w = instrument.get_wavelength()
            w = int(float(w) + 0.5)
            azcam.log(f"Actual wavelength is {w}")

            # make exposure
            for _ in range(self.flush_before_exposure):
                exposure.test(0)

            if self.include_dark_images:
                darktitle = f"dark image for {etime} secs"
                exposure.expose(etime, "dark", f"{darktitle}")

            exposure.expose(etime, "flat", f"{title}")

        # copy diode cal file to local folder
        try:
            f1 = os.path.join(self.diode_cal_folder, self.diode_cal_file)
            f2 = os.path.join(subfolder, "diode_cal.txt")
            shutil.copyfile(f1, f2)
        except FileNotFoundError:
            pass

        # copy diode qe file to local folder
        try:
            f1 = os.path.join(self.diode_cal_folder, self.diode_qe_file)
            f2 = os.path.join(subfolder, "diode_qe.txt")
            shutil.copyfile(f1, f2)
        except FileNotFoundError:
            pass

        # copy flux cal file to local folder
        try:
            f1 = os.path.join(self.flux_cal_folder, self.flux_cal_file)
            f2 = os.path.join(subfolder, "flux_cal.txt")
            shutil.copyfile(f1, f2)
        except FileNotFoundError:
            pass

        # finish
        instrument.delete_keyword("REFCUR")
        azcam.utils.restore_imagepars(impars, currentfolder)

        return

    def analyze(self):
        """
        Analyze an exisiting QE series of flats.
        Includes Newport power meter calibration.
        """

        h = 6.62607015e-34  # J⋅s
        c = 2.99792458e8  # m/s

        azcam.log("Analyzing QE sequence")

        rootname = "qe."
        subfolder = "analysis"

        # read DiodeCalibration file
        self.diode_wavelength = []
        self.sphere_current = []
        self.diode_power = []

        if self.use_powermeter:
            with open(self.flux_cal_file, "r") as df:
                for line in df.readlines():
                    line = line.strip()
                    if len(line) == 0 or line.startswith("#"):
                        continue
                    tokens = line.split("\t")
                    self.diode_wavelength.append(int(float(tokens[0]) + 0.5))
                    self.diode_power.append(float(tokens[1]))

        else:
            with open(self.diode_cal_file, "r") as df:
                for line in df.readlines():
                    line = line.strip()
                    if len(line) == 0 or line.startswith("#"):
                        continue
                    tokens = line.split("\t")
                    self.diode_wavelength.append(int(float(tokens[0]) + 0.5))
                    self.sphere_current.append(float(tokens[1]))
                    self.diode_current.append(float(tokens[2]))

            self.diode_qe = {}
            with open(self.diode_qe_file, "r") as dqf:
                for line in dqf.readlines():
                    line = line.strip()
                    if len(line) == 0 or line.startswith("#"):
                        continue
                    tokens = line.split("\t")
                    self.diode_qe[int(float(tokens[0]) + 0.5)] = float(tokens[1])

        startingfolder = azcam.utils.curdir()
        if self.overscan_correct or self.zero_correct or self.include_dark_images:
            # create analysis subfolder
            startingfolder, subfolder = azcam.utils.make_file_folder(subfolder)

            # copy all image files to analysis folder
            azcam.log("Making copy of image files for analysis")
            for filename in glob.glob(os.path.join(startingfolder, "*.fits")):
                shutil.copy(filename, subfolder)

            azcam.utils.curdir(subfolder)  # move for analysis folder - assume it already exists
        else:
            subfolder = startingfolder

        _, StartingSequence = azcam.utils.find_file_in_sequence(rootname)
        SequenceNumber = StartingSequence

        # scale by gain
        if azcam.db.tools["gain"].valid:
            self.system_gain = azcam.db.tools["gain"].system_gain
        else:
            azcam.log("WARNING: no gain values found for scaling")

        curfolder = azcam.utils.curdir()

        # bias level
        zerofilename = rootname + "%04d" % SequenceNumber
        zerofilename = os.path.join(curfolder, zerofilename) + ".fits"
        zmeans = azcam.fits.mean(zerofilename)

        # get sphere diode dark current from bias image
        if not self.use_powermeter:
            zerofilename = rootname + "%04d" % SequenceNumber
            zerofilename = os.path.join(curfolder, zerofilename) + ".fits"
            zmeans = azcam.fits.mean(zerofilename)
            try:
                spheredarkcurrent = float(azcam.fits.get_keyword(zerofilename, "REFCUR"))
            except Exception:
                spheredarkcurrent = 0.0

        nextfile = zerofilename  # just to start loop
        SequenceNumber = SequenceNumber + 1

        # loop through image files
        self.exposures = []  # exposure times as read from data
        self.throughputs = []
        self.wavelengths = []  # wavelengths as read from data
        self.qe = {}
        self.fluxes = []
        self.means = []
        while os.path.exists(nextfile):

            if self.include_dark_images:
                darkfilename = rootname + "%04d" % (SequenceNumber)
                darkfilename = os.path.join(curfolder, darkfilename) + ".fits"

                qefilename = rootname + "%04d" % (SequenceNumber + 1)
                qefilename = os.path.join(curfolder, qefilename) + ".fits"
            else:
                qefilename = rootname + "%04d" % SequenceNumber
                qefilename = os.path.join(curfolder, qefilename) + ".fits"

            wave = 0
            exptime = 0
            meantemp = -999
            spherecurrent = 0.0

            try:
                exptime = float(azcam.fits.get_keyword(qefilename, "EXPTIME"))
                wave = float(azcam.fits.get_keyword(qefilename, "WAVLNGTH"))
                wave = int(float(wave) + 0.5)
            except Exception:
                # try wavelength in OBJECT keyword for manual testing
                s = azcam.fits.get_keyword(qefilename, "OBJECT")
                wave = s.split(" ")[0]
                wave = int(float(wave) + 0.5)

            self.exposures.append(exptime)

            try:
                meantemp = float(azcam.fits.get_keyword(qefilename, "CAMTEMP"))
            except Exception:
                meantemp = -999.0

            try:
                spherecurrent = float(azcam.fits.get_keyword(qefilename, "REFCUR"))
                spherecurrent = abs(spherecurrent - spheredarkcurrent)
            except Exception:
                spherecurrent = 0.0

            try:
                bin1 = int(azcam.fits.get_keyword(qefilename, "CCDBIN1"))
                bin2 = int(azcam.fits.get_keyword(qefilename, "CCDBIN2"))
                binning = bin1 * bin2
            except Exception:
                binning = 1  # assume no keyword means no binning

            for idiode, w in enumerate(self.diode_wavelength):
                if int(w) >= int(wave):
                    break

            windowwaves = sorted(self.window_trans.keys())
            for w in windowwaves:
                if int(float(w) + 0.5) >= int(wave):
                    windowstrans = float(self.window_trans[w])
                    break

            self.throughputs.append(windowstrans)

            # bias or dark correct
            if self.include_dark_images:
                azcam.fits.sub(qefilename, darkfilename, qefilename)
            elif self.overscan_correct:
                azcam.fits.colbias(qefilename, fit_order=self.fit_order)

            # scale to electrons by system gain
            qeimage = Image(qefilename)

            if self.overscan_correct or self.include_dark_images:
                qeimage.set_scaling(self.system_gain, None)
            else:
                qeimage.set_scaling(self.system_gain, zmeans)
            qeimage.assemble(1)

            # write scaled images as fits files
            qeimage.save_data_format = -32
            qeimage.write_file(f"qeimage_{wave}_{exptime:03f}.fits", 6)

            # use mask from defects object
            if self.use_edge_mask:
                if not azcam.db.tools["defects"].valid:
                    self.masked_image = numpy.ma.masked_where(
                        azcam.db.tools["defects"].defects_mask, qeimage.buffer
                    )
                else:
                    azcam.db.tools["defects"].make_edge_mask(qeimage.buffer)
                    # fixme
                    # self.masked_image = azcam.db.tools["defects"].masked_image
                    self.masked_image = numpy.ma.masked_invalid(qeimage.buffer)
            else:
                self.masked_image = numpy.ma.masked_invalid(qeimage.buffer)

            if len(self.qeroi) == 0:
                qemean = self.masked_image.mean()
            else:
                # qemean=self.masked_image[self.qeroi[0]:self.qeroi[1],self.qeroi[2]:self.qeroi[3]].mean()
                maskedimage = self.masked_image[
                    self.qeroi[2] : self.qeroi[3], self.qeroi[0] : self.qeroi[1]
                ]
                qemean = numpy.ma.mean(maskedimage)

            # use either newport power meter or calibrated diode for standard
            if self.use_powermeter:
                # calculate diode power [W/cm]
                dpower = self.diode_power[idiode]
                # compute flux in photons/mm^2/sec from W/cm^2
                ephoton = h * c / (wave * 1.0e-9)
                dpower = dpower / ephoton / 100
                self.fluxes.append(dpower)
            else:
                # calculate diode current from reference current
                dcurrent = self.diode_current[idiode]
                # compute current cal diode current from sphere current
                diodecurrent = dcurrent
                diodecurrent = abs(diodecurrent) / self.diode_area  # diode amps/mm^2
                diodecurrent = (
                    diodecurrent
                    / self.diode_qe[wave]
                    / 1.602e-19
                    # diodecurrent / self.diode_qe[idiode] / 1.602e-19
                )  # diode photons/mm^2/sec
                self.fluxes.append(diodecurrent)
                dpower = diodecurrent

            detectorcurrent = (qemean / (exptime + self.exptime_offset)) / binning  # e/pixel/sec
            detectorcurrent = detectorcurrent / self.pixel_area  # e/mm^2/sec

            qe = (detectorcurrent / dpower) * self.cal_scale / windowstrans

            # QY correction
            qy = min(1.0, wave / 340.0)
            qe = qe * qy

            # global scale
            qe = qe * self.global_scale

            azcam.log(f"QE [{wave} nm] = {qe:.3f}")

            self.means.append(qemean)

            self.wavelengths.append(wave)
            self.qe[wave] = qe

            SequenceNumber = SequenceNumber + 1
            if self.include_dark_images:
                SequenceNumber = SequenceNumber + 1
            nextfile = os.path.join(curfolder, rootname + "%04d" % SequenceNumber) + ".fits"

        # analyze grades for each wavelength
        for wave in self.wavelengths:
            if self.qe_specs != {}:
                try:
                    if self.qe[wave] < self.qe_specs[wave]:
                        self.grade = "FAIL"
                        self.grades[wave] = "FAIL"
                    else:
                        self.grades[wave] = "PASS"
                except KeyError:
                    self.grades[wave] = "UNKNOWN"
            else:
                self.grades[wave] = "UNKNOWN"

        if self.grade_sensor:
            if "FAIL" in self.grades:
                self.grade = "FAIL"
            else:
                self.grade = "PASS"
            azcam.log("Grade = %s" % self.grade)
        else:
            self.grade = "UNDEFINED"

        self.mean_temp = meantemp  # not mean yet

        # plot results
        if self.create_plots:
            self.plot()

        # copy processed files to starting folder
        if startingfolder != subfolder:
            try:
                shutil.copy("qe.png", startingfolder)
            except Exception:
                pass

        # define dataset
        # "Flux @ sensor is Flux*Throughput/CalScal"
        # "Flux is [photons/sec/mm^2@diode]"

        self.dataset = {
            "data_file": self.data_file,
            "grade": self.grade,
            "cal_scale": self.cal_scale,
            "mean_temp": self.mean_temp,
            "wavelengths": self.wavelengths,
            "qe": self.qe,
            "means": self.means,
            "exposures": self.exposures,
            "fluxes": self.fluxes,
            "throughputs": self.throughputs,
            "system_gain": self.system_gain,
        }

        # write files
        azcam.utils.curdir(startingfolder)
        self.write_datafile()
        if self.create_reports:
            self.report()

        self.valid = True

        return

    def plot(self):
        """
        Plot QE data.
        """

        # setup figure
        bigfont = 18
        pbottom = 0.13
        ptop = 0.88
        pleft = 0.15
        pright = 0.95
        wspace = 0.2
        hspace = 0.2

        # make figure
        fig = azcam.plot.plt.figure()
        fignum = fig.number
        azcam.plot.move_window(fignum)
        if self.plot_title == "":
            fig.text(
                0.55,
                0.91,
                "Quantum Efficiency",
                horizontalalignment="center",
                fontsize=bigfont,
            )
        else:
            fig.text(
                0.55,
                0.91,
                f"{self.plot_title}",
                horizontalalignment="center",
                fontsize=bigfont,
            )
        fig.subplots_adjust(
            left=pleft,
            bottom=pbottom,
            right=pright,
            top=ptop,
            wspace=wspace,
            hspace=hspace,
        )
        ax = azcam.plot.plt.gca()
        ax.grid(1)
        azcam.plot.plt.xlabel("Wavelength [nm]", fontsize=bigfont)
        azcam.plot.plt.ylabel("Measured QE", fontsize=bigfont)

        ax.yaxis.set_major_locator(azcam.plot.plt.MaxNLocator(11))
        x = 2 * max(self.wavelengths) - min(self.wavelengths) + 1
        x = int(x / 100.0)
        ax.xaxis.set_major_locator(azcam.plot.plt.MaxNLocator(x))

        if self.mean_temp != -999:
            labels = [f"Mean Temp = {self.mean_temp:.0f} C"]
            ax.annotate(
                labels[0],
                xy=(0.6, 0.1),
                xycoords="axes fraction",
                horizontalalignment="left",
                verticalalignment="top",
            )

        # plot data
        waves = self.wavelengths
        qevals = []
        for w in waves:
            qevals.append(self.qe[w])
        azcam.plot.plt.errorbar(waves, [x * 100.0 for x in qevals], yerr=3.0, marker="o", ls="")

        if len(self.plot_limits) == 2:
            azcam.plot.plt.xlim(self.plot_limits[0][0], self.plot_limits[0][1])
            azcam.plot.plt.ylim(self.plot_limits[1][0], self.plot_limits[1][1])
        elif len(self.plot_limits) == 1:
            azcam.plot.plt.xlim(self.plot_limits[0][0], self.plot_limits[0][1])
        else:
            pass

        # plot specs
        if len(self.qe_specs) > 0:
            for wave in self.qe_specs:
                if self.qe_specs[wave] > 0:
                    x = wave
                    y = self.qe_specs[wave] * 100.0
                    azcam.plot.plt.plot(x, y, ls="", marker="_", markersize=5, color="red")

        # save figure
        azcam.plot.plt.show()
        azcam.plot.save_figure(fignum, "qe.png")

        return

    def report(self):
        """
        Make report files.
        """

        QEPLOT = "qe.png"

        lines = []

        lines.append("# Quantum Efficiency Analysis")
        # lines.append("")

        if self.grade != "UNDEFINED":
            s = "QE grade = %s" % self.grade
            lines.append(s)
            lines.append("")

        lines.append(f"![QE Plot]({os.path.abspath(QEPLOT)})  ")
        lines.append("")
        # lines.append("*QE Plot.*")
        # lines.append("")

        s = "|**Wavelength**|**QE**|**QE Spec.**|**Grade**|"
        lines.append(s)
        s = "|:---|:---:|:---:|:---:|"
        lines.append(s)
        for wave in self.wavelengths:
            if self.qe_specs != {}:
                try:
                    spec = self.qe_specs[wave]
                except KeyError:
                    spec = 0
            else:
                spec = 0
            grade = "" if self.grades[wave] == "UNKNOWN" else self.grades[wave]
            if spec == 0:
                s = f"{wave}|{self.qe[wave]:5.03f}||{grade}|"
            else:
                s = f"{wave}|{self.qe[wave]:5.03f}|{spec:5.03f}|{grade}|"
            lines.append(s)

        # Make report files
        self.write_report(self.report_file, lines)

        return
