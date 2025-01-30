"""
Contains the main azcam database class.
"""

from typing import Any, Union, List, Dict

import azcam
from azcam.logger import AzCamLogger
from azcam.parameters import Parameters


class AzcamDatabase(object):
    """
    The azcam database class.
    """

    version: str = azcam.__version__
    """current azcam version"""

    wd: Union[str, None] = None
    """the current working directory"""

    verbosity: int = 1
    """verbosity level for messages"""

    mode: str = ""
    """operating mode (server or console)"""

    abortflag: int = 0
    """abort flag, 1 (true) if an abort has occurred"""

    datafolder: str = ""
    """system datafolder"""

    systemname: str = ""
    """system name"""

    systemfolder: str = ""
    """system root folder"""

    tools: dict = {}
    """dict of tools"""

    cli: dict = {}
    """dict of CLI commands"""

    scripts: dict = {}
    """dict of scripts"""

    headers: dict = {}
    """header objects"""

    headerorder: list = []
    """header order in image header"""

    logger: AzCamLogger = AzCamLogger()
    """logger object"""

    parameters: Parameters
    """parameters object"""

    # *************************************************************************
    # parameter table
    # *************************************************************************
    par_table: dict = {
        # exposure
        "autotitle": "exposure.auto_title",
        "imagetype": "exposure.image_type",
        "exposureflag": "exposure.exposure_flag",
        "exposuresequencedelay": "exposure.exposure_sequence_delay",
        "exposuresequencetotal": "exposure.exposure_sequence_total",
        "exposuresequencenumber": "exposure.exposure_sequence_number",
        "exposuresequenceflush": "exposure.exposure_sequence_flush",
        "exposureupdatingheader": "exposure.updating_header",
        "isexposuresequence": "exposure.is_exposure_sequence",
        "displayimage": "exposure.display_image",
        "sendimage": "exposure.send_image",
        "savefile": "exposure.save_file",
        "flusharray": "exposure.flush_array",
        "tdidelay": "exposure.tdi_delay",
        "tdimode": "exposure.tdi_mode",
        "pardelay": "exposure.par_delay",
        "exposureguidemode": "exposure.guide_mode",
        "exposureguidestatus": "exposure.guide_status",
        "lastfilename": "exposure.last_filename",
        "imagefiletype": "exposure.filetype",
        "imageheaderfile": "exposure.imageheaderfile",
        "imagetest": "exposure.test_image",
        "imagesequencenumber": "exposure.sequence_number",
        "imageautoincrementsequencenumber": "exposure.auto_increment_sequence_number",
        "imageincludesequencenumber": "exposure.include_sequence_number",
        "imageautoname": "exposure.autoname",
        "imageoverwrite": "exposure.overwrite",
        "imageroot": "exposure.root",
        "imagefolder": "exposure.folder",
        # image
        "imagesizex": "exposure.image.focalplane.numcols_image",
        "imagesizey": "exposure.image.focalplane.numrows_image",
        "numpiximage": "exposure.image.focalplane.numpix_image",
        "colbin": "exposure.image.focalplane.col_bin",
        "rowbin": "exposure.image.focalplane.row_bin",
        "firstcol": "exposure.image.focalplane.first_col",
        "firstrow": "exposure.image.focalplane.first_row",
        "lastcol": "exposure.image.focalplane.last_col",
        "lastrow": "exposure.image.focalplane.last_row",
        # instrument
        "instrumentenabled": "instrument.is_enabled",
        "instrumentfocus": "instrument.focus_position",
        # telescope
        "telescopeenabled": "telescope.is_enabled",
        "telescopefocus": "telescope.focus_position",
        # tempcon
        "controltemperature": "tempcon.control_temperature",
        "camtemp": "tempcon.temperatures[0]",
        "dewtemp": "tempcon.temperatures[1]",
        # controller
        "utilityboardinstalled": "controller.utility_board_installed",
        "pciboardinstalled": "controller.pci_board_installed",
        "timingboardinstalled": "controller.timing_board_installed",
        "videogain": "controller.video_gain",
        "videospeed": "controller.video_speed",
        "usereadlock": "controller.use_read_lock",
        "pcifile": "controller.pci_file",
        "timingfile": "controller.timing_file",
        "utilityfile": "controller.utility_file",
        "timingboard": "controller.timing_board",
        "videoboards": "controller.video_boards",
        "clockboards": "controller.clock_boards",
        # database
        "systemname": "db.systemname",
        "abortflag": "db.abortflag",
        "verbosity": "db.verbosity",
        "hostname": "db.hostname",
        "version": "db.version",
    }
    """dict of general parameters"""

    imageparnames: List[str] = [
        "imageroot",
        "imageincludesequencenumber",
        "imageautoname",
        "imageautoincrementsequencenumber",
        "imagetest",
        "imagetype",
        "imagetitle",
        "imageoverwrite",
        "imagefolder",
    ]
    """image parameters"""

    exposureflags: Dict[str, int] = {
        "NONE": 0,
        "EXPOSING": 1,
        "ABORT": 2,
        "PAUSE": 3,
        "RESUME": 4,
        "READ": 5,
        "PAUSED": 6,
        "READOUT": 7,
        "SETUP": 8,
        "WRITING": 9,
        "GUIDEERROR": 10,
        "ERROR": 11,
    }
    """exposure flags"""

    # *************************************************************************
    # db methods
    # *************************************************************************

    def __init__(self) -> None:
        pass

    def get(self, name: str) -> Any:
        """
        Returns a database attribute by name.
        Args:
          name: name of attribute to return
        Returns:
          value or None if *name* is not defined
        """

        try:
            obj = getattr(self, name)
        except AttributeError:
            obj = None

        return obj

    def set(self, name: str, value: Any) -> None:
        """
        Sets a database attribute value.
        Args:
          name: name of attribute to set
          value: value of attribute to be set
        """

        # if not hasattr(self, name):
        #    return

        setattr(self, name, value)

        return
