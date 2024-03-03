"""
Contains the FocusConsole class.
"""

from typing import Union, List, Optional

import azcam
import azcam.utils
from azcam.console.tools.console_tools import ConsoleTools


class FocusConsole(ConsoleTools):
    """
    Focus tool for consoles.
    Usually implemented as the "focus" tool.
    """

    def __init__(self) -> None:
        super().__init__("focus")

        #: Number of exposures in focus sequence
        self.number_exposures = 7
        #: Number of focus steps between each exposure in a frame
        self.focus_step = 30
        #: Number of rows to shift detector for each focus step
        self.detector_shift = 10
        #: exposure time
        self.exposure_time = 1.0
        #: flag to not prompt when set_pars already called
        self.set_pars_called = 0

    def initalize(self):
        """
        Initialize focus routine.
        """

        return azcam.db.tools["server"].command(f"{self.objname}.initialize")

    def reset(self):
        """
        Reset focus tool to default values.
        """

        self.exposure_time = 1.0
        self.number_exposures = 7
        self.focus_step = 30
        self.detector_shift = 10
        self.set_pars_called = 0

        return azcam.db.tools["server"].command(f"{self.objname}.reset")

    def abort(self):
        """
        Abort focus exposure.
        """

        return azcam.db.tools["server"].command(f"{self.objname}.abort")

    def set_pars(
        self,
        exposure_time: float,
        number_exposures: int = 7,
        focus_step: float = 30,
        detector_shift: int = 10,
    ):
        """
        Set focus related parameters.
        Args:
            number_exposures: Number of exposures in focus sequence.
            focus_step: Number of focus steps between each exposure in a frame.
            detector_shift: Number of rows to shift detector for each focus step.
            exposuretime: Exposure time i seconds.

        """

        self.exposure_time = float(exposure_time)
        self.number_exposures = int(number_exposures)
        self.focus_step = float(focus_step)
        self.detector_shift = int(detector_shift)

        azcam.db.tools["server"].command(
            f"{self.objname}.set_pars {self.exposure_time} {self.number_exposures} {self.focus_step} {self.detector_shift}"
        )

        self.set_pars_called = 1

        return

    def run(
        self,
        exposure_time: [float, str] = "prompt",
        number_exposures: [int, str] = "prompt",
        focus_step: [float, str] = "prompt",
        detector_shift: [int, str] = "prompt",
    ):
        """
        Execute the focus sequence.
        If focus.set_pars() was previously called then those values are used and input here is ignored.
        Args:
            number_exposures: Number of exposures in focus sequence.
            focus_step: Number of focus steps between each exposure in a frame.
            detector_shift: Number of rows to shift detector for each focus step.
            exposuretime: Exposure time in seconds.
        """

        if self.set_pars_called:
            pass

        else:
            if exposure_time == "prompt":
                self.exposure_time = float(
                    azcam.utils.prompt("Exposure time (sec)", self.exposure_time)
                )
            if number_exposures == "prompt":
                self.number_exposures = float(
                    azcam.utils.prompt("Number of exposures", self.number_exposures)
                )
            if focus_step == "prompt":
                self.focus_step = float(
                    azcam.utils.prompt("Focus step size", self.focus_step)
                )

            if detector_shift == "prompt":
                self.detector_shift = float(
                    azcam.utils.prompt(
                        "Number detector rows to shift", self.detector_shift
                    )
                )

        azcam.db.tools["server"].command(
            f"{self.objname}.run {self.exposure_time} {self.number_exposures} {self.focus_step} {self.detector_shift}"
        )

        return
