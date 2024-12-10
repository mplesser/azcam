"""
Contains the TempConASCOM class.
"""

import azcam
import azcam.exceptions
from azcam.tools.tempcon import TempCon


class TempConASCOM(TempCon):
    """
    Temperature control class for cameras using ASCOM.
    """

    def __init__(self, tool_id="tempcon", description=None):
        super().__init__(tool_id, description)

        self.temperature_ids = [0, 1]  # camtemp, dewtemp

        self.init_commands = []

    def define_keywords(self):
        """
        Defines and resets tempcon keywords.
        """

        self.set_keyword("CAMTEMP", 0.0, "Camera temperature", "float")
        self.set_keyword("DEWTEMP", 0.0, "Dewar temperature", "float")
        self.set_keyword("TEMPUNIT", "C", "Temperature units", "str")

        return

    def initialize(self):
        """
        Initialize CryoConM24TemperatureControl temperature controller.
        """

        if self.is_initialized:
            return
        if not self.is_enabled:
            azcam.exceptions.warning(f"{self.description} is not enabled")
            return

        # set control temp
        self.set_control_temperature(self.control_temperature)

        self.is_initialized = 1

        return

    def set_control_temperature(
        self, temperature: float = None, temperature_id: int = -1
    ):
        """
        Set control temperature in Celsius.
        Args:
            temperature: temperature to set
            temperature_id: temperature ID number
                * 0 is TempA
                * 1 is TempB
        """

        if temperature is None:
            temperature = self.control_temperature
        else:
            self.control_temperature = float(temperature)

        # turn cooler ON
        azcam.db.tools["tempcon"].set_cooler(1)

        azcam.db.tools["controller"].camera.SetCCDTemperature = temperature

        return

    def get_temperature(self, temperature_id: int = 0):
        """
        Reads temperatures from the tempcon controller.
        Args:
            temperature_id: temperature ID number
        Returns:
            temperature: temperature read
        """

        if not self.is_enabled:
            # azcam.exceptions.warning("Tempcon not enabled")
            return -999.9

        if not self.is_initialized:
            # azcam.exceptions.warning("Tempcon not initialized")
            return -999.9

        temperature_id = int(temperature_id)
        if temperature_id == 0:
            pass
        elif temperature_id == 1:
            pass
        else:
            raise azcam.exceptions.AzcamError("bad temperature_id in get_temperature")

        reply = azcam.db.tools["controller"].camera.CCDTemperature
        try:
            temp = float(reply)
        except ValueError:
            temp = self.bad_temp_value

        temp = self.apply_corrections(temp, temperature_id)

        return temp

    def get_cooler_power(self):
        """
        Reads cooler power.
        Returns:
            temperature: temperature read
        """

        return azcam.db.tools["controller"].camera.CoolerPower

    def set_cooler(self, state):
        """
        Sets cooler ON (1) of OFF (0).
        Args:
            state: 1 for ON, 0 for OFF
        """

        azcam.db.tools["controller"].camera.CoolerOn = state

        return
