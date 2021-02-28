"""
Contains the base System class.
The System class contains custom code for a specific system, 
including "system header" commands. 
"""

import azcam
from azcam.baseobject import Objects
from azcam.header import Header, ObjectHeaderMethods
from azcam.console_tools import ConsoleTools


class System(Objects, ObjectHeaderMethods):
    """
    System tool class.
    """

    def __init__(self, system_name, template_file=None):

        super().__init__("system", system_name)

        self.header = Header(system_name, template_file)
        self.header.set_header("system", 0)

        # self.define_keywords()

        return


class SystemConsole(ConsoleTools):
    """
    System header interface for console.
    """

    def __init__(self) -> None:
        self.objname = "system"
        azcam.db.cli_objects[self.objname] = self
        setattr(azcam.db, self.objname, self)
