"""
API interface for azcamserver.
"""

import azcam


class API(object):
    """
    API interface for server application.
    """

    def __init__(self):

        setattr(azcam, "api", self)
        azcam.db.cli_cmds["api"] = self

    def get(self, name):
        """
        Returns an API object by name.
        Returns None if api.name is not defined.
        If name is "all" then return a list of api object names.
        """

        if name == "all":
            objects = dir(self)
            for obj in objects[:]:
                if obj.startswith("_"):
                    objects.remove(obj)
            if "get" in objects:
                objects.remove("get")
            return objects

        try:
            obj = getattr(self, name)
        except AttributeError:
            obj = None

        return obj
