"""
Contains the base System class.
The System class contains custom code for a specific system, 
including "system header" commands. 
"""

import azcam
from azcam.tools import Tools
from azcam.header import Header, ObjectHeaderMethods
from azcam.console_tools import ConsoleTools


class System(Tools, ObjectHeaderMethods):
    """
    System tool class.
    """

    def __init__(self, system_name, template_file=None):

        Tools.__init__(self, "system", system_name)

        self.header = Header(system_name, template_file)
        self.header.set_header("system", 0)

        return


class SystemConsole(ConsoleTools):
    """
    System header interface for console.
    """

    def __init__(self) -> None:
        self.objname = "system"
        azcam.db.cli_tools[self.objname] = self
        setattr(azcam.db, self.objname, self)
