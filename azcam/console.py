import azcam

azcam.db.app_type = 2  # console

from azcam.api_console import API

api = API()

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
