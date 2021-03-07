"""
Main base object class.
Only used by other base object classes.
"""

import typing

import azcam


class Tools(object):
    """
    Base class used by tools (controller, instrument, telescope, etc.).

    Attributes:
        self.tool_id (str): name used to reference the tool (controller, display, ...)
        self.description (str): descriptive of the tool
        self.enabled (bool): True (default) when tool is enabled
        self.initialized (bool): True when tool has been initialized
        self.is_reset (bool): True when tool has been reset
    """

    def __init__(self, tool_id: str, description: str = None):
        """
        Args:
            tool_id: name used to reference the tool (controller, display, ...)
            description: descriptive of this tool
        """

        # id is the name used to reference the tool (controller, display, ...)
        self.tool_id = tool_id

        # descriptive name
        if description is None:
            self.description = self.tool_id
        else:
            self.description = description

        # True when tool is enabled
        self.enabled = 1

        # True when tool has been initialized
        self.initialized = 0

        # True when tool has been reset
        self.is_reset = 0

        # save instance to db
        setattr(azcam.db, self.tool_id, self)

        # save tool name
        if self.tool_id not in azcam.db.toolnames:
            azcam.db.toolnames.append(self.tool_id)

        # save for command line
        azcam.db.cli_tools[self.tool_id] = self

        # allow remote access if server
        try:
            azcam.db.remote_tools.append(self.tool_id)
        except AttributeError:
            pass

    def initialize(self):
        """
        Initialize the tool.
        """

        if self.initialized:
            return

        if not self.enabled:
            azcam.AzcamWarning(f"{self.description} is not enabled")
            return

        self.initialized = 1

        return

    def reset(self):
        """
        Reset the tool.
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
