"""
Contains the local, temporary database referenced as "azcam.db".
"""

import typing


class AzcamDatabase(object):

    wd = None
    """working directory"""

    # verbosity level for messages
    verbosity = 1

    # operating mode (server or console)
    mode = None

    # abort flag, True if an abort has occurred
    abortflag = 0

    # folders
    datafolder = ""

    # last error status
    errorstatus = ["OK", ""]

    # tools available to CLI namespace
    cli_tools = {}

    # exposure flags, may be used anywhere
    exposureflags = {}

    # header objects
    headers = {}

    # header order in image header
    headerorder = []

    # azcamparameters
    parameters = {
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
        "instrumentname": "instrument.name",
        "instrumentenabled": "instrument.enabled",
        "instrumentfocus": "instrument.focus_position",
        # telescope
        "telescopename": "telescope.name",
        "telescopeenabled": "telescope.enabled",
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
        "version": "db.version",
        "abortflag": "db.abortflag",
        "errorstatus": "db.errorstatus",
        "verbosity": "db.verbosity",
        "hostname": "db.hostname",
    }

    # local database entries
    # image parameters
    imageparnames = [
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

    # exposure flags
    exposureflags = {
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

    # tool names
    toolnames = []

    def __init__(self):
        """
        Create db object.
        """

        pass

    def get(self, name: str) -> typing.Any:
        """
        Returns a database attribute by name.
        Args:
            name: name of attribute to return
        Returns:
            value or None if *name* is not defined.
        """

        try:
            obj = getattr(self, name)
        except AttributeError:
            obj = None

        return obj

    def set(self, name: str, value: typing.Any):
        """
        Sets a database attribute value.
        Args:
            name: name of attribute to set
            value: value of attribute to set
        """

        if not hasattr(self, name):
            return

        setattr(self, name, value)

        return
