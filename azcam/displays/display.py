"""
Contains the Ds9Display class.
"""

import azcam


class Display(object):
    """
    azcam's interface to SAO's ds9 image display tool.
    """

    def __init__(self, name="display"):

        #: display name
        self.name = name

        #: display ID
        self.id = ""

        #: True when display in enabled
        self.enabled = 1

        #: True when display in initialized
        self.initialized = 0

        # set default display server
        self.default_display = 0

        # save object
        setattr(azcam.db, name, self)
        azcam.db.objects[name] = self

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

    def reset(self):
        """
        Reset dispaly object.
        """

        return

    def set_display(self, display_number=-1):
        """
        Set the current display by number.

        :param int display_number: Number for display to be used (0->N)
        :return None:
        """

        return
