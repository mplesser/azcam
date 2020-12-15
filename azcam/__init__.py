# bring these into azcam namespace so importing not required
# from azcam.exceptions import AzcamError, AzcamWarning
from azcam import fits
from azcam import utils
from azcam import plot

api = None

# clean namespace (never used directly again)
# del azcam.exceptions
