import azcam
from azcam.parameters import Parameters
from azcam.api_console import API
from azcam.database import AzcamDatabase

db = AzcamDatabase()

# local configuration parameters
params = Parameters("azcamconsole")
setattr(azcam.db, "params", params)
azcam.db.cli_objects["params"] = params

API()

# logging
from azcam.logging import Logger

azcam.db.logger = Logger()
azcam.log = azcam.db.logger.log  # to allow azcam.log()

# clean namespace (never used directly again)
del azcam.api_console
