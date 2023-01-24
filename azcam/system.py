"""
Contains the base System object.
The System class contains custom code for a specific system,
including "system header" commands.
"""

from azcam.header import Header, ObjectHeaderMethods


class System(ObjectHeaderMethods):
    """
    System class.
    """

    def __init__(self, system_name, template_file=None):

        self.header = Header(system_name, template_file)
        self.header.set_header("system", 0)

        self.system = self

        return
