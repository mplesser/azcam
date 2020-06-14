"""
azcam observation control
"""

import socket

# bring these into azcam namespace so importing not required
from .exceptions import AzcamError, AzcamWarning
from .database import db
from .utils import log
from .image import Image
from . import utils, plot, fits

# save this machine's hostname and ip address
db.hostname = socket.gethostname()
db.hostip = socket.gethostbyname(db.hostname)

# clean namespace
del database, socket, exceptions
