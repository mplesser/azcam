"""
API interface for azcamserver.
"""

import sys

import azcam


class API(object):
    def __init__(self) -> None:
        pass

    def get(self, name):
        """
        Returns an API object by name.
        Returns None if api.name is not defined.
        """

        try:
            obj = getattr(self, name)
        except AttributeError:
            obj = None

        return obj


# create instance
api = API()
