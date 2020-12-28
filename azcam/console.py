import azcam
from azcam.api_console import API

# api
api = API()
azcam.api = API()

# logging
from azcam.logging import Logger

azcam.db.logger = Logger()
azcam.log = azcam.db.logger.log  # to allow azcam.log()

azcam.api.config.default_pardict_name = "azcamconsole"

# clean namespace (never used directly again)
del azcam.api_console
