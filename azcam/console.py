import azcam
from azcam.parameters import Parameters
from azcam.console_tools import load

# console mode
azcam.db.mode = "console"

# local configuration parameters
params = Parameters("azcamconsole")
setattr(azcam.db, "params", params)
azcam.db.cli_tools["params"] = params

# logging
from azcam.logging import Logger

azcam.db.logger = Logger()
azcam.log = azcam.db.logger.log  # to allow azcam.log()
