"""
Contains the ControllerConsole classe.
"""

import azcam
from azcam.console.tools.console_tools import ConsoleTools


class ControllerConsole(ConsoleTools):
    """
    Controller tool for consoles.
    Usually implemented as the "controller" tool.
    """

    def __init__(self) -> None:
        super().__init__("controller")

    def set_shutter(self, state: int = 0):
        """
        Open or close a shutter.

        Args:
            state: 1 to open shutter or 0 to close
        """

        return azcam.db.tools["server"].command(f"{self.objname}.set_shutter {state}")
