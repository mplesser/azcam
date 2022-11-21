"""
Contains the TempConArchon class.
"""

import azcam
from azcam.tools.tempcon import TempCon


class TempConArchon(TempCon):
    """
    Defines the Archon temperature control tool.
    """

    def __init__(self, tool_id="tempcon", description=None):

        super().__init__(tool_id, description)

        self.num_temp_reads = 1
        self.control_temperature = -120.0
        self.heaterx_board = "MOD2"

        self.temperature_ids = [0, 1]  # camtemp, dewtemp

        self.last_temps = 3 * [self.bad_temp_value]  # last readings for during exposure

        return

    def define_keywords(self):
        """
        Defines and resets instrument keywords.
        """

        self.set_keyword("CAMTEMP", 0.0, "Camera temperature", "float")
        self.set_keyword("DEWTEMP", 0.0, "Dewar temperature", "float")
        self.set_keyword("TEMPUNIT", "C", "Temperature units", "str")

        return

    def get_temperature(self, temperature_id=0):
        """
        Read a camera temperature.
        TemperaureID's are:
        0 => TEMPA
        1 => TEMPB
        2 => TEMPC
        """

        if not self.enabled:
            return -999.9

        if not self.initialized:
            return -999.9

        if not azcam.db.tools["controller"].heater_board_installed:
            return self.bad_temp_value

        if not azcam.db.tools["controller"].is_reset:
            return self.bad_temp_value

        temperature_id = int(temperature_id)
        if temperature_id == 0:
            Address = f"{self.heaterx_board}/TEMPA"
        elif temperature_id == 1:
            Address = f"{self.heaterx_board}/TEMPB"
        elif temperature_id == 2:
            Address = f"{self.heaterx_board}/TEMPC"
        else:
            raise azcam.AzcamError("bad temperature_id in get_temperature")

        # Don't read hardware while exposure is in progess
        flag = azcam.db.tools["exposure"].exposure_flag
        if flag != azcam.db.tools["exposure"].exposureflags["NONE"]:
            return self.last_temps[temperature_id]

        # read temperature
        avetemp = 0
        for _ in range(self.num_temp_reads):
            temp = float(azcam.db.tools["controller"].get_status()[Address])
            avetemp += temp
        temp = avetemp / self.num_temp_reads

        temp = self.apply_corrections(temp, temperature_id)

        # make nice float
        temp = float(int(temp * 1000.0) / 1000.0)

        # use some limits
        if temp > 100.0 or temp < -300.0:
            temp = -999.9

        # save temp
        self.last_temps[temperature_id] = temp

        return temp
