import socket

import azcam
from azcam.database import AzcamDatabase
from azcam.api_server import API

azcam._app_type = 1  # server

db = AzcamDatabase()
azcam.db = db  # temporary
azcam.api = API()
azcam.api.db = db

# logging
from azcam.logging import Logger

azcam.api.db.logger = Logger()
azcam.log = azcam.api.db.logger.log  # to allow azcam.log()

# exceptions: azcam.AzcamError and azcam.AzcamWarning
from azcam.exceptions import AzcamError, AzcamWarning

azcam.AzcamError = AzcamError
azcam.AzcamWarning = AzcamWarning

# save this machine's hostname and ip address
azcam.api.db.hostname = socket.gethostname()
azcam.api.db.hostip = socket.gethostbyname(db.hostname)

# clean namespace (never used directly again)
del azcam.api_server
del azcam.database
del azcam.exceptions
del azcam.logging