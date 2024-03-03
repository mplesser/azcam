"""
Contains the InstrumentConsole class.
"""

from typing import Any, List, Optional

import azcam
from azcam.console.tools.console_tools import ConsoleTools


class InstrumentConsole(ConsoleTools):
    """
    Instrument tool for consoles.
    Usually implemented as the "instrument" tool.
    """

    def __init__(self) -> None:
        super().__init__("instrument")

    # ***************************************************************************
    # comparisons
    # ***************************************************************************
    def get_all_comps(self):
        """
        Return all valid comparison names.
        Useful for clients to determine which type of comparison exposures are supported.
        """

        return azcam.db.tools["server"].command(f"{self.objname}.get_all_comps")

    def get_comps(self):
        """
        Return a list of the active comparison lamps.
        """

        return azcam.db.tools["server"].command(f"{self.objname}.get_comps")

    def set_comps(self, comp_names=None):
        """
        Set comparisons which are to be turned on and off with comps_on() and comps_off().
        comp_names is a single string or a list of strings to be set as active.
        """

        return azcam.db.tools["server"].command(
            f"{self.objname}.set_comps {comp_names}"
        )

    def comps_on(self):
        """
        Turn on active comparisons.
        """

        return azcam.db.tools["server"].command(f"{self.objname}.comps_on")

    def comps_off(self):
        """
        Turn off active comparisons.
        """

        return azcam.db.tools["server"].command(f"{self.objname}.comps_off")

    # ***************************************************************************
    # filters
    # ***************************************************************************
    def get_filters(self, filter_id=0):
        """
        Return a list of all available/loaded filters.
        """

        return azcam.db.tools["server"].command(
            f"{self.objname}.get_filters {filter_id}"
        )

    def set_filter(self, filter_name: str, filter_id: int = 0) -> Optional[str]:
        """
        Set instrument filter position.

        :param filter_name: filter value to set
        :param filter_id: filter ID flag
        """

        return azcam.db.tools["server"].command(
            f"{self.objname}.set_filter {filter_name} {filter_id}"
        )

    def get_filter(self, filter_id: int = 0) -> str:
        """
        Get instrument filter position.

        :param filter_id: filter ID flag (use negative value for a list of all filters)
        """

        return azcam.db.tools["server"].command(
            f"{self.objname}.get_filter {filter_id}"
        )

    # ***************************************************************************
    # wavelengths
    # ***************************************************************************
    def set_wavelength(
        self, wavelength: float, wavelength_id: int = 0, nd: int = -1
    ) -> Optional[str]:
        """
        Set wavelength, optionally changing neutral density.

        :param wavelength: wavelength value, may be a string such as 'clear' or 'dark'
        :param wavelength_id: wavelength ID flag
        :param nd: neutral density value to set
        """

        return azcam.db.tools["server"].command(
            f"{self.objname}.set_wavelength {wavelength} {wavelength_id}"
        )

    def get_wavelength(self, wavelength_id: int = 0) -> float:
        """
        Get instrument wavelength.

        :param wavelength_id: wavelength ID flag  (use negative value for a list of all wavelengths)
        """

        reply = float(
            azcam.db.tools["server"].command(
                f"{self.objname}.get_wavelength {wavelength_id}"
            )
        )

        return reply

    # ***************************************************************************
    # focus
    # ***************************************************************************
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

        azcam.db.tools["server"].command(
            f"{self.objname}.set_focus {focus_value} {focus_id} {focus_type}"
        )

        return

    def get_focus(
        self,
        focus_id: int = 0,
    ) -> float:
        """
        Get the current focus position.

        :param focus_id: focus sensor ID flag
        """

        reply = azcam.db.tools["server"].command(f"{self.objname}.get_focus {focus_id}")

        return float(reply)

    def get_pressures(self) -> List[float]:
        """
        Return a list of all instrument pressures.
        """

        reply = azcam.db.tools["server"].command(f"{self.objname}.get_pressures")
        if type(reply) == str:
            reply = reply.split(" ")

        return [float(x) for x in reply]

    def set_shutter(self, state: int = 0, shutter_id: int = 0) -> Optional[str]:
        """
        Open or close a shutter.
        Args:
            state: shutter state, 0 for close and 1 for open
            shutter_id: Shutter ID flag

        """

        return azcam.db.tools["server"].command(
            f"{self.objname}.set_shutter {state} {shutter_id}"
        )

    def get_power(self, wavelength: float, power_id: int = 0) -> float:
        """
        Returns power meter reading.
        Args:
            wavelength: wavelength for power meter
            power_id: power ID flag
        Returns:
            mean_power: measured mean power in Watts/cm2
        """

        reply = azcam.db.tools["server"].command(
            f"{self.objname}.get_power {wavelength} {power_id}"
        )

        return float(reply)

    def get_currents(self) -> List[float]:
        """
        Return a list of all instrument currents.
        """

        reply = azcam.db.tools["server"].command(f"{self.objname}.get_currents")

        return [float(x) for x in reply]

    def get_current(
        self,
        shutter_state: int = 1,
        diode_id: int = 0,
    ) -> float:
        """
        Returns measured instrument diode current.
        Args:
            shutter_state: open (1), close (0), unchanged (2) shutter during diode read
            diode_id: diode ID flag (system dependent)
        Returns:
            current: measured curent in amps
        """

        reply = azcam.db.tools["server"].command(
            f"{self.objname}.get_current  {shutter_state} {diode_id}"
        )

        return float(reply)
