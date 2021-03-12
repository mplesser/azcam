"""
Contains the base TempCon class.
"""

from typing import Optional, Union, List

import azcam
from azcam.tools import Tools
from azcam.header import Header, ObjectHeaderMethods
from azcam.console_tools import ConsoleTools


class TempCon(Tools, ObjectHeaderMethods):
    """
    The base temperature control tool.
    """

    def __init__(self, tool_id: str = "tempcon", description: str = None):
        """
        Creates the tool.

        Args:
            tool_id: Name of tool
            description: Description of tool, defaults to tool_id.
        """

        super().__init__(tool_id, description)

        # control or set temperature at which to regulate
        self.AAA = 0.0
        """AAA docstring - control or set temperature at which to regulate"""

        # control temperature number (which temp is regulated)
        self.control_temperature_number = 0

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

        # create the temp control Header object
        self.header = Header("Temperature")
        self.header.set_header("tempcon", 4)

        # add keywords
        self.header.keywords = {"CAMTEMP": "CAMTEMP", "DEWTEMP": "DEWTEMP"}
        self.header.comments = {
            "CAMTEMP": "Camera temperature in C",
            "DEWTEMP": "Dewar temperature in C",
        }
        self.header.typestrings = {"CAMTEMP": "float", "DEWTEMP": "float"}
        self.define_keywords()

        azcam.db.tools_init["tempcon"] = self
        azcam.db.tools_reset["tempcon"] = self

        return

    def reset(self) -> None:
        """
        Reset tempcon tool.
        """

        if not self.enabled:
            return

        if not self.initialized:
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
    def set_control_temperature(self, temperature: float = None, temperature_id: int = 0) -> None:
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

    def apply_corrections(self, temperature: float, temperature_id: int = 0) -> None:
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
        else:
            raise azcam.AzcamError("invalid keyword")

        # store value in Header
        if keyword == "CAMTEMP":
            temp = float(f"{temp:.03f}")
            self.header.set_keyword("CAMTEMP", temp, "Camera temperature in C", float)
        elif keyword == "DEWTEMP":
            temp = float(f"{temp:.03f}")
            self.header.set_keyword("DEWTEMP", temp, "Dewar temperature in C", float)

        t = self.header.typestrings[keyword]

        return [temp, self.header.comments[keyword], t]


class TempconConsole(ConsoleTools):
    """
    Temperature controller tool for consoles.
    Usually implemented as the "tempcon" tool.
    """

    def __init__(self) -> None:
        super().__init__("tempcon")

    def set_control_temperature(
        self, control_temperature: float, temperature_id: int = 0
    ) -> Optional[str]:
        """
        Set the control temperature (set point).
        Args:
            control_temperature: control temperature in Celsius.
            temperature_id: temperature sensor identifier
        """

        return azcam.db.server.command(
            f"{self.objname}.set_control_temperature {control_temperature} {temperature_id}"
        )

    def get_control_temperature(self, temperature_id: int = 0) -> Union[str, float]:
        """
        Get the control temperature (set point).
        Args:
            temperature_id: temperature sensor identifier
        Returns:
            control_temperature: control temperature
        """

        reply = azcam.db.server.command(f"{self.objname}.get_control_temperature {temperature_id}")

        return float(reply)

    def get_temperatures(self) -> List[float]:
        """
        Return all system temperatures.
        Returns:
            temperatures: list of temperatures read
        """

        reply = azcam.db.server.command(f"{self.objname}.get_temperatures")

        return [float(x) for x in reply]

    def get_temperature(self, temperature_id: int = 0) -> float:
        """
        Returns a system temperature.
        Args:
            temperature_id: temperature sensor identifier
        Returns:
            temperature: temperature read
        """

        reply = azcam.db.server.command(f"{self.objname}.get_temperature {temperature_id}")

        return float(reply)
