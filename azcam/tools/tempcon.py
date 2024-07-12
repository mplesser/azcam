"""
Contains the base TempCon class.
"""

from typing import List

import azcam
import azcam.exceptions
from azcam.header import Header, ObjectHeaderMethods
from azcam.tools.tools import Tools
from typing import Union, List, Optional


class TempCon(Tools, ObjectHeaderMethods):
    """
    The base temperature control tool.
    Usually implemented as the "tempcon" tool.
    """

    def __init__(self, tool_id: str = "tempcon", description: str = None):
        """
        Creates the tool.

        Args:
            tool_id: Name of tool
            description: Description of tool, defaults to tool_id.
        """

        Tools.__init__(self, tool_id, description)

        self.control_temperature = -999.0
        """control temperature in Celsius"""
        self.control_temperature_number = 0
        """control temperature number for regulattion)"""

        # system temperatures
        self.temperature_ids = [0]

        # True to correct temperature offset and scale for each temperature
        # Scaling is **new = old * scale + offset**
        self.temperature_correction = 0
        # temperature offset corrections for each temperature
        self.temperature_offsets = [0.0]
        # temperature scale corrections
        self.temperature_scales = [1.0]
        # calibration flags for each temperature
        self.temperature_cals = [3]

        # value returned when temperature read is bad
        self.bad_temp_value = -999.9

        self.last_temps = 3 * [self.bad_temp_value]  # last readings for during exposure

        # create the temp control Header object
        self.header = Header("Temperature")
        self.header.set_header("tempcon", 4)

        # add keywords
        self.define_keywords()

        azcam.db.tools_init["tempcon"] = self
        azcam.db.tools_reset["tempcon"] = self

        return

    def initialize(self):
        """
        Initialize tool.
        """

        self.is_initialized = 1

        return

    def reset(self) -> None:
        """
        Reset tempcon tool.
        """

        if not self.is_enabled:
            return

        if not self.is_initialized:
            self.initialize()

        self.set_control_temperature()

        return

    # ***************************************************************************
    # exposure
    # ***************************************************************************
    def exposure_start(self) -> None:
        """
        Custom commands before exposure starts.
        """

        return

    def exposure_finish(self) -> None:
        """
        Custom commands after exposure finishes.
        """

        return

    # ***************************************************************************
    # temperatures
    # ***************************************************************************
    def set_control_temperature(
        self, temperature: float = None, temperature_id: int = 0
    ) -> None:
        """
        Set the control temperature (set point).
        Args:
            temperature: control temperature in Celsius. If not specified, use saved value
            temperature_id: temperature sensor identifier
        """

        if temperature is None:
            temperature = self.control_temperature
        else:
            self.control_temperature = temperature

        return

    def get_control_temperature(self, temperature_id: int = 0) -> float:
        """
        Get the control temperature (set point).
        Args:
            temperature_id: temperature sensor identifier
        Returns:
            control_temperature: control temperature
        """

        return self.control_temperature

    def get_temperatures(self) -> List[float]:
        """
        Return all system temperatures.
        Returns:
            temperatures: list of temperatures read
        """

        temps = []
        for temperature_id in self.temperature_ids:
            p = self.get_temperature(temperature_id)
            temps.append(p)

        return temps

    def get_temperature(self, temperature_id: int = 0) -> float:
        """
        Returns a system temperature.
        Args:
            temperature_id: temperature sensor identifier
        Returns:
            temperature: temperature read
        """

        return self.bad_temp_value

    # ***************************************************************************
    # calibrations
    # ***************************************************************************
    def set_calibrations(self, cals: List[int]) -> None:
        """
        Set calibration curves for temperature sensors.
        The values of these flags are from the list below which define the calibration curves to use
        for each sensor's temperature conversion.

          * 0 => DT670  diode
          * 1 => AD590  sensor
          * 2 => 1N4148 diode
          * 3 => 1N914  diode
        Args:
            cals: list of flags defining each temperature sensor type
        """

        self.temperature_cals = []
        for i, cal in enumerate(cals):
            self.temperature_cals.append(cal)

        return

    def set_corrections(
        self,
        temperature_offsets: List[float] = None,
        temperature_scales: List[float] = None,
    ) -> None:
        """
        Set temperature correction values and enable correction.
        If both parameters are None then correction is disabled.
        Args:
            temperature_offsets: list of offsets for each temperature
            temperature_scales: list of scale factors for each temperature
        """

        # set and save values
        if temperature_offsets is None and temperature_scales is None:
            self.temperature_correction = 0
        else:
            self.temperature_correction = 1
        if temperature_offsets is not None:
            self.temperature_offsets = temperature_offsets
        if temperature_scales is not None:
            self.temperature_scales = temperature_scales

        return

    def apply_corrections(self, temperature: float, temperature_id: int = 0) -> float:
        """
        Correct the temperatures for offset and scale is temperature correction is enabled.
        Args:
            temperature: temperatures to be corrected
            temperature_id: temperature ID number
        Returns:
            corrected_temperature: temperature after correction has been appied
        """

        if self.temperature_correction:
            return (
                temperature * self.temperature_scales[temperature_id]
                + self.temperature_offsets[temperature_id]
            )
        else:
            return temperature

    # ***************************************************************************
    # keywords
    # ***************************************************************************
    def define_keywords(self):
        """
        Defines and resets tempcon keywords.
        """

        return

    def get_keyword(self, keyword: str) -> List:
        """
        Read a temperature keyword value and returns it as [value, comment, type string]
        Args:
            keyword: name of keyword
        Returns:
            list of [keyword, comment, type]
        """

        reply = self.get_temperatures()

        if keyword == "CAMTEMP":
            temp = reply[0]
        elif keyword == "DEWTEMP":
            temp = reply[1]
        elif keyword in self.get_keywords():
            value = self.header.values[keyword]
            temp = value
        else:
            raise azcam.exceptions.AzcamError(f"invalid keyword: {keyword}")

        # store temperature values in header
        if keyword == "CAMTEMP":
            temp = float(f"{temp:.03f}")
            self.header.set_keyword("CAMTEMP", temp, "Camera temperature in C", "float")
            self.header.set_keyword(
                "CCDTEMP1", temp, "Camera temperature in C", "float"
            )
        elif keyword == "DEWTEMP":
            temp = float(f"{temp:.03f}")
            self.header.set_keyword("DEWTEMP", temp, "Dewar temperature in C", "float")
            self.header.set_keyword("CCDTEMP2", temp, "Dewar temperature in C", "float")
        t = self.header.typestrings[keyword]

        return [temp, self.header.comments[keyword], t]
