"""
*azcam.console* is imported to define console mode, create the azcamconsole parameters dictionary, and define a logger.
"""

import azcam
from azcam.logger import Logger
from azcam.parameters import Parameters

import azcam.database_console as database
db = database.AzcamDatabase()
azcam.db = db
db.tools["db"] = db

# console mode
azcam.db.mode = "console"

# parameters
parameters = Parameters("azcamconsole")

# logging
azcam.db.logger = Logger()
azcam.log = azcam.db.logger.log  # to allow azcam.log()
