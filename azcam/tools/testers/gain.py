import math
import os
import shutil

import numpy

import azcam
from azcam.tools.testers.basetester import Tester
from astropy.io import fits as pyfits


class Gain(Tester):
    """
    Acquire and analyze gain (PTC point) data.
    """

    def __init__(self):

        super().__init__("gain")

        self.exposure_type = "flat"
        self.exposure_time = -1
        self.exposure_level = -1  # exposure_level in electrons/pixel, -1 do not used
        self.number_pairs = 1
        self.overwrite = 0
        self.wavelength = -1  # -1 do not change wavelength
        self.video_processor_gain = []  # uV/DN for each channel
        self.system_noise_correction = []  # camera noise (no sensor) in DN

        self.include_dark_images = 0  # include dark images in acquire & analysis
        self.dark_frame = None

        self.clear_arrray = 0

        self.readnoise_spec = -1  # read noise spec (max) in electrons

        self.data_file = "gain.txt"
        self.report_file = "gain"

        self.imagefolder = ""
        self.image_zero = ""
        self.image_flat1 = ""
        self.image_flat2 = ""

        # outputs
        self.system_gain = []
        self.noise = []
        self.mean = []
        self.sdev = []
        self.zero_mean = []
        self.sensitivity = []

    def find(self):
        """
        Acquire and Analyze a PTC point for find gain, noise, scale, and offset.
        Does not create a report during analysis.
        """

        createreport = self.create_reports
        self.create_reports = 0

        self.acquire()

        cd = azcam.utils.curdir()
        azcam.utils.curdir(self.imagefolder)

        self.analyze()

        self.create_reports = createreport

        azcam.utils.curdir(cd)

        return

    def acquire(self):
        """
        Acquire a bias image and two flat field images to generate a PTC point.
        ExposureTime is the exposure time in seconds.
        """

        azcam.log("Acquiring gain sequence")

        if self.exposure_time == -1:
            ExposureTime = azcam.db.tools["exposure"].get_exposuretime()
            azcam.log(f"Exposure time not specified, using current value of {ExposureTime:0.3f}")
        else:
            ExposureTime = self.exposure_time

        # save pars to be changed
        impars = {}
        azcam.utils.save_imagepars(impars)

        # create new subfolder
        if self.overwrite:
            if os.path.exists("gain"):
                shutil.rmtree("gain")
        currentfolder, subfolder = azcam.utils.make_file_folder("gain")
        azcam.db.parameters.set_par("imagefolder", subfolder)

        self.imagefolder = subfolder

        azcam.db.parameters.set_par("imageincludesequencenumber", 1)
        azcam.db.parameters.set_par("imageautoincrementsequencenumber", 1)
        azcam.db.parameters.set_par("imageautoname", 0)  # manually set name
        azcam.db.parameters.set_par("imagetest", 0)  # turn off TestImage
        azcam.db.parameters.set_par("imageoverwrite", 1)

        # clear device
        if self.clear_arrray:
            azcam.db.tools["exposure"].test(0)

        # set wavelength
        if self.wavelength > 0:
            wave = int(self.wavelength)
            wave1 = azcam.db.tools["instrument"].get_wavelength()
            wave1 = int(wave1)
            if wave1 != wave:
                azcam.log(f"Setting wavelength to {wave} nm")
                azcam.db.tools["instrument"].set_wavelength(wave)
                wave1 = azcam.db.tools["instrument"].get_wavelength()
                wave1 = int(wave1)
            azcam.log(f"Current wavelength is {wave1} nm")

        azcam.db.parameters.set_par("imageroot", "ptc.")
        for loop in range(self.number_pairs):

            if self.number_pairs > 1:
                azcam.log(f"Starting gain sequence {loop + 1}/{self.number_pairs}")

            # bias image
            azcam.db.parameters.set_par("imagetype", "zero")
            zerofilename = azcam.db.tools["exposure"].get_filename()
            self.image_zero = zerofilename
            azcam.log("Taking bias exposure")
            azcam.db.tools["exposure"].expose(0, "zero", "PTC bias")

            # take dark
            if self.include_dark_images:
                self.dark_frame = azcam.db.tools["exposure"].get_filename()
                azcam.db.tools["exposure"].expose(ExposureTime, "dark", "PTC dark")

            # take flats
            azcam.db.parameters.set_par("imagetype", self.exposure_type)
            azcam.log(f"Taking two flats for {ExposureTime:0.3f} seconds")
            flat1filename = azcam.db.tools["exposure"].get_filename()
            self.image_flat1 = flat1filename
            azcam.db.tools["exposure"].expose(ExposureTime, self.exposure_type, "PTC frame 1")
            azcam.log("Image 1 finished")
            flat2filename = azcam.db.tools["exposure"].get_filename()
            self.image_flat2 = flat2filename
            azcam.db.tools["exposure"].expose(ExposureTime, self.exposure_type, "PTC frame 2")
            azcam.log("Image 2 finished")

        # finish
        azcam.utils.restore_imagepars(impars, currentfolder)
        azcam.log("Gain sequence finished")

        return

    def analyze(self):
        """
        Analyze a bias image and two flat field images to generate a PTC point.
        """

        azcam.log("Analyzing gain sequence")

        rootname = "ptc."

        # bias image
        _, StartingSequence = azcam.utils.find_file_in_sequence(rootname)
        zerofilename = rootname + f"{StartingSequence:04d}"
        zerofilename = azcam.utils.make_image_filename(zerofilename)
        SequenceNumber = StartingSequence

        NumExt, _, _ = azcam.fits.get_extensions(zerofilename)
        NumExt = max(1, NumExt)

        # get ROI
        self.roi = azcam.utils.get_image_roi()
        if len(self.roi) == 1:
            self.roi.append(self.roi[0])

        # these will be mean values if more than one sequence is analyzed
        self.system_gain = [0] * NumExt
        self.noise = [0] * NumExt
        self.mean = [0] * NumExt
        self.sdev = [0] * NumExt
        self.zero_mean = [0] * NumExt
        self.sensitivity = [0] * NumExt

        loop = 0
        while os.path.exists(zerofilename):
            loop += 1

            SequenceNumber += 1

            if self.include_dark_images:
                darkfilename = rootname + f"{SequenceNumber:04d}"
                darkfilename = darkfilename + ".fits"
                SequenceNumber += 1
            else:
                darkfilename = None

            flat1filename = rootname + f"{SequenceNumber:04d}"
            flat1filename = azcam.utils.make_image_filename(flat1filename)
            SequenceNumber += 1
            flat2filename = rootname + f"{SequenceNumber:04d}"
            flat2filename = azcam.utils.make_image_filename(flat2filename)

            # ExposureTime = float(azcam.fits.get_keyword(flat1filename, "EXPTIME"))

            gain, noise, mean, sdev = self.measure_gain(
                zerofilename, flat1filename, flat2filename, darkfilename
            )

            # correct readnoise
            if self.system_noise_correction != []:
                for chan in range(NumExt):
                    rn = math.sqrt(
                        noise[chan] ** 2 - gain[chan] * self.system_noise_correction[chan] ** 2
                    )
                    noise[chan] = rn

            self.system_gain = [a + b for a, b in zip(self.system_gain, gain)]
            self.noise = [a + b for a, b in zip(self.noise, noise)]
            self.mean = [a + b for a, b in zip(self.system_gain, mean)]
            self.sdev = [a + b for a, b in zip(self.sdev, sdev)]

            # get zero mean for Offset
            zeromean = azcam.fits.mean(zerofilename, self.roi[1])
            self.zero_mean = [a + b for a, b in zip(self.zero_mean, zeromean)]

            azcam.log("Channel system_gain[e/DN] Noise[e]")
            for i in range(len(self.system_gain)):
                azcam.log(f"{i:02d}      {gain[i]:0.02f}             {noise[i]:0.01f}")

            SequenceNumber = SequenceNumber + 1
            zerofilename = rootname + f"{SequenceNumber:04d}"
            zerofilename = azcam.utils.make_image_filename(zerofilename)

        # get means from sums
        self.system_gain = [x / loop for x in self.system_gain]
        self.noise = [x / loop for x in self.noise]
        self.mean = [x / loop for x in self.mean]
        self.sdev = [x / loop for x in self.sdev]
        self.zero_mean = [x / loop for x in self.zero_mean]

        # set grade based on read noise only
        if self.readnoise_spec != -1:
            self.grade = "PASS"
            for rn in self.noise:
                if rn > self.readnoise_spec:
                    self.grade = "FAIL"
                    break

        if self.video_processor_gain != []:
            for chan, gain in enumerate(self.system_gain):
                self.sensitivity[chan] = self.video_processor_gain[chan] / gain

        # define dataset
        self.dataset = {
            "data_file": self.data_file,
            "grade": self.grade,
            "system_noise_correction": self.system_noise_correction,
            "system_gain": self.system_gain,
            "noise": self.noise,
            "mean": self.mean,
            "sdev": self.sdev,
            "zero_mean": self.zero_mean,
            "sensitivity": self.sensitivity,
        }

        # write output files
        self.write_datafile()
        if self.create_reports:
            self.report()

        # finish
        self.valid = 1

        return

    def measure_gain(self, Zero, Flat1, Flat2, Dark=None):
        """
        Calculate gain and noise from a bias and photon transfer image pair.
        """

        Zero = azcam.utils.make_image_filename(Zero)
        Flat1 = azcam.utils.make_image_filename(Flat1)
        Flat2 = azcam.utils.make_image_filename(Flat2)

        if Dark is not None:
            Dark = azcam.utils.make_image_filename(Dark)

        # extensions are elements 1 -> NumExt
        NumExt, first_ext, last_ext = azcam.fits.get_extensions(Zero)
        if NumExt == 0:
            data_ffci = []
            gain = []
            noise = []
            flat_mean = []
            ffci_sdev = []
            NumExt = 1
        elif NumExt == 1:
            data_ffci = [0]
            gain = [0]
            noise = [0]
            flat_mean = [0]
            ffci_sdev = [0]
        else:
            data_ffci = [0]
            gain = [0]
            noise = [0]
            flat_mean = [0]
            ffci_sdev = [0]

        # get ROI
        self.roi = azcam.utils.get_image_roi()

        # get zero mean and sigma
        zmean = azcam.fits.mean(Zero, self.roi[1])
        zsdev = azcam.fits.sdev(Zero, self.roi[1])

        if self.include_dark_images:
            dmean = azcam.fits.mean(Dark, self.roi[0])

        # get flat mean for each extension
        fmean = azcam.fits.mean(Flat1, self.roi[0])
        for ext in range(first_ext, last_ext):
            if self.include_dark_images:
                flat_mean.append(fmean[ext - 1] - dmean[ext - 1])
            else:
                flat_mean.append(fmean[ext - 1] - zmean[ext - 1])

        # open files
        imf1 = pyfits.open(Flat1)
        imf2 = pyfits.open(Flat2)
        if self.include_dark_images:
            dark1 = pyfits.open(Dark)

        # make ffci data
        #   order is .data[] order, not EXT/IM order
        for ext in range(first_ext, last_ext):
            imf1[ext].data = imf1[ext].data.astype("float32")
            imf2[ext].data = imf2[ext].data.astype("float32")
            if self.include_dark_images:
                dark1[ext].data = dark1[ext].data.astype("float32")
                data_ffci.append(imf1[ext].data - dark1[ext].data)
            else:
                data_ffci.append(imf1[ext].data - imf2[ext].data)

        imf1.close()
        imf2.close()

        # get stats in same ROI of each section
        roi = self.roi[0]
        for ext in range(first_ext, last_ext):
            ffci_sdev.append(
                data_ffci[ext][roi[2] : roi[3], roi[0] : roi[1]].std() / math.sqrt(2.0)
            )
            try:
                g = flat_mean[ext] / (ffci_sdev[ext] ** 2 - zsdev[ext - 1] ** 2)
                if numpy.isnan(g):
                    gain.append(0.0)
                else:
                    gain.append(g)
            except Exception as message:
                azcam.log(message)
                gain.append(0.0)
            noise.append(gain[ext] * zsdev[ext - 1])

        if len(gain) > 1:
            return [
                gain[1:],
                noise[1:],
                flat_mean[1:],
                ffci_sdev[1:],
            ]  # these are all lists
        else:
            return [gain, noise, flat_mean, ffci_sdev]  # these are all lists

    def get_system_gain(self):
        """
        Returns the system gain.
        """

        if self.valid:
            if self.system_gain == []:
                self.analyze()
        else:
            self.read_datafile()

        return self.system_gain

    def report(self):
        """
        Make report files.
        """

        lines = []

        lines.append("# Gain Analysis")
        lines.append("")

        if self.system_noise_correction == []:
            s = "Read Noise in electrons IS NOT system noise corrected"
            lines.append(s)
            lines.append("")
        else:
            s = "Read Noise in electrons IS system noise corrected"
            lines.append(s)
            lines.append("")
            mean = numpy.array(self.system_noise_correction).mean()
            s = f"Mean system noise correction = {mean:5.01f} DN"
            lines.append(s)
            lines.append("")

        if self.grade != "UNDEFINED":
            s = f"Gain grade = {self.grade}"
            lines.append(s)
            lines.append("")

        if self.readnoise_spec != -1:
            s = f"Read noise spec = {self.readnoise_spec:5.1f} electrons"
            lines.append(s)
            lines.append("")

        s = "|**Channel**|**Gain [e/DN]**|**Noise [e]**|**Sens. [uV/e]**|**Bias[DN]**|"
        lines.append(s)
        s = "|:---|:---:|:---:|:---:|:---:|"
        lines.append(s)

        for chan in range(len(self.system_gain)):
            s = f"|{chan:02d}|{self.system_gain[chan]:5.02f}|{self.noise[chan]:5.01f}|{self.sensitivity[chan]:5.02f}|{self.zero_mean[chan]:7.01f}|"
            lines.append(s)

        # Make report files
        self.write_report(self.report_file, lines)

        return

    def fe55_gain(self):
        """
        Set gain.system_gain to azcam.db.tools["fe55"].system_gain values.
        """

        self.system_gain = azcam.db.tools["fe55"].system_gain

        return
