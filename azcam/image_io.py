"""
azcam image I/O routines.
"""

import os
import time
import warnings

import numpy
from astropy.io import fits as pyfits


class ImageIO(object):
    """
    Methods for azcam image I/O.
    """

    def __init__(self):
        super().__init__()

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

        # check AzCam header
        try:
            azcam_head = hdr["AZCAM-HEAD"]
            if azcam_head == "OK":
                self.azcam_header = 1
            else:
                self.azcam_header = 0
        except KeyError:
            self.azcam_header = 0

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

        if self.azcam_header == 1:
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

            if self.azcam_header == 1:
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
