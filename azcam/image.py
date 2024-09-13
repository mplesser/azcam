"""
Contains the Image class.
"""

import math
import os
import time
import warnings

import azcam
import azcam.utils
import azcam.exceptions
import numpy
from astropy.io import fits as pyfits
from azcam.header import Header
from azcam.image_focalplane import FocalPlane


class Image(object):
    """
    Class to create and manipulate the standard azcam image object.
    """

    def __init__(self, filename=""):
        super().__init__()

        self.is_valid = 0
        """True when image is valid"""
        self.is_written = 0
        """True when image has been written to disk"""
        self.toggle = 0
        """True when image is first ready"""
        self.filename = ""
        """image filename"""
        self.overwrite = 0
        """True to allow overwritting image file"""
        self.test_image = 0
        """True when the image is a test image (overwrite is automatic)"""
        self.make_lockfile = 0
        """ True to make a lock file when image is written"""
        self.filetype = 0
        """image file type"""
        self.title = ""
        """title string"""

        # image size - columns
        self.size_x = 0
        # image szie - rows
        self.size_y = 0
        # numpy image buffer for assembled image [y,x]
        self.buffer = []
        self.in_buffer = []
        self.out_buffer = []
        # True if image was read from a file
        self.from_file = 0
        # True if image was read from a file and has ITL header
        self.itl_header = 0

        self.transposed_image = 0
        self.flip_image = 0

        # WCS
        self.write_wcs = 1
        # set default values for the scale and offset
        self.scales = []
        self.offsets = []
        # numpy image data buffer
        self.data = []
        # display image
        self.display_image = 0

        # assembly
        self.assemble_image = 0
        # flag to trim overscan, True means trim
        self.trim = 1
        # True when image Data has been assembled into Buffer
        self.assembled = 0
        # True if image is trimmed
        self.trimmed = 0
        # assembled image size (may be different due to trimming the prescan and overscan)
        self.asmsize = (0, 0)

        # Data type (numpy array data type after reading) - default 16-bit integer
        self.data_type = 16
        # BITPIX value - before accessing data buffer
        self.bitpix = 16
        # BITPIX value - after accessing data buffer
        self.bitpix2 = 0
        # BZERO value
        self.bzero = 0
        # BSCALE value
        self.bscale = 0

        # data types for fits images
        self.data_types = {
            8: "uint8",
            16: "uint16",
            32: "uint32",
            64: "uint64",
            -32: "float32",
            -64: "float64",
        }
        self.filetypes = {"FITS": 0, "MEF": 1, "BIN": 2, "ASM": 6}
        # final data array type
        self.array_type = 0
        # Allows saving data using other data format than BITPIX2
        self.save_data_format = 16

        # sub-tools
        self.header = Header()
        self.focalplane = FocalPlane()
        self.asm_header = Header()  # Header for assembled image

        # read a file if specified when instance created
        if filename != "":
            self.read_file(filename)

    def read_file(self, filename: str):
        """
        Read FITS image file (standard or MEF).
        """

        filename = azcam.utils.make_image_filename(filename)
        self.filename = filename

        self.filetype = self.filetypes["FITS"]
        self.assembled = 0
        self.is_valid = 0
        self.toggle = 0

        self.header = Header(self)  # new header

        # read file
        self._read_fits_file(self.filename)

        return

    def write_file(self, filename: str, filetype: int = -1):
        """
        Write image to disk file.
        filetype is 0 for FITS, 1 for MEF, 2 for BIN, 6 for assembled.
        """

        filename = azcam.utils.make_image_filename(filename)
        self.filename = filename

        # delete file if it exists
        if self.overwrite and os.path.exists(filename):
            os.remove(filename)

        if self.test_image and os.path.exists(filename):
            os.remove(filename)

        if filetype == -1:
            filetype = self.filetype

        if filetype == 0:
            self._write_fits_file(filename)
        elif filetype == 1:
            self._write_mef_file(filename)
        elif filetype == 2:
            self._write_bin_file(filename)
        elif filetype == 6:
            self._write_asm_fits_file(filename)
        else:
            raise azcam.exceptions.AzcamError("Invalid filetype for Image")

        # optionally make a lock file indicating the image file has been written
        if self.make_lockfile:
            lockfile = filename.replace(".bin", ".OK")
            with open(lockfile, "w"):
                pass

        return

    def assemble(self, trim: int = -1):
        """
        Assemble .data into .buffer.
        """

        if not self.is_valid:
            raise azcam.exceptions.AzcamError("image is not valid")

        if self.assembled:
            return

        # update self.asmsize
        self.asmsize = (self.focalplane.numcols_image, self.focalplane.numrows_image)

        # create self.buffer which is a single numpy image buffer for a fully assembled
        # image [row,cols] or [y,x]) - if image is not read from file
        if self.from_file != 1:
            if self.data.dtype == "float64":
                self.buffer = numpy.empty(
                    shape=[self.size_y, self.size_x], dtype="float64"
                )
            else:
                self.buffer = numpy.empty(
                    shape=[self.size_y, self.size_x], dtype="float32"
                )

        Offsets = self.offsets
        Scales = self.scales

        if trim == 1:
            prescan1 = self.focalplane.numcols_underscan
            overscan1 = self.focalplane.numcols_overscan
            prescan2 = self.focalplane.numrows_underscan
            overscan2 = self.focalplane.numrows_overscan

            # update the assembled image size

            # 12Sep13 Zareba
            num_under = self.focalplane.numamps_x * self.focalplane.numcols_overscan
            num_over = self.focalplane.numamps_x * self.focalplane.numcols_underscan
            size_x = self.size_x - num_under - num_over

            # 12Sep13 Zareba
            num_under = self.focalplane.numamps_y * self.focalplane.numrows_overscan
            num_over = self.focalplane.numamps_y * self.focalplane.numrows_underscan
            size_y = self.size_y - num_under - num_over

            self.asmsize = (size_x, size_y)
            self.asmsize = self.asmsize
            imgSize = size_x * size_y

            # reshape Buffer
            self.buffer = numpy.resize(self.buffer, imgSize)
            self.buffer = self.buffer.reshape((self.asmsize[1], self.asmsize[0]))

        else:
            prescan1 = 0
            overscan1 = 0
            prescan2 = 0
            overscan2 = 0

            self.asmsize = (self.size_x, self.size_y)
            self.asmsize = self.asmsize
            imgSize = self.size_x * self.size_y

            # reschape Buffer - if needed
            if self.data.size != self.buffer.size:
                self.buffer = numpy.resize(self.buffer, imgSize)
                self.buffer = self.buffer.reshape((self.asmsize[1], self.asmsize[0]))

        # destination AmpX and AmpY size corrected for prescan and overscan values
        dstAmpX = self.focalplane.numcols_amp - prescan1 - overscan1
        dstAmpY = self.focalplane.numrows_amp - prescan2 - overscan2

        # source AmpX and AmpY size including prescan and overscan
        srcAmpX = self.focalplane.numcols_amp
        srcAmpY = self.focalplane.numrows_amp

        ampX = self.focalplane.numcols_amp
        ampY = self.focalplane.numrows_amp

        self.lineLen = ampX - prescan1 - overscan1

        self.startLine = prescan2
        self.stopLine = ampY - prescan2 - overscan2

        Ext = self.focalplane.jpg_ext
        AmpFlip = self.focalplane.amp_cfg

        pixNum = 0

        for parAmps in range(0, self.focalplane.num_par_amps_det):
            # remove the prescan and overscane lines from the image
            extBase = parAmps * self.focalplane.num_ser_amps_det

            srcLine = prescan2
            for line in range(parAmps * dstAmpY, parAmps * dstAmpY + dstAmpY):
                lineStart = 0

                for currExt in range(
                    extBase, extBase + self.focalplane.num_ser_amps_det
                ):
                    # copy one line from the current extension

                    indx = Ext[currExt] - 1  # current amplifier
                    flip = int(
                        AmpFlip[indx]
                    )  # determine flip for the current extension

                    if flip == 0:  # no flip
                        posX = srcLine * srcAmpX + prescan1
                        self.buffer[line][lineStart : lineStart + dstAmpX] = (
                            self.data[indx][posX : posX + dstAmpX] - Offsets[indx]
                        ) * Scales[indx]

                        lineStart += self.lineLen
                        pixNum += self.lineLen

                    if flip == 1:  # x flip: reverse the readout sequence
                        posX = srcLine * srcAmpX + prescan1
                        self.buffer[line][lineStart : lineStart + dstAmpX] = (
                            self.data[indx][posX : posX + dstAmpX][::-1] - Offsets[indx]
                        ) * Scales[indx]

                        lineStart += self.lineLen
                        pixNum += self.lineLen

                    if flip == 2:  # y flip: get the flip line
                        posX = (srcAmpY - srcLine - overscan2 - 1) * srcAmpX + prescan1
                        self.buffer[line][lineStart : lineStart + dstAmpX] = (
                            self.data[indx][posX : posX + dstAmpX] - Offsets[indx]
                        ) * Scales[indx]

                        lineStart += self.lineLen
                        pixNum += self.lineLen

                    if (
                        flip == 3
                    ):  # xy flip; get the flip line and reverse the readout sequence
                        posX = (srcAmpY - srcLine - prescan2 - 1) * srcAmpX + prescan1
                        self.buffer[line][lineStart : lineStart + dstAmpX] = (
                            self.data[indx][posX : posX + dstAmpX][::-1] - Offsets[indx]
                        ) * Scales[indx]

                        lineStart += self.lineLen
                        pixNum += self.lineLen

                srcLine += 1

        # reshape the Buffer to 2D
        self.buffer = self.buffer.reshape((self.asmsize[1], self.asmsize[0]))

        # set isAssembled
        self.assembled = 1

        # set isTrimmed
        if trim == 1:
            self.trimmed = 1

        return

    def set_scaling(
        self, gains: list[float] | None = None, offsets: list[float] | None = None
    ):
        """
        Set gains and offsets for image assembly.

        Args:
            gains: gains values for each image section in [e/DN]
            offsets: offsets or bias values for each image section
        """

        self.num_extensions = self.focalplane.numamps_image

        # set default values for the scale and offset
        self.scales = numpy.empty(shape=[self.num_extensions], dtype="f")
        for ext in range(self.num_extensions):
            self.scales[ext] = 1.0
        self.offsets = numpy.empty(shape=[self.num_extensions], dtype="f")
        for ext in range(self.num_extensions):
            self.offsets[ext] = 0.0

        if gains is None:
            gains = len(self.data) * [1.0]

        if offsets is None:
            offsets = len(self.data) * [0.0]

        # Scales is gain (inverse electrical gain)
        for chan in range(len(self.data)):
            self.scales[chan] = gains[chan]
            self.offsets[chan] = offsets[chan]

        return

    def _read_fits_file(self, filename):
        """
        Reads an image from a FITS or MEF disk file into the image structure.
        """

        self.assembled = 0
        self.is_valid = 0
        self.toggle = 0

        # clear focal plane header
        self.focalplane.header.delete_all_items()

        self.hdulist = pyfits.open(filename)
        if len(self.hdulist) == 2:
            NumExt = 0
            first_ext = 0
            last_ext = 1
        else:
            n = 0
            for i in range(len(self.hdulist)):
                if "XTENSION" in self.hdulist[i].header:
                    if self.hdulist[i].header["XTENSION"] == "IMAGE":
                        n += 1
            first_ext = 1
            last_ext = n + 1
            NumExt = n

        self.NumBinTables = 0  # temp
        self.num_extensions = NumExt

        # update number of amplifiers and number of extensions
        self.focalplane.numamps_image = max(1, NumExt) - self.NumBinTables
        cntExt = self.focalplane.numamps_image

        # update file type
        if self.num_extensions > 0:
            self.filetype = self.filetypes["MEF"]
        else:
            self.filetype = self.filetypes["FITS"]

        # get main header
        hdr = self.hdulist[0].header

        if self.num_extensions > 0:
            self.bitpix = self.hdulist[1].header["BITPIX"]
            try:
                self.bzero = self.hdulist[1].header["BZERO"]
                self.bscale = self.hdulist[1].header["BSCALE"]
            except KeyError:
                self.bzero = 0
                self.bscale = 0

            self.data_type = self.hdulist[1].data.dtype
            self.bitpix2 = self.hdulist[1].header["BITPIX"]
            self.save_data_format = self.bitpix
        else:
            self.bitpix = self.hdulist[0].header["BITPIX"]

            try:
                self.bzero = self.hdulist[0].header["BZERO"]
                self.bscale = self.hdulist[0].header["BSCALE"]
            except KeyError:
                self.bzero = 0
                self.bscale = 0

            self.data_type = self.hdulist[0].data.dtype
            self.bitpix2 = self.hdulist[0].header["BITPIX"]
            self.save_data_format = self.bitpix

        # get object name
        try:
            self.title = hdr["OBJECT"]
        except KeyError:
            self.title = ""

        # check ITL header
        try:
            ITLHead = hdr["ITL-HEAD"]
            if ITLHead == "OK":
                self.itl_header = 1
            else:
                self.itl_header = 0
        except KeyError:
            self.itl_header = 0

        # set Array type - output data type
        self.array_type = self.data_types[self.bitpix2]

        # check if first item is col bin or row bin
        try:
            self.focalplane.col_bin = hdr["CCDBIN1"]
            self.focalplane.row_bin = hdr["CCDBIN2"]
        except KeyError:
            self.focalplane.col_bin = 1
            self.focalplane.row_bin = 1

        self.focalplane.refpix1 = 0.0
        self.focalplane.refpix2 = 0.0

        if self.itl_header == 1:
            # create empty arrays for focal plane values
            self.focalplane.amp_cfg = numpy.ndarray(shape=(cntExt), dtype="<u2")
            self.focalplane.det_number = numpy.ndarray(shape=(cntExt), dtype="<u2")
            self.focalplane.ext_number = numpy.ndarray(shape=(cntExt), dtype="<u2")
            self.focalplane.jpg_ext = numpy.ndarray(shape=(cntExt), dtype="<u2")
            self.focalplane.detpos_x = numpy.ndarray(shape=(cntExt), dtype="<u2")
            self.focalplane.detpos_y = numpy.ndarray(shape=(cntExt), dtype="<u2")
            self.focalplane.amppos_x = numpy.ndarray(shape=(cntExt), dtype="<u2")
            self.focalplane.amppos_y = numpy.ndarray(shape=(cntExt), dtype="<u2")
            self.focalplane.amppix1 = numpy.ndarray(shape=(cntExt), dtype="<u2")
            self.focalplane.amppix2 = numpy.ndarray(shape=(cntExt), dtype="<u2")
            self.focalplane.gapx = numpy.ndarray(shape=(cntExt), dtype="float32")
            self.focalplane.gapy = numpy.ndarray(shape=(cntExt), dtype="float32")
            self.focalplane.extpos_x = numpy.ndarray(shape=(cntExt), dtype="<u2")
            self.focalplane.extpos_y = numpy.ndarray(shape=(cntExt), dtype="<u2")

            self.focalplane.ext_name = cntExt * [""]

            # prepare arrays for image transformations
            self.focalplane.wcs.atm_1_1 = numpy.ndarray(shape=(cntExt), dtype="<i2")
            self.focalplane.wcs.atm_2_2 = numpy.ndarray(shape=(cntExt), dtype="<i2")
            self.focalplane.wcs.atv1 = numpy.ndarray(shape=(cntExt), dtype="<i2")
            self.focalplane.wcs.atv2 = numpy.ndarray(shape=(cntExt), dtype="<i2")
            self.focalplane.wcs.ltm_1_1 = numpy.ndarray(shape=(cntExt), dtype="<i2")
            self.focalplane.wcs.ltm_2_2 = numpy.ndarray(shape=(cntExt), dtype="<i2")
            self.focalplane.wcs.ltv_1 = numpy.ndarray(shape=(cntExt), dtype="float32")
            self.focalplane.wcs.ltv_2 = numpy.ndarray(shape=(cntExt), dtype="float32")
            self.focalplane.wcs.dtm_1_1 = numpy.ndarray(shape=(cntExt), dtype="<i2")
            self.focalplane.wcs.dtm_2_2 = numpy.ndarray(shape=(cntExt), dtype="<i2")
            self.focalplane.wcs.dtv_1 = numpy.ndarray(shape=(cntExt), dtype="<i2")
            self.focalplane.wcs.dtv_2 = numpy.ndarray(shape=(cntExt), dtype="<i2")

            # prepare arrays for WCS
            self.focalplane.wcs.rot_deg = numpy.ndarray(shape=(cntExt), dtype="float32")
            self.focalplane.wcs.scale1 = numpy.ndarray(shape=(cntExt), dtype="float32")
            self.focalplane.wcs.scale2 = numpy.ndarray(shape=(cntExt), dtype="float32")
            self.focalplane.wcs.cd_1_1 = numpy.ndarray(shape=(cntExt), dtype="float32")
            self.focalplane.wcs.cd_1_2 = numpy.ndarray(shape=(cntExt), dtype="float32")
            self.focalplane.wcs.cd_2_1 = numpy.ndarray(shape=(cntExt), dtype="float32")
            self.focalplane.wcs.cd_2_2 = numpy.ndarray(shape=(cntExt), dtype="float32")

            # read focal plane keywords from the main header
            try:
                self.focalplane.numdet_x = hdr["NUM-DETX"]
                self.focalplane.numdet_y = hdr["NUM-DETY"]
                self.focalplane.numamps_x = hdr["NUM-AMPX"]
                self.focalplane.numamps_y = hdr["NUM-AMPY"]
                self.focalplane.refpix1 = hdr["REF-PIX1"]
                self.focalplane.refpix2 = hdr["REF-PIX2"]

                # update num_ser_amps_det and num_par_amps_det
                self.focalplane.num_ser_amps_det = self.focalplane.numamps_x
                self.focalplane.num_par_amps_det = self.focalplane.numamps_y
            except KeyError:
                pass

            if NumExt == 0:
                try:
                    self.focalplane.amp_cfg[0] = hdr["AMP-CFG"]
                    self.focalplane.det_number[0] = hdr["DET-NUM"]
                    self.focalplane.ext_number[0] = hdr["EXT-NUM"]
                    self.focalplane.jpg_ext[0] = hdr["JPG-EXT"]
                    self.focalplane.detpos_x[0] = hdr["DET-POSX"]
                    self.focalplane.detpos_y[0] = hdr["DET-POSY"]
                    self.focalplane.amppos_x[0] = hdr["AMP-POSX"]
                    self.focalplane.amppos_y[0] = hdr["AMP-POSY"]
                    self.focalplane.amppix1[0] = hdr["AMP-PIX1"]
                    self.focalplane.amppix2[0] = hdr["AMP-PIX2"]
                except KeyError:
                    pass
        else:
            pass

        if NumExt == 0:
            # single extension file
            numcols = hdr["NAXIS1"]  # includes overscan
            numrows = hdr["NAXIS2"]
            numcols = int(numcols)
            numrows = int(numrows)

            # get image size
            self.size_x = numcols
            self.size_y = numrows

            self.focalplane.numcols_amp = numcols
            self.focalplane.numrows_amp = numrows
            self.focalplane.numpix_amp = numrows * numcols
            self.focalplane.numcols_image = numcols
            self.focalplane.numrows_image = numrows
            self.focalplane.numpixels = numrows * numcols

            # read overscan and prescan values
            try:
                self.focalplane.numcols_overscan = hdr["OVRSCAN1"]
                self.focalplane.numrows_overscan = hdr["OVRSCAN2"]
                self.focalplane.numcols_underscan = hdr["PRESCAN1"]
                self.focalplane.numrows_underscan = hdr["PRESCAN1"]
            except KeyError:
                pass

            # create offsets and scales arrays with default values
            self.offsets = numpy.empty(shape=[1], dtype="float32")
            self.scales = numpy.empty(shape=[1], dtype="float32")
            self.offsets[0] = 0.0
            self.scales[0] = 1.0

        else:
            # multiple extension file
            try:
                hdr = pyfits.getheader(filename, 1)
                section = hdr[
                    "DATASEC"
                ]  # includes overscan, total binned pixels per amp
                section = section.lstrip("[")
                section = section.split(":")
                fc = int(section[0])
                section1 = section[1].split(",")
                lc = int(section1[0])
                fr = int(section1[1])
                lr = int(section[2].rstrip("]"))
                numrows = lr - fr + 1
                numcols = lc - fc + 1

                self.focalplane.numviscols_amp = numcols
                self.focalplane.numvisrows_amp = numrows

                numcols = int(hdr["NAXIS1"])
                numrows = int(hdr["NAXIS2"])

                hdr = pyfits.getheader(filename, 0)
                self.focalplane.numamps_image = int(hdr["NAMPS"])
            except KeyError:
                pass

            # overscan and underscan taken from the first extension
            try:
                self.focalplane.numcols_overscan = self.hdulist[1].header["OVRSCAN1"]
                self.focalplane.numcols_underscan = self.hdulist[1].header["PRESCAN1"]
                self.focalplane.numrows_overscan = self.hdulist[1].header["OVRSCAN2"]
                self.focalplane.numrows_underscan = self.hdulist[1].header["PRESCAN2"]
            except KeyError:
                self.focalplane.numcols_overscan = 0
                self.focalplane.numcols_underscan = 0
                self.focalplane.numrows_overscan = 0
                self.focalplane.numrows_underscan = 0

            self.focalplane.num_amps_det = NumExt
            self.focalplane.numpix_amp = numrows * numcols
            self.focalplane.numcols_amp = numcols
            self.focalplane.numrows_amp = numrows

            self.focalplane.numcols_image = numcols * self.focalplane.num_ser_amps_det
            self.focalplane.numpixels = (
                self.focalplane.numpix_amp * self.focalplane.numamps_image
            )
            self.focalplane.numrows_image = numrows * self.focalplane.num_par_amps_det

            self.size_x = numcols * self.focalplane.num_ser_amps_det
            self.size_y = numrows * self.focalplane.num_par_amps_det

            # create offsets and scales arrays with default values
            self.offsets = numpy.empty(shape=[last_ext - 1], dtype="float32")
            self.scales = numpy.empty(shape=[last_ext - 1], dtype="float32")

            for indx in range(0, NumExt):
                self.offsets[indx] = 0.0
                self.scales[indx] = 1.0

            if self.itl_header == 1:
                for indx in range(1, NumExt + 1):
                    try:
                        self.focalplane.amp_cfg[indx - 1] = self.hdulist[indx].header[
                            "AMP-CFG"
                        ]
                        self.focalplane.det_number[indx - 1] = self.hdulist[
                            indx
                        ].header["DET-NUM"]
                        self.focalplane.ext_number[indx - 1] = self.hdulist[
                            indx
                        ].header["EXT-NUM"]
                        self.focalplane.jpg_ext[indx - 1] = self.hdulist[indx].header[
                            "JPG-EXT"
                        ]
                        self.focalplane.detpos_x[indx - 1] = self.hdulist[indx].header[
                            "DET-POSX"
                        ]
                        self.focalplane.detpos_y[indx - 1] = self.hdulist[indx].header[
                            "DET-POSY"
                        ]
                        self.focalplane.extpos_x[indx - 1] = self.hdulist[indx].header[
                            "EXT-POSX"
                        ]
                        self.focalplane.extpos_y[indx - 1] = self.hdulist[indx].header[
                            "EXT-POSY"
                        ]
                        self.focalplane.amppix1[indx - 1] = self.hdulist[indx].header[
                            "AMP-PIX1"
                        ]
                        self.focalplane.amppix2[indx - 1] = self.hdulist[indx].header[
                            "AMP-PIX2"
                        ]
                        # self.focalplane.refpix1[indx - 1] = self.hdulist[indx].header["CRPIX1"]
                        # self.focalplane.refpix2[indx - 1] = self.hdulist[indx].header["CRPIX2"]

                        self.focalplane.ext_name[indx - 1] = f"IM{indx}"  # new

                        DetSec = self.hdulist[indx].header["DETSEC"]
                        DetSec = (DetSec.lstrip("[").rstrip("]")).split(",")

                        self.focalplane.gapx[indx - 1] = float(
                            self.focalplane.amppix1[indx - 1]
                        ) - float(DetSec[0].split(":")[0])
                        self.focalplane.gapy[indx - 1] = float(
                            self.focalplane.amppix2[indx - 1]
                        ) - float(DetSec[1].split(":")[0])

                        self.focalplane.amppos_x[indx - 1] = self.hdulist[indx].header[
                            "AMP-POSX"
                        ]
                        self.focalplane.amppos_y[indx - 1] = self.hdulist[indx].header[
                            "AMP-POSY"
                        ]

                    except KeyError:
                        pass

                    # read the WCS keywords from main header
                    try:
                        # image transformation keywords
                        self.focalplane.wcs.atm_1_1[indx - 1] = self.hdulist[
                            indx
                        ].header["ATM1_1"]
                        self.focalplane.wcs.atm_2_2[indx - 1] = self.hdulist[
                            indx
                        ].header["ATM2_2"]
                        self.focalplane.wcs.atv1[indx - 1] = self.hdulist[indx].header[
                            "ATV1"
                        ]
                        self.focalplane.wcs.ltv_2[indx - 1] = self.hdulist[indx].header[
                            "ATV2"
                        ]
                        self.focalplane.wcs.ltm_1_1[indx - 1] = self.hdulist[
                            indx
                        ].header["LTM1_1"]
                        self.focalplane.wcs.ltm_2_2[indx - 1] = self.hdulist[
                            indx
                        ].header["LTM2_2"]
                        self.focalplane.wcs.ltv_1[indx - 1] = self.hdulist[indx].header[
                            "LTV1"
                        ]
                        self.focalplane.wcs.ltv_2[indx - 1] = self.hdulist[indx].header[
                            "LTV2"
                        ]
                        self.focalplane.wcs.dtm_1_1[indx - 1] = self.hdulist[
                            indx
                        ].header["DTM1_1"]
                        self.focalplane.wcs.dtm_2_2[indx - 1] = self.hdulist[
                            indx
                        ].header["DTM2_2"]
                        self.focalplane.wcs.dtv_1[indx - 1] = self.hdulist[indx].header[
                            "DTV1"
                        ]
                        self.focalplane.wcs.dtv_2[indx - 1] = self.hdulist[indx].header[
                            "DTV2"
                        ]

                        # WCS keywords
                        self.focalplane.wcs.rot_deg[indx - 1] = self.hdulist[
                            indx
                        ].header["ROT-DEG"]
                        self.focalplane.wcs.scale1[indx - 1] = self.hdulist[
                            indx
                        ].header["SCALE1"]
                        self.focalplane.wcs.scale2[indx - 1] = self.hdulist[
                            indx
                        ].header["SCALE2"]
                        self.focalplane.wcs.cd_1_1[indx - 1] = self.hdulist[
                            indx
                        ].header["CD1_1"]
                        self.focalplane.wcs.cd_1_2[indx - 1] = self.hdulist[
                            indx
                        ].header["CD1_2"]
                        self.focalplane.wcs.cd_2_1[indx - 1] = self.hdulist[
                            indx
                        ].header["CD2_1"]
                        self.focalplane.wcs.cd_2_2[indx - 1] = self.hdulist[
                            indx
                        ].header["CD2_2"]

                    except KeyError:
                        pass

        # ---------------------------- data -------------------------------------------------------

        # create .data numpy array and scale data,
        #    .hdulist[0].data is [nrows][ncols] -> .data[0] is the first row
        if NumExt == 0:
            self.data = numpy.ndarray(
                shape=(1, self.focalplane.numpix_amp),
                buffer=self.hdulist[0].data,
                dtype=self.data_type,
            ).copy()
        else:
            self.data = numpy.empty(
                shape=[self.focalplane.numamps_image, self.focalplane.numpix_amp],
                dtype=self.data_type,
            ).copy()

            for chan in range(first_ext, last_ext):
                self.data[chan - 1, :] = numpy.ndarray(
                    shape=(self.focalplane.numpix_amp),
                    buffer=self.hdulist[chan].data,
                    dtype=self.data_type,
                ).copy()

        # take care of the big-endian/little-endian format
        if self.array_type == "float64":
            self.data = self.data.astype("float64")
        else:
            self.data = self.data.astype("float32")

        self.hdulist.close()

        self.is_valid = 1

        if self.array_type == "float64":
            self.buffer = numpy.empty(shape=[self.size_y, self.size_x], dtype="float64")

            self.in_buffer = numpy.empty(
                shape=[self.size_y, self.size_x], dtype="float64"
            )
            self.out_buffer = numpy.empty(
                shape=[self.size_y, self.size_x], dtype="float64"
            )
            self.in_buffer = self.data.astype("float64")
        else:
            self.buffer = numpy.empty(shape=[self.size_y, self.size_x], dtype="float32")

            self.in_buffer = numpy.empty(
                shape=[self.size_y, self.size_x], dtype="float32"
            )
            self.out_buffer = numpy.empty(
                shape=[self.size_y, self.size_x], dtype="float32"
            )
            self.in_buffer = self.data.astype("float32")

        # set flags
        self.from_file = 1
        self.is_written = 1

        return

    def _write_fits_file(self, filename, filetype=0):
        """
        Write the FITS or MEF image to disk
        filetype is 0, 1, or 6 for FITS, MEF, or assembled.
        """

        Overwrite = self.overwrite or self.test_image

        fldr = os.path.dirname(filename)
        fldr = os.path.normpath(fldr)
        if fldr != "" and not os.path.exists(fldr):
            s = f"folder {fldr} does not exist"
            raise FileNotFoundError(s)

        # ERROR if file exists and overwrite flag not set
        if os.path.exists(filename):
            if Overwrite:
                loop = 0
                while loop < 10:
                    try:
                        os.remove(filename)
                        break
                    except Exception as details:
                        s = "ERROR deleting previous image file: %s" % repr(details)
                        loop += 1
                        time.sleep(0.5)
                if loop > 10:
                    return ["ERROR", s]
            else:
                s = "ERROR " + filename + " exists but Overwrite flag is not set"
                return ["ERROR", s]

        # assemble image as needed
        if self.assemble_image:
            self.assemble()

        if filetype == self.filetypes["FITS"]:
            self._write_standardfits_file(filename)
        elif filetype == self.filetypes["MEF"]:
            self._write_mef_file(filename)
        elif filetype == self.filetypes["ASM"]:
            self._write_asm_fits_file(filename)

        return

    def _write_standardfits_file(self, filename):
        """
        Write a standard (non-MEF) FITS file.
        """

        # allow case sensitive ext_name
        pyfits.EXTENSION_NAME_CASE_SENSITIVE = True

        # make PHU with data
        if self.focalplane.numamps_image == 1:
            if self.transposed_image:
                nx = self.focalplane.numcols_image
                ny = self.focalplane.numrows_image
            else:
                nx = self.focalplane.numrows_image
                ny = self.focalplane.numcols_image
            data = numpy.ndarray(
                shape=(nx, ny),
                dtype=self.data_types[self.save_data_format],
                buffer=self.data[0],
            )
            if self.transposed_image:
                data = data.transpose()
            if self.flip_image:
                data = numpy.flipud(data)
            hdu = pyfits.PrimaryHDU(data=data)
        else:
            if not self.assembled:
                self.assemble(1)
            hdu = pyfits.PrimaryHDU(data=self.buffer)

        # add header cards to PHU
        hdu.header.set("NAXIS", 2, "number of data axes")
        self._write_PHU(hdu)

        # update focal plane keywords
        self.focalplane.update_header_keywords()
        self.focalplane.update_ext_keywords()

        # add coord header cards to PHU
        self._write_extension_header(1, hdu)

        # add WCS header cards
        self._write_wcs_keywords(1, hdu)

        # create a hdu list
        self.hdulist = pyfits.HDUList([hdu])

        # write it all to a disk file (mod 11jul13)
        try:
            self.hdulist.writeto(filename)
        except Exception:
            time.sleep(0.2)
            self.hdulist.writeto(filename)

        self.hdulist.close()

        return

    def _write_mef_file(self, filename):
        """
        Write an MEF image file.
        """

        # allow case sensitive ext_name
        pyfits.EXTENSION_NAME_CASE_SENSITIVE = True

        # make PHU (no data)
        phdu = pyfits.PrimaryHDU()

        numHDUs = self.focalplane.numamps_image

        # add header cards to PHU
        self._write_PHU(phdu)

        # create a list of hdu's for MEF file
        self.hdulist = pyfits.HDUList([phdu])

        # loop through HDU's, creating extensions and writing data
        for ext_number in range(1, numHDUs + 1):  # first HDU is 1 not 0
            # create the extension name
            ext_name = self.focalplane.ext_name[ext_number - 1]

            # get the image data for this extension
            numrows_amp = self.focalplane.numrows_amp
            numcols_amp = self.focalplane.numcols_amp
            data = numpy.ndarray(
                shape=(numrows_amp, numcols_amp),
                dtype=self.data_types[self.save_data_format],
                buffer=self.data[ext_number - 1],
            )

            hdu = pyfits.ImageHDU(data=data, name=str(ext_name))
            hdu.header.set("NAXIS", 2, "number of data axes")
            hdu.header.set("INHERIT", True, "extension inherits PHDU keyword/values?")
            hdu.header.set("BUNIT", "ADU", "Physical unit of array values")

            # add coord header cards to this extension
            self._write_extension_header(ext_number, hdu)

            # add WCS header cards to this extension
            self._write_wcs_keywords(ext_number, hdu)

            # add Focal plane header cards to this extension
            self._write_focalplane_keywords(ext_number, hdu)

            # hdu is read-only, so make a copy in order to scale(I have no idea why)
            hdu1 = hdu.copy()
            hdu1.scale("int16", "", bzero=32768, bscale=1)

            # keywords may be removed so make sure and replace, ???
            try:
                del hdu1.header["BZERO"]
                del hdu1.header["BSCALE"]
            except KeyError:
                pass
            hdu1.header.set("BZERO", 32768.0, after=7)
            hdu1.header.set("BSCALE", 1.0, after=8)

            # append to hdulist
            self.hdulist.append(hdu1)

        # now write it all to a disk file
        self.hdulist.writeto(filename)

        self.hdulist.close()

        return

    def _write_asm_fits_file(self, filename):
        """
        Write an assembled single extension FITS image file.
        """

        # allow case sensitive ext_name
        pyfits.EXTENSION_NAME_CASE_SENSITIVE = True

        # make PHU with data
        if not self.assembled:
            self.assemble(1)

        data = numpy.ndarray(
            shape=(self.asmsize[1], self.asmsize[0]),
            dtype=self.data_types[self.save_data_format],
            buffer=self.buffer.astype(self.data_types[self.save_data_format]),
        )
        hdu = pyfits.PrimaryHDU(data=data, header=self.hdulist[0].header)

        # add header cards to PHU
        hdu.header.set("NAXIS", 1, "number of data axes")
        self._write_asm_fits_header(hdu)

        # update focal plane keywords
        self.focalplane.update_header_keywords()

        # update focal plane extension keywords
        self.focalplane.update_ext_keywords()

        # create a new hdu list - do not overwrite the original header
        self.asm_header.hdulist = pyfits.HDUList([hdu])

        # write it all to a disk file
        if filename.startswith("!"):
            filename = filename[1:]
            overwrite = True
        else:
            overwrite = False
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            self.asm_header.hdulist.writeto(filename, overwrite=overwrite)

        self.asm_header.hdulist.close()

        return

    def _write_bin_file(self, filename):
        """
        Write buffer as binary image to disk.
        """

        self.size_x = self.focalplane.numcols_image
        self.size_y = self.focalplane.numrows_image

        if not self.assembled:
            self.assemble(1)

        with open(filename, "wb") as fd:
            fd.write(self.buffer.astype("uint16").squeeze())

        return

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
                    hdu.header.set(head[0], head[1], head[2], after=curpos)
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

        x_Val1 = xVal1
        y_Val1 = yVal1
        y_Val2 = yVal2
        x_Val2 = xVal2  # ? added 07sep24

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
