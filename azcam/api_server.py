"""
API interface for azcamserver.
"""

import azcam


class API(object):
    """
    API interface for server application.
    """

    def __init__(self):

        super().__init__()

        setattr(azcam, "api", self)
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
