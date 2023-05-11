"""
AzCam is a software framework for the acquisition and analysis of image data
from scientific imaging systems as well as the control of instrumentation.
It is intended to be customized for specific hardware, observational,
and data reduction requirements.
"""

from importlib import metadata

__version__ = metadata.version(__package__)
__version_info__ = tuple(int(i) for i in __version__.split(".") if i.isdigit())

import typing

# import here so future importing is not required
from azcam.functions import fits
from azcam.functions import utils
from azcam.exceptions import AzcamError, AzcamWarning
<<<<<<< HEAD
from azcam.database import AzcamDatabase

#db = AzcamDatabase()
=======
from azcam.logger import Logger

# logger object
logger: Logger = Logger()
"""logger object"""
>>>>>>> 0c9e7c82d30b48a5a080d9e0cbfb7d59d0e2b810

# initially azcam.log() is print(), will usually be overwritten
log: typing.Callable = print

# clean namespace
del metadata
del typing
