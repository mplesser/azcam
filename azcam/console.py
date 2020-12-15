import azcam
from .api_console import API

azcam._app_type = 2  # console

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

api = API()

# database configuration
# setattr(api, "db", azcam.db)
azcam.db.cli_cmds["db"] = azcam.db

# clean namespace (never used directly again)
del azcam.api_console
