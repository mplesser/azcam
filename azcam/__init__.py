import socket

from .logging import logger
from .api_azcam import api
from .database import db

# bring these into azcam namespace so importing not required
from .exceptions import AzcamError, AzcamWarning

# bring in functions
from .functions import fits, plot, utils

log = logger.log  # to allow azcam.log()
db.logger = logger

# save this machine's hostname and ip address
db.hostname = socket.gethostname()
db.hostip = socket.gethostbyname(db.hostname)

# clean namespace (never used directly again)
del socket
del database
del exceptions
del functions
