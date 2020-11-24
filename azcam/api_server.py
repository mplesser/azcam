"""
API interface for azcamserver.
"""

import sys

import azcam

# import azcam.api_azcam


class API(object):
    """
    API interface for server application.
    """

    def __init__(self):

        super().__init__()

        azcam.db.cli_cmds["api"] = self

    def _get(self, name):
        """
        Returns an API object by name.
        Returns None if api.name is not defined.
        """

        try:
            obj = getattr(self, name)
        except AttributeError:
            obj = None

        return obj
