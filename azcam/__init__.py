# bring these into azcam namespace so importing is not required

from azcam import fits
from azcam import utils
from azcam import plot
from azcam import image
from azcam.utils import get_tools
from azcam.database import AzcamDatabase
from azcam.exceptions import AzcamError, AzcamWarning

db = AzcamDatabase()
