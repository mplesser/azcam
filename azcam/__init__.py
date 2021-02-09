# bring these into azcam namespace so importing is not required

from azcam import fits
from azcam import utils
from azcam import plot

from .database import AzcamDatabase

db = AzcamDatabase()

from azcam.exceptions import AzcamError, AzcamWarning
