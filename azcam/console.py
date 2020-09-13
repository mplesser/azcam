import azcam
from azcam.functions.api_console import API

api = API()

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
