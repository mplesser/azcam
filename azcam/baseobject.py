"""
Main base object class.
Only used by other base object classes.
"""

import typing

import azcam


class Objects(object):
    """
    Base class used by main objects (controller, instrument, telescope, etc.).

    Attributes:
        self.id (str): name used to reference the object (controller, display, ...)
        self.name (str): descriptive name for the object
        self.enabled (bool): True (default) when object is enabled
        self.initialized (bool): True when object has been initialized
        self.is_reset (bool): True when object has been reset
    """

    def __init__(self, obj_id: str, name: str = "unknown"):
        """
        Args:
            obj_id: name used to reference the object (controller, display, ...)
            name: descriptive name for the object
        """

        # id is the name used to reference the object (controller, display, ...)
        self.id = obj_id

        # name is a descriptive name for the object
        self.name = name

        # True when object is enabled
        self.enabled = 1

        # True when object has been initialized
        self.initialized = 0

        # True when object has been reset
        self.is_reset = 0

        # save instance to db
        setattr(azcam.db, self.id, self)

        # save for command line
        azcam.db.cli_objects[self.id] = self

        # allow remote access if server
        try:
            azcam.db.remote_objects.append(self.id)
        except AttributeError:
            pass

    def initialize(self):
        """
        Initialize the object.
        """

        if self.initialized:
            return

        if not self.enabled:
            azcam.AzcamWarning(f"{self.name} is not enabled")
            return

        self.initialized = 1

        return

    def reset(self):
        """
        Reset the object.
        """

        self.is_reset = 1

        return

    def get(self, name: str) -> typing.Any:
        """
        Returns an existing attribute of this class.
        Args:
            name: name of attribute to return
        Returns:
            value: value of attribute or None if not defined
        """

        if not hasattr(self, name):
            return

        attr = getattr(self, name)

        return attr

    def set(self, name: str, value: typing.Any):
        """
        Sets an existing attribute value of this class.
        Args:
            name: name of attribute to set
            value: value of attribute to set
        """

        if not hasattr(self, name):
            return

        setattr(self, name, value)

        return
