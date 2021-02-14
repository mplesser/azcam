"""
Contains the base System class.
The System class contains custom code for a specific system, 
including "system header" commands. 
"""

from azcam.baseobject import Objects
from azcam.header import Header, ObjectHeaderMethods


class System(Objects, ObjectHeaderMethods):
    """
    System class.
    """

    def __init__(self, system_name, template_file=None):

        super().__init__("system", system_name)

        self.header = Header(system_name, template_file)
        self.header.set_header("system", 0)

        # self.define_keywords()

        return
