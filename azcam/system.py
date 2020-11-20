"""
Contains the base System class.
"""

from typing import List

from azcam.baseobject import Objects
from azcam.header import Header


class System(Objects):
    """
    System class.
    """

    def __init__(self, system_name, template_file=None):

        super().__init__("system", system_name)

        # create the temp control Header object
        self.header = Header(system_name, template_file)
        self.header.set_header("system", 0)

        # add keywords
        self.define_keywords()

        return
