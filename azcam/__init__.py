"""
azcam.__init__
"""

import socket

# bring these into azcam namespace so importing not required
from .exceptions import AzcamError, AzcamWarning
from .database import db
from .image import Image

# bring in functions
from .functions import logging
from .functions import utils
from .functions import plot
from .functions import fits

# bring in for convenience
from .functions.logging import log

# save this machine's hostname and ip address
db.hostname = socket.gethostname()
db.hostip = socket.gethostbyname(db.hostname)

# clean namespace
del database, socket, exceptions, image
del functions, send_image, focalplane, header
