"""
Contains the base Controller class.
"""

import azcam
from azcam.tools import Tools
from azcam.header import Header, ObjectHeaderMethods
from azcam.console_tools import ConsoleTools


class Controller(Tools, ObjectHeaderMethods):
    """
    The base controller tool.
    Usually implemented as the "controller" tool.

    Attributes:
        self.interface_type (int): 0 = demo, 4 = PCIe
        self.header (Header object): controller header
        self.exposure_time (float): exposure time (secs)
        self.detpars (DetPars object):
        self.reset_flag (bool): True if the controller has been reset
    """

    def __init__(self, tool_id="controller", description=None):
        """
        Args:
            tool_id: tool name
            description:   description of this tool
        """

        Tools.__init__(self, tool_id, description)

        # interface type (0 = demo, 4 = PCIe)
        self.interface_type = 0

        # create the controller Header object
        self.header = Header("Controller")
        self.header.set_header("controller", 2)

        self.exposure_time = 0

        self.detpars = DetPars()

        self.reset_flag = 0

        azcam.db.tools_init["controller"] = self
        azcam.db.tools_reset["controller"] = self

    def set_roi(self):
        """
        Sets ROI parameters values in the controller based on focalplane parameters.
        """

        return

    def set_shutter_state(self, flag: bool = 0):
        """
        Sets the shutter state during an exposure.
        Args:
            flag: True open shutter during exposure, False close shutter during exposure
        """

        return

    def set_shutter(self, state: bool, shutter_id: int = 0):
        """
        Open or close controller shutter.
        Args:
            state: True to open shutter, False to close shutter
            shutter_id: shutter ID number
        """

        return

    def flush(self, cycles=1):
        """
        Flush or clear out the sensor.
        Returns after clearing is finished, which could take many seconds.
        Args:
            cycles: number of times to flush sensor
        """

        return


class DetPars(object):
    """
    Defines detector parameters for controller shifting, image size, etc.
    These are updated by exposure.set_format, .set_focalplane, and .set_roi.
    Attributes:
        self.numpix_image (int):
        self.numcols_image (int):
        self.numrows_image (int):

        self.ns_total (int):
        self.ns_predark (int):
        self.ns_underscan (int):
        self.ns_overscan (int):
        self.np_total (int):
        self.np_predark (int):
        self.np_underscan (int):
        self.np_overscan (int):
        self.np_frametransfer (int):

        self.first_col (int):
        self.last_col (int):
        self.first_row (int):
        self.last_row (int):
        self.col_bin (int):
        self.row_bin (int):

        self.framet (int):
        self.xdata (int):
        self.xflush (int):
        self.xpreskip (int):
        self.xunderscan (int):
        self.xskip (int):
        self.xpostskip (int):
        self.xoverscan (int):
        self.ydata (int):
        self.yflush (int):
        self.ypreskip (int):
        self.yunderscan (int):
        self.yskip (int):
        self.ypostskip (int):
        self.yoverscan (int):

        self.coltotal (int):
        self.colusct (int):
        self.coluscw (int):
        self.coluscm (int):
        self.coloscw (int):
        self.coloscm (int):
        self.rowtotal (int):
        self.rowusct (int):
        self.rowuscw (int):
        self.rowuscm (int):
        self.rowoscw (int):
        self.rowoscm (int):
    """

    def __init__(self):
        """
        Create detpars database.
        """

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


class ControllerConsole(ConsoleTools):
    """
    Controller tool for consoles.
    Usually implemented as the "controller" tool.
    """

    def __init__(self) -> None:
        super().__init__("controller")

    def set_shutter(self, state: int = 0):
        """
        Open or close a shutter.

        :param state:

        """

        return azcam.db.server.command(f"{self.objname}.set_shutter {state}")
