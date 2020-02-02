"""
Contains the base TempCon class.
"""

from typing import List

import azcam
from azcam.header import Header


class TempCon(object):
    """
    Temperature control class.
    """

    def __init__(self, name="tempcon"):

        #: temperature controller name
        self.name = name

        #: temperature controller ID
        self.id = ""

        #: True if temperature control is initialized
        self.initialized = 0

        #: True if temperature control is enabled
        self.enabled = 0

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

        #: value returned when temperature read is bad
        self.bad_temp_value = -999.9

        # create the temp control Header object
        self.header = Header("Temperature")
        self.header.set_header("tempcon", 4)

        # add keywords
        self.define_keywords()

        # save object
        setattr(azcam.db, name, self)
        azcam.db.objects[name] = self

        return

    def initialize(self):
        """
        Initialize the temperature control interface.
        """

        if self.initialized:
            return

        if not self.enabled:
            return

        # self.temperature_offsets = self.number_sensors * [0.0]
        # self.temperature_scales = self.number_sensors * [1.0]
        # self.temperature_cals = self.number_sensors * [3]

        self.initialized = 1

        return

    def reset(self) -> None:
        """
        Reset tempcon object.
        """

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

    def set_control_temperature(
        self, temperature: float = None, temperature_id: int = 0
    ) -> None:
        """
        Set the control temperature (set point).

        :param temperature: control temperature in Celsius. If not specified, use saved value
        :param temperature_id: temperature ID number
        """

        if temperature is None:
            temperature = self.control_temperature
        else:
            self.control_temperature = temperature

        return

    def get_control_temperature(self, temperature_id: int = 0) -> float:
        """
        Get the control temperature (set point).

        :param temperature_id: temperature ID number
        """

        return self.control_temperature

    def get_temperatures(self) -> List[float]:
        """
        Return all system temperatures.
        """

        temps = [self.get_temperature(i) for i in range(self.number_sensors)]

        return temps

    def get_temperature(self, temperature_id: int = 0) -> float:
        """
        Returns a system temperature.

        :param temperature_id: temperature ID number
        """

        temp = self.bad_temp_value

        return temp

    def set_calibrations(self, cals: List[int]) -> None:
        """
        Set calibration curves for temperature sensors.

        :param cals: list of flags defining each temperature sensor type

        The values of these flags are from the list below which define the calibration curves to use
        for each sensor's temperature conversion.

           * 0 => DT670  diode
           * 1 => AD590  sensor
           * 2 => 1N4148 diode
           * 3 => 1N914  diode
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

        :param temperature_offsets: list of offsets for each temperature
        :param temperature_scales: list of scale factors for each temperature
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

        :param temperature: temperatures to be corrected
        :param temperature_id: temperature ID number
        """

        if self.temperature_correction:
            corrected_temp = (
                temperature * self.temperature_scales[temperature_id]
                + self.temperature_offsets[temperature_id]
            )
            return corrected_temp
        else:
            return temperature

    def define_keywords(self) -> None:
        """
        Defines temperature control keywords if they are not already defined.
        """

        if len(self.header.keywords) != 0:
            return

        # add keywords
        keywords = ["CAMTEMP", "DEWTEMP"]
        comments = {
            "CAMTEMP": "Camera temperature in C",
            "DEWTEMP": "Dewar temperature in C",
        }
        types = {"CAMTEMP": float, "DEWTEMP": float}

        for key in keywords:
            self.header.set_keyword(key, "", comments[key], types[key])

        return

    def read_keyword(self, keyword: str) -> List:
        """
        Read a temperature keyword value and returns it as [value, comment, type string].

        :param keyword: keyword name to read
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

        t = self.header.get_type_string(self.header.typestrings[keyword])

        return [temp, self.header.comments[keyword], t]

    def read_header(self) -> List[List]:
        """
        Reads, records, and returns the current header.
        Returns [Header[]]: Each element Header[i] contains the sublist (keyword, value, comment, and type).
        Example: Header[2][1] is the value of keyword 2 and Header[2][3] is its type
        """

        header = []
        keywords = self.header.get_all_keywords()

        for key in keywords:
            reply = self.read_keyword(key)
            list1 = [key, reply[0], reply[1], reply[2]]
            header.append(list1)

        return header

    def update_header(self) -> None:
        """
        Update headers, reading current data.
        """

        if not self.enabled:
            self.header.delete_all_keywords()
            return

        # update header
        self.define_keywords()
        self.read_header()

        return
