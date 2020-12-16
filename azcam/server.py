import socket

import azcam
from azcam.database import AzcamDatabase
from azcam.api_server import API

azcam._app_type = 1  # server

azcam.api = API()
azcam.api.db = azcam.db

# logging
from azcam.logging import Logger

azcam.db.logger = Logger()
azcam.log = azcam.db.logger.log  # to allow azcam.log()

# exceptions: azcam.AzcamError and azcam.AzcamWarning
from azcam.exceptions import AzcamError, AzcamWarning

azcam.AzcamError = AzcamError
azcam.AzcamWarning = AzcamWarning

# save this machine's hostname and ip address
azcam.db.hostname = socket.gethostname()
azcam.db.hostip = socket.gethostbyname(azcam.db.hostname)

# clean namespace (never used directly again)
del azcam.api_server
del azcam.database
del azcam.exceptions
del azcam.logging
