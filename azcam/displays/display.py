"""
Contains the Ds9Display class.
"""

import azcam
from azcam.baseobject import Objects


class Display(Objects):
    """
    azcam's interface to SAO's ds9 image display tool.
    """

    def __init__(self, obj_id="display", obj_name="Display"):

        super().__init__(obj_id, obj_name)

        # set default display server
        self.default_display = 0

    def initialize(self):
        """
        Initialize display.
        """

        if self.initialized:
            return

        if not self.enabled:
            azcam.AzcamWarning("Display is not enabled")
            return

        self.set_display(self.default_display)

        return

    def set_display(self, display_number):
        """
        Set the current display by number.

        :param int display_number: Number for display to be used (0->N)
        :return None:
        """

        return
