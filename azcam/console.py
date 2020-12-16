import azcam
from azcam.api_console import API

azcam._app_type = 2  # console

# api (with remote db)
api = API()
azcam.api = API()

# logging
from azcam.logging import Logger

azcam.db.logger = Logger()
azcam.log = azcam.db.logger.log  # to allow azcam.log()

# exceptions: azcam.AzcamError and azcam.AzcamWarning
from azcam.exceptions import AzcamError, AzcamWarning

azcam.AzcamError = AzcamError
azcam.AzcamWarning = AzcamWarning

# local database entries
#: image parameters
azcam.db.imageparnames = [
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

#: exposure flags
azcam.db.exposureflags = {
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


# clean namespace (never used directly again)
del azcam.api_console
