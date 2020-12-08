import socket

from .logging import Logger
from .database import db

# bring these into azcam namespace so importing not required
from .exceptions import AzcamError, AzcamWarning

# bring in functions
from . import fits, plot, utils

# logging
db.logger = Logger()
log = db.logger.log  # to allow azcam.log()

# save this machine's hostname and ip address
db.hostname = socket.gethostname()
db.hostip = socket.gethostbyname(db.hostname)

api = None

# clean namespace (never used directly again)
del socket
del database
del exceptions
