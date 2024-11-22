"""
Contains the Image class.
"""

import os

import azcam
import azcam.utils
import azcam.exceptions
import numpy
from azcam.header import Header
from azcam.image_focalplane import FocalPlane
from azcam.image_headers import ImageHeaders
from azcam.image_io import ImageIO


class Image(ImageHeaders, ImageIO):
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
