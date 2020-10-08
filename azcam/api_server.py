"""
API interface for azcamserver.
"""

import sys

import azcam
import azcam.api_azcam


class API(azcam.api_azcam.API):
    """
    API interface for server application.
    """

    def __init__(self):

        super().__init__()

        azcam.db.cli_cmds["api"] = self


# create instance
api = API()
