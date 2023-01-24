import glob
import os
import shutil

import numpy

import azcam
from azcam.image import Image
from azcam.tools.testers.basetester import Tester


class Superflat(Tester):
    """
    Flat field image acquisition and analysis.
    """

    def __init__(self):

        super().__init__("superflat")

        # acquire
        self.exposure_type = "flat"
        self.exposure_levels = []  # exposure levels in e/pix
        self.exposure_times = [1.0]  # exposure times if no exposure_levels
        self.wavelength = 500.0  # wavelength for images
        self.number_images_acquire = [2]  # number of images

        # analyze
        self.combination_type = "median"
        self.overscan_correct = 1  # flag to overscan correct images
        self.zero_correct = 0  # flag to correct with bias residuals
        self.superflat_filename = "superflat.fits"  # filename of superflat image
        self.scaled_superflat_filename = (
            "superflatscaled.fits"  # filename of gain corrected fits image
        )
        self.system_gain = []

    def acquire(self):
        """
        Acquire a set of flat field images.
        """

        azcam.log("Acquiring Superflat sequence")

        # save pars to be changed
        impars = {}
        azcam.utils.save_imagepars(impars)
        currentfolder = azcam.utils.curdir()

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

        # clear device
        azcam.db.tools["exposure"].test(0)

        # Try exposure_level to get ExposureTime
        if azcam.db.tools["detcal"].valid and len(self.exposure_levels) > 0:
            azcam.log("Using exposure_levels")

            meanelectrons = azcam.db.tools["detcal"].mean_electrons

            self.exposure_times = numpy.array(self.exposure_levels) / meanelectrons[wave]
        elif len(self.exposure_times) > 0:
            azcam.log("Using ExposureTimes")
        else:
            raise azcam.AzcamError("could not determine exposure times")

        for setnum, exposuretime in enumerate(self.exposure_times):

            azcam.db.parameters.set_par(
                "imageroot", "superflat."
            )  # for automatic data analysis
            azcam.db.parameters.set_par(
                "imageincludesequencenumber", 1
            )  # use sequence numbers
            azcam.db.parameters.set_par("imageautoname", 0)  # manually set name
            azcam.db.parameters.set_par(
                "imageautoincrementsequencenumber", 1
            )  # inc sequence numbers
            azcam.db.parameters.set_par("imagetest", 0)  # turn off TestImage

            # create new subfolder
            currentfolder, newfolder = azcam.utils.make_file_folder("superflat", 1, 1)
            azcam.db.parameters.set_par("imagefolder", newfolder)

            for loop in range(self.number_images_acquire[setnum]):
                exposuretime = self.exposure_times[setnum]

                azcam.log(
                    "Taking SuperFlat image %d of %d for %.3f seconds"
                    % (loop + 1, self.number_images_acquire[setnum], exposuretime)
                )
                azcam.db.tools["exposure"].expose(
                    exposuretime, self.exposure_type, "superflat flat"
                )

            # finish this set
            azcam.utils.restore_imagepars(impars, currentfolder)

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

        if self.overscan_correct or self.zero_correct:
            # create analysis subfolder
            startingfolder, subfolder = azcam.utils.make_file_folder("analysis")

            # copy all image files to analysis folder
            azcam.log("Making copy of image files for analysis")
            for filename in glob.glob(os.path.join(startingfolder, "*.fits")):
                shutil.copy(filename, subfolder)

            azcam.utils.curdir(subfolder)  # move to analysis folder
        else:
            azcam.utils.curdir(subfolder)  # move to analysis folder - assume it exists

        _, StartingSequence = azcam.utils.find_file_in_sequence(rootname)
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
            nextfile = os.path.join(subfolder, rootname + "%04d" % SequenceNumber) + ".fits"
            loop += 1

        # median combine all images
        azcam.log("Combining superflat images (%s)" % self.combination_type)
        azcam.fits.combine(filelist, self.superflat_filename, self.combination_type)

        # make superflat image scaled by gain
        if azcam.db.tools["gain"].valid:
            self.system_gain = azcam.db.tools["gain"].system_gain
        else:
            azcam.log("WARNING: no gain values found for scaling")

        superflat_image = Image(self.superflat_filename)
        if self.overscan_correct:
            superflat_image.set_scaling(self.system_gain, None)
        else:
            superflat_image.set_scaling(self.system_gain, gain.zero_mean)
        superflat_image.assemble(1)
        fig = azcam.plot.plt.figure()
        fignum = fig.number
        azcam.plot.move_window(fignum)
        azcam.plot.plot_image(superflat_image)
        azcam.plot.plt.title("Superflat Combined Image")
        azcam.plot.plt.show()
        azcam.plot.save_figure(fignum, "superflatimage")
        superflat_image.overwrite = 1
        superflat_image.save_data_format = -32  # could be >16 bits with scaling
        superflat_image.write_file(self.scaled_superflat_filename, 6)
        del superflat_image  # remove lock

        # copy superflat and plot to starting folder
        if startingfolder != subfolder:
            shutil.copy(self.superflat_filename, startingfolder)
            shutil.copy(self.scaled_superflat_filename, startingfolder)
            shutil.copy("superflatimage.png", startingfolder)
            self.superflat_filename = os.path.join(startingfolder, self.superflat_filename)
            self.scaled_superflat_filename = os.path.join(
                startingfolder, self.scaled_superflat_filename
            )

        # finish
        azcam.utils.curdir(startingfolder)
        return
