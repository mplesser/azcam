"""
Contains the base TempConArchon class.
"""

import azcam
from azcam.server.tempcons.tempcon import TempCon


class TempConArchon(TempCon):
    """
    Defines the Archon temperature control class.
    Requires MOD2 to be the HEATERX board.
    """

    def __init__(self, *args):

        super().__init__(*args)

        self.enabled = 1
        self.num_temp_reads = 1
        self.control_temperature = -120.0

        self.last_temps = 3 * [self.bad_temp_value]  # last readings for during exposure

        return

    def set_control_temperature(self, temperature=None, temperature_id=0):
        """
        Set controller/detector control temperature.
        Ignored if heater board is installed.
        Temperature is temperature to set in Celsius.
        """

        if not self.enabled:
            return

        return

    def get_temperatures(self):
        """
        Updates and returns the current TEMPA, TEMPB, and TEMPC temperatures from HEATERX board.
        -999.9 value updated if board is not installed or other any error occurs.
        Returns [Temp1,Temp2,Temp3] where Temps are temperaturess in Celsius.
        """

        # return bad_temp_value if no utlity board
        if not azcam.db.objects["controller"].heater_board_installed:
            return 3 * [self.bad_temp_value]

        # Don't read hardware while exposure is in progess, return last values read
        exposure = azcam.db.objects["exposure"]
        flag = exposure.exposure_flag
        if flag != azcam.db.exposureflags["NONE"]:
            return self.last_temps

        camtemp = self.get_temperature(0)

        dewtemp = self.get_temperature(1)

        diodetemp = self.get_temperature(2)

        return [camtemp, dewtemp, diodetemp]

    def get_temperature(self, temperature_id=0):
        """
        Read a camera temperature.
        TemperaureID's are:
        0 => TEMPA
        1 => TEMPB
        2 => TEMPC
        """

        if not self.enabled:
            # azcam.AzcamWarning("Tempcon not enabled")
            return -999.9

        if not self.initialized:
            # azcam.AzcamWarning("Tempcon not initialized")
            return -999.9

        controller = azcam.db.objects["controller"]
        exposure = azcam.db.objects["exposure"]

        if not controller.heater_board_installed:
            return self.bad_temp_value

        if not controller.is_reset:
            return self.bad_temp_value

        # define dictionary entry
        if temperature_id == 0:
            Address = "MOD2/TEMPA"
        elif temperature_id == 1:
            Address = "MOD2/TEMPB"
        elif temperature_id == 2:
            Address = "MOD2/TEMPC"
        else:
            return "ERROR bad temperature_id"

        # Don't read hardware while exposure is in progess
        flag = exposure.exposure_flag
        if flag != azcam.db.exposureflags["NONE"]:
            return self.last_temps[temperature_id]

        # read temperature
        avetemp = 0
        for _ in range(self.num_temp_reads):
            temp = float(controller.get_status()[Address])
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
