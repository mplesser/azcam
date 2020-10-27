import socket

from .database import db
# bring these into azcam namespace so importing not required
from .exceptions import AzcamError, AzcamWarning
# bring in functions
from .functions import fits, logging, plot, utils
# bring in for convenience
from .functions.logging import log
from .image import Image

# save this machine's hostname and ip address
db.hostname = socket.gethostname()
db.hostip = socket.gethostbyname(db.hostname)
