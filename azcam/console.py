import azcam
from .api_console import API

azcam.db.app_type = 2  # console

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

# clean namespace (never used directly again)
del azcam.api_console
