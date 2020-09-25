"""
API commands for server application.
"""

import azcam


class API(object):
    """
    API interface for server application.
    """

    def __init__(self):

        pass

    def test(self):
        """
        Just a test method.
        """

        azcam.log("I do nothing")

        return
