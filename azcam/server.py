import socket

import azcam
import azcam.api

# server mode
azcam.db.mode = "server"

# tools which can be accessed remotely
azcam.db.remote_tools = []

# local configuration parameters
from azcam.parameters import Parameters

params = Parameters("azcamserver")
setattr(azcam.db, "params", params)
azcam.db.cli_tools["params"] = params
azcam.db.remote_tools.append("params")

# logging
from azcam.logging import Logger

azcam.db.logger = Logger()
azcam.log = azcam.db.logger.log  # to allow azcam.log()

# save this machine's hostname and ip address
azcam.db.hostname = socket.gethostname()
azcam.db.hostip = socket.gethostbyname(azcam.db.hostname)

# tool_id's which are reset or initialized with exposure
azcam.db.tools_reset = {}
azcam.db.tools_init = {}

# clean namespace (never used directly again)
del azcam.database
del azcam.exceptions
del azcam.logging
