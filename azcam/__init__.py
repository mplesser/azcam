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
from azcam import fits
from azcam import utils
from azcam.exceptions import AzcamError, AzcamWarning
from azcam.logger import Logger
from azcam.database import Database

# logger object
logger: Logger = Logger()

# initially azcam.log() is print(), will usually be overwritten
log: typing.Callable = print

# database placeholder
db: Database = Database()

# clean namespace
del metadata
del typing
# del Database
