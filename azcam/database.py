"""
Contains the azcam database db.
"""

import typing


class AzcamDatabase(object):

    # database entries are class attributes

    #: version - the definitive azcam version (verify with setup.py)
    version = "20.0"

    #: working directory
    wd = None

    #: verbosity level for messages
    verbosity = 1

    #: display prefix in log messages
    use_logprefix = 1

    #: abort flag, True if an abort has occurred
    abortflag = 0

    #: parameter filename
    parfile: str = ""

    #: last error status
    errorstatus = ["OK", ""]

    #: file type constants
    filetypes = {"FITS": 0, "MEF": 1, "BIN": 2, "ASM": 6}

    #: image parameters
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

    #: ROI for image analysis
    imageroi = []

    #: list of current system objects
    objects = {}

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

    #: header objects
    headers = {}

    #: header order in image header
    headerorder: typing.List[str] = []

    #: logger
    logger = None

    #: objects (from classes) generally available everywhere
    objects: typing.Dict[str, typing.Any] = {}

    #: azcamparameters only used by azcam
    azcamparameters = {}

    #: object which provides header corrdinates
    coord_object = "telescope"

    #: folders
    datafolder = ""

    def __init__(self):
        pass


# create instance
db = AzcamDatabase()
