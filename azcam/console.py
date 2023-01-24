"""
*azcam.console* is imported to define console mode, create the azcamconsole parameters dictionary, and define a logger.
"""

import azcam
from azcam.logger import Logger
from azcam.parameters import Parameters

# console mode
azcam.db.mode = "console"

# parameters
parameters = Parameters("azcamconsole")

# logging
azcam.db.logger = Logger()
azcam.log = azcam.db.logger.log  # to allow azcam.log()
