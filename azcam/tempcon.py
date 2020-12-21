"""
Contains the base TempCon class.
"""

from typing import List

import azcam
from azcam.baseobject import Objects
from azcam.header import Header


class TempCon(Objects):
    """
    Temperature control class.
    """

    def __init__(self, obj_id="tempcon", name="tempcon"):

        super().__init__(obj_id, name)

        self.id

        #: control or set temperature at which to regulate
        self.control_temperature = 0.0

        #: control temperature number (which temp is regulated)
        self.control_temperature_number = 0

        #: True to correct temperature offset and scale for each temperature
        #: Scaling is **new = old * scale + offset**
        self.temperature_correction = 0
        #: temperature offset corrections for each temperature
        self.temperature_offsets = [0.0]
        #: temperature scale corrections
        self.temperature_scales = [1.0]
        #: calibration flags for each temperature
        self.temperature_cals = [3]

        #: number of temperature sensors
        self.number_sensors = 4

        #: log temperatures
        self.log_temps = False

        #: value returned when temperature read is bad
        self.bad_temp_value = -999.9

        # create the temp control Header object
        self.header = Header("Temperature")
        self.header.set_header("tempcon", 4)

        # add keywords
        self.header.keywords = {"CAMTEMP": "CAMPTEMP", "DEWTEMP": "DEWTEMP"}
        self.header.comments = {
            "CAMTEMP": "Camera temperature in C",
            "DEWTEMP": "Dewar temperature in C",
        }
        self.header.typestrings = {"CAMTEMP": "float", "DEWTEMP": "float"}
        self.define_keywords()

        return

    def initialize(self):
        """
        Initialize the temperature control interface.
        """

        if self.initialized:
            return

        if not self.enabled:
            azcam.AzcamWarning(f"{self.name} is not enabled")
            return

        self.initialized = 1

        return

    def reset(self) -> None:
        """
        Reset tempcon object.
        """

        if not self.enabled:
            return

        self.set_control_temperature()

        return

    # *** exposure ***

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

        temps = [self.get_temperature(i) for i in range(self.number_sensors)]

        if self.log_temps:
            azcam.log(f"templog: {temps[0]} {temps[1]} {temps[2]} {temps[3]}", logconsole=0)

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
        self, temperature_offsets: List[float] = None, temperature_scales: List[float] = None,
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
            temp = float(int(temp * 1000.0) / 1000.0)
            self.header.set_keyword("CAMTEMP", temp, "Camera temperature in C", float)
        elif keyword == "DEWTEMP":
            temp = float(int(temp * 1000.0) / 1000.0)
            self.header.set_keyword("DEWTEMP", temp, "Dewar temperature in C", float)

        t = self.header.self.header.typestrings[keyword]

        return [temp, self.header.comments[keyword], t]
