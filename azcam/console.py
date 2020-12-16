import azcam
from azcam.api_console import API

azcam._app_type = 2  # console

# api
api = API()
azcam.api = API()

azcam.db.cli_cmds.update({"db": azcam.db})

# logging
from azcam.logging import Logger

azcam.db.logger = Logger()
azcam.log = azcam.db.logger.log  # to allow azcam.log()

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
