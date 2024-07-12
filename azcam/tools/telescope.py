"""
Contains the base Telescope class.
"""

import azcam
from azcam.header import Header, ObjectHeaderMethods
from azcam.tools.tools import Tools


class Telescope(Tools, ObjectHeaderMethods):
    """
    The base telescope tool.
    Usually implemented as the "telescope" tool.
    """

    def __init__(self, tool_id="telescope", description=None):
        Tools.__init__(self, tool_id, description)

        # focus position
        self.focus_position = 0

        # create the temp control Header object
        self.header = Header("Telescope")
        self.header.set_header("telescope", 5)

        azcam.db.tools_init["telescope"] = self
        azcam.db.tools_reset["telescope"] = self

    def initialize(self):
        """
        Initialize tool.
        """

        self.is_initialized = 1

        return

    def reset(self):
        """
        Reset tool.
        """

        self.is_reset = 1

        return

    # ***************************************************************************
    # exposure
    # ***************************************************************************

    def exposure_start(self):
        """
        Optional call before exposure starts.
        """

        return

    def exposure_finish(self):
        """
        Optional call after exposure finishes.
        """

        return
