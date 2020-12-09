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

api = None

# save this machine's hostname and ip address
db.hostname = socket.gethostname()
db.hostip = socket.gethostbyname(db.hostname)

# clean namespace (never used directly again)
del socket, database, exceptions, Logger
