"""
Contains the FocalPlane and WCS classes.
"""

import azcam
import numpy
from azcam.header import Header, ObjectHeaderMethods


class FocalPlane(ObjectHeaderMethods):
    """
    The FocalPlane class describes a focalplane layout.
    """

    def __init__(self):
        """
        Create an instance of FocalPlane class.
        """

        #: focalplane header object
        self.header = Header("Focalplane")

        #: World Coordinate System object
        self.wcs = WCS(self)

        # only needed for server side
        self.header.set_header("focalplane")

        # fixed values
        # for multiple CCD detectors:
        # 0 - each CCD has its own physical coordinates
        # 1 - combine physical coordinates (physical coordinates
        #    are the same as detector coordinates)
        self.split_physical_coords = 0
        #: number of detectors along X axis
        self.numdet_x: int = 1
        #: number of detectors along Y axis
        self.numdet_y: int = 1
        #: amplifier readout orientation (new)
        self.amp_cfg: list = [0]
        # detector number for each detector
        self.det_number = [1]
        # extension number for each amplifier
        self.ext_number = [1]
        # extension name for each amplifier
        self.ext_name = ["1"]
        # extension number order for each amplifier when creating binary image
        self.jpg_ext = [1]
        # detector position in x direction in pixels
        self.detpos_x = [1]
        # detector position in y direction in pixels
        self.detpos_y = [1]
        # amplifier's positions along X axis
        self.extpos_x = [1]
        # amplifier's positions along Y axis
        self.extpos_y = [1]
        # amplifier's positions in pixels along X axis
        self.amppix1 = [1]
        # amplifier's positions in pixels along Y axis
        self.amppix2 = [1]
        # gap between amplifiers in X. value different than 0
        #    means that there is a gap on the left side of the amplifier.
        # gapx is the sum of all gaps on the left side of the amplifier.
        self.gapx = [0]
        # gap between amplifiers in Y. value different than 0 means
        #    that there is a gap below of the amplifier.
        # gapy is the sum of all gaps below the amplifier.
        self.gapy = [0]

        # number of amplifiers along X axis
        self.numamps_x = 1
        # number of amplifiers along Y axis
        self.numamps_y = 1
        # reference (zeropoint) position X (in pixels)
        self.refpix1 = 1
        # reference (zeropoint) position Y (in pixels)
        self.refpix2 = 1
        # unbinned number of visible pixels per amplifier along X axis
        self.ampvispix_x = 1
        # unbinned number of visible pixels per amplifier along Y axis
        self.ampvispix_y = 1

        # amplifer gain values in e/DN
        self.gains = []
        # amplifer read noise in e
        self.rdnoises = []

        # calculated values
        # number of pixels in image
        self.numpix_image = 0
        # number of bytes per image
        self.numbytes_image = 0
        # number of columns per image
        self.numcols_image = 0
        # number of rows per image
        self.numrows_image = 0
        # number of total amps per image
        self.numamps_image = 1
        # number of detectors
        self.num_detectors = 1

        # number of columns per amplifier
        self.numcols_amp = 1
        # number of row per amplifier
        self.numrows_amp = 1
        # number of serial amps per detector
        self.num_ser_amps_det = 1
        # number of parallel amps per detector
        self.num_par_amps_det = 1
        # number of total amps per detector
        self.num_amps_det = 1

        # first column
        self.first_col = 1
        # first row
        self.first_row = 1
        # last column
        self.last_col = 1
        # last row
        self.last_row = 1
        # column binning
        self.col_bin = 1
        # row binning
        self.row_bin = 1

        # number of visible columns per amplifier
        self.numviscols_amp = 1
        # number of visible rows per amplifier
        self.numvisrows_amp = 1
        # number of visible columns per amplifier
        self.numviscols_image = 1
        # number of visible rows per amplifier
        self.numvisrows_image = 1

        # number of colums in overscan
        self.numcols_overscan = 0
        # number of rows in overscan
        self.numrows_overscan = 0
        # number of colums in underscan
        self.numcols_underscan = 0
        # number of rows in underscan
        self.numrows_underscan = 0
        # underscan skips
        self.xunderscan = 0
        self.yunderscan = 0
        # overscan skips
        self.xoverscan = 0
        self.yoverscan = 0

        # bias location constants
        self.BL_COLUNDER = 1
        self.BL_COLOVER = 2
        self.BL_ROWUNDER = 3
        self.BL_ROWOVER = 4
        self.bias_location = self.BL_COLOVER

        # number of pixels per amplifier
        self.numpix_amp = 1
        # number of pixels per detector
        self.numpix_det = 1

        # shifting
        self.ns_total = 0
        self.ns_predark = 0
        self.ns_underscan = 0
        self.ns_overscan = 0
        self.np_total = 0
        self.np_predark = 0
        self.np_underscan = 0
        self.np_overscan = 0
        self.np_frametransfer = 0

        # set shifting parameters
        self.coltotal = 0
        self.colusct = 0
        self.coluscw = 0
        self.coluscm = 0
        self.coloscw = 0
        self.coloscm = 0
        self.rowtotal = 0
        self.rowusct = 0
        self.rowuscw = 0
        self.rowuscm = 0
        self.rowoscw = 0
        self.rowoscm = 0
        self.framet = 0

    def update_header_keywords(self):
        """
        Update focal plane keywords in header
        """

        self.header.set_keyword("ITL-HEAD", "OK", "ITL Header flag", "str")
        self.header.set_keyword(
            "NUM-DETX", self.numdet_x, "Number of detectors in X", "int"
        )
        self.header.set_keyword(
            "NUM-DETY", self.numdet_y, "Number of detectors in Y", "int"
        )
        self.header.set_keyword(
            "NUM-AMPX", self.numamps_x, "Number of amplifiers in X", "int"
        )
        self.header.set_keyword(
            "NUM-AMPY", self.numamps_y, "Number of amplifiers in Y", "int"
        )
        self.header.set_keyword("REF-PIX1", self.refpix1, "Reference pixel 1", "int")
        self.header.set_keyword("REF-PIX2", self.refpix2, "Reference pixel 2", "int")

        return

    def update_ext_keywords(self):
        """
        Update focal plane keywords for single extension
        """
        self.header.set_keyword("AMP-CFG", self.amp_cfg[0], "Amplifier configuration")
        self.header.set_keyword("DET-NUM", self.det_number[0], "Detector number")
        self.header.set_keyword("EXT-NUM", self.ext_number[0], "extension number")
        self.header.set_keyword("JPG-EXT", self.jpg_ext[0], "Image section")
        self.header.set_keyword("DET-POSX", self.detpos_x[0], "Detector position in X")
        self.header.set_keyword("DET-POSY", self.detpos_y[0], "Detector position in Y")
        self.header.set_keyword("Ext-PosX", self.extpos_x[0], "Amplifier position in X")
        self.header.set_keyword("Ext-PosY", self.extpos_y[0], "Amplifier position in Y")
        self.header.set_keyword(
            "AMP-PIX1", self.amppix1[0], "Amplifier pixel position in X"
        )
        self.header.set_keyword(
            "AMP-PIX2", self.amppix2[0], "Amplifier pixel position in Y"
        )

        return

    def update_header(self):
        """
        Update headers, reading current data.
        """

        self.update_header_keywords()

        return

    def set_format(
        self,
        ns_total: int = -1,
        ns_predark: int = -1,
        ns_underscan: int = -1,
        ns_overscan: int = -1,
        np_total: int = -1,
        np_predark: int = -1,
        np_underscan: int = -1,
        np_overscan: int = -1,
        np_frametransfer: int = -1,
    ):
        """
        Set the detector format.
        Args:
            ns_total: number of visible columns
            ns_predark: number of physical dark underscan columns
            ns_underscan: desired number of desired dark underscan columns
            ns_overscan: number of dark overscan columns
            np_total: number of visible rows
            np_predark: number of physical dark underscan rows
            np_underscan: number of desired dark underscan rows
            np_overscan: number of desired dark overscan rows
            np_frametransfer: rows to frame transfer shift
        """

        ns_total = int(ns_total)
        ns_predark = int(ns_predark)
        ns_underscan = int(ns_underscan)
        ns_overscan = int(ns_overscan)
        np_total = int(np_total)
        np_predark = int(np_predark)
        np_underscan = int(np_underscan)
        np_overscan = int(np_overscan)
        np_frametransfer = int(np_frametransfer)

        # defaults
        if ns_total == -1:
            ns_total = self.ns_total
        if ns_predark == -1:
            ns_predark = self.ns_predark
        if ns_underscan == -1:
            ns_underscan = self.ns_underscan
        if ns_overscan == -1:
            ns_overscan = self.ns_overscan
        if np_total == -1:
            np_total = self.np_total
        if np_predark == -1:
            np_predark = self.np_predark
        if np_underscan == -1:
            np_underscan = self.np_underscan
        if np_overscan == -1:
            np_overscan = self.np_overscan
        if np_frametransfer == -1:
            np_frametransfer = self.np_frametransfer

        # sets the format parameters for a detector
        self.ns_total = int(ns_total)
        self.ns_predark = int(ns_predark)
        self.ns_underscan = int(ns_underscan)
        self.ns_overscan = int(ns_overscan)
        self.np_total = int(np_total)
        self.np_predark = int(np_predark)
        self.np_underscan = int(np_underscan)
        self.np_overscan = int(np_overscan)
        self.np_frametransfer = int(np_frametransfer)

        # set shifting parameters
        self.coltotal = int(ns_total)
        self.colusct = int(ns_predark)
        self.coluscw = int(ns_underscan)
        self.coluscm = 0
        self.coloscw = int(ns_overscan)
        self.coloscm = 0
        self.rowtotal = int(np_total)
        self.rowusct = int(np_predark)
        self.rowuscw = int(np_underscan)
        self.rowuscm = 0
        self.rowoscw = int(np_overscan)
        self.rowoscm = 0
        self.framet = int(np_frametransfer)

        return

    def get_format(self):
        """
        Return a list of current detector format parameters
        """

        return [
            self.ns_total,
            self.ns_predark,
            self.ns_underscan,
            self.ns_overscan,
            self.np_total,
            self.np_predark,
            self.np_underscan,
            self.np_overscan,
            self.np_frametransfer,
        ]

    def set_focalplane(
        self, numdet_x=-1, numdet_y=-1, numamps_x=-1, numamps_y=-1, amp_cfg=[0]
    ):
        """
        Sets focal plane configuration. Use after set_format() and before set_roi().
        This command replaces SetConfiguration.
        Default focalplane values are set here.
        numdet_x defines number of detectors in Column direction.
        numdet_y defines number of detectors in Row direction.
        numamps_x defines number of amplifiers in Column direction.
        numamps_y defines number of amplifiers in Row direction.
        amp_cfg defines each amplifier's orientation (ex: [0,1,2,3]).
        0 - normal
        1 - flip x
        2 - flip y
        3 - flip x and y
        """

        if numdet_x == -1:
            numdet_x = self.numdet_x
        if numdet_y == -1:
            numdet_y = self.numdet_y
        if numamps_x == -1:
            numamps_x = self.numamps_x
        if numamps_y == -1:
            numamps_y = self.numamps_y

        self.numdet_x = numdet_x
        self.numdet_y = numdet_y
        self.numamps_x = numamps_x
        self.numamps_y = numamps_y
        self.amp_cfg = amp_cfg

        # set the keywords in the main header
        self.header.set_keyword(
            "N-DET-X", self.numdet_x, "Number of detectors in X", "int"
        )
        self.header.set_keyword(
            "N-DET-Y", self.numdet_y, "Number of detectors in Y", "int"
        )
        self.header.set_keyword(
            "N-AMPS-X", self.numamps_x, "Number of amplifiers in X", "int"
        )
        self.header.set_keyword(
            "N-AMPS-Y", self.numamps_y, "Number of amplifiers in Y", "int"
        )

        # set number of detectors
        self.num_detectors = self.numdet_x * self.numdet_y

        # set amps per detector
        self.num_ser_amps_det = int(self.numamps_x / self.numdet_x)
        self.num_par_amps_det = int(self.numamps_y / self.numdet_y)
        self.num_amps_det = self.num_ser_amps_det * self.num_par_amps_det

        # set amps in focal plane
        self.numamps_image = self.num_detectors * self.num_amps_det

        # set unbinned number of visible pixels per amplifier along X and Y axis
        self.ampvispix_x = int(self.ns_total / self.numamps_x)
        self.ampvispix_y = int(self.np_total / self.numamps_y)

        # set default values
        self.set_default_values()

        # initialize WCS so array size is correct, values may be manually set later
        self.wcs.initialize()

        return

    def get_focalplane(self):
        """
        Returns the focal plane configuration.
        """

        return [
            self.numdet_x,
            self.numdet_y,
            self.numamps_x,
            self.numamps_y,
            self.amp_cfg,
        ]

    def set_roi(
        self,
        first_col=-1,
        last_col=-1,
        first_row=-1,
        last_row=-1,
        col_bin=-1,
        row_bin=-1,
        roi_num=0,
    ):
        """
        Sets the ROI values for a specified ROI.
        Currently only one ROI (0) is supported.
        These values are for the entire focal plane, not just one detector.
        """

        # set current values
        first_col = int(first_col)
        last_col = int(last_col)
        first_row = int(first_row)
        last_row = int(last_row)
        col_bin = int(col_bin)
        row_bin = int(row_bin)
        roi_num = int(roi_num)

        if first_col == -1:
            first_col = self.first_col
        if last_col == -1:
            last_col = self.last_col
        if first_row == -1:
            first_row = self.first_row
        if last_row == -1:
            last_row = self.last_row
        if col_bin == -1:
            col_bin = self.col_bin
        if row_bin == -1:
            row_bin = self.row_bin

        self.first_col = int(first_col)
        self.last_col = int(last_col)
        self.first_row = int(first_row)
        self.last_row = int(last_row)
        self.col_bin = int(col_bin)
        self.row_bin = int(row_bin)
        self.roi_num = int(roi_num)

        # bad fix for ROI now entire focalplane - change later!
        if self.numdet_x > 1:
            lc = last_col / self.numdet_x
            lr = last_row / self.numdet_y
        else:
            lc = last_col
            lr = last_row

        fc = first_col
        fr = first_row
        # calculate variables for shifting a single AMPLIFIER
        self.xunderscan = int(min(self.colusct / self.col_bin, self.coluscw))
        self.xskip = int(
            min(self.colusct - self.xunderscan * self.col_bin, self.coluscm)
        )
        self.xpreskip = self.colusct - self.xskip - self.xunderscan * self.col_bin
        self.xskip += fc - 1
        self.xdata = (lc - (fc - 1)) / self.col_bin
        self.xdata = max(0, self.xdata)
        self.xdata = int(self.xdata / self.num_ser_amps_det)
        self.xpostskip = self.coltotal / self.numamps_x - (
            (fc - 1) + self.xdata * self.col_bin
        )
        self.xpostskip = int(max(0, self.xpostskip))
        self.xpostskip += self.coloscm
        self.xoverscan = self.coloscw

        self.numcols_amp = self.xunderscan + self.xdata + self.xoverscan
        self.numcols_overscan = self.xoverscan
        self.numviscols_amp = self.xdata
        # self.numviscols_image=self.numviscols_amp*self.num_ser_amps_det*self.numamps_x
        self.numviscols_image = (
            self.numviscols_amp * self.num_ser_amps_det * self.numdet_x
        )

        self.yunderscan = int(min(self.rowusct / self.row_bin, self.rowuscw))
        self.yskip = int(
            min(self.rowusct - self.yunderscan * self.row_bin, self.rowuscm)
        )
        self.ypreskip = self.rowusct - self.yskip - self.yunderscan * self.row_bin
        self.yskip += self.first_row - 1
        self.ydata = (lr - (fr - 1)) / self.row_bin
        self.ydata = max(0, self.ydata)
        self.ydata = int(self.ydata / self.num_par_amps_det)
        self.ypostskip = self.rowtotal / self.numamps_y - (
            (fr - 1) + self.ydata * self.row_bin
        )
        self.ypostskip = int(max(0, self.ypostskip))
        self.ypostskip += self.rowoscm
        self.yoverscan = self.rowoscw

        self.numrows_amp = self.yunderscan + self.ydata + self.yoverscan
        self.numrows_overscan = self.yoverscan
        self.numvisrows_amp = self.ydata
        # self.numvisrows_image=self.numvisrows_amp*self.num_par_amps_det*self.numamps_y
        self.numvisrows_image = (
            self.numvisrows_amp * self.num_par_amps_det * self.numdet_y
        )

        self.numpix_amp = self.numcols_amp * self.numrows_amp

        # totals for a single DETECTOR
        self.numcols_det = self.numcols_amp * self.num_ser_amps_det
        self.numrows_det = self.numrows_amp * self.num_par_amps_det
        self.numpix_det = self.numcols_det * self.numrows_det

        # totals for the IMAGE
        self.numpix_image = self.numpix_det * self.num_detectors
        self.numcols_image = self.numcols_det * self.numdet_x
        self.numrows_image = self.numrows_det * self.numdet_y
        self.numbytes_image = self.numpix_image * 2

        # number of UNBINNED pixels to flush during clear
        self.xflush = (
            self.xpreskip
            + self.xskip
            + self.xpostskip
            + (self.xunderscan + self.xdata + self.xoverscan) * self.col_bin
        )
        self.yflush = (
            self.ypreskip
            + self.yskip
            + self.ypostskip
            + (self.yunderscan + self.ydata + self.yoverscan) * self.row_bin
        )

        self.set_amp_positions()

        return

    def get_roi(self, roi_num=0):
        """
        Returns a list of the ROI parameters for the roi_num specified.
        Currently only one ROI (0) is supported.
        Returned list format is (first_col,last_col,first_row,last_row,col_bin,row_bin).
        """

        return [
            self.first_col,
            self.last_col,
            self.first_row,
            self.last_row,
            self.col_bin,
            self.row_bin,
        ]

    def roi_reset(self):
        """
        Resets detector ROI values to full frame, current binning.
        """

        # get focalplane format
        reply = self.get_format()

        # update controller shifting parameters
        self.set_roi(1, reply[0], 1, reply[4], -1, -1)

        return reply

    def set_amp_positions(self):
        """
        Calculates amplifiers positions including gaps between amplifiers and CCDs
        New: Zareba 23Mar2012
        """
        self.amppix1 = numpy.empty(shape=[self.numamps_image], dtype="<u2")
        self.amppix2 = numpy.empty(shape=[self.numamps_image], dtype="<u2")

        indx = 0
        for flip in self.amp_cfg:
            if flip == 0:
                flip_x = 0
                flip_y = 0
            elif flip == 1:
                flip_x = 1
                flip_y = 0
            elif flip == 2:
                flip_x = 0
                flip_y = 1
            else:
                flip_x = 1
                flip_y = 1

            size_x = self.numviscols_amp * self.col_bin
            size_y = self.numvisrows_amp * self.row_bin

            self.amppix1[indx] = (
                (self.extpos_x[indx] - 1) * size_x
                + flip_x * size_x
                + self.gapx[indx]
                + 1
                - flip_x
            )
            self.amppix2[indx] = (
                (self.extpos_y[indx] - 1) * size_y
                + flip_y * size_y
                + self.gapy[indx]
                + 1
                - flip_y
            )

            indx += 1

        return

    def set_default_values(self):
        """
        Sets default values for focalplane variables
        """

        # set default values for the extension names, 'im1' -> 'imN'
        # use _WCS file to set nonstandard values (focalplane.ext_name = [...])
        self.ext_name = numpy.empty(shape=[self.numamps_image], dtype="S16")
        for ext in range(self.numamps_image):
            self.ext_name[ext] = f"IM{(ext + 1)}"
        self.ext_name = [y.decode() for y in self.ext_name]  # new

        # set default values for the etension numbers, 1 -> N
        # use _WCS.py file to set nonstandard values ( focalplane.ext_number = [...])
        self.ext_number = numpy.empty(shape=[self.numamps_image], dtype="<u2")
        for ext in range(self.numamps_image):
            self.ext_number[ext] = ext + 1

        # set default values for the jpg extension values, 1 -> N
        # use _WCS.py file to set nonstandard values (focalplane.jpg_ext = [...])
        self.jpg_ext = numpy.empty(shape=[self.numamps_image], dtype="<u2")
        for ext in range(self.numamps_image):
            self.jpg_ext[ext] = ext + 1

        # set default values for the gaps, 0
        self.gapx = numpy.empty(shape=[self.numamps_image], dtype="<u2")
        for ext in range(self.numamps_image):
            self.gapx[ext] = 0
        self.gapy = numpy.empty(shape=[self.numamps_image], dtype="<u2")
        for ext in range(self.numamps_image):
            self.gapy[ext] = 0

        # set extension positions
        self.extpos_x = numpy.empty(shape=[self.numamps_image], dtype="<u2")
        for ext in range(self.numamps_image):
            self.extpos_x[ext] = 1
        self.extpos_y = numpy.empty(shape=[self.numamps_image], dtype="<u2")
        for ext in range(self.numamps_image):
            self.extpos_y[ext] = 1

        self.det_number = numpy.empty(shape=[self.numamps_image], dtype="<u2")
        numpy.ndarray.fill(self.det_number, 1)
        self.detpos_x = numpy.empty(shape=[self.numamps_image], dtype="<u2")
        numpy.ndarray.fill(self.detpos_x, 1)
        self.detpos_y = numpy.empty(shape=[self.numamps_image], dtype="<u2")
        numpy.ndarray.fill(self.detpos_y, 1)

        return

    def set_extension_name(self, ext_name):
        for i, ext in enumerate(ext_name):
            self.ext_name[i] = ext

        return

    def set_extension_extnum(self, ext_number):
        for i, ext in enumerate(ext_number):
            self.ext_number[i] = ext

        return

    def set_ref_pixel(self, xy):
        """
        Set the reference pixel.
        xy is [X,Y] in pixels.
        """

        self.refpix1 = xy[0]
        self.refpix2 = xy[1]

        return

    def set_extension_position(self, xy):
        """
        Set the extension position of each amplifier.
        xy is [[X,Y]] in index numbers, starting at [1,1].
        """

        for i, xy_ in enumerate(xy):
            self.extpos_x[i] = xy_[0]
            self.extpos_y[i] = xy_[1]

        return

    def set_jpg_order(self, indices):
        """
        Set JPG image positions.
        """

        self.jpg_ext = indices

        return


