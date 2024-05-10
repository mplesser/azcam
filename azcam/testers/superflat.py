import glob
import os
import shutil

import numpy

import azcam
import azcam.utils
import azcam.fits
import azcam.image
import azcam.console.plot
import azcam.exceptions
from azcam.testers.basetester import Tester


class Superflat(Tester):
    """
    Flat field image acquisition and analysis.
    """

    def __init__(self):
        super().__init__("superflat")

        # acquire
        self.exposure_type = "flat"
        self.use_exposure_level = 1
        self.exposure_level = 30000  # exposure level in DN
        self.exposure_time = 1.0  # exposure time if no exposure_level
        self.wavelength = 500.0  # wavelength for images
        self.number_images_acquire = 3  # number of images

        # analyze
        self.combination_type = "median"
        self.overscan_correct = 1  # flag to overscan correct images
        self.zero_correct = 0  # flag to correct with bias residuals
        self.superflat_filename = "superflat.fits"  # filename of superflat image
        self.scaled_superflat_filename = (
            "superflatscaled.fits"  # filename of gain corrected fits image
        )
        self.system_gain = []

        self.fit_order = 3
        """fit order for overscan correction"""

    def acquire(self):
        """
        Acquire a set of flat field images.
        """

        azcam.log("Acquiring Superflat sequence")

        # save pars to be changed
        impars = {}
        azcam.db.parameters.save_imagepars(impars)
        currentfolder = azcam.utils.curdir()

        # set wavelength
        if self.wavelength > 0:
            wave = int(self.wavelength)
            wave1 = int(azcam.db.tools["instrument"].get_wavelength())
            if wave1 != wave:
                azcam.log(f"Setting wavelength to {wave} nm")
                azcam.db.tools["instrument"].set_wavelength(wave)

        # clear device
        imname = azcam.db.tools["exposure"].get_filename()
        azcam.db.tools["exposure"].test(0)
        bin1 = int(azcam.fits.get_keyword(imname, "CCDBIN1"))
        bin2 = int(azcam.fits.get_keyword(imname, "CCDBIN2"))
        binning = bin1 * bin2

        # Try exposure_level to get ExposureTime
        if self.use_exposure_level:
            azcam.log("Using exposure_level")

            meancounts = azcam.db.tools["detcal"].mean_counts[wave]
            self.exposure_time = (
                self.exposure_level
                / meancounts
                / binning
                * (
                    azcam.db.tools["gain"].system_gain[0]
                    / azcam.db.tools["detcal"].system_gain[0]
                )
            )

        elif self.exposure_time > 0:
            azcam.log("Using exposure_time")
        else:
            raise azcam.exceptions.AzcamError("could not determine exposure times")

        azcam.db.parameters.set_par("imageroot", "superflat.")
        azcam.db.parameters.set_par("imageincludesequencenumber", 1)
        azcam.db.parameters.set_par("imageautoname", 0)
        azcam.db.parameters.set_par("imageautoincrementsequencenumber", 1)
        azcam.db.parameters.set_par("imagetest", 0)

        # create new subfolder
        currentfolder, subfolder = azcam.console.utils.make_file_folder(
            "superflat", 1, 0
        )
        azcam.db.parameters.set_par("imagefolder", subfolder)

        for loop in range(self.number_images_acquire):
            azcam.log(
                f"Taking SuperFlat image {(loop + 1)} of {self.number_images_acquire} for {self.exposure_time:0.03f} seconds"
            )
            azcam.db.tools["exposure"].expose(
                self.exposure_time, self.exposure_type, "superflat flat"
            )

        azcam.db.parameters.restore_imagepars(impars)
        azcam.utils.curdir(currentfolder)

        # finish
        azcam.log("Superflat sequence finished")

        return

    def analyze(self):
        """
        Analyze an existing SuperFlat image sequence for LSST.
        """

        azcam.log("Analyzing superflat sequence")

        rootname = "superflat."

        self.superflat_filename = "superflat.fits"  # filename of superflat image
        self.scaled_superflat_filename = (
            "superflatscaled.fits"  # filename of gain corrected fits image
        )

        startingfolder = azcam.utils.curdir()
        subfolder = startingfolder

        # create analysis subfolder
        startingfolder, subfolder = azcam.console.utils.make_file_folder("analysis")

        # copy all image files to analysis folder
        azcam.log("Making copy of image files for analysis")
        for filename in glob.glob(os.path.join(startingfolder, "*.fits")):
            shutil.copy(filename, subfolder)

        azcam.utils.curdir(subfolder)  # move to analysis folder

        _, StartingSequence = azcam.console.utils.find_file_in_sequence(rootname)
        SequenceNumber = StartingSequence

        # start analyzing sequence
        nextfile = os.path.join(subfolder, rootname + "%04d" % SequenceNumber) + ".fits"
        NumExt, _, _ = azcam.fits.get_extensions(nextfile)
        loop = 0
        filelist = []
        while os.path.exists(nextfile):
            azcam.log("Processing %s" % os.path.basename(nextfile))
            filelist.append(nextfile)

            # colbias
            if self.overscan_correct:
                azcam.fits.colbias(nextfile, fit_order=self.fit_order)

            # "debias" correct with residuals after colbias
            if self.zero_correct:
                debiased = azcam.db.tools["bias"].debiased_filename
                biassub = "biassub.fits"
                azcam.fits.sub(nextfile, debiased, biassub)
                os.remove(nextfile)
                os.rename(biassub, nextfile)

            SequenceNumber = SequenceNumber + 1
            nextfile = (
                os.path.join(subfolder, rootname + "%04d" % SequenceNumber) + ".fits"
            )
            loop += 1

        # median combine all images
        azcam.log("Combining superflat images (%s)" % self.combination_type)
        azcam.fits.combine(
            filelist, self.superflat_filename, self.combination_type, overscan_correct=0
        )

        # make superflat image scaled by gain
        if azcam.db.tools["gain"].valid:
            self.system_gain = azcam.db.tools["gain"].system_gain
        else:
            azcam.log("WARNING: no gain values found for scaling")

        superflat_image = azcam.image.Image(self.superflat_filename)
        if self.overscan_correct:
            superflat_image.set_scaling(self.system_gain, None)
        else:
            superflat_image.set_scaling(
                self.system_gain, azcam.db.tools["gain"].zero_mean
            )
        superflat_image.assemble(1)
        fig = azcam.console.plot.plt.figure()
        fignum = fig.number
        azcam.console.plot.move_window(fignum)
        azcam.console.plot.plot_image(superflat_image)
        azcam.console.plot.plt.title("Superflat Combined Image")
        azcam.console.plot.plt.show()
        azcam.console.plot.save_figure(fignum, "superflatimage")
        superflat_image.overwrite = 1
        superflat_image.save_data_format = -32  # could be >16 bits with scaling
        superflat_image.write_file(self.scaled_superflat_filename, 6)
        del superflat_image  # remove lock

        # copy superflat and plot to starting folder
        if startingfolder != subfolder:
            shutil.copy(self.superflat_filename, startingfolder)
            shutil.copy(self.scaled_superflat_filename, startingfolder)
            shutil.copy("superflatimage.png", startingfolder)
            self.superflat_filename = os.path.join(
                startingfolder, self.superflat_filename
            )
            self.scaled_superflat_filename = os.path.join(
                startingfolder, self.scaled_superflat_filename
            )

        # finish
        azcam.utils.curdir(startingfolder)
        return
