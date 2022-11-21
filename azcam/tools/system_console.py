"""
Contains the base SystemConsole tool.
"""

import azcam
from azcam.tools.console_tools import ConsoleTools


class SystemConsole(ConsoleTools):
    """
    System header interface for console.
    Usually implemented as the "system" tool.
    """

    def __init__(self) -> None:

        ConsoleTools.__init__(self, "system")
