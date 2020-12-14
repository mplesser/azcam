"""
Contains the azcam database db.
"""

import typing


class AzcamDatabase(object):

    #: version - the definitive azcam version (verify with setup.py)
    version = "20.3"

    #: working directory
    wd = None

    #: verbosity level for messages
    verbosity = 1

    #: abort flag, True if an abort has occurred
    abortflag = 0

    #: object which provides header corrdinates
    coord_object = "telescope"

    #: folders
    datafolder = ""

    #: last error status
    errorstatus = ["OK", ""]

    #: file type constants
    filetypes = {"FITS": 0, "MEF": 1, "BIN": 2, "ASM": 6}

    #: ROI for image analysis
    imageroi = []

    #: application type.  0 => unknown, 1 => server, 2 => console
    app_type = 0

    #: list of objects available to CLI namespace
    cli_cmds = {}

    #: exposure flags, may be used anywhere
    exposureflags = {}

    #: header objects
    headers = {}

    #: header order in image header
    headerorder = []

    #: azcamparameters
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

    def __init__(self):
        pass

    def get(self, name: str) -> typing.Any:
        """
        Returns an database attribute by name.
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


# create instance
db = AzcamDatabase()
