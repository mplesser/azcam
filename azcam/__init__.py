from .database import AzcamDatabase

# bring these into azcam namespace so importing is not required
from azcam import fits
from azcam import utils
from azcam import plot

# local database
db = AzcamDatabase()

# exceptions: azcam.AzcamError and azcam.AzcamWarning
from azcam.exceptions import AzcamError, AzcamWarning
