"""
Contains the SystemHeader class.
"""

import azcam
from azcam.header import Header


class SystemHeader(Header):
    """
    Define system header which contains system/project specific information.
    """

    def __init__(self, systemname, template=""):
        """
        Create a system header, reading a template file if sepcified.

        :param str template: filename of template file.
        """

        super().__init__("System")

        # create the header object
        # self.header = Header("System")
        self.set_header("system", 0)

        self.set_title(f"System")
        self.set_keyword("SYSNAME", systemname, "System name")

        if template != "":
            azcam.db.objects["exposure"].imageheaderfile = template
            self.read_file(template)

    def update_header(self):
        """
        Update header, reading current data.
        """

        return
