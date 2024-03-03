"""
Contains the base Telescope class.
"""

import azcam
from azcam.console.tools.console_tools import ConsoleTools


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
