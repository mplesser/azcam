import math
import os
import shutil

import numpy
from astropy.io import fits as pyfits

import azcam
import azcam.utils
import azcam.fits
import azcam.image
import azcam.console.utils
import azcam.console.plot
from azcam.testers.basetester import Tester


class GainMap(Tester):
    """
    Acquire and analyze gain (PTC point) data.
    """

    def __init__(self):
        super().__init__("gainmap")

        self.exposure_type = "flat"
        self.exposure_time = -1
        self.exposure_level = -1  # exposure_level in electrons/pixel, -1 do not used
        self.number_flat_images = 10
        self.number_bias_images = 10
        self.overwrite = 0
        self.wavelength = -1  # -1 do not change wavelength
        self.clear_arrray = 0

        self.data_file = "gainmap.txt"
        self.gainmap_fitsfile = "gainmap.fits"
        self.gainmap_plotfile = "gainmap.png"
        self.report_file = "gainmap"

        # files
        self.imagefolder = ""
        self.flat_filenames = []
        self.bias_filenames = []

        # images
        self.flat_images = []
        self.bias_images = []
        self.flatcube = numpy.array
        self.mean_flatimage = numpy.array
        self.sdev_flatimage = numpy.array
        self.var_flatimage = numpy.array

        self.biascube = numpy.array
        self.mean_biasimage = numpy.array
        self.sdev_biasimage = numpy.array

        self.gainmap_image = numpy.array

        self.image_zero = ""
        self.image_flat1 = ""
        self.image_flat2 = ""

        # outputs
        self.gain_min = 0
        self.gain_max = 0
        self.gain_median = 0

        self.system_gain = []
        self.noise = []
        self.mean = []
        self.sdev = []
        self.zero_mean = []

    def acquire(self):
        """
        Acquire a series if bias image and a series of flat field images.
        These are used to generate a PTC point at every pixel.
        """

        azcam.log("Acquiring gainmap sequence")

        if self.exposure_time == -1:
            et = azcam.db.tools["exposure"].get_exposuretime()
            azcam.log(f"Exposure time not specified, using current value of {et:0.3f}")
        else:
            et = self.exposure_time

        # save pars to be changed
        impars = {}
        azcam.db.parameters.save_imagepars(impars)

        # create new subfolder
        if self.overwrite:
            if os.path.exists("gainmap"):
                shutil.rmtree("gainmap")
        currentfolder, subfolder = azcam.console.utils.make_file_folder("gainmap")
        azcam.db.parameters.set_par("imagefolder", subfolder)
        self.imagefolder = subfolder

        azcam.db.parameters.set_par("imageincludesequencenumber", 1)
        azcam.db.parameters.set_par("imageautoincrementsequencenumber", 1)
        azcam.db.parameters.set_par("imageautoname", 0)  # manually set name
        azcam.db.parameters.set_par("imagetest", 0)  # turn off TestImage
        azcam.db.parameters.set_par("imageoverwrite", 1)

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
        if self.clear_arrray:
            azcam.db.tools["exposure"].test(0)

        # bias images
        azcam.db.parameters.set_par("imageroot", "bias.")
        for loop in range(self.number_bias_images):
            azcam.db.parameters.set_par("imagetype", "zero")
            azcam.log(f"Taking bias exposure {loop+1}/{self.number_bias_images}")
            azcam.db.tools["exposure"].expose(0, "zero", "Gainmap bias frame")

        # flat images
        azcam.db.parameters.set_par("imageroot", "gainmap.")
        for loop in range(self.number_flat_images):
            azcam.db.parameters.set_par("imagetype", self.exposure_type)
            azcam.log(f"Taking flats {loop+1}/{self.number_flat_images}")
            azcam.db.tools["exposure"].expose(
                et, self.exposure_type, f"Gainmap frame {loop}"
            )
            azcam.log(f"Image {loop} finished")

        # finish
        azcam.db.parameters.restore_imagepars(impars)
        azcam.utils.curdir(currentfolder)
        azcam.log("Gainmap sequence finished")

        return

    def analyze(self):
        """
        Analyze a bias image and multiple flat field images to generate a PTC point at every pixel.
        """

        azcam.log("Analyzing gainmap sequence")

        startingfolder = azcam.utils.curdir()

        # get list of bias images
        rootname = "bias."
        _, starting_sequence = azcam.console.utils.find_file_in_sequence(rootname)
        sequence_number = starting_sequence
        self.bias_filenames = []
        while True:
            biasfile = (
                os.path.join(startingfolder, rootname + f"{sequence_number:04d}")
                + ".fits"
            )
            if not os.path.exists(biasfile):
                break
            biasfile = azcam.utils.fix_path(biasfile)
            self.bias_filenames.append(biasfile)
            sequence_number += 1

        # get list of all flat images
        rootname = "gainmap."
        _, starting_sequence = azcam.console.utils.find_file_in_sequence(rootname)
        sequence_number = starting_sequence
        self.flat_filenames = []
        while True:
            flatfile = (
                os.path.join(startingfolder, rootname + f"{sequence_number:04d}")
                + ".fits"
            )
            if not os.path.exists(flatfile):
                break
            flatfile = azcam.utils.fix_path(flatfile)
            self.flat_filenames.append(flatfile)
            sequence_number += 1

        NumExt, _, _ = azcam.fits.get_extensions(self.bias_filenames[0])
        NumExt = max(1, NumExt)

        # these will be mean values if more than one sequence is analyzed
        self.system_gain = [0] * NumExt
        self.noise = [0] * NumExt
        self.mean = [0] * NumExt
        self.sdev = [0] * NumExt
        self.zero_mean = [0] * NumExt

        loop = 0

        # make assembled bias images
        self.bias_images = []
        for frame in self.bias_filenames:
            im = azcam.image.Image(frame)
            im.assemble(1)  # assembled an trim overscan
            self.bias_images.append(im)

        # make assembled flat images
        self.flat_images = []
        for frame in self.flat_filenames:
            im = azcam.image.Image(frame)
            im.assemble(1)  # assembled an trim overscan
            self.flat_images.append(im)

        # stack data and make 2D stats
        self.flatcube = numpy.stack([im.buffer for im in self.flat_images])
        self.mean_flatimage = self.flatcube.mean(axis=0)
        self.sdev_flatimage = self.flatcube.std(axis=0)
        self.var_flatimage = numpy.square(self.sdev_flatimage)

        self.biascube = numpy.stack([im.buffer for im in self.bias_images])
        self.mean_biasimage = self.biascube.mean(axis=0)
        self.sdev_biasimage = self.biascube.std(axis=0)
        self.var_biasimage = numpy.square(self.sdev_biasimage)

        # make gain map
        self.gainmap_image = self.mean_flatimage / (
            self.var_flatimage - self.var_biasimage
        )
        self.gain_mean = self.gainmap_image.mean()
        self.gain_min = self.gainmap_image.min()
        self.gain_max = self.gainmap_image.max()
        self.gain_median = numpy.median(self.gainmap_image)
        self.gain_sdev = self.gainmap_image.std()

        # outputs
        azcam.log(f"Mean gain is {self.gain_mean:0.02f}")
        azcam.log(f"Minimum gain is {self.gain_min:0.02f}")
        azcam.log(f"Maximum gain is {self.gain_max:0.02f}")
        azcam.log(f"Median gain is {self.gain_median:0.02f}")
        azcam.log(f"Gain sdev is {self.gain_sdev:0.02f}")

        azcam.console.plot.plt.imshow(
            self.gainmap_image,
            cmap="gray",
            origin="lower",
            vmin=self.gain_mean - self.gain_sdev,
            vmax=self.gain_mean + self.gain_sdev,
        )
        azcam.console.plot.plt.title("Gain Map")
        fignum = azcam.console.plot.plt.gcf().number
        azcam.console.plot.save_figure(fignum, self.gainmap_plotfile)
        azcam.console.plot.move_window(fignum)

        # create gainmap FITS file
        hdul = pyfits.HDUList()
        hdul.append(pyfits.PrimaryHDU())
        hdul.append(pyfits.ImageHDU(data=self.gainmap_image))
        hdul.writeto(self.gainmap_fitsfile, overwrite=True)

        # define dataset
        self.dataset = {
            "data_file": self.data_file,
            "gain_mean": f"{self.gain_mean:0.03f}",
            "gain_min": f"{self.gain_min:0.03f}",
            "gain_max": f"{self.gain_max:0.03f}",
            "gain_median": f"{self.gain_median:0.03f}",
            "gain_sdev": f"{self.gain_sdev:0.03f}",
        }

        # write output files
        self.write_datafile()
        if self.create_reports:
            self.report()

        # finish
        self.valid = 1

        return

    def report(self):
        """
        Make report files.
        """

        lines = ["# Gain Map", ""]

        s = f"Gain mean = {self.gain_mean:0.03f}"
        lines.append(s)
        lines.append("")
        s = f"Gain minimum = {self.gain_min:0.03f}"
        lines.append(s)
        lines.append("")
        s = f"Gain maximum = {self.gain_max:0.03f}"
        lines.append(s)
        lines.append("")
        s = f"Gain median = {self.gain_median:0.03f}"
        lines.append(s)
        lines.append("")
        s = f"Gain sdev = {self.gain_sdev:0.03f}"
        lines.append(s)
        lines.append("")

        lines.append(f"![Dark Image]({os.path.abspath(self.gainmap_plotfile)})  ")
        lines.append("*Gain Map Image.*")
        lines.append("")

        # Make report files
        self.write_report(self.report_file, lines)

        return
