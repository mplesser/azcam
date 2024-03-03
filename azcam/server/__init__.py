"""
*azcamserver* supports the server-side code for the AzCam image acquisition and analysis package.
"""

import typing
from typing import List, Dict

# initially azcam.log() is print(), will usually be overwritten
log: typing.Callable = print

mode = "server"
"""azcam mode, usually server or console"""

# clean namespace
del typing
