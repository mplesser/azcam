"""
Contains the base Telescope class.
"""

import azcam
from azcam.baseobject import Objects
from azcam.header import Header, ObjectHeaderMethods
from azcam.console_tools import ConsoleTools


class Telescope(Objects, ObjectHeaderMethods):
    """
    Base telescope class.
    """

    def __init__(self, obj_id="telescope", name="Telescope"):

        super().__init__(obj_id, name)

        # focus position
        self.focus_position = 0

        # create the temp control Header object
        self.header = Header("Telescope")
        self.header.set_header("telescope", 5)

        azcam.db.objects_init["telescope"] = self
        azcam.db.objects_reset["telescope"] = self

    def initialize(self):
        """
        Initializes the telescope interface.
        """

        if self.initialized:
            return

        if not self.enabled:
            azcam.AzcamWarning(f"{self.name} is not enabled")
            return

        return

    def reset(self):
        """
        Reset telescope object.
        """

        return

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
    Telescope class for client.
    """

    def __init__(self) -> None:
        super().__init__("telescope")

    def initialize(self) -> None:
        """
        Initialize telescope.
        """

        return azcam.db.server.rcommand(f"{self.objname}.initialize")

    def reset(self) -> None:
        """
        Reset exposure.
        """

        return azcam.db.server.rcommand(f"{self.objname}.reset")

    def get_focus(self, focus_id: int = 0) -> float:
        """
        Get the current focus position.

        :param focus_id: focus sensor ID flag
        """

        reply = azcam.db.server.rcommand(f"{self.objname}.get_focus {focus_id}")

        return float(reply)

    def set_focus(
        self,
        focus_value: float,
        focus_id: int = 0,
        focus_type: str = "absolute",
    ) -> None:
        """
        Set instrument focus position. The focus value may be an absolute position
        or a relative step if supported by hardware.

        :param focus_value: focus position
        :param focus_id: focus sensor ID flag
        :param focus_type: focus type (absolute or step)
        """

        azcam.db.server.rcommand(f"{self.objname}.set_focus {focus_value} {focus_id} {focus_type}")

        return

    def get_focus(self, focus_id: int = 0) -> float:
        """
        Get the current focus position.

        :param focus_id: focus sensor ID flag
        """

        reply = azcam.db.server.rcommand(f"{self.objname}.get_focus {focus_id}")

        return float(reply)
