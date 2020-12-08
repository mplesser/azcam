"""
Contains the azcam database db.
"""

import typing


class AzcamDatabase(object):

    #: version - the definitive azcam version (verify with setup.py)
    version = "20.0"

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

    exposureflags_rev = {v: k for k, v in exposureflags.items()}

    #: header objects
    headers = {}

    #: header order in image header
    headerorder: typing.List[str] = []

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