class WCS(object):
    def __init__(self, FPobject):
        # ref to parent focalplane object
        self.fpobj = FPobject

        # tool which provides RA and DEC info
        #  usually telecope or instrument
        self.coord_object = "telescope"

        # Equinox of WCS - default value 2000
        self.equinox = 2000
        # WCS dimensionality - default value 2
        self.wcs_dim = 2
        # True if CD matrix is used, False if rot_deg and scale1,2 are used
        self.cd_matrix = 0
        # coordinate type - x axis
        self.ctype1 = "RA---TAN"
        # coordinate type - y axis
        self.ctype2 = "DEC--TAN"

        # RA position of image
        self.ra_deg = ""
        # DEC position of image
        self.dec_deg = ""
        # default RA position
        self.def_ra = "00:00:00.00"
        # default DEC position
        self.def_dec = "00:00:00.00"

        # True if CD matrix is used, False if rot_deg and scale1, 2 are used
        self.cd_matrix = 0
        # translation matrix: CD1_1 - number of pixel per detector pixel
        self.cd_1_1 = 1
        # translation matrix: CD1_2 - rotation
        self.cd_1_2 = 1
        # translation matrix: CD2_1 - rotation
        self.cd_2_1 = 1
        # translation matrix: CD2_2 - number of pixel per detector pixel
        self.cd_2_2 = 1

        # rotation in deg
        self.rot_deg = [0]

        # scale - x axis - deg/pixel
        self.scale1 = [1.0 / 3600.0]
        # scale - y axis - deg/pixel
        self.scale2 = [1.0 / 3600.0]

        # CCD to amplifier transformation matrix x
        self.atm_1_1 = [1]
        # CCD to amplifier transformation matrix y
        self.atm_2_2 = [1]
        # CCD to amplifier transformation vector x
        self.atv1 = [1]
        # CCD to amplifier transformation vector y
        self.atv2 = [1]

        # CCD to image transformation matrix x
        self.ltm_1_1 = [1]
        # CCD to image transformation matrix y
        self.ltm_2_2 = [1]
        # CCD to image transformation vector x
        self.ltv_1 = [1]
        # CCD to image transformation vector y
        self.ltv_2 = [1]

        # CCD to detector transformation matrix x
        self.dtm_1_1 = [1]
        # CCD to detector transformation matrix y
        self.dtm_2_2 = [1]
        # CCD to detector transformation vector x
        self.dtv_1 = [1]
        # CCD to detector transformation vector x
        self.dtv_2 = [1]

    def initialize(self):
        numexts = self.fpobj.numamps_image

        self.atm_1_1 = numpy.empty(shape=[numexts], dtype="<i4")
        self.atm_2_2 = numpy.empty(shape=[numexts], dtype="<i4")
        self.atv1 = numpy.empty(shape=[numexts], dtype="<i4")
        self.atv2 = numpy.empty(shape=[numexts], dtype="<i4")

        self.ltm_1_1 = numpy.empty(shape=[numexts], dtype="<f")
        self.ltm_2_2 = numpy.empty(shape=[numexts], dtype="<f")
        self.ltv_1 = numpy.empty(shape=[numexts], dtype="<f")
        self.ltv_2 = numpy.empty(shape=[numexts], dtype="<f")

        self.dtm_1_1 = numpy.empty(shape=[numexts], dtype="<u2")
        self.dtm_2_2 = numpy.empty(shape=[numexts], dtype="<u2")
        self.dtv_1 = numpy.empty(shape=[numexts], dtype="<u2")
        self.dtv_2 = numpy.empty(shape=[numexts], dtype="<u2")

        # rotation in deg
        self.rot_deg = numpy.empty(shape=[numexts], dtype="<f")
        for ext in range(numexts):
            self.rot_deg[ext] = 0.0

        # scale - x axis - deg/pixel
        self.scale1 = numpy.empty(shape=[numexts], dtype="<f")
        for ext in range(numexts):
            self.scale1[ext] = 1.0 / 3600.0
        # scale - y axis - deg/pixel
        self.scale2 = numpy.empty(shape=[numexts], dtype="<f")
        for ext in range(numexts):
            self.scale2[ext] = 1.0 / 3600.0

        return

    def get_ra_dec(self):
        """
        Get RA and DEC from telescope header.
        They should have been copied from telescope header to this image header.
        """

        if self.coord_object is None:
            return

        try:
            get_ra = azcam.db.tools[self.coord_object].header.get_keyword("RA")
            self.ra_deg = self._ra_to_deg(get_ra[0])
        except Exception:
            self.ra_deg = self._ra_to_deg(self.def_ra)

        try:
            get_dec = azcam.db.tools[self.coord_object].header.get_keyword("DEC")
            self.dec_deg = self._dec_to_deg(get_dec[0])
        except Exception:
            self.dec_deg = self._dec_to_deg(self.def_dec)

        return

    def _dec_to_deg(self, dec):
        """
        Convert DEC into decimal degrees
        """

        sgn = +1.0
        dms = [0, 0, 0]

        sign = dec[0]
        if sign == "-":
            sgn = -1.0
            dec = dec[1:]
        else:
            if sign == "+":
                sgn = +1.0
                dec = dec[1:]

        x = dec.split(":")

        itm = len(x)
        for i in range(itm):
            if i <= 2:
                dms[i] = x[i]

        return (int(dms[0]) + int(dms[1]) / 60.0 + float(dms[2]) / 3600.0) * sgn

    def _ra_to_deg(self, ra):
        """
        Convert RA into decimal degrees
        """

        hms = [0, 0, 0]

        x = ra.split(":")

        itm = len(x)
        for i in range(itm):
            if i <= 2:
                hms[i] = x[i]

        return (int(hms[0]) + int(hms[1]) / 60.0 + float(hms[2]) / 3600.0) * 15
