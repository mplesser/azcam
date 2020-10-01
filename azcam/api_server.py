"""
API commands for server application.
"""

import azcam
from azcam import db


class API(object):
    """
    API interface for server application.
    """

    def __init__(self):

        setattr(azcam.db, "api", self)
        azcam.db.cmd_objects["api"] = self
        azcam.db.cli_cmds["api"] = self

    def test(self):
        """
        Just a test method.
        """

        azcam.log("I do nothing")

        return

    def get_status(self):
        """
        Get current exposure status.
        """

        return db.exposure.get_status()
