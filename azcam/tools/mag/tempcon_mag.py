"""
Contains the base TempConMag class.
"""

import azcam
import azcam.exceptions
from azcam.tools.tempcon import TempCon


class TempConMag(TempCon):
    """
    Defines the MAG temperature control class.
    """

    def __init__(self, tool_id="tempcon", description="Mag tempcon"):
        super().__init__(tool_id, description)

        self.num_temp_reads = 3
        self.control_temperature = self.bad_temp_value  # no active control

        return

    def get_temperature(self, temperature_id: int = 0):
        """
        Returns the current detector temperature in Celsius.
        """

        if not self.is_enabled:
            # azcam.exceptions.warning("Tempcon not enabled")
            return -999.9

        if not self.is_initialized:
            # azcam.exceptions.warning("Tempcon not initialized")
            return -999.9

        itemp1 = itemp = 0.0
        for _ in range(self.num_temp_reads):  # multiple reads for average
            status = azcam.db.tools["controller"].magio("gcam_get_temp", 0)
            itemp1 = int(status[1])  # get temp in DN
            itemp = itemp + itemp1
        itemp = itemp / self.num_temp_reads  # make average

        if itemp > 8196:  # convert to Celsius
            itemp = itemp - 16384

        temp = (itemp - 902) * (-26.0 / 1164.0)  # float

        temp = self.apply_corrections(temp, 0)

        # make nice float
        temp = float(int(temp * 1000.0) / 1000.0)

        # use some limits
        if temp > 100.0 or temp < -300.0:
            temp = self.bad_temp_value

        return temp
