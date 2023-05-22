"""
*azcam.tools* contains the `Tools` base tool class.
"""

import azcam


class Tools(object):
    """
    Base class used by tools (controller, instrument, telescope, etc.).
    """

    def __init__(self, tool_id: str, description: str or None = None):
        """
        Args:
            tool_id: name used to reference the tool (controller, display, ...)
            description: description of this tool
        """

        #: name used to reference the tool ("controller", "display", ...)
        self.tool_id: str = tool_id

        #: descriptive tool name
        self.description: str = ""
        if description is None:
            self.description = self.tool_id
        else:
            self.description = description

        #: 1 when tool is enabled
        self.enabled: int = 1

        #: 1 when tool has been initialized
        self.initialized: int = 0

        #: 1 when tool has been reset
        self.is_reset: int = 0

        # save tool name
        if self.tool_id not in azcam.db.tools:
            azcam.db.tools[self.tool_id] = self

        #: verbosity for debug, >0 is more verbose
        self.verbosity = 0

    def initialize(self) -> None:
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

    def reset(self) -> None:
        """
        Reset the tool.
        """

        self.is_reset = 1

        return
