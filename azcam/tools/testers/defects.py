import os
import shutil

import numpy

import azcam
from azcam.image import Image
from azcam.tools.testers.basetester import Tester


class Defects(Tester):
    """
    Find and quantify image azcam.db.tools["defects"].
    """

    def __init__(self):

        super().__init__("defects")

        # edge mask
        self.use_edge_mask = 1  # use edge mask to ignore some pixels
        self.edge_size = 9  # number of pixels to exclude if use_edge_mask

        # other masks
        self.dark_mask = 0
        self.bright_mask = 0
        self.defects_mask = 0

        # bright defects
        self.brightdefects_datafile = "brightdefects.txt"
        self.brightdefectsreport_rst = "brightdefects"
        self.dark_filename = "dark.fits"  # dark image for bright defects
        self.BrightPixelRejectionMask = "BrightPixelRejectionMask.png"
        self.bright_pixel_reject = -1  # reject dark image pixels above this e/pix/sec
        self.bright_defects_grade = "FAIL"
        self.bright_rejected_pixels = -1
        self.allowable_bright_pixels = -1
        self.allowable_bright_defects_per_column = -1  # allowable defects per column
        self.total_bright_pixels = -1  # total pixels with mask

        # dark defects
        self.darkdefects_datafile = "darkdefects.txt"
        self.darkdefectsreport_file = "darkdefects"
        self.DarkPixelRejectionMask = "DarkPixelRejectionMask.png"
        self.flat_filename = "superflat.fits"  # flat image for dark pixels
        self.dark_pixel_reject = -1  # reject dark pixels below this value from mean
        self.dark_defects_grade = "FAIL"
        self.dark_rejected_pixels = -1
        self.allowable_dark_pixels = -1
        self.allowable_dark_defects_per_column = -1  # allowable defects per column
        self.total_dark_pixels = -1  # total pixels with mask

        # total defects
        self.data_file = "defects.txt"
        self.report_file = "defects"
        self.defects_mask_filename = "DefectsMask.fits"
        self.PixelRejectionMask = "PixelRejectionMask.png"
        self.total_rejected_pixels = -1
        self.allowable_rejected_pixels = -1  # allowable total number of defective pixels
        self.allowable_bad_fraction = -1  # allowable total fraction of defective pixels

        self.report_include_plots = 1  # include plots in report file

    def analyze(self):
        """
        Find dark defects in a flat/superflat image.
        """

        azcam.log("Combining data from Bright and Dark analysis")

        self.allowable_rejected_pixels = int(self.totalpixels * self.allowable_bad_fraction)

        # make total defects mask
        self.make_defects_mask()

        self.total_rejected_pixels = numpy.count_nonzero(self.defects_mask)
        print(f"Total rejected pixels: {self.total_rejected_pixels}")

        if self.total_rejected_pixels <= self.allowable_rejected_pixels:
            self.grade = "PASS"
        else:
            self.grade = "FAIL"

        # define dataset
        self.dataset = {
            "brightdefects_datafile": self.brightdefects_datafile,
            "bright_defects_grade": self.bright_defects_grade,
            "allowable_bright_pixels": self.allowable_bright_pixels,
            "bright_pixel_reject": float(self.bright_pixel_reject),
            "bright_rejected_pixels": float(self.bright_rejected_pixels),
            "darkdefects_datafile": self.darkdefects_datafile,
            "dark_defects_grade": self.dark_defects_grade,
            "allowable_dark_pixels": self.allowable_dark_pixels,
            "dark_pixel_reject": float(self.dark_pixel_reject),
            "dark_rejected_pixels": float(self.dark_rejected_pixels),
            "data_file": self.data_file,
            "grade": self.grade,
            "allowable_rejected_pixels": self.allowable_rejected_pixels,
            "total_rejected_pixels": float(self.total_rejected_pixels),
        }

        # write output files
        self.write_datafile()
        if self.create_reports:
            self.report()

        return

    def analyze_dark_defects(self):
        """
        Find dark defects in a flat/superflat image.
        """

        azcam.log("Analyzing illuminated image for dark defects")

        self.dark_defects_grade = "UNKNOWN"
        self.dark_rejected_pixels = 0

        CurrentFolder = azcam.utils.curdir()

        # reject dark pixels from superflat
        # superflat.analyze() should have been run already
        s = "Rejecting illuminated pixels below %.3f of mean" % self.dark_pixel_reject
        azcam.log(s)

        superflatimagename = azcam.utils.make_image_filename(self.flat_filename)
        self.template = superflatimagename
        NumExt, _, _ = azcam.fits.get_extensions(superflatimagename)

        superflatimage = Image(superflatimagename)

        # scale by gain
        superflatimage.set_scaling(
            azcam.db.tools["gain"].get_system_gain(), None
        )  # no offsets as ColBiased
        superflatimage.assemble(1)  # now in electrons

        self.dark_masked_image = numpy.ma.asarray(superflatimage.buffer)

        # clip to 16-bits
        # self.dark_masked_image = numpy.ma.MaskedArray.clip(self.dark_masked_image, 0, 65535)

        # calculate stats
        self.totalpixels = numpy.ma.count(self.dark_masked_image)
        mean = numpy.ma.mean(self.dark_masked_image)
        darklimit = mean * self.dark_pixel_reject
        self.dark_masked_image = numpy.ma.masked_where(
            self.dark_masked_image < darklimit, self.dark_masked_image, copy=False
        )
        rejectedpixels = self.totalpixels - numpy.ma.count(self.dark_masked_image)
        self.dark_rejected_pixels = rejectedpixels
        print(f"Actual dark pixels rejected: {self.dark_rejected_pixels}/{self.totalpixels}")

        # optionally create edge mask
        if self.use_edge_mask:
            self.make_edge_mask(superflatimage.buffer)

            # get total dark not including masked edges
            combined_mask = numpy.bitwise_and(self.edge_mask, self.dark_masked_image.mask)
            self.dark_rejected_pixels = numpy.count_nonzero(combined_mask)
        else:
            pass

        s = "SuperflatMean= %.1f" % mean
        azcam.log(s)

        # account for allowable defects per column
        if self.allowable_bright_defects_per_column != -1:
            pass

        # self.allowable_dark_pixels = int(totalpixels * self.allowable_bad_fraction)
        s = "RejectedDarkPixels= %d (%.2f%%)" % (
            self.dark_rejected_pixels,
            (float(self.dark_rejected_pixels) / self.totalpixels) * 100.0,
        )
        azcam.log(s)

        if self.grade_sensor:
            if self.allowable_dark_pixels != -1:
                if rejectedpixels >= self.allowable_dark_pixels:
                    self.dark_defects_grade = "FAIL"
                else:
                    self.dark_defects_grade = "PASS"
                s = "Grade = %s" % self.dark_defects_grade
                azcam.log(s)

        # save dark mask
        fig = azcam.plot.plt.figure()
        fignum = fig.number
        azcam.plot.move_window(fignum)
        azcam.plot.plt.title("Dark Pixel Rejection Mask")
        self.dark_mask = numpy.ma.getmask(self.dark_masked_image).astype("uint8")
        implot = azcam.plot.plt.imshow(self.dark_mask)
        implot.set_cmap("gray")
        azcam.plot.plt.show()
        azcam.plot.save_figure(fignum, "DarkPixelRejectionMask")

        # write mask as FITS
        maskfile = Image(superflatimagename)
        maskfile.hdulist[0].header["OBJECT"] = "dark pixel mask"
        maskfile.assemble(1)  # for parameters
        maskfile.buffer = self.dark_mask
        maskfile.save_data_format = 8
        maskfile.overwrite = 1
        maskfile.write_file("DarkPixelRejectionMask.fits", 6)

        # copy data files to initial folder
        try:
            shutil.copy("DarkPixelRejectionMask.png", CurrentFolder)
            shutil.copy("DarkPixelRejectionMask.fits", CurrentFolder)
        except Exception:
            pass

        # write output files
        azcam.utils.curdir(CurrentFolder)
        if self.create_reports:
            self.make_dark_defects_report()

        return

    def analyze_bright_defects(self):
        """
        Find bright defects in dark signal image.
        """

        azcam.log("Analyzing dark image for bright defects")

        self.bright_defects_grade = "UNKNOWN"
        self.bright_rejected_pixels = 0

        # reject bright pixels from dark median combined and colbiased image
        s = "Rejecting bright pixels above %.3f e/pix/sec" % self.bright_pixel_reject
        azcam.log(s)

        darkfilename = azcam.utils.make_image_filename(self.dark_filename)
        self.template = darkfilename
        NumExt, _, _ = azcam.fits.get_extensions(darkfilename)

        darkimage = Image(darkfilename)

        # Assemble and scale by gain
        darkimage.set_scaling(azcam.db.tools["gain"].get_system_gain(), None)
        darkimage.assemble(1)

        # scale darkimage data by exposure time and binning to get per pixel per second
        bin1 = azcam.fits.get_keyword(darkfilename, "CCDBIN1")
        bin2 = azcam.fits.get_keyword(darkfilename, "CCDBIN2")
        binned = int(bin1) * int(bin2)
        exptime = float(azcam.fits.get_keyword(darkfilename, "EXPTIME"))
        darkimage.buffer = darkimage.buffer * binned / exptime

        self.bright_masked_image = numpy.ma.asarray(darkimage.buffer)

        # clip to 16-bits
        self.bright_masked_image = numpy.ma.MaskedArray.clip(self.bright_masked_image, 0, 65535)
        self.bright_masked_image = numpy.ma.masked_where(
            self.bright_masked_image > self.bright_pixel_reject,
            self.bright_masked_image,
            copy=False,
        )

        self.actual_bright_pixels = numpy.count_nonzero(
            self.bright_masked_image.mask
        )  # includes edges
        azcam.log(f"Actual number of bright pixels: {self.actual_bright_pixels}")

        # optionally create edge mask
        if self.use_edge_mask:
            self.make_edge_mask(self.bright_masked_image)

            # get total bright not including masked edges
            combined_mask = numpy.bitwise_and(self.edge_mask, self.bright_masked_image.mask)
            self.total_bright_pixels = numpy.count_nonzero(combined_mask)
        else:
            self.total_bright_pixels = self.actual_bright_pixels

        # save dark mask
        fig = azcam.plot.plt.figure()
        fignum = fig.number
        azcam.plot.move_window(fignum)
        azcam.plot.plt.title("Bright Pixel Rejection Mask")
        self.bright_mask = numpy.ma.getmask(self.bright_masked_image).astype("uint8")
        implot = azcam.plot.plt.imshow(self.bright_mask)
        implot.set_cmap("gray")
        azcam.plot.plt.show()
        azcam.plot.save_figure(fignum, "BrightPixelRejectionMask")

        # write mask as FITS
        maskfile = Image(darkfilename)
        maskfile.hdulist[0].header["OBJECT"] = "bright pixel mask"
        maskfile.assemble(1)  # for parameters
        maskfile.buffer = self.bright_mask
        maskfile.save_data_format = 8
        maskfile.overwrite = 1
        maskfile.write_file("BrightPixelRejectionMask.fits", 6)

        # count bright rejected pixels
        self.bright_rejected_pixels = self.total_bright_pixels

        if self.allowable_bright_defects_per_column != -1:
            pass

        # this is correct count, but mask not yet correct
        s = "BrightRejectedPixels=%d" % self.bright_rejected_pixels
        azcam.log(s)

        if self.grade_sensor:
            if self.allowable_bright_pixels != -1:
                if self.bright_rejected_pixels >= self.allowable_bright_pixels:
                    self.bright_defects_grade = "FAIL"
                else:
                    self.bright_defects_grade = "PASS"
                s = "Grade = %s" % self.bright_defects_grade
                azcam.log(s)

        # write output files
        if self.create_reports:
            self.make_bright_defects_report()

        return

    # ********************************************************************************************
    # contiguous pixels
    # ********************************************************************************************

    def find_section(
        self,
        x_coord,
        y_coord,
        num_sections_vertical,
        num_sections_horizontal,
        vertical_pixels,
        horizontal_pixels,
    ):
        """
        Find the section the group of bad pixels resides in based off a coordinate in the group. Can be used for any
        number of horizontal and vertical sections.
        """

        section_width = horizontal_pixels / num_sections_horizontal
        section_height = vertical_pixels / num_sections_vertical
        section_num = 0

        i = 1
        j = 1

        # Make sure values are 1 or larger
        if num_sections_vertical < 1 & num_sections_horizontal < 1:
            pass

        else:
            # Determine section number
            # Go through horizontal sections first
            while (i <= num_sections_horizontal) & (section_num == 0):
                if x_coord < (section_width * i):
                    # When horizontal section has been found, go through vertical sections
                    while j <= num_sections_vertical:
                        if y_coord < (section_height * j):
                            if j == 1:
                                section_num = i
                                return section_num
                            else:
                                section_num = i + (num_sections_horizontal * (j - 1))
                                return section_num

                        else:
                            j = j + 1

                else:
                    i = i + 1

        # Return statements in while loop

    def make_defects_mask(self):
        """
        Create a single mask from Edge Mask, Bright mask, and Dark mask.
        Execute AFTER dark and bright defects are found.
        """

        # combine masks, values may be > 1
        temp = numpy.logical_or(self.bright_mask, self.dark_mask)
        self.defects_mask = numpy.logical_and(temp, self.edge_mask)

        fig = azcam.plot.plt.figure()
        fignum = fig.number
        azcam.plot.move_window(fignum)
        azcam.plot.plt.title("Pixel Rejection Mask")
        implot = azcam.plot.plt.imshow(self.defects_mask.astype("uint8"))
        implot.set_cmap("gray")
        azcam.plot.plt.show()
        azcam.plot.save_figure(fignum, "PixelRejectionMask")

        # write mask as FITS
        defectsmask = Image(self.template)  # just a template
        defectsmask.assemble(1)
        # defectsmask.buffer=numpy.ma.getmask(self.DefectsMask).astype('uint8')
        defectsmask.buffer = self.defects_mask.astype("uint8")
        defectsmask.save_data_format = 8
        defectsmask.overwrite = 1
        defectsmask.write_file(self.defects_mask_filename, 6)
        self.defects_mask_filename = os.path.abspath(self.defects_mask_filename)

        self.valid = True  # defects mask in now valid

        return

    def make_edge_mask(self, ImageBuffer, edge_size=-1):
        """
        Creates a mask the size of ImageBuffer which has its edges masked to 0.
        The mask is a numpy array filled with bools.
        Inp: edge_size (or self.edge_size) is the integer number of pixels closest to edge to mask.
        Out: .edge_mask is the numpy array.
        """

        if not self.use_edge_mask:
            return

        # create new masked array
        self.edge_mask = numpy.full(ImageBuffer.shape, True)  # mask

        # edge size
        if edge_size != -1:
            es = edge_size
        else:
            es = self.edge_size

        # set edge pixels as valid (true)
        nrows, ncols = ImageBuffer.shape
        for y in range(nrows):
            for x in range(ncols):
                if x - es < 0:
                    self.edge_mask[y, x] = False
                elif x + es + 1 > ncols:
                    self.edge_mask[y, x] = False
                elif y - es < 0:
                    self.edge_mask[y, x] = False
                elif y + es + 1 > nrows:
                    self.edge_mask[y, x] = False

        return

    def read_defects_mask(self, filename=""):
        """
        Read a defects mask (FITS format).
        """

        if filename == "":
            filename = self.defects_mask_filename

        defectsimage = Image(filename)
        defectsimage.assemble(1)
        self.DefectsImage = defectsimage

        # self.DefectsMask=numpy.ma.masked_invalid(defectsimage.buffer)
        self.defects_mask = numpy.ma.masked_where(
            defectsimage.buffer > 0, defectsimage.buffer
        )  # 0 or 1, not >1

        self.valid = True  # defects mask in now valid

        del defectsimage

        return

    def get_defect_coords(self, mask_in):
        """
        Get the coordinates [col,row] of defects, not including edge mask.
        """

        nrows = len(mask_in)
        ncols = len(mask_in[0])

        # mask=numpy.ma.getmask(mask_in)
        coords = mask_in.nonzero()
        lc = len(coords[0])

        coords1 = []
        for i in range(lc):
            row = coords[0][i]
            col = coords[1][i]

            if self.use_edge_mask:
                if row < self.edge_size:
                    pass
                elif row >= (nrows - self.edge_size):
                    pass
                elif col < self.edge_size:
                    pass
                elif col >= (ncols - self.edge_size):
                    pass
                else:
                    coords1.append([col, row])
            else:
                coords1.append([col, row])

        # return [col,row] pairs
        coords2 = sorted(coords1, key=lambda k: [k[0], k[1]])
        return coords2

    def plot_defects_mask(self):
        """
        Plot the defective pixel mask.
        """

        fig = azcam.plot.plt.figure()
        fignum = fig.number
        azcam.plot.move_window(fignum)
        azcam.plot.plt.title("Pixel Rejection Mask")
        implot = azcam.plot.plt.imshow(self.defects_mask.astype("uint8"))
        implot.set_cmap("gray")
        azcam.plot.plt.show()
        azcam.plot.save_figure(fignum, "PixelRejectionMask")

        return

    def make_bright_defects_report(self):
        """
        Write bright defects report file.
        """

        lines = []

        lines.append("# Bright Defects Analysis")
        lines.append("")
        lines.append(
            f"Rejecting bright pixels above {self.bright_pixel_reject:.01f} electrons/pix/sec"
        )
        lines.append("")
        lines.append(f"Number of bright rejected: {self.bright_rejected_pixels}")
        lines.append("")
        lines.append(f"Allowable bad pixels: {self.allowable_bright_pixels}")
        lines.append("")

        # add plots
        if self.report_include_plots:
            lines.append(
                f"![Bright pixel rejection mask]({os.path.abspath(self.BrightPixelRejectionMask)}) "
            )
            lines.append("")
            lines.append("*Bright pixel rejection mask.*")
            lines.append("")

        # Make report files
        self.write_report(self.brightdefectsreport_rst, lines)

        return

    def make_dark_defects_report(self):
        """
        Write dark defects report file.
        """

        lines = []

        lines.append("# Dark Defects Analysis")
        lines.append("")
        lines.append(f"Rejecting dark pixels below {self.dark_pixel_reject:.03f} mean")
        lines.append("")
        lines.append(f"Number of dark rejected: {self.dark_rejected_pixels}")
        lines.append("")
        lines.append(f"Allowable bad pixels: {self.allowable_dark_pixels}")
        lines.append("")

        # add plots
        if self.report_include_plots:
            lines.append(
                f"![Dark pixel rejection mask]({os.path.abspath(self.DarkPixelRejectionMask)}) "
            )
            lines.append("")
            lines.append("*Dark pixel rejection mask.*")
            lines.append("")

        # Make report files
        self.write_report(self.darkdefectsreport_file, lines)

        return

    def report(self):
        """
        Write defects report file for Bright and Dark.
        Run only after all analysis has been completed.
        """

        lines = []

        lines.append("# Defects Analysis")
        lines.append("")
        if self.grade != "UNDEFINED":
            lines.append(f"Total defects grade: {self.grade}")
            lines.append("")
        lines.append(f"Number of pixels rejected: {self.total_rejected_pixels}")
        lines.append("")
        lines.append(f"Allowable total bad pixels: {self.allowable_rejected_pixels}")
        lines.append("")

        lines.append("# Bright Defects Analysis")
        lines.append("")
        lines.append(
            f"Rejecting bright pixels above {self.bright_pixel_reject:.01f} electrons/pix/sec"
        )
        lines.append("")
        lines.append(f"Number of bright rejected pixels: {self.bright_rejected_pixels}")
        lines.append("")
        lines.append(f"Allowable bright pixels: {self.allowable_bright_pixels}")
        lines.append("")

        lines.append("# Dark Defects Analysis")
        lines.append("")
        lines.append(f"Rejecting dark pixels below {self.dark_pixel_reject:.03f} mean")
        lines.append("")
        lines.append(f"Number of dark rejected pixels: {self.dark_rejected_pixels}")
        lines.append("")
        lines.append(f"Allowable dark pixels: {self.allowable_dark_pixels}")
        lines.append("")

        if self.report_include_plots:
            lines.append('<div style="page-break-after: always;"></div>')

            lines.append(
                f"![Bright pixel rejection mask]({os.path.abspath(self.BrightPixelRejectionMask)}) "
            )
            lines.append("")
            lines.append("*Bright pixel rejection mask.*")
            lines.append("")

            lines.append(
                f"![Dark pixel rejection mask]({os.path.abspath(self.DarkPixelRejectionMask)}) "
            )
            lines.append("")
            lines.append("*Dark pixel rejection mask.*")
            lines.append("")

            lines.append(
                f"![Total pixel rejection mask]({os.path.abspath(self.PixelRejectionMask)}) "
            )
            lines.append("")
            lines.append("*Total pixel rejection mask.*")
            lines.append("")

        # Make report files
        self.write_report(self.report_file, lines)

        return

    def copy_data_files(self, folder=""):
        """
        Copy data files to proper report folder.
        """

        files = [
            "brightdefects.pdf",
            "brightdefects.md",
            "brightdefects.txt",
            "BrightPixelRejectionMask.png",
            "BrightPixelRejectionMask.fits",
            "darkdefects.pdf",
            "darkdefects.md",
            "darkdefects.txt",
            "DarkPixelRejectionMask.png",
            "DarkPixelRejectionMask.fits",
        ]

        # destination folder
        if folder == "":
            fldr = os.path.abspath("../defects")
        else:
            fldr = os.path.abspath(folder)

        if os.path.exists(fldr):
            azcam.log("Existing defects folder: %s" % fldr)
        else:
            azcam.log("Creating new defects folder: %s" % fldr)
            os.mkdir(fldr)

        for f in files:
            azcam.log("Copying: %s" % f)
            # allow errors as some files may not exist
            try:
                shutil.copy(f, fldr)
            except Exception:
                pass

        return
