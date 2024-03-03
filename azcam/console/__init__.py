import typing
from typing import List, Dict

# import here so future importing is not required
from azcam.console import utils

# initially azcam.log() is print(), will usually be overwritten
log: typing.Callable = print

mode = "console"
"""azcam mode, usually server or console"""

# clean namespace
del typing


import azcam.console.console
