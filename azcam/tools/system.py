"""
Contains the base System tool.
The System class contains custom code for a specific system,
including "system header" commands.
"""

from azcam.tools.header import Header, ObjectHeaderMethods
from azcam.tools.tools import Tools


class System(Tools, ObjectHeaderMethods):
    """
    System tool class.
    Usually implemented as the "system" tool.
    """

    def __init__(self, system_name, template_file=None):

        Tools.__init__(self, "system", system_name)

        self.header = Header(system_name, template_file)
        self.header.set_header("system", 0)

        return
