import socket

import azcam
from azcam.api_server import API
from azcam.configuration import Config

azcam._app_type = 1  # server

azcam.api = API()
azcam.api.db = azcam.db
azcam.db.cli_cmds.update({"db": azcam.db})

azcam.api.config = Config()
azcam.api.genpars = azcam.api.config  # temporary for azcamtool

# logging
from azcam.logging import Logger

azcam.db.logger = Logger()
azcam.log = azcam.db.logger.log  # to allow azcam.log()

# save this machine's hostname and ip address
azcam.db.hostname = socket.gethostname()
azcam.db.hostip = socket.gethostbyname(azcam.db.hostname)

# clean namespace (never used directly again)
del azcam.api_server
del azcam.database
del azcam.exceptions
del azcam.logging
