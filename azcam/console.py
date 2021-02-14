import azcam
from azcam.configuration import Config
from azcam.api_console import API
from azcam.database import AzcamDatabase

db = AzcamDatabase()

# local configuration parameters
config = Config("azcamconsole")
setattr(azcam.db, "config", config)
azcam.db.cli_objects["config"] = config

API()

# logging
from azcam.logging import Logger

azcam.db.logger = Logger()
azcam.log = azcam.db.logger.log  # to allow azcam.log()

# clean namespace (never used directly again)
del azcam.api_console
