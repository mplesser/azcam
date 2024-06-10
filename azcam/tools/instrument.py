"""
Contains the base Instrument class.
"""

import time
from typing import Any, List, Optional

import azcam
from azcam.header import Header, ObjectHeaderMethods
from azcam.tools.tools import Tools


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

    def initialize(self):
        """
        Initialize tool.
        """

        self.is_initialized = 1

        return

    def reset(self):
        """
        Reset tool.
        """

        self.is_reset = 1

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
