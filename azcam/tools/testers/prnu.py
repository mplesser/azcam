import glob
import os
import shutil

import numpy

import azcam
from azcam.image import Image
from azcam.tools.testers.basetester import Tester


class Prnu(Tester):
    """
    Photo-Response Non-Uniformity (PRNU) acquisition and analysis.
    """

    def __init__(self):

        super().__init__("prnu")

        self.exposure_type = "flat"
        self.root_name = "prnu."  # allow for analyzing QE data
        self.allowable_deviation_from_mean = -1  # allowable deviation from mean signal
        self.exposures = {}  # dictionary of {wavelength:exposure times}
        self.use_edge_mask = False  # flag to use defects exclusion mask
        self.grades = {}  # Pass/Fail grades at each wavelength {wave:grade}

        self.fit_order = 3  # order of overscan correction fit

        self.bias_image_in_sequence = 1  # flag true if first image is a bias image

        self.overscan_correct = 0  # flag to overscan correct images
        self.zero_correct = 0  # flag to correct with bias residuals

        self.wavelengths = []  # wavelengths

        # outputs
        self.prnu_file = ""
        self.Prnus = {}  # PRNU at each image in sequence {wavelength:PRNU}

        self.data_file = "prnu.txt"
        self.report_file = "prnu"

    def acquire(self):
        """
        Acquire a bias image and one or more flats for PRNU analysis.
        ExposureTimes and Wavelengths are read from ExposuresFile text file.
        """

        azcam.log("Acquiring PRNU sequence")

        # save pars to be changed
        impars = {}
        azcam.utils.save_imagepars(impars)

        # create new subfolder
        currentfolder, newfolder = azcam.utils.make_file_folder("prnu")
        azcam.db.parameters.set_par("imagefolder", newfolder)

        # clear device
        azcam.db.tools["exposure"].test(0)

        azcam.db.parameters.set_par("imageroot", "prnu.")  # for automatic data analysis
        azcam.db.parameters.set_par(
            "imageincludesequencenumber", 1
        )  # use sequence numbers
        azcam.db.parameters.set_par("imageautoname", 0)  # manually set name
        azcam.db.parameters.set_par(
            "imageautoincrementsequencenumber", 1
        )  # inc sequence numbers
        azcam.db.parameters.set_par("imagetest", 0)  # turn off TestImage

        # bias image
        azcam.db.parameters.set_par("imagetype", "zero")
        filename = os.path.basename(azcam.db.tools["exposure"].get_filename())
        azcam.log("Taking PRNU bias: %s" % filename)
        azcam.db.tools["exposure"].expose(0, "zero", "PRNU bias")

        waves = list(self.exposures.keys())
        waves.sort()
        for wave in waves:
            wavelength = float(wave)
            exposuretime = self.exposures[wave]

            if wavelength > 0:
                azcam.log(f"Moving to wavelength: {int(wavelength)}")
                azcam.db.tools["instrument"].set_wavelength(wavelength)
                wave = azcam.db.tools["instrument"].get_wavelength()
                wave = int(wave)
                azcam.log(f"Current wavelength: {wave}")
            filename = os.path.basename(azcam.db.tools["exposure"].get_filename())
            azcam.log(f"Taking PRNU image for {exposuretime:.3f} seconds at {wavelength:.1f} nm")
            azcam.db.tools["exposure"].expose(
                exposuretime, self.exposure_type, f"PRNU image {wavelength:.1f} nm"
            )

        # finish
        azcam.utils.restore_imagepars(impars, currentfolder)
        azcam.log("PRNU sequence finished")

        return

    def analyze(self):
        """
        Analyze an existing PRNU image sequence for LSST.
        """

        azcam.log("Analyzing PRNU sequence")

        rootname = self.root_name
        self.grade = "UNDEFINED"
        subfolder = "analysis"
        self.images = []

        startingfolder = azcam.utils.curdir()

        if self.overscan_correct or self.zero_correct:
            # create analysis subfolder
            startingfolder, subfolder = azcam.utils.make_file_folder(subfolder)

            # copy all image files to analysis folder
            azcam.log("Making copy of image files for analysis")
            for filename in glob.glob(os.path.join(startingfolder, "*.fits")):
                shutil.copy(filename, subfolder)

            azcam.utils.curdir(subfolder)  # move for analysis folder - assume it already exists
        else:
            subfolder = startingfolder

        currentfolder = azcam.utils.curdir()
        _, StartingSequence = azcam.utils.find_file_in_sequence(rootname)
        SequenceNumber = StartingSequence

        # bias image (first in sequence)
        zerofilename = rootname + "%04d" % StartingSequence
        zerofilename = os.path.join(currentfolder, zerofilename) + ".fits"
        zerofilename = azcam.utils.make_image_filename(zerofilename)

        if self.bias_image_in_sequence:
            SequenceNumber += 1

        nextfile = os.path.normpath(
            os.path.join(currentfolder, rootname + "%04d" % (SequenceNumber)) + ".fits"
        )

        # get gain values
        if azcam.db.tools["gain"].valid:
            self.system_gain = azcam.db.tools["gain"].system_gain
        else:
            azcam.log("WARNING: no gain values found for scaling")
            numext, _, _ = azcam.fits.get_extensions(zerofilename)
            self.system_gain = numext * [1.0]

        # loop over files
        self.grades = {}
        while os.path.exists(nextfile):
            if azcam.utils.check_keyboard(0) == "q":
                break

            # perhaps skip some wavelengths
            try:
                wavelength = azcam.fits.get_keyword(nextfile, "WAVLNGTH")
                wavelength = int(float(wavelength) + 0.5)
                if wavelength not in self.wavelengths:
                    SequenceNumber = SequenceNumber + 1
                    nextfile = (
                        os.path.join(currentfolder, rootname + "%04d" % SequenceNumber) + ".fits"
                    )
                    continue
            except Exception:
                wavelength = SequenceNumber

            azcam.log("Processing image %s" % os.path.basename(nextfile))

            # "debias" correct with residuals after colbias
            if self.zero_correct:
                debiased = azcam.db.tools["bias"].debiased_filename
                biassub = "biassub.fits"
                azcam.fits.sub(nextfile, debiased, biassub)
                os.remove(nextfile)
                os.rename(biassub, nextfile)

            # colbias
            if self.overscan_correct:
                azcam.fits.colbias(nextfile, fit_order=self.fit_order)

            # scale to electrons by system gain
            prnuimage = Image(nextfile)

            if self.overscan_correct:
                prnuimage.set_scaling(self.system_gain, None)
            else:
                prnuimage.set_scaling(self.system_gain, azcam.db.tools["gain"].zero_mean)
            prnuimage.assemble(1)
            prnuimage.save_data_format = -32
            prnuimage.write_file("prnu_%d.fits" % wavelength, 6)

            # use mask from defects tool
            if self.use_edge_mask:
                if not azcam.db.tools["defects"].valid:
                    azcam.db.tools["defects"].make_edge_mask(prnuimage.buffer)
                self.masked_image = numpy.ma.masked_where(
                    azcam.db.tools["defects"].defects_mask,
                    prnuimage.buffer,
                )
            else:
                self.masked_image = numpy.ma.masked_invalid(prnuimage.buffer)

            stdev = numpy.ma.std(self.masked_image)
            mean = numpy.ma.mean(self.masked_image)

            prnu = stdev / mean

            self.Prnus[wavelength] = float(prnu)
            if self.allowable_deviation_from_mean != -1:
                if prnu <= self.allowable_deviation_from_mean:
                    GRADE = "PASS"
                else:
                    GRADE = "FAIL"
            else:
                GRADE = "UNDEFINED"

            self.grades[wavelength] = GRADE

            s = "PRNU at %7.1f nm is %5.1f%%, Grade = %s" % (
                wavelength,
                prnu * 100,
                GRADE,
            )
            azcam.log(s)

            SequenceNumber = SequenceNumber + 1
            nextfile = os.path.join(currentfolder, rootname + "%04d" % SequenceNumber) + ".fits"

        if "FAIL" in list(self.grades.values()):
            self.grade = "FAIL"
        else:
            self.grade = "PASS"
        s = "Grade = %s" % self.grade

        if not self.grade_sensor:
            self.grade = "UNDEFINED"

        azcam.log(s)

        # define dataset
        self.dataset = {
            "data_file": self.data_file,
            "grade": self.grade,
            "allowable_deviation_from_mean": self.allowable_deviation_from_mean,
            "Prnus": self.Prnus,
            "grades": self.grades,
        }

        # write data file
        azcam.utils.curdir(startingfolder)
        self.write_datafile()
        if self.create_reports:
            self.report()

        # finish
        self.valid = True
        return

    def report(self):
        """
        Write dark report file.
        """

        lines = []

        lines.append("# PRNU Analysis")
        lines.append("")

        if self.allowable_deviation_from_mean != -1:
            if self.grade != "UNDEFINED":
                s = f"PRNU grade = {self.grade}"
                lines.append(s)
                lines.append("")
            s = f"PRNU spec= {(self.allowable_deviation_from_mean * 100.0):.1f}%"
            lines.append(s)
            lines.append("")

        s = "|**Wavelength**|**PRNU [%]**|"
        lines.append(s)
        s = "|:---|:---:|"
        lines.append(s)

        waves = list(self.Prnus.keys())
        waves.sort()
        for wave in waves:
            s = f"|{wave:04d}|{(100.0 * self.Prnus[wave]):7.01f}|"
            lines.append(s)

        # Make report files
        self.write_report(self.report_file, lines)

        return

    def copy_data_files(self, folder=""):
        """
        Copy data files to proper report folder.
        """

        files = ["prnu.txt", "prnu.md", "prnu.pdf"]

        # destination folder
        if folder == "":
            fldr = os.path.abspath("../prnu")
        else:
            fldr = os.path.abspath(folder)

        if os.path.exists(fldr):
            azcam.log("Existing PRNU folder: %s" % fldr)
        else:
            azcam.log("Creating new PRNU folder: %s" % fldr)
            os.mkdir(fldr)

        for f in files:
            azcam.log("Copying: %s" % f)
            try:
                shutil.copy(f, fldr)
            except Exception as message:
                azcam.log(message)

        return
