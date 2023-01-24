import os
import shutil
import time

import azcam
from azcam.tools.testers.basetester import Tester


class Bias(Tester):
    """
    Bias (zero) image acquisition and analysis.
    """

    def __init__(self):

        super().__init__("bias")

        #: combination method
        self.combination_type = "median"
        #: combined image with no colbias
        self.superbias_filename = "superbias.fits"
        #: residual image after combined and colbiased
        self.debiased_filename = "debiased.fits"
        #: order of overscan correction fit, 0 => row by row
        self.fit_order = 3

        self.mean = []
        self.sdev = []
        self.means = []
        self.sdevs = []
        self.imagelist = []

        #: output data file
        self.data_file = "bias.txt"
        #: output report file
        self.report_file = "bias"

        #: delay between exposures [sec]
        self.delay = 0.0

    def acquire(self):
        """
        Acquire bias image sets for bias measurement.
        """

        azcam.log("Acquiring bias sequence")

        # save pars to be changed
        impars = {}
        azcam.utils.save_imagepars(impars)

        # create new subfolder
        currentfolder, newfolder = azcam.utils.make_file_folder("bias")
        azcam.db.parameters.set_par("imagefolder", newfolder)

        # clear device
        azcam.db.tools["exposure"].test(0)

        azcam.db.parameters.set_par("imageroot", "bias.")  # for automatic data analysis
        azcam.db.parameters.set_par(
            "imageincludesequencenumber", 1
        )  # use sequence numbers
        azcam.db.parameters.set_par("imageautoname", 0)  # manually set name
        azcam.db.parameters.set_par(
            "imageautoincrementsequencenumber", 1
        )  # inc sequence numbers
        azcam.db.parameters.set_par("imagetest", 0)  # turn off TestImage

        # take bias images
        azcam.db.parameters.set_par("imagetype", "zero")  # for get_image_filename()
        for i in range(self.number_images_acquire):
            filename = os.path.basename(azcam.db.tools["exposure"].get_filename())
            azcam.log(f"Taking bias image {i + 1}/{self.number_images_acquire}: {filename}")
            azcam.db.tools["exposure"].expose(0, "zero", "bias image")
            if i < self.number_images_acquire - 1:
                time.sleep(self.delay)

        # finish
        azcam.utils.restore_imagepars(impars, currentfolder)
        azcam.log("Bias sequence finished")

        return

    def analyze(self):
        """
        Analyze an existing bias series.

        Creates a superbias and a debiased image.
        The superbias image is the median combined iamge and the debiased image
        is then overscan corrected.
        """

        azcam.log("Analyzing bias sequence")

        rootname = "bias."

        # reset parameters
        self.means = []
        self.sdevs = []
        self.mean = []
        self.sdev = []
        self.imagelist = []
        self.superbias_filename = "superbias.fits"
        self.debiased_filename = "debiased.fits"

        startingfolder = azcam.utils.curdir()
        _, starting_sequence = azcam.utils.find_file_in_sequence(rootname)
        sequence_number = starting_sequence

        # ROI is  for mean and sdev
        self.roi = azcam.utils.get_image_roi()

        # get first filename
        zerofilename = rootname + f"{starting_sequence:04d}"
        zerofilename = os.path.join(startingfolder, zerofilename) + ".fits"
        nextfile = zerofilename

        # all images must have same image sections
        numext, first_ext, last_ext = azcam.fits.get_extensions(zerofilename)

        # find the names, means, sdevs of all images
        while os.path.exists(nextfile):

            self.imagelist.append(nextfile)

            mean, sdev, _ = azcam.fits.stat(nextfile, self.roi[0])  # use first ROI not overscan
            mr = []
            sr = []
            for _ in range(first_ext, last_ext):
                mr.append(mean)
                sr.append(sdev)

            self.means.append(mean)
            self.sdevs.append(sdev)

            sequence_number = sequence_number + 1
            nextfile = os.path.join(startingfolder, rootname + f"{sequence_number:04d}") + ".fits"

        # make superbias (median combined with no overscan correction)
        azcam.log(f"Creating superbias image: {self.superbias_filename}")
        azcam.fits.combine(
            self.imagelist,
            self.superbias_filename,
            "median",
            overscan_correct=0,
        )

        # get mean values over all images for each image section
        numext = max(1, numext)
        self.mean = numext * [0.0]
        self.sdev = numext * [0.0]
        for imagemean in self.means:  # imagemean is a list for each image
            for imsec, imsectionmean in enumerate(imagemean):
                self.mean[imsec] += imsectionmean
        for imagesdev in self.sdevs:  # imagesdev is a list for each image
            for imsec, imsectionsdev in enumerate(imagesdev):
                self.sdev[imsec] += imsectionsdev

        lm = len(self.means)
        self.mean = [float(m / lm) for m in self.mean]
        self.sdev = [float(s / lm) for s in self.sdev]

        # make debiased image (superbias with colbias)
        azcam.log(f"Creating debiased image: {self.debiased_filename}")
        shutil.copy(self.superbias_filename, self.debiased_filename)

        azcam.fits.colbias(self.debiased_filename, self.fit_order)

        # save absolute filenames
        self.debiased_filename = os.path.abspath(self.debiased_filename)
        self.superbias_filename = os.path.abspath(self.superbias_filename)

        # define dataset
        self.dataset = {
            "data_file": self.data_file,
            "grade": self.grade,
            "mean": self.mean,
            "sdev": self.sdev,
            "debiased_filename": self.debiased_filename,
            "superbias_filename": self.superbias_filename,
            "means": self.means,
            "sdevs": self.sdevs,
        }

        # write output files
        azcam.utils.curdir(startingfolder)
        self.write_datafile()
        if self.create_reports:
            self.report()

        # finish
        self.valid = 1

        return

    def report(self):
        """
        Write bias report file.
        """

        lines = ["# Bias Analysis", ""]

        if self.grade != "UNDEFINED":
            lines.append(f"Bias grade = {self.grade}")
            lines.append("")

        s = "|**Channel**|**Mean (DN)**|**Noise (DN)**|"
        lines.append(s)
        s = "|:---|:---:|:---:|"
        lines.append(s)

        for chan in range(len(self.mean)):
            s = f"|{chan:02d}|{self.mean[chan]:.0f}|{self.sdev[chan]:.01f}|"
            lines.append(s)

        # Make report files
        self.write_report(self.report_file, lines)

        return
