"""
submodule for azcam.console
"""

from .api_console import API

api = API()

# cleanup namespace
del api_console
