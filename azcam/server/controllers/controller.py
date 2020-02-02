"""
Contains the base Controller class.
"""

import azcam
from azcam.header import Header


class Controller(object):
    """
    Base controller class for Azcam.
    """

    def __init__(self, name="controller"):

        #: controller name
        self.name = name

        #: controller ID
        self.id = ""

        #: True when controller is enabled
        self.enabled = 1
        #: True when contorller is initialized
        self.initialized = 0
        #: interface type (0 = demo, 4 = PCIe)
        self.interface_type = 0
        # True when controller has been reset
        self.is_reset = 0

        # create the controller Header object but name it "Camera"
        self.header = Header("Camera")
        self.header.set_header("controller", 2)

        self.exposure_time = 0

        self.dewar_number = 0

        self.detpars = DetPars()

        self.reset_flag = 0

        # save object
        setattr(azcam.db, name, self)
        azcam.db.objects[name] = self

    def set_roi(self):
        """
        Sets ROI parameters values in the controller based on focalplane parameters.
        """

        return

    def set_shutter_state(self, Flag="close"):
        """
        Sets the shutter state during an exposure.
        Flag is:
        open -> close shutter during exposure
        close -> open shutter during exposure
        """

        return

    def set_shutter(self, state, shutter_id=0):
        """
        Open or close controller shutter.
        """

        return

    def update_header(self):
        """
        Update header.
        Normally controller keywords are set during reset.
        """

        return

    def stop_idle(self):
        """
        Stop idle clocking.
        """

        return


class DetPars(object):
    """
    Defines detector parameters for controller shifting, image size, etc.
    These are updated by exposure.set_format, .set_focalplane, and .set_roi.
    """

    def __init__(self):
        """
        Create detpars database.
        """

        # update these as needed from exposure

        self.numpix_image = 0
        self.numcols_image = 0
        self.numrows_image = 0

        self.ns_total = 0
        self.ns_predark = 0
        self.ns_underscan = 0
        self.ns_overscan = 0
        self.np_total = 0
        self.np_predark = 0
        self.np_underscan = 0
        self.np_overscan = 0
        self.np_frametransfer = 0

        self.first_col = 0
        self.last_col = 0
        self.first_row = 0
        self.last_row = 0
        self.col_bin = 0
        self.row_bin = 0

        self.framet = 0
        self.xdata = 0
        self.xflush = 0
        self.xpreskip = 0
        self.xunderscan = 0
        self.xskip = 0
        self.xpostskip = 0
        self.xoverscan = 0
        self.ydata = 0
        self.yflush = 0
        self.ypreskip = 0
        self.yunderscan = 0
        self.yskip = 0
        self.ypostskip = 0
        self.yoverscan = 0

        # shifting parameters
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

        return
