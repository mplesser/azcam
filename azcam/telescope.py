"""
Contains the base Telescope class.
"""

import azcam
from azcam.baseobject import Objects
from azcam.header import Header


class Telescope(Objects):
    """
    Base telescope class.
    """

    def __init__(self, obj_id="telescope", obj_name="Telescope"):

        super().__init__(obj_id, obj_name)

        # keywords for header, list of [keyword, comment, type]
        self.keywords = {}

        # focus position
        self.focus_position = 0

        # create the temp control Header object
        self.header = Header("Telescope")
        self.header.set_header("telescope", 5)

    def initialize(self):
        """
        Initializes the telescope interface.
        """

        if self.initialized:
            return

        if not self.enabled:
            azcam.AzcamWarning(f"{self.name} is not enabled")
            return

        return

    def reset(self):
        """
        Reset telescope object.
        """

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
