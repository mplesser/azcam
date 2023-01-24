"""
Contains the base Telescope class.
"""

import azcam
from azcam.header import Header, ObjectHeaderMethods
from azcam.tools.tools import Tools
from azcam.tools.console_tools import ConsoleTools


class Telescope(Tools, ObjectHeaderMethods):
    """
    The base telescope tool.
    Usually implemented as the "telescope" tool.
    """

    def __init__(self, tool_id="telescope", description=None):

        Tools.__init__(self, tool_id, description)

        # focus position
        self.focus_position = 0

        # create the temp control Header object
        self.header = Header("Telescope")
        self.header.set_header("telescope", 5)

        azcam.db.tools_init["telescope"] = self
        azcam.db.tools_reset["telescope"] = self

    # ***************************************************************************
    # exposure
    # ***************************************************************************

    def exposure_start(self):
        """
        Optional call before exposure starts.
        """

        return

    def exposure_finish(self):
        """
        Optional call after exposure finishes.
        """

        return

class TelescopeConsole(ConsoleTools):
    """
    Telescope tool for consoles.
    Usually implemented as the "telescope" tool.
    """

    def __init__(self) -> None:
        super().__init__("telescope")

    def get_focus(self, focus_id: int = 0) -> float:
        """
        Get the current telescope focus position.
        Args:
            focus_id: focus sensor ID flag
        """

        reply = azcam.db.tools["server"].command(f"{self.objname}.get_focus {focus_id}")

        return float(reply)

    def set_focus(
        self,
        focus_value: float,
        focus_id: int = 0,
        focus_type: str = "absolute",
    ) -> None:
        """
        Set the telescope focus position. The focus value may be an absolute position
        or a relative step if supported by hardware.
        Args:
            focus_value: focus position
            focus_id: focus sensor ID flag
            focus_type: focus type (absolute or step)
        """

        azcam.db.tools["server"].command(
            f"{self.objname}.set_focus {focus_value} {focus_id} {focus_type}"
        )

        return
