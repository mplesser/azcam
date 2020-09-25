import numpy
import glob
import os
import shutil

import azcam
from azcam.console import api
import azcam.testers
from azcam.testers.basetester import Tester


class Dark(Tester):
    """
    Dark signal acquisition and analysis.
    """

    def __init__(self):

        super().__init__("dark")

        # acquisition
        self.exposure_type = "dark"
        self.number_images_acquire = 1
        self.exposure_time = -1
        self.overscan_correct = 1  # flag to overscan correct images
        self.zero_correct = 1  # flag to correct with bias residuals

        # analysis
        self.fit_order = 3  # order of overscan correction fit

        self.use_edge_mask = False  # flag True to use defects mask

        self.mean_dark_spec = -1  # spec on mean dark signal (e/pix/sec)

        self.dark_limit = -1  # spec on individual pixels (e/pixel/sec)
        self.dark_fraction = -1  # fraction of pixels required to be less than DarkLimit

        self.bright_pixel_reject = -1  # optionally reject bright pixels (e/pix/sec)

        # analysis outputs
        self.num_rejected_bright_pixels = 0  # number of bright pixels rejected
        self.mean_dark_signal = -1  # mean dark signal (e/pix/sec)
        self.median_dark_signal = -1  # median dark signal (e/pix/sec)

        self.dark_fraction_measured1 = -1
        self.dark_rate_measured1 = -1
        self.dark_fraction_measured2 = -1
        self.dark_rate_measured2 = -1
        self.means = []
        self.sdev = []
        self.hist_bins = []
        self.temperatures = []
        self.total_pixels = 0  # total non-masked pixels
        self.hist_values = []
        self.hist_fractions = []
        self.report_dark_per_hour = 1

        # analysis output files
        self.data_file = "dark.txt"
        self.report_file = "dark"
        self.dark_filename = "dark.fits"
        self.scaled_dark_filename = "darkscaled.fits"
        self.dark_reference_filename = "darkref.fits"

        self.full_hist_plot = "full_hist.png"
        self.cumm_hist_plot = "cumm_hist.png"
        self.darkimage_plot = "darkimage.png"
        self.report_plots = ["full_hist", "cumm_hist", "darkimage"]

    def acquire(self):
        """
        Acquire dark image sets (1 sec dark, long dark) for a dark current measurement.
        NumberImages is the number of iamge sets to take.
        ExposureTime is the exposure time of dark image in seconds.
        """

        azcam.log("Acquiring dark sequence")

        # save pars to be changed
        impars = {}
        api.save_imagepars(impars)

        # create new subfolder
        currentfolder, newfolder = azcam.utils.make_file_folder("dark")
        api.set_par("imagefolder", newfolder)

        # clear device
        api.tests()

        api.set_par("imageroot", "dark.")  # for automatic data analysis
        api.set_par("imageincludesequencenumber", 1)  # use sequence numbers
        api.set_par("imageautoname", 0)  # manually set name
        api.set_par("imageautoincrementsequencenumber", 1)  # inc sequence numbers
        api.set_par("imagetest", 0)  # turn off TestImage

        # loop through images
        for imgnum in range(self.number_images_acquire):

            # pre-dark bias
            api.set_par("imagetype", "dark")  # for GetFilename
            filename = os.path.basename(api.get_image_filename())
            azcam.log(f"Taking pre-dark image: {filename}")
            temp = api.get_temperature()
            azcam.log(f"Current temperatures: {temp}")
            api.expose(0, "zero", "pre-dark bias image")

            # take dark image
            api.set_par("imagetype", "dark")
            filename = os.path.basename(api.get_image_filename())
            azcam.log(
                f"Taking dark image {imgnum + 1} for {self.exposure_time:0.3f} seconds: {filename}"
            )
            temp = api.get_temperature()
            azcam.log(f"  Current temperatures: {temp}")
            api.expose(self.exposure_time, "dark", "dark image")

        # finish
        api.restore_imagepars(impars, currentfolder)
        azcam.log("Dark sequence finished")

        return

    def analyze(self):
        """
        Analyze an exisiting series zeros and darks for dark current measurement.
        """

        azcam.log("Analyzing dark signal")

        self.temperatures = []
        self.means = []
        self.gains = []
        rootname = "dark."
        subfolder = "analysis"

        # optionally copy files to analysis subfolder
        if self.overscan_correct or self.zero_correct:
            startingfolder, subfolder = azcam.utils.make_file_folder(subfolder)

            # copy all image files to analysis folder
            azcam.log("Making copy of image files for analysis")
            for filename in glob.glob(os.path.join(startingfolder, "*.fits")):
                shutil.copy(filename, subfolder)

            azcam.utils.curdir(subfolder)  # move for analysis folder
        else:
            startingfolder = azcam.utils.curdir()

        currentfolder = azcam.utils.curdir()

        # analyze a sequence
        _, StartingSequence = azcam.utils.find_file_in_sequence(rootname)

        # get gain and ROI
        self.system_gain = azcam.testers.gain.get_system_gain()
        self.roi = azcam.utils.get_image_roi()

        # get bias image
        zerofilename = rootname + f"{StartingSequence:04d}"
        zerofilename = os.path.join(currentfolder, zerofilename) + ".fits"

        NumExt, _, _ = azcam.fits.get_extensions(zerofilename)

        # get list of dark images
        darks = []
        seq = StartingSequence + 1  # pairs are bias then dark
        while True:
            df = os.path.join(currentfolder, rootname) + f"{seq:04d}.fits"
            if os.path.exists(df):
                darks.append(df)
                seq += 2
            else:
                break
        numdarks = len(darks)

        # median combine all dark images
        masterdark = self.dark_filename
        if numdarks == 1:
            s = f"One dark image found: {darks[0]}"
            shutil.copyfile(darks[0], masterdark)
            if self.overscan_correct:
                azcam.fits.colbias(masterdark, fit_order=self.fit_order)
        else:
            azcam.fits.combine(
                darks,
                masterdark,
                "median",
                overscan_correct=self.overscan_correct,
                fit_order=self.fit_order,
            )
            s = f"{numdarks} dark images have been combined into {masterdark}"
        azcam.log(s)

        # "debias" correct with residuals after colbias
        if self.zero_correct:
            debiased = azcam.testers.bias.debiased_filename
            biassub = "biassub.fits"
            azcam.fits.sub(masterdark, debiased, biassub)
            os.remove(masterdark)
            os.rename(biassub, masterdark)

        # get binning and temperature from header
        exptime = float(azcam.fits.get_keyword(masterdark, "EXPTIME"))
        try:
            self.temperature = float(azcam.fits.get_keyword(masterdark, "CAMTEMP"))
        except Exception:
            self.temperature = 999
        bin1 = azcam.fits.get_keyword(masterdark, "CCDBIN1")
        bin2 = azcam.fits.get_keyword(masterdark, "CCDBIN2")
        binned = int(bin1) * int(bin2)

        # create dark image
        self.darkimage = azcam.Image(masterdark)

        # set scale from gain
        history = azcam.fits.get_history(masterdark)
        if "SCALED" not in history:
            azcam.log("Scale by gain values")
            self.darkimage.set_scaling(self.system_gain, None)

        # Assemble dark for histogram
        self.darkimage.assemble(1)

        # save dark reference image, bias corrected and scaled to DN per second
        azcam.fits.mult(masterdark, 1.0 / exptime, self.dark_reference_filename)

        # scale darkimage data by exposure time and binning to get electrons per pixel per second
        self.darkimage.buffer = self.darkimage.buffer / binned / exptime

        # save gain scaled image
        self.darkimage.overwrite = 1
        self.darkimage.save_data_format = "float32"
        self.darkimage.write_file(self.scaled_dark_filename, 6)  # FITS

        # get total number of pixels image
        totalpixels = self.darkimage.buffer.shape[0] * self.darkimage.buffer.shape[1]

        # use mask from defects object (may be edge only)
        if self.use_edge_mask:
            if azcam.testers.defects.valid:
                self.MaskedImage = numpy.ma.masked_where(
                    azcam.testers.defects.defects_mask,
                    self.darkimage.buffer,
                )
            else:
                azcam.testers.defects.make_edge_mask(self.darkimage.buffer)
                self.MaskedImage = azcam.testers.defects.MaskedImage
        else:
            self.MaskedImage = numpy.ma.masked_invalid(self.darkimage.buffer)

        # optionally mask bright pixels
        if self.bright_pixel_reject != -1:
            self.MaskedImage = numpy.ma.masked_where(
                self.MaskedImage > self.bright_pixel_reject,
                self.MaskedImage,
                copy=False,
            )
            self.num_rejected_bright_pixels = totalpixels - numpy.ma.count(
                self.MaskedImage
            )
            azcam.log(
                f"Number of rejected bright pixels: {self.num_rejected_bright_pixels}"
            )

        # get number of pixels not masked
        self.total_pixels = numpy.ma.count(self.MaskedImage)

        # get mask alone
        self.Mask = numpy.ma.getmask(self.MaskedImage)

        # get valid data as 1D array
        self.validdata = self.MaskedImage.compressed()
        self.mean_dark_signal = self.validdata.mean()
        self.median_dark_signal = numpy.median(self.validdata)

        # PASS or FAIL on mean dark signal if specified
        if self.mean_dark_spec != -1:
            azcam.log(
                f"Mean dark signal is {self.mean_dark_signal:0.5f} e/pix/sec ({self.mean_dark_signal * 3600.0:0.1f} e/pix/hr)"
            )
            azcam.log(
                f"Mean dark signal spec is {self.mean_dark_spec:0.5f} e/pix/sec ({self.mean_dark_spec * 3600.0:0.1f} e/pix/hr)"
            )
            if self.mean_dark_signal > self.mean_dark_spec:
                self.grade = "FAIL"
            else:
                self.grade = "PASS"

        if not self.grade_sensor:
            self.grade = "UNDEFINED"

        # setup histogram
        # numbins = self.validdata.max() * 1000.0

        # report on dark signal historgram if DarkFraction specified
        if self.dark_fraction != -1:
            # hist, bins = numpy.histogram(self.validdata, bins=int(numbins) - 1)  # values and bins
            hist, bins = numpy.histogram(self.validdata, bins="auto")  # values and bins

            self.hist_values = hist
            self.hist_bins = bins

            histsum = 0.0
            self.dark_fraction_measured2 = 0
            for bnum, histvalue in enumerate(hist):  # bins are less than bnum+1 value
                binvalue = bins[bnum + 1]
                histsum += histvalue
                frac = histsum / self.total_pixels
                if frac >= self.dark_fraction:
                    s = f"{frac * 100:0.2f} of pixels are below {binvalue:0.4f} e/pix/sec"
                    azcam.log(s)
                    self.dark_fraction_measured2 = frac
                    self.dark_rate_measured2 = binvalue
                    break

            # compare to specification
            histsum = 0.0
            self.hist_bins = []
            self.hist_values = []
            self.hist_fractions = []
            REPORT = True
            for bnum, histvalue in enumerate(hist):  # bins are less than bnum+1 value
                binvalue = bins[bnum + 1]
                histsum += histvalue
                frac = histsum / self.total_pixels
                if binvalue > 0:
                    self.hist_bins.append(binvalue)
                    self.hist_values.append(histvalue)
                    self.hist_fractions.append(frac)
                if binvalue >= self.dark_limit and REPORT:
                    self.dark_fraction_measured1 = frac
                    self.dark_rate_measured1 = binvalue
                    s1 = f"{self.dark_fraction_measured1 * 100:0.2f} of pixels are below {self.dark_rate_measured1:0.4f} e/pix/sec"
                    azcam.log(s1)
                    REPORT = False  # stop checking
                    if frac >= self.dark_fraction:
                        self.grade = "PASS"
                    else:
                        self.grade = "FAIL"

        azcam.log(f"Grade = {self.grade}")

        if self.create_plots:
            self.plot()

        # set absolute filenames
        self.dark_filename = os.path.abspath(self.dark_filename)
        self.scaled_dark_filename = os.path.abspath(self.scaled_dark_filename)
        self.dark_reference_filename = os.path.abspath(self.dark_reference_filename)
        self.darkimage_plot = os.path.abspath(self.darkimage_plot)
        self.full_hist_plot = os.path.abspath(self.full_hist_plot)
        self.full_hist_plot = os.path.abspath(self.full_hist_plot)

        # copy processed dark file starting folder
        if startingfolder != subfolder:
            shutil.copy(self.dark_filename, startingfolder)
            shutil.copy(self.scaled_dark_filename, startingfolder)
            shutil.copy(self.dark_reference_filename, startingfolder)
            if self.create_plots:
                shutil.copy(self.darkimage_plot, startingfolder)
                shutil.copy(self.full_hist_plot, startingfolder)
                shutil.copy(self.cumm_hist_plot, startingfolder)

        # define dataset
        self.dataset = {
            "data_file": self.data_file,
            "grade": self.grade,
            "temperature": self.temperature,
            "total_pixels": float(self.total_pixels),
            "mean_dark_signal": float(self.mean_dark_signal),
            "dark_fraction_measured1": float(self.dark_fraction_measured1),
            "dark_rate_measured1": float(self.dark_rate_measured1),
            "dark_fraction_measured2": float(self.dark_fraction_measured2),
            "dark_rate_measured2": float(self.dark_rate_measured2),
            "hist_bins": numpy.array(self.hist_bins).tolist(),
            "hist_fractions": numpy.array(self.hist_fractions).tolist(),
            "hist_values": numpy.array(self.hist_values).tolist(),
        }

        # write output files
        azcam.utils.curdir(startingfolder)
        self.write_datafile()
        if self.create_reports:
            self.report()

        # finish
        self.valid = True

        return

    def plot(self):
        """
        Plot analysis results.
        """

        # plot dark image
        fig = azcam.plot.plt.figure()
        fignum = fig.number
        azcam.plot.move_window(fignum)
        # darkimage.plot()
        azcam.plot.plot_image(self.darkimage)
        azcam.plot.plt.title("Combined Dark Image")
        azcam.plot.plt.show()
        azcam.plot.save_figure(fignum, self.darkimage_plot)

        # plot cummulative histogram
        fig = azcam.plot.plt.figure()
        fignum = fig.number
        azcam.plot.move_window(fignum)
        azcam.plot.plt.hist(
            self.validdata, bins="auto", density=1, histtype="step", cumulative=True
        )
        ax = azcam.plot.plt.gca()
        ax.set_xlabel("Dark Signal [e/pix/sec]")
        ax.set_ylabel("Pixel Fraction")
        azcam.plot.plt.ylim(0.5, 1.0)
        ax.set_yticks(
            [0.50, 0.55, 0.60, 0.65, 0.70, 0.75, 0.80, 0.85, 0.90, 0.95, 1.00]
        )
        azcam.plot.plt.xlim(0.0, self.mean_dark_signal * 10.0)

        if self.mean_dark_spec != -1:
            azcam.plot.plt.axvline(
                x=self.mean_dark_signal, linestyle="-", color="green", label="Mean"
            )
            azcam.plot.plt.legend(loc="upper right")
            azcam.plot.plt.axvline(
                x=self.mean_dark_spec, linestyle="--", color="red", label="Spec"
            )
            azcam.plot.plt.legend(loc="upper right")
        if self.dark_limit != -1:
            azcam.plot.plt.axhline(
                y=self.dark_fraction, linestyle="--", color="red", label="Fraction"
            )
            azcam.plot.plt.axvline(
                x=self.dark_limit, linestyle="--", color="blue", label="Limit"
            )
            azcam.plot.plt.legend(loc="upper right")

        azcam.plot.plt.title("Dark Signal Cummulative Histogram")
        azcam.plot.plt.show()
        azcam.plot.save_figure(fignum, self.cumm_hist_plot)

        # plot full signal histogram
        fig = azcam.plot.plt.figure()
        fignum = fig.number
        azcam.plot.move_window(fignum)
        # xmax = min(self.mean_dark_signal * 10.0, self.validdata.max())
        # azcam.plot.plt.hist(self.validdata, "auto", histtype="step", log=True)
        xmax = self.mean_dark_signal * 100.0
        histvals = self.validdata[self.validdata < xmax]
        azcam.plot.plt.hist(histvals, range=[0.0, xmax], histtype="step", log=True)
        ax = azcam.plot.plt.gca()
        ax.set_xlabel("Dark Signal [e/pix/sec]")
        ax.set_ylabel("Pixels")
        azcam.plot.plt.title("Dark Signal Histogram")
        azcam.plot.plt.ylim(1.0)
        if self.mean_dark_spec != -1:
            azcam.plot.plt.axvline(
                x=self.mean_dark_signal, linestyle="-", color="green", label="Mean"
            )
            azcam.plot.plt.legend(loc="upper right")
            ax.annotate(
                f"{self.mean_dark_signal:0.5f}",
                xy=(self.mean_dark_signal, 10000),
                xytext=(0, 0),
                ha="center",
                textcoords="offset points",
            )
        azcam.plot.plt.show()
        azcam.plot.save_figure(fignum, self.full_hist_plot)

        return

    def report(self):
        """
        Write report file.
        """

        lines = ["# Dark Signal Analysis", ""]

        if self.grade != "UNDEFINED":
            s = f"Dark signal grade = {self.grade}  "
            lines.append(s)

        if self.dark_fraction != -1:
            s = f"{self.dark_fraction_measured1 * 100:0.1f} of pixels are below {self.dark_rate_measured1:0.3f} e/pix/sec  "
            lines.append(s)
            s = f"{self.dark_fraction_measured2 * 100:0.1f} of pixels are below {self.dark_rate_measured2:0.3f} e/pix/sec   "
            lines.append(s)

        if self.mean_dark_spec != -1:
            if self.report_dark_per_hour:
                s = f"Mean dark signal is {self.mean_dark_signal:0.5f} e/pix/sec ({self.mean_dark_signal * 3600.0:0.1f} e/pix/hr)  "
            else:
                s = f"Mean dark signal is {self.mean_dark_signal:0.5f} e/pix/sec  "
            lines.append(s)
            if self.report_dark_per_hour:
                s = f"Dark signal spec is {self.mean_dark_spec:0.5f} e/pix/sec ({self.mean_dark_spec * 3600.0:0.1f} e/pix/hr)  "
            else:
                s = f"Dark signal spec is {self.mean_dark_spec:0.5f} e/pix/sec  "

        lines.append("")
        if "cumm_hist" in self.report_plots:
            lines.append(
                f"![Cumulative Histogram]({os.path.abspath(self.cumm_hist_plot)})  "
            )
            lines.append("*Cumulative Histogram.*")
            lines.append("")

        if "full_hist" in self.report_plots:
            lines.append(f"![Full Histogram]({os.path.abspath(self.full_hist_plot)})  ")
            lines.append("*Full Histogram.*")
            lines.append("")

        if "darkimage" in self.report_plots:
            lines.append(f"![Dark Image]({os.path.abspath(self.darkimage_plot)})  ")
            lines.append("*Dark Image.*")
            lines.append("")

        # Make report files
        self.write_report(self.report_file, lines)

        return
