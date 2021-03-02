"""
Contains the display tool.
This tool is often implemented both by server and console.
"""

import azcam
from azcam.baseobject import Objects
from azcam.header import Header, ObjectHeaderMethods


class Display(Objects, ObjectHeaderMethods):
    """
    The base display tool for server and consoles.
    Usually implemented as the "display" tool.
    """

    def __init__(self, obj_id="display", name="Display"):

        super().__init__(obj_id, name)

        # create the display Header object
        self.header = Header("Display")
        self.header.set_header("display", 2)

        # set default display server
        self.default_display = 0

        # allow initialization of display on server in exposure
        try:
            azcam.db.objects_init["display"] = self
        except AttributeError:
            pass

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

    def display(self, image, extension_number=-1):
        """
        Display a file on the image display.
        If specified for an MEF file, only extension_number is displayed.

        :param image: a filename or an image object
        :param int extension_number: FITS extension number of image, -1 for all
        :return None:
        """

        raise NotImplementedError
