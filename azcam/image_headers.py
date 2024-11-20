"""
Contains code for calculating and writing image header information.
"""

import os
import math

import azcam


class ImageHeaders(object):
    """
    Class for image headers.
    """

    def __init__(self):
        super().__init__()

    def _write_PHU(self, hdu):
        """
        Write primary header for FITS or MEF file.
        """

        numHDUs = self.focalplane.numamps_image
        if numHDUs == 1:  # no extensions for single amp
            numHDUs = 0
        hdu.header.set(
            "NEXTEND", numHDUs, "Number of extensions"
        )  # near top of FITS header
        hdu.header.set(
            "BITPIX", 16, "array data type"
        )  # so 8 bits never shows up in PHU

        # DETSIZE is whole mosaic size or CCD if single device (unbinned)
        x = (
            self.focalplane.ampvispix_x
            * self.focalplane.num_ser_amps_det
            * self.focalplane.numdet_x
        )
        y = (
            self.focalplane.ampvispix_y
            * self.focalplane.num_par_amps_det
            * self.focalplane.numdet_y
        )
        s = "[1:%d,1:%d]" % (x, y)
        hdu.header.set("DETSIZE", s, "Detector size")

        # CCDSUM is binning
        s = "%d %d" % (self.focalplane.col_bin, self.focalplane.row_bin)
        hdu.header.set("CCDSUM", s, "CCD pixel summing")
        hdu.header.set(
            "CCDBIN1", self.focalplane.col_bin, "Binning factor along axis 1"
        )
        hdu.header.set(
            "CCDBIN2", self.focalplane.row_bin, "Binning factor along axis 2"
        )

        # filename at acquisition (no folder)
        filename = self.filename
        filename = os.path.basename(filename)
        hdu.header.set("FILENAME", filename, "base filename at acquisition")

        hdu.header.set("NCCDS", self.focalplane.num_detectors, "Number of CCDs")
        hdu.header.set("NAMPS", self.focalplane.numamps_image, "Number of amplifiers")

        # keywords are written after exposure is completed
        curpos = len(hdu.header)
        for headername in azcam.db.headerorder:
            item_header = azcam.db.headers[headername]
            cheader = item_header.get_header()  # list of kw, value, comment, type]
            if cheader == [] or cheader is None:
                continue
            # first add the comment lines
            for comm in item_header.title:
                hdu.header.add_comment(item_header.title[comm], after=curpos)
                curpos = curpos + 1

            # add the keywords
            for head in cheader:
                if head[0].lower() == "comment":
                    hdu.header.add_comment(head[1], after=curpos)
                elif head[0].lower() == "history":
                    hdu.header.add_history(head[1], after=curpos)
                else:
                    try:
                        hdu.header.set(head[0], head[1], head[2], after=curpos)
                    except Exception:
                        curpos -= 1
                curpos += 1

        return

    def _write_asm_fits_header(self, hdu):
        """
        Write primary header for assembled FITS file.
        11Sep13 Zareba
        """

        # no extensions
        numHDUs = 2

        hdu.header.set("EXTEND", True, "")
        hdu.header.set("NEXTEND", numHDUs, "Number of extensions")
        hdu.header.set("BITPIX", 16, "array data type")

        # DETSIZE is whole mosaic size or CCD if single device (unbinned)
        x = self.asmsize[0]
        y = self.asmsize[1]
        s = "[1:%d,1:%d]" % (x, y)
        hdu.header.set("DETSIZE", s, "Detector size")

        # CCDSUM is binning
        s = "%d %d" % (self.focalplane.col_bin, self.focalplane.row_bin)
        hdu.header.set("CCDSUM", s, "CCD pixel summing")
        hdu.header.set(
            "CCDBIN1", self.focalplane.col_bin, "Binning factor along axis 1"
        )
        hdu.header.set(
            "CCDBIN2", self.focalplane.row_bin, "Binning factor along axis 2"
        )

        # filename at acquisition (no folder)
        filename = self.filename
        filename = os.path.basename(filename)
        hdu.header.set("FILENAME", filename, "base filename at acquisition")

        hdu.header.set("NCCDS", 1, "Number of CCDs")
        hdu.header.set("NAMPS", 1, "Number of amplifiers")

        # all these keywords are written after exposure is finished
        curpos = len(hdu.header)
        for item in self.header.items:
            cheader = item.header.get_header()
            if cheader == []:
                continue
            # first add the comment lines
            for comm in item.header.title:
                # add the comment line
                hdu.header.add_comment(item.header.title[comm], after=curpos)
                curpos = curpos + 1

            # add the keywords
            for head in cheader:
                if head[0].lower() == "comment":
                    hdu.header.add_comment(head[1], after=curpos)
                elif head[0].lower() == "history":
                    hdu.header.add_history(head[1], after=curpos)
                else:
                    hdu.header.set(head[0], head[1], head[2], after=curpos)
                curpos += 1

        return

    def _write_extension_header(self, ext_number, hdu):
        """
        Write the extension header for a FITS/MEF file.
        ext_number starts at 1 (for MEF and FITS).
        """

        # make nice header text
        curpos = len(hdu.header)
        hdu.header.add_comment(
            "==================================================================",
            after=curpos,
        )
        hdu.header.add_comment("Image", after=curpos + 1)
        hdu.header.add_comment(
            "==================================================================",
            after=curpos + 2,
        )
        curpos = curpos + 3

        # DATASEC is actual DATA BINNED pixels in the final image
        # does not include over/under scans
        self.datasecx1 = self.focalplane.xunderscan + 1
        self.datasecx2 = self.focalplane.xunderscan + self.focalplane.numviscols_amp
        self.datasecy1 = self.focalplane.yunderscan + 1
        self.datasecy2 = self.focalplane.yunderscan + self.focalplane.numvisrows_amp

        # BIASSEC is over or under scan - based on its location
        # defaults to DATASEC if none requested
        self.biassecx1 = self.datasecx1
        self.biassecx2 = self.datasecx2
        self.biassecy1 = self.datasecy1
        self.biassecy2 = self.datasecy2

        if self.focalplane.bias_location == self.focalplane.BL_COLUNDER:
            self.biassecx1 -= self.focalplane.xunderscan
            self.biassecx2 -= self.focalplane.numviscols_amp
        elif self.focalplane.bias_location == self.focalplane.BL_COLOVER:
            self.biassecx1 += self.focalplane.numviscols_amp
            self.biassecx2 += self.focalplane.xoverscan
        elif self.focalplane.bias_location == self.focalplane.BL_ROWUNDER:
            self.biassecy1 -= self.focalplane.yunderscan
            self.biassecy2 -= self.focalplane.numvisrows_amp
        elif self.focalplane.bias_location == self.focalplane.BL_ROWOVER:
            self.biassecy1 += self.focalplane.numvisrows_amp
            self.biassecy2 += self.focalplane.yoverscan

        # TRIMSEC is DATASEC, the pixels to keep after removing BIASSEC
        self.trimsecx1 = self.datasecx1
        self.trimsecx2 = self.datasecx2
        self.trimsecy1 = self.datasecy1
        self.trimsecy2 = self.datasecy2

        # CCDSEC is unbinned
        # new code - unbinned
        self.ccdsecX1 = self.datasecx1
        self.ccdsecX2 = self.focalplane.ampvispix_x
        self.ccdsecY1 = self.datasecy1
        self.ccdsecY2 = self.focalplane.ampvispix_y

        # old code - binned
        self.ccdsecx1 = self.datasecx1
        self.ccdsecx2 = self.datasecx2
        self.ccdsecy1 = self.datasecy1
        self.ccdsecy2 = self.datasecy2

        # ORIGSEC is entire device in binned coordinates
        self.origsecx1 = 1
        # self.origsecx2	= self.coltotal/self.col_bin GSZ
        self.origsecx2 = (
            self.focalplane.numcols_amp
            * self.focalplane.num_ser_amps_det
            / self.focalplane.col_bin
        )
        self.origsecy1 = 1
        # self.origsecy2	= self.rowtotal/self.row_bin
        self.origsecy2 = (
            self.focalplane.numrows_amp
            * self.focalplane.num_par_amps_det
            / self.focalplane.row_bin
        )

        # determine amplifier orientation: new version GSZ 04.14.2011
        ampflip = self.focalplane.amp_cfg[ext_number - 1]

        # calculate which part of mosaic from HDU (increments first in X)
        ny = self.focalplane.extpos_y[ext_number - 1]
        nx = self.focalplane.extpos_x[ext_number - 1]
        det_number = self.focalplane.det_number[ext_number - 1]
        hdu.header.set(
            "IMAGEID",
            self.focalplane.ext_number[ext_number - 1],
            "Image ID",
            after=curpos,
        )  # int

        curpos += 1

        s = "ccd%d" % det_number
        hdu.header.set("CCDNAME", s, "CCD name", after=curpos)  # string
        curpos += 1

        # all unbinned
        # DETECTOR refers to the mosaic
        # CCD refers to the individual detector
        # AMP refers to data from one amplifier
        # DETSIZE is entire image size

        xVal = (
            self.focalplane.ampvispix_x
            * self.focalplane.num_ser_amps_det
            * self.focalplane.numdet_x
        )
        yVal = (
            self.focalplane.ampvispix_y
            * self.focalplane.num_par_amps_det
            * self.focalplane.numdet_y
        )
        s = "[1:%d,1:%d]" % (xVal, yVal)
        hdu.header.set("DETSIZE", s, "Detector size", after=curpos)  # string
        curpos += 1

        # CCDSIZE is the image size on each CCD, unbinned
        xVal = self.focalplane.ampvispix_x * self.focalplane.num_ser_amps_det
        yVal = self.focalplane.ampvispix_y * self.focalplane.num_par_amps_det
        s = "[1:%d,1:%d]" % (xVal, yVal)
        hdu.header.set("CCDSIZE", s, "CCD size", after=curpos)  # string
        curpos += 1

        # write the extension coordinate keywords
        if self.focalplane.numcols_overscan > 0:
            s = "[%d:%d,%d:%d]" % (
                self.focalplane.numviscols_amp + 1,
                self.focalplane.numviscols_amp + self.focalplane.numcols_overscan,
                1,
                self.focalplane.numvisrows_amp,
            )
        else:
            s = "[1:%d,1:%d]" % (
                self.focalplane.numviscols_amp,
                self.focalplane.numvisrows_amp,
            )
        hdu.header.set("BIASSEC", s, "Bias section", after=curpos)  # string
        curpos += 1

        # DATASEC is data region
        s = "[%d:%d,%d:%d]" % (
            self.datasecx1,
            self.datasecx2,
            self.datasecy1,
            self.datasecy2,
        )
        hdu.header.set("DATASEC", s, "Data section", after=curpos)  # string
        curpos += 1

        # TRIMSEC is trim region for trimming and display
        s = "[%d:%d,%d:%d]" % (
            self.trimsecx1,
            self.trimsecx2,
            self.trimsecy1,
            self.trimsecy2,
        )
        hdu.header.set("TRIMSEC", s, "Trim section", after=curpos)  # string
        curpos += 1

        # AMPSEC is the data from one amp (DATASEC for one amp), unbinned
        if ampflip == 0:
            # no flip
            s = "[%d:%d,%d:%d]" % (
                self.ccdsecX1,
                self.ccdsecX2,
                self.ccdsecY1,
                self.ccdsecY2,
            )
        elif ampflip == 1:
            # flip in x
            s = "[%d:%d,%d:%d]" % (
                self.ccdsecX2,
                self.ccdsecX1,
                self.ccdsecY1,
                self.ccdsecY2,
            )
        elif ampflip == 2:
            # flip in y
            s = "[%d:%d,%d:%d]" % (
                self.ccdsecX1,
                self.ccdsecX2,
                self.ccdsecY2,
                self.ccdsecY1,
            )
        elif ampflip == 3:
            # flip both
            s = "[%d:%d,%d:%d]" % (
                self.ccdsecX2,
                self.ccdsecX1,
                self.ccdsecY2,
                self.ccdsecY1,
            )

        hdu.header.set("AMPSEC", s, "Amplifier section", after=curpos)  # string
        curpos += 1

        # CCDSEC is not the same as DETSEC for a mosaic

        # amplifier's positions for CCDSEC
        if self.focalplane.detpos_x[ext_number - 1] > 1:
            Nx = (
                self.focalplane.extpos_x[ext_number - 1]
                - self.focalplane.detpos_x[ext_number - 1]
            )
        else:
            Nx = nx

        if self.focalplane.detpos_y[ext_number - 1] > 1:
            Ny = (
                self.focalplane.extpos_y[ext_number - 1]
                - self.focalplane.detpos_y[ext_number - 1]
            )
        else:
            Ny = ny

        # DETSEC is the region from the mosaic where this data is from
        # defines how image is displayed and includes flips

        if self.focalplane.numamps_x == 1:
            lastCol = self.focalplane.last_col
        else:
            lastCol = self.focalplane.ampvispix_x

        if self.focalplane.numamps_y == 1:
            lastRow = self.focalplane.last_row
        else:
            lastRow = self.focalplane.ampvispix_y

        skipX1 = self.focalplane.first_col - 1
        skipX2 = self.focalplane.ampvispix_x - self.focalplane.last_col
        if skipX2 < 0:
            skipX2 = 0
        skipY1 = self.focalplane.first_row - 1
        skipY2 = self.focalplane.ampvispix_y - self.focalplane.last_row
        if skipY2 < 0:
            skipY2 = 0

        skipX1bin = skipX1 / self.focalplane.col_bin
        skipY1bin = skipY1 / self.focalplane.row_bin

        if ampflip == 0:  # no flip
            flip_x = 1
            flip_y = 1

            # DETSEC
            xVal1 = (nx - 1) * self.focalplane.ampvispix_x + self.focalplane.first_col
            xVal2 = nx * lastCol
            yVal1 = (ny - 1) * self.focalplane.ampvispix_y + self.focalplane.first_row
            yVal2 = ny * lastRow

            # CCDSEC
            X_Val1 = (Nx - 1) * self.focalplane.ampvispix_x + self.focalplane.first_col
            X_Val2 = Nx * lastCol
            Y_Val1 = (Ny - 1) * self.focalplane.ampvispix_y + self.focalplane.first_row
            Y_Val2 = Ny * lastRow

            # CCDSEC1 binned version of CCDSEC - 15Aug12 Zareba
            xCCD1 = skipX1bin + 1
            if xCCD1 == 0:
                xCCD1 = 1
            xCCD2 = (self.focalplane.ampvispix_x - skipX1) / self.focalplane.col_bin
            if xCCD2 == 0:
                xCCD2 = 1

            yCCD1 = skipY1bin + 1
            if yCCD1 == 0:
                yCCD1 = 1
            yCCD2 = (self.focalplane.ampvispix_y - skipY2) / self.focalplane.row_bin
            if yCCD2 == 0:
                yCCD2 = 1

            s = "[%d:%d,%d:%d]" % (xVal1, xVal2, yVal1, yVal2)
        elif ampflip == 1:  # flip in x
            flip_x = -1
            flip_y = 1

            # DETSEC
            xVal1 = nx * lastCol
            xVal2 = (nx - 1) * self.focalplane.ampvispix_x + self.focalplane.first_col
            yVal1 = (ny - 1) * self.focalplane.ampvispix_y + self.focalplane.first_row
            yVal2 = ny * lastRow

            # CCDSEC
            X_Val1 = Nx * lastCol
            X_Val2 = (Nx - 1) * self.focalplane.ampvispix_x + self.focalplane.first_col
            Y_Val1 = (Ny - 1) * self.focalplane.ampvispix_y + self.focalplane.first_row
            Y_Val2 = Ny * lastRow

            # CCDSEC1 binned version of CCDSEC - 15Aug12 Zareba
            xCCD1 = (
                (Nx * self.focalplane.ampvispix_x) - skipX1
            ) / self.focalplane.col_bin
            if xCCD1 == 0:
                xCCD1 = 1
            xCCD2 = (
                (Nx - 1) * self.focalplane.ampvispix_x - skipX1
            ) / self.focalplane.col_bin + 1
            if xCCD2 == 0:
                xCCD2 = 1

            yCCD1 = skipY1bin + 1
            if yCCD1 == 0:
                yCCD1 = 1
            yCCD2 = (self.focalplane.ampvispix_y - skipY2) / self.focalplane.row_bin
            if yCCD2 == 0:
                yCCD2 = 1

            s = "[%d:%d,%d:%d]" % (xVal1, xVal2, yVal1, yVal2)
        elif ampflip == 2:  # flip in y
            flip_x = 1
            flip_y = -1

            # DETSEC
            xVal1 = (nx - 1) * self.focalplane.ampvispix_x + self.focalplane.first_col
            xVal2 = nx * lastCol
            yVal1 = ny * lastRow
            yVal2 = (ny - 1) * self.focalplane.ampvispix_y + self.focalplane.first_row

            # CCDSEC
            X_Val1 = (Nx - 1) * self.focalplane.ampvispix_x + self.focalplane.first_col
            X_Val2 = Nx * lastCol
            Y_Val1 = Ny * lastRow
            Y_Val2 = (Ny - 1) * self.focalplane.ampvispix_y + self.focalplane.first_row

            # CCDSEC1 binned version of CCDSEC - 15Aug12 Zareba

            xCCD1 = skipX1bin + 1
            if xCCD1 == 0:
                xCCD1 = 1
            xCCD2 = (self.focalplane.ampvispix_x - skipX1) / self.focalplane.col_bin
            if xCCD2 == 0:
                xCCD2 = 1

            yCCD1 = (
                (Ny * self.focalplane.ampvispix_y) - skipY1
            ) / self.focalplane.row_bin
            if yCCD1 == 0:
                yCCD1 = 1
            yCCD2 = (
                (Ny - 1) * self.focalplane.ampvispix_y - skipY1
            ) / self.focalplane.row_bin + 1
            if yCCD2 == 0:
                yCCD2 = 1

            s = "[%d:%d,%d:%d]" % (xVal1, xVal2, yVal1, yVal2)
        elif ampflip == 3:  # flip both
            flip_x = -1
            flip_y = -1

            # DETSEC
            xVal1 = nx * lastCol
            xVal2 = (nx - 1) * self.focalplane.ampvispix_x + self.focalplane.first_col
            yVal1 = ny * lastRow
            yVal2 = (ny - 1) * self.focalplane.ampvispix_y + self.focalplane.first_row

            # CCDSEC
            X_Val1 = Nx * lastCol
            X_Val2 = (Nx - 1) * self.focalplane.ampvispix_x + self.focalplane.first_col
            Y_Val1 = Ny * lastRow
            Y_Val2 = (Ny - 1) * self.focalplane.ampvispix_y + self.focalplane.first_row

            # CCDSEC1 binned version of CCDSEC
            xCCD1 = (
                (Nx - 1) * self.focalplane.ampvispix_x - skipX1
            ) / self.focalplane.col_bin + 1
            if xCCD1 == 0:
                xCCD1 = 1
            xCCD2 = (
                (Nx * self.focalplane.ampvispix_x) - skipX1
            ) / self.focalplane.col_bin
            if xCCD2 == 0:
                xCCD2 = 1

            yCCD1 = (
                (Ny * self.focalplane.ampvispix_y) - skipY1
            ) / self.focalplane.row_bin
            if yCCD1 == 0:
                yCCD1 = 1
            yCCD2 = (
                (Ny - 1) * self.focalplane.ampvispix_y - skipY1
            ) / self.focalplane.row_bin + 1
            if yCCD2 == 0:
                yCCD2 = 1

            s = "[%d:%d,%d:%d]" % (xVal1, xVal2, yVal1, yVal2)

        x_Val1 = float(xVal1)
        y_Val1 = float(yVal1)
        y_Val2 = float(yVal2)
        x_Val2 = float(xVal2)  # ? added 07sep24

        # do not overwrite x_Val1 and y_Val2; these are needed to calculate LTV1 and LTV2
        hdu.header.set("DETSEC", s, "Detector section", after=curpos)
        curpos += 1

        s = "[%d:%d,%d:%d]" % (X_Val1, X_Val2, Y_Val1, Y_Val2)
        hdu.header.set("CCDSEC", s, "CCD section", after=curpos)
        curpos += 1

        s = "[%d:%d,%d:%d]" % (xCCD1, xCCD2, yCCD1, yCCD2)
        hdu.header.set(
            "CCDSEC1", s, "CCD section with binning", after=curpos
        )  # extra keyword 14Sep10

        curpos += 1

        # other versions of same info
        hdu.header.set(
            "OVRSCAN1", self.focalplane.xoverscan, "Overscan on axis 1", after=curpos
        )
        curpos += 1
        hdu.header.set(
            "OVRSCAN2", self.focalplane.yoverscan, "Overscan on axis 2", after=curpos
        )
        curpos += 1
        hdu.header.set(
            "PRESCAN1", self.focalplane.xunderscan, "Underscan on axis 1", after=curpos
        )
        curpos += 1
        hdu.header.set(
            "PRESCAN2", self.focalplane.yunderscan, "Underscan on axis 2", after=curpos
        )
        curpos += 1

        # include CCDSUM
        s = "%s %s" % (self.focalplane.col_bin, self.focalplane.row_bin)
        hdu.header.set("CCDSUM", s, "CCD pixel summing", after=curpos)
        curpos += 1

        if self.focalplane.numamps_image > 1:
            self.focalplane.wcs.ltm_1_1[ext_number - 1] = flip_x / float(
                self.focalplane.col_bin
            )
            self.focalplane.wcs.ltm_2_2[ext_number - 1] = flip_y / float(
                self.focalplane.row_bin
            )

            if self.focalplane.split_physical_coords == 1:
                # split physical coordinates
                self.focalplane.wcs.ltv_1[ext_number - 1] = (
                    -flip_x * X_Val1 + 1
                ) / float(self.focalplane.col_bin)
                self.focalplane.wcs.ltv_2[ext_number - 1] = (
                    -flip_y * Y_Val1 + 1
                ) / float(self.focalplane.row_bin)
            else:
                # combine physical coordinates
                self.focalplane.wcs.ltv_1[ext_number - 1] = (
                    -flip_x * x_Val1 + 1
                ) / float(self.focalplane.col_bin)
                self.focalplane.wcs.ltv_2[ext_number - 1] = (
                    -flip_y * y_Val1 + 1
                ) / float(self.focalplane.row_bin)

            # include LTM1_1, LTM2_2, LTV1, and LTV2
            hdu.header.set(
                "LTM1_1",
                self.focalplane.wcs.ltm_1_1[ext_number - 1],
                "CCD to image transformation",
                after=curpos,
            )
            curpos += 1
            hdu.header.set(
                "LTM2_2",
                self.focalplane.wcs.ltm_2_2[ext_number - 1],
                "CCD to image transformation",
                after=curpos,
            )
            curpos += 1
            hdu.header.set(
                "LTV1",
                self.focalplane.wcs.ltv_1[ext_number - 1],
                "CCD to image transformation",
                after=curpos,
            )
            curpos += 1
            hdu.header.set(
                "LTV2",
                self.focalplane.wcs.ltv_2[ext_number - 1],
                "CCD to image transformation",
                after=curpos,
            )
            curpos += 1

            self.focalplane.wcs.atm_1_1[ext_number - 1] = flip_x
            self.focalplane.wcs.atm_2_2[ext_number - 1] = flip_y

            Ns = self.focalplane.ampvispix_x
            Np = self.focalplane.ampvispix_y

            if flip_x == -1:
                ext = 1
            else:
                ext = 0

            if self.focalplane.split_physical_coords == 1:
                # ATV1 for split physical coordinates
                if self.focalplane.wcs.atm_1_1[ext_number - 1] == 1:
                    self.focalplane.wcs.atv1[ext_number - 1] = -(Ns * (Nx - 1) + ext)
                else:
                    self.focalplane.wcs.atv1[ext_number - 1] = Ns * Nx + ext
            else:
                # ATV1 for combined physical coordinates
                if self.focalplane.wcs.atm_1_1[ext_number - 1] == 1:
                    self.focalplane.wcs.atv1[ext_number - 1] = -(
                        Ns * (self.focalplane.extpos_x[ext_number - 1] - 1) + ext
                    )
                else:
                    self.focalplane.wcs.atv1[ext_number - 1] = (
                        Ns * self.focalplane.extpos_x[ext_number - 1] + ext
                    )

            if flip_y == -1:
                ext = 1
            else:
                ext = 0

            if self.focalplane.split_physical_coords == 1:
                # ATV2 for split physical coordinates
                if self.focalplane.wcs.atm_2_2[ext_number - 1] == 1:
                    self.focalplane.wcs.atv2[ext_number - 1] = -(Np * (Ny - 1) + ext)
                else:
                    self.focalplane.wcs.atv2[ext_number - 1] = Np * Ny + ext
            else:
                # ATV2 for combined physical coordinates
                if self.focalplane.wcs.atm_2_2[ext_number - 1] == 1:
                    self.focalplane.wcs.atv2[ext_number - 1] = -(
                        Np * (self.focalplane.extpos_y[ext_number - 1] - 1) + ext
                    )
                else:
                    self.focalplane.wcs.atv2[ext_number - 1] = (
                        Np * self.focalplane.extpos_y[ext_number - 1] + ext
                    )

            # include ATM1_1, ATM2_2, ATV1, and ATV2
            hdu.header.set(
                "ATM1_1",
                self.focalplane.wcs.atm_1_1[ext_number - 1],
                "CCD to amplifier transformation",
                after=curpos,
            )
            curpos += 1
            hdu.header.set(
                "ATM2_2",
                self.focalplane.wcs.atm_2_2[ext_number - 1],
                "CCD to amplifier transformation",
                after=curpos,
            )
            curpos += 1
            hdu.header.set(
                "ATV1",
                self.focalplane.wcs.atv1[ext_number - 1],
                "CCD to amplifier transformation",
                after=curpos,
            )
            curpos += 1
            hdu.header.set(
                "ATV2",
                self.focalplane.wcs.atv2[ext_number - 1],
                "CCD to amplifier transformation",
                after=curpos,
            )
            curpos += 1

            # calculate CCD to detector transformation matrix and vectors

            # DTV1 and DTV2 set to 0 combines physical coordinates for all CCDs
            self.focalplane.wcs.dtm_1_1[ext_number - 1] = 1
            self.focalplane.wcs.dtm_2_2[ext_number - 1] = 1

            if self.focalplane.split_physical_coords == 1:
                # DTV1 and DTV2 for split physical coordinates
                self.focalplane.wcs.dtv_1[ext_number - 1] = (
                    (self.focalplane.detpos_x[ext_number - 1] - 1)
                    * self.focalplane.ampvispix_x
                    * self.focalplane.num_par_amps_det
                )
                self.focalplane.wcs.dtv_2[ext_number - 1] = (
                    (self.focalplane.detpos_y[ext_number - 1] - 1)
                    * self.focalplane.ampvispix_y
                    * self.focalplane.num_ser_amps_det
                )
            else:
                # DTV1 and DTV2 for combined physical coordinates
                self.focalplane.wcs.dtv_1[ext_number - 1] = 0
                self.focalplane.wcs.dtv_2[ext_number - 1] = 0

            # include DTM1_1, DTM2_2, DTV1, and DTV2
            hdu.header.set(
                "DTM1_1",
                self.focalplane.wcs.dtm_1_1[ext_number - 1],
                "CCD to detector transformation",
                after=curpos,
            )
            curpos += 1
            hdu.header.set(
                "DTM2_2",
                self.focalplane.wcs.dtm_2_2[ext_number - 1],
                "CCD to detector transformation",
                after=curpos,
            )
            curpos += 1
            hdu.header.set(
                "DTV1",
                self.focalplane.wcs.dtv_1[ext_number - 1],
                "CCD to detector transformation",
                after=curpos,
            )
            curpos += 1
            hdu.header.set(
                "DTV2",
                self.focalplane.wcs.dtv_2[ext_number - 1],
                "CCD to detector transformation",
                after=curpos,
            )
            curpos += 1
        else:
            # detectors with single amplifer

            # calculate CCD to image transformation matrix and vectors
            self.focalplane.wcs.ltm_1_1[ext_number - 1] = flip_x / float(
                self.focalplane.col_bin
            )
            self.focalplane.wcs.ltm_2_2[ext_number - 1] = flip_y / float(
                self.focalplane.row_bin
            )

            self.focalplane.wcs.ltv_1[ext_number - 1] = (
                self.datasecx1
                - self.focalplane.wcs.ltm_1_1[ext_number - 1] * x_Val1
                - 0.5 * (1 - self.focalplane.wcs.ltm_1_1[ext_number - 1])
            )
            self.focalplane.wcs.ltv_2[ext_number - 1] = (
                self.datasecy2
                - self.focalplane.wcs.ltm_2_2[ext_number - 1] * y_Val2
                - 0.5 * (1 - self.focalplane.wcs.ltm_2_2[ext_number - 1])
            )

            # include LTM1_1, LTM2_2, LTV1, and LTV2
            hdu.header.set(
                "LTM1_1",
                self.focalplane.wcs.ltm_1_1[ext_number - 1],
                "CCD to image transformation",
                after=curpos,
            )
            curpos += 1
            hdu.header.set(
                "LTM2_2",
                self.focalplane.wcs.ltm_2_2[ext_number - 1],
                "CCD to image transformation",
                after=curpos,
            )
            curpos += 1
            hdu.header.set(
                "LTV1",
                self.focalplane.wcs.ltv_1[ext_number - 1],
                "CCD to image transformation",
                after=curpos,
            )
            curpos += 1
            hdu.header.set(
                "LTV2",
                self.focalplane.wcs.ltv_2[ext_number - 1],
                "CCD to image transformation",
                after=curpos,
            )
            curpos += 1

            self.focalplane.wcs.atm_1_1[ext_number - 1] = flip_x
            self.focalplane.wcs.atm_2_2[ext_number - 1] = flip_y

            Ns = self.focalplane.ampvispix_x
            Np = self.focalplane.ampvispix_y

            if Nx > 1:
                ext = 1
            else:
                ext = 0

            if self.focalplane.wcs.atm_1_1[ext_number - 1] == 1:
                self.focalplane.wcs.atv1[ext_number - 1] = -(
                    Ns * (self.focalplane.extpos_x[ext_number - 1] - 1) + ext
                )
            else:
                self.focalplane.wcs.atv1[ext_number - 1] = (
                    Ns * self.focalplane.extpos_x[ext_number - 1] + ext
                )

            if Ny > 1:
                ext = 1
            else:
                ext = 0

            if self.focalplane.wcs.atm_2_2[ext_number - 1] == 1:
                self.focalplane.wcs.atv2[ext_number - 1] = -(
                    Np * (self.focalplane.extpos_y[ext_number - 1] - 1) + ext
                )
            else:
                self.focalplane.wcs.atv2[ext_number - 1] = (
                    Np * self.focalplane.extpos_y[ext_number - 1] + ext
                )

            hdu.header.set(
                "ATM1_1",
                self.focalplane.wcs.atm_1_1[ext_number - 1],
                "CCD to amplifier transformation",
                after=curpos,
            )
            curpos += 1
            hdu.header.set(
                "ATM2_2",
                self.focalplane.wcs.atm_2_2[ext_number - 1],
                "CCD to amplifier transformation",
                after=curpos,
            )
            curpos += 1
            hdu.header.set(
                "ATV1",
                self.focalplane.wcs.atv1[ext_number - 1],
                "CCD to amplifier transformation",
                after=curpos,
            )
            curpos += 1
            hdu.header.set(
                "ATV2",
                self.focalplane.wcs.atv2[ext_number - 1],
                "CCD to amplifier transformation",
                after=curpos,
            )
            curpos += 1

            # DTV1 and DTV2 are set to 0 since there is only one CCD
            self.focalplane.wcs.dtm_1_1[ext_number - 1] = 1
            self.focalplane.wcs.dtm_2_2[ext_number - 1] = 1

            self.focalplane.wcs.dtv_1[ext_number - 1] = 0
            self.focalplane.wcs.dtv_2[ext_number - 1] = 0

            hdu.header.set(
                "DTM1_1",
                self.focalplane.wcs.dtm_1_1[ext_number - 1],
                "CCD to detector transformation",
                after=curpos,
            )
            curpos += 1
            hdu.header.set(
                "DTM2_2",
                self.focalplane.wcs.dtm_2_2[ext_number - 1],
                "CCD to detector transformation",
                after=curpos,
            )
            curpos += 1
            hdu.header.set(
                "DTV1",
                self.focalplane.wcs.dtv_1[ext_number - 1],
                "CCD to detector transformation",
                after=curpos,
            )
            curpos += 1
            hdu.header.set(
                "DTV2",
                self.focalplane.wcs.dtv_2[ext_number - 1],
                "CCD to detector transformation",
                after=curpos,
            )
            curpos += 1

        return

    def _write_wcs_keywords(self, ext_number, hdu):
        """
        Define and write the WCS keywords to the header.
        ext_number starts at 1 (for MEF and FITS).
        """

        if not self.write_wcs:
            return

        curpos = len(hdu.header)
        hdu.header.add_comment(
            "==================================================================",
            after=curpos,
        )
        hdu.header.add_comment("WCS", after=curpos + 1)
        hdu.header.add_comment(
            "==================================================================",
            after=curpos + 2,
        )
        curpos = curpos + 3
        hdu.header.set(
            "EQUINOX", self.focalplane.wcs.equinox, "Equinox of WCS", after=curpos
        )
        curpos += 1
        hdu.header.set(
            "WCSDIM", self.focalplane.wcs.wcs_dim, "WCS Dimensionality", after=curpos
        )
        curpos += 1
        hdu.header.set(
            "CTYPE1", self.focalplane.wcs.ctype1, "Coordinate type", after=curpos
        )
        curpos += 1
        hdu.header.set(
            "CTYPE2", self.focalplane.wcs.ctype2, "Coordinate type", after=curpos
        )
        curpos += 1

        self.focalplane.wcs.get_ra_dec()

        if self.focalplane.wcs.ctype1.startswith("RA"):
            hdu.header.set(
                "CRVAL1",
                self.focalplane.wcs.ra_deg,
                "Coordinate reference value",
                after=curpos,
            )
            curpos += 1
            hdu.header.set(
                "CRVAL2",
                self.focalplane.wcs.dec_deg,
                "Coordinate reference value",
                after=curpos,
            )
        else:
            hdu.header.set(
                "CRVAL1",
                self.focalplane.wcs.dec_deg,
                "Coordinate reference value",
                after=curpos,
            )
            curpos += 1
            hdu.header.set(
                "CRVAL2",
                self.focalplane.wcs.ra_deg,
                "Coordinate reference value",
                after=curpos,
            )

        curpos += 1

        ampflip = self.focalplane.amp_cfg[ext_number - 1]  # from to 0 through 3
        if ampflip == 0:  # no flip
            flip_x = 1
            flip_y = 1
        elif ampflip == 1:  # flip in x
            flip_x = -1
            flip_y = 1
        elif ampflip == 2:  # flip in y
            flip_x = 1
            flip_y = -1
        elif ampflip == 3:  # flip both
            flip_x = -1
            flip_y = -1

        ref1 = (
            self.focalplane.refpix1 - self.focalplane.amppix1[ext_number - 1]
        ) * self.focalplane.wcs.atm_1_1[ext_number - 1]
        ref1 = (ref1 - (self.focalplane.first_col - 1)) / self.focalplane.col_bin

        ref2 = (
            self.focalplane.refpix2 - self.focalplane.amppix2[ext_number - 1]
        ) * self.focalplane.wcs.atm_2_2[ext_number - 1]
        ref2 = (ref2 - (self.focalplane.first_row - 1)) / self.focalplane.row_bin

        hdu.header.set("CRPIX1", ref1, "Coordinate reference pixel", after=curpos)
        curpos += 1
        hdu.header.set("CRPIX2", ref2, "Coordinate reference pixel", after=curpos)
        curpos += 1

        if self.focalplane.wcs.cd_matrix == 0:
            alfa = self.focalplane.wcs.rot_deg[ext_number - 1]

            CD1_1 = (
                self.focalplane.wcs.scale1[ext_number - 1]
                * self.focalplane.col_bin
                * math.cos(alfa * 2 * math.pi / 360.0)
            ) * flip_x
            CD1_2 = (
                self.focalplane.wcs.scale2[ext_number - 1]
                * self.focalplane.row_bin
                * (-math.sin(alfa * 2 * math.pi / 360.0))
            ) * flip_y
            CD2_1 = (
                self.focalplane.wcs.scale1[ext_number - 1]
                * self.focalplane.col_bin
                * math.sin(alfa * 2 * math.pi / 360.0)
            ) * flip_x
            CD2_2 = (
                self.focalplane.wcs.scale2[ext_number - 1]
                * self.focalplane.row_bin
                * math.cos(alfa * 2 * math.pi / 360.0)
            ) * flip_y

            hdu.header.set("CD1_1", CD1_1, "Coordinate matrix", after=curpos)
            curpos += 1
            hdu.header.set("CD1_2", CD1_2, "Coordinate matrix", after=curpos)
            curpos += 1
            hdu.header.set("CD2_1", CD2_1, "Coordinate matrix", after=curpos)
            curpos += 1
            hdu.header.set("CD2_2", CD2_2, "Coordinate matrix", after=curpos)
            curpos += 1
        else:
            hdu.header.set(
                "CD1_1",
                self.focalplane.wcs.cd_1_1[ext_number - 1],
                "Coordinate matrix",
                after=curpos,
            )
            curpos += 1
            hdu.header.set(
                "CD1_2",
                self.focalplane.wcs.cd_1_2[ext_number - 1],
                "Coordinate matrix",
                after=curpos,
            )
            curpos += 1
            hdu.header.set(
                "CD2_1",
                self.focalplane.wcs.cd_2_1[ext_number - 1],
                "Coordinate matrix",
                after=curpos,
            )
            curpos += 1
            hdu.header.set(
                "CD2_2",
                self.focalplane.wcs.cd_2_2[ext_number - 1],
                "Coordinate matrix",
                after=curpos,
            )
            curpos += 1

        return

    def _write_focalplane_keywords(self, ext_number, hdu):
        """
        Define and write the focal plane keywords to the header.
        ext_number starts at 1 (for MEF and FITS).
        """

        curpos = len(hdu.header)
        hdu.header.add_comment(
            "==================================================================",
            after=curpos,
        )
        hdu.header.add_comment("AzCam Focal plane", after=curpos + 1)
        hdu.header.add_comment(
            "==================================================================",
            after=curpos + 2,
        )
        curpos += 3
        hdu.header.set(
            "AMP-CFG",
            self.focalplane.amp_cfg[ext_number - 1],
            "Amplifier configuration",
            after=curpos,
        )
        curpos += 1
        hdu.header.set(
            "DET-NUM",
            self.focalplane.det_number[ext_number - 1],
            "Detector number",
            after=curpos,
        )
        curpos += 1
        hdu.header.set(
            "EXT-NUM",
            self.focalplane.ext_number[ext_number - 1],
            "extension number",
            after=curpos,
        )
        curpos += 1
        hdu.header.set(
            "JPG-EXT",
            self.focalplane.jpg_ext[ext_number - 1],
            "Image section",
            after=curpos,
        )
        curpos += 1
        hdu.header.set(
            "DET-POSX",
            self.focalplane.detpos_x[ext_number - 1],
            "Detector position in X",
            after=curpos,
        )
        curpos += 1
        hdu.header.set(
            "DET-POSY",
            self.focalplane.detpos_y[ext_number - 1],
            "Detector position in Y",
            after=curpos,
        )
        curpos += 1
        hdu.header.set(
            "Ext-PosX",
            self.focalplane.extpos_x[ext_number - 1],
            "Amplifier position in X",
            after=curpos,
        )
        curpos += 1
        hdu.header.set(
            "Ext-PosY",
            self.focalplane.extpos_y[ext_number - 1],
            "Amplifier position in Y",
            after=curpos,
        )
        curpos += 1
        hdu.header.set(
            "AMP-PIX1",
            self.focalplane.amppix1[ext_number - 1],
            "Amplifier pixel position in X",
            after=curpos,
        )
        curpos += 1
        hdu.header.set(
            "AMP-PIX2",
            self.focalplane.amppix2[ext_number - 1],
            "Amplifier pixel position in Y",
            after=curpos,
        )
        curpos += 1
        hdu.header.set(
            "GAIN",
            self.focalplane.gains[ext_number - 1],
            "Amplifier gain",
            after=curpos,
        )
        curpos += 1
        hdu.header.set(
            "RDNOISE",
            self.focalplane.rdnoises[ext_number - 1],
            "Amplifier read noise",
            after=curpos,
        )
        curpos += 1

        return
