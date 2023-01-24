"""
Contains the base Instrument class.
"""

import time
from typing import Any, List, Optional

import azcam
from azcam.header import Header, ObjectHeaderMethods
from azcam.tools.tools import Tools
from azcam.tools.console_tools import ConsoleTools


class Instrument(Tools, ObjectHeaderMethods):
    """
    The base instrument tool.
    Usually implemented as the "instrument" tool.
    """

    def __init__(self, tool_id="instrument", description=None):

        Tools.__init__(self, tool_id, description)

        # active comparisons
        self.active_comps = []

        # True if shutter controls comps
        self.shutter_strobe = 0

        # focus position
        self.focus_position = 0

        # system pressures
        self.pressure_ids = [0]

        # system currents
        self.current_ids = [0]

        azcam.db.tools_init["instrument"] = self
        azcam.db.tools_reset["instrument"] = self

        # instrument header object
        self.header = Header("Instrument")
        self.header.set_header("instrument", 3)

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
        Optional tempcon.call after exposure finishes.
        """

        return

    # ***************************************************************************
    # comparisons
    # ***************************************************************************
    def get_all_comps(self):
        """
        Return all valid comparison names.
        Useful for clients to determine which type of comparison exposures are supported.
        """

        raise NotImplementedError

    def get_comps(self):
        """
        Return a list of the active comparison lamps.
        """

        return self.active_comps

    def set_comps(self, comp_names: List[str] = None):
        """
        Set comparisons to be turned on and off with comps_on() and comps_off().
        Args:
            comp_names: list of string (or a single string) of comparison names
        """

        if type(comp_names) == str:
            comp_names = comp_names.split(" ")

        self.active_comps = comp_names

        return

    def comps_on(self):
        """
        Turn on active comparisons.
        """

        return

    def comps_off(self):
        """
        Turn off active comparisons.
        """

        return

    def comps_delay(self, delay_time=0):
        """
        Delays for delay_time for comparison lamp warmup.
        May internally set delay based on comp selection.
        Args:
            delay_time: delay in seconds
        """

        time.sleep(delay_time)

        return

    # ***************************************************************************
    # filters
    # ***************************************************************************
    def get_filters(self, filter_id=0):
        """
        Return a list of all available/loaded filters.
        Args:
            filter_id: filter mechanism ID
        """

        raise NotImplementedError

    def get_filter(self, filter_id=0):
        """
        Return the current/loaded filter, typically the filter in the beam.
        Args:
            filter_id: filter mechanism ID
        """

        raise NotImplementedError

    def set_filter(self, filter_name, filter_id=0):
        """
        Set the current/loaded filter, typically the filter in the beam.
        Args:
            filter_name: filter name to set. Could be a number or filter name.
            filter_id: filter mechanism ID
        """

        raise NotImplementedError

    # ***************************************************************************
    # wavelengths
    # ***************************************************************************
    def get_wavelengths(self, wavelength_id: int = 0):
        """
        Returns a list of valid wavelengths.
        Used for filter and LED based systems.
        Args:
            wavelength_id: wavelength mechanism ID
        """

        raise NotImplementedError

    def get_wavelength(self, wavelength_id: int = 0):
        """
        Returns the current wavelength.
        Args:
            wavelength_id: wavelength mechanism ID
        """

        raise NotImplementedError

    def set_wavelength(self, wavelength: Any, wavelength_id: int = 0):
        """
        Set the current wavelength, typically for a filter or grating.
        Args:
            wavelength: wavelength value to set. Could be a number or filter name.
            wavelength_id: wavelength mechanism ID
        """

        raise NotImplementedError

    # ***************************************************************************
    # focus
    # ***************************************************************************
    def get_focus(self, focus_id=0):
        """
        Return the current instrument focus position.
        focus_id is the focus mechanism ID.
        """

        raise NotImplementedError("get_focus")

    def set_focus(self, focus_position, focus_id=0, focus_type="absolute"):
        """
        Move (or step) the instrument focus.
        focus_position is the focus position or step size.
        focus_id is the focus mechanism ID.
        focus_type is "absolute" or "step".
        """

        raise NotImplementedError("set_focus")

    # ***************************************************************************
    # pressure
    # ***************************************************************************
    def get_pressures(self):
        """
        Return a list of all instrument pressures.
        """

        pressures = []
        for pressure_id in self.pressure_ids:
            p = self.get_pressure(pressure_id)
            pressures.append(p)

        return pressures

    def get_pressure(self, pressure_id=0):
        """
        Read an instrument pressure.
        """

        raise NotImplementedError

    def set_pressure(self, pressure, pressure_id=0):
        """
        Sets an instrument pressure.
        """

        raise NotImplementedError

    # ***************************************************************************
    # shutter
    # ***************************************************************************
    def set_shutter(self, state, shutter_id=0):
        """
        Open or close the instrument shutter.
        state is 1 for open and 0 for close.
        shutter_id is the shutter mechanism ID.
        """

        raise NotImplementedError

    # ***************************************************************************
    # power meter
    # ***************************************************************************
    def get_power(self, wavelength: float, power_id: int = 0) -> float:
        """
        Returns power meter reading.
        Args:
            wavelength: wavelength for power meter
            power_id: power ID flag
        Returns:
            mean_power: mean power in Watts/cm2
        """

        raise NotImplementedError

    # ***************************************************************************
    # electrometer
    # ***************************************************************************
    def get_currents(self):
        """
        Return a list of all instrument currents.
        """

        currents = []
        for current_id in self.current_ids:
            p = self.get_current(current_id)
            currents.append(p)

        return currents

    def get_current(self, shutter_state: int = 1, current_id: int = 0) -> float:
        """
        Read instrument current, usually from an electrometer.
        Args:
            current_id: current source ID
            shutter_state: shutter state during read
        Returns:
            current: measured current in amps
        """

        raise NotImplementedError

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

        return azcam.db.tools["server"].command(f"{self.objname}.set_comps {comp_names}")

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

        return azcam.db.tools["server"].command(f"{self.objname}.get_filters {filter_id}")

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

        return azcam.db.tools["server"].command(f"{self.objname}.get_filter {filter_id}")

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
            azcam.db.tools["server"].command(f"{self.objname}.get_wavelength {wavelength_id}")
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

        return azcam.db.tools["server"].command(f"{self.objname}.set_shutter {state} {shutter_id}")

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
