"""
Contains the TempConArc class.
"""

import math

import azcam
import azcam.exceptions
from azcam.tools.tempcon import TempCon


class TempConArc(TempCon):
    """
    Defines the ARC temperature control class.
    This is used for Gen1, Gen2, and Gen3 ARC controllers.
    """

    def __init__(self, tool_id="tempcon", description=None):
        super().__init__(tool_id, description)

        self.num_temp_reads = 5

        self.temperature_ids = [0, 1]  # camtemp, dewtemp

        return

    def define_keywords(self):
        """
        Defines and resets tempcon keywords.
        """

        self.set_keyword("CAMTEMP", 0.0, "Camera temperature", "float")
        self.set_keyword("DEWTEMP", 0.0, "Dewar temperature", "float")
        self.set_keyword("TEMPUNIT", "C", "Temperature units", "str")

        return

    def set_control_temperature(self, temperature=None, temperature_id=0):
        """
        Set controller/detector control temperature.
        Ignored if no utlity board is installed.
        Temperature is temperature to set in Celsius.
        """

        if not self.is_enabled:
            azcam.exceptions.warning(f"{self.description} is not enabled")
            return

        TEMPSET = 0x01C

        # ignore if no utlity board
        if not azcam.db.tools["controller"].utility_board_installed:
            return

        # ignore if controller is not reset
        if not azcam.db.tools["controller"].is_reset:
            return

        if temperature is None:
            temperature = self.control_temperature
        else:
            self.control_temperature = float(temperature)

        temperature_id = int(temperature_id)
        counts = self.convert_temp_to_counts(2, self.control_temperature)
        azcam.db.tools["controller"].write_memory(
            "Y", azcam.db.tools["controller"].UTILITYBOARD, TEMPSET, int(counts)
        )

        return

    def get_temperature(self, temperature_id=0):
        """
        Read a utlity board temperature.
        TemperaureID's are:
        0 => CAMTEMP
        1 => DEWTEMP
        2 => DIODETEMP
        """

        if not self.is_enabled:
            # azcam.exceptions.warning("Tempcon not enabled")
            return -999.9

        if not self.is_initialized:
            # azcam.exceptions.warning("Tempcon not initialized")
            return -999.9

        if not azcam.db.tools["controller"].utility_board_installed:
            return self.bad_temp_value

        if not azcam.db.tools["controller"].is_reset:
            return self.bad_temp_value

        # define DSP address
        if temperature_id == 0:
            Address = 13
        elif temperature_id == 1:
            Address = 14
        elif temperature_id == 2:
            Address = 12
        else:
            raise azcam.exceptions.AzcamError("bad temperature_id in get_temperature")

        temperature_id = int(temperature_id)

        # Don't read hardware while exposure is in progess
        flag = azcam.db.tools["exposure"].exposure_flag
        if flag != azcam.db.tools["exposure"].exposureflags["NONE"]:
            return self.last_temps[temperature_id]

        # read temperature
        cmd = "RDM"
        avecount = 0
        try:
            for _ in range(self.num_temp_reads):
                reply = azcam.db.tools["controller"].board_command(
                    cmd, azcam.db.tools["controller"].UTILITYBOARD, 0x400000 | Address
                )  # Y space
                counts = int(reply)
                avecount += counts
        except ValueError:
            raise azcam.exceptions.AzcamError("could not read temperature")
        counts = avecount / self.num_temp_reads

        # convert from counts to Celsius
        temp = self.convert_counts_to_temp(
            self.temperature_cals[temperature_id], counts
        )

        temp = self.apply_corrections(temp, temperature_id)

        # make nice float
        temp = float(int(temp * 1000.0) / 1000.0)

        # use some limits
        if temp > 100.0 or temp < -300.0:
            temp = -999.9

        # save temp
        self.last_temps[temperature_id] = temp

        return temp

    def convert_counts_to_temp(self, calflag: int, counts: int) -> float:
        """
        Convert counts (DN) to degrees Celsius.
        Uses Chebyechev polynomial.

        :param calflag: calibration curve to use
        :param counts: value to convert

          * 0 => convert DT670  counts to degrees C
          * 1 => convert AD590  counts to degrees C
          * 2 => convert 1N4148 counts to degrees C
          * 3 => convert 1N914  counts to degrees C
        """

        MAXBOUND = 11
        B = [
            82.017868,
            -59.064244,
            -1.356615,
            1.055396,
            0.837341,
            0.431875,
            0.440840,
            -0.061588,
            0.209414,
            -0.120882,
            0.055734,
            -0.035974,
        ]
        C = [
            306.592351,
            -205.393808,
            -4.695680,
            -2.031603,
            -0.071792,
            -0.437682,
            0.176352,
            -0.182516,
            0.064687,
            -0.027019,
            0.010019,
        ]
        A = MAXBOUND * [0]
        MAXDIODE = 19
        DC = [
            2600,
            2728,
            2823,
            2966,
            3003,
            3009,
            3070,
            3107,
            3118,
            3139,
            3166,
            3183,
            3217,
            3256,
            3269,
            3329,
            3357,
            3379,
            3417,
        ]  # diode count array
        DT = [
            311,
            277,
            250,
            210,
            200,
            190,
            180,
            170,
            160,
            155,
            150,
            147,
            137,
            127,
            117,
            107,
            97,
            87,
            77,
        ]  # diode temp array

        NOAO = [471.3507, -581.5675, 558.4024, -786.8676, 628.3720, -219.7995]

        VMIN = 0.07000
        VMAX = 1.122751
        VOLTMAX = 3.0
        VOLTMIN = -3.0
        COUNTMAX = 4095
        COUNTMIN = 0
        GAIN = 2.0  # this is the gain before ADC

        if calflag == 0:  # DT670 counts to Celsius
            # convert counts to voltage
            voltage = (
                ((VOLTMAX - VOLTMIN) / (COUNTMAX - COUNTMIN + 1))
                * (counts - 2048)
                / GAIN
            )

            if voltage > VMAX:
                temp = -999.9
                return temp
            elif voltage < VMIN:
                temp = +999.9
                return temp

            if voltage >= 0.986974:
                for i in range(MAXBOUND):  # 24.5 to 100.0 K
                    A[i] = B[i]
                    zl = 0.909416
                    zu = 1.122751
            else:
                for i in range(MAXBOUND):  # 100 to 500k
                    A[i] = C[i]
                    zl = 0.07000
                    zu = 0.99799

            x = ((voltage - zl) - (zu - voltage)) / (zu - zl)
            temp = 0.0
            for i in range(MAXBOUND):
                temp += A[i] * math.cos(i * math.acos(x))
            temp -= 273.13  # K to C
            return temp

        elif calflag == 1:  # AD590 case counts to Celsius
            temp = 0.16012 * counts - 599.5
            return temp

        elif calflag == 2:  # 1N4148 diode counts to Celsius
            if counts < DC[0]:
                temp = +999.9
                return temp
            elif counts > DC[MAXDIODE - 1]:
                temp = -999.9
                return temp

            for i in range(MAXDIODE):
                if counts < DC[i]:
                    inc = ((DT[i - 1] - DT[i]) / (DC[i - 1] - DC[i])) * (counts - DC[i])
                    temp = DT[i] + inc - 273.13  # simple for now
                    break
            return temp

        elif calflag == 3:  # 1N914 diode voltage to Celsius
            # convert counts to voltage
            voltage = (
                ((VOLTMAX - VOLTMIN) / (COUNTMAX - COUNTMIN + 1))
                * (counts - 2048)
                / GAIN
            )

            temp = (
                NOAO[0]
                + voltage * NOAO[1]
                + pow(voltage, 2) * NOAO[2]
                + pow(voltage, 3) * NOAO[3]
                + pow(voltage, 4) * NOAO[4]
                + pow(voltage, 5) * NOAO[5]
                - 273.13
            )
            return temp

        else:
            raise azcam.exceptions.AzcamError("ConvertCountsToTemp", "invalid calflag")

    def convert_temp_to_counts(self, calflag: int, temperature: float) -> float:
        """
        Convert degrees Celsius to counts.

        :param calflag: calibration flag to use
        :param temperature: temperature in C to convert
        """

        NOAOINV = [6.00e-09, -3.50e-06, -0.0021, 1.1616]  # inverse of NOAO

        if calflag == 2:  # 1N914 diode case Celsius to counts
            VOLTMAX = 3.0
            VOLTMIN = -3.0
            COUNTMAX = 4095
            COUNTMIN = 0
            GAIN = 2.0  # this is the gain before ADC

            inp = temperature + 273.13  # C to K
            voltage = (
                NOAOINV[3]
                + inp * NOAOINV[2]
                + pow(inp, 2) * NOAOINV[1]
                + pow(inp, 3) * NOAOINV[0]
            )
            counts = ((COUNTMAX - COUNTMIN + 1) / (VOLTMAX - VOLTMIN)) * (
                voltage * GAIN
            ) + 2048

        else:
            raise azcam.exceptions.AzcamError("convert_temp_to_counts invalid calflag")

        return counts
