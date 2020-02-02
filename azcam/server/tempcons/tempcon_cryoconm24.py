"""
Contains the base TempConCryoCon class.
"""

import socket
import time

import azcam
from azcam.server.tempcons.tempcon import TempCon

"""
Example commands:
    tempcon.server.command("input A:units C")
    tempcon.server.command("input B:units C")
    tempcon.server.command("input C:units C")
    tempcon.server.command("input A:isenix 2")  # LS DT-670
    tempcon.server.command("input B:isenix 2")  # LS DT-670
    tempcon.server.command("input C:isenix 2")  # LS DT-670
    tempcon.server.command("loop 1:type pid")  # PID control
    tempcon.server.command("loop 1:range mid")  # range (0.5W,5W,50W)
    tempcon.server.command("loop 1:maxpwr 100")  # max power on this range
"""


class TempConCryoCon(TempCon):
    """
    Cryogenic Control Systems Model 24 temperature control class.
    """

    def __init__(self, *args):

        super().__init__(*args)

        self.host = ""
        self.port = 5000

        self.enabled = 1
        self.initialized = 0

        self.init_commands = []

    def initialize(self):
        """
        Initialize CryoConM24TemperatureControl temperature controller.
        """

        if not self.enabled:
            azcam.AzcamWarning("Tempcon is not enabled")
            return

        if self.initialized:
            return

        # recreate in case host/port changed
        self.server = TempconServerInterface(self.host, self.port, self.name)

        # query ID
        try:
            self.server.command("*IDN?;")
        except socket.timeout:
            azcam.AzcamWarning("Could not query temperature controller")
            return

        # set PID mode
        self.server.command("LOOP 1:TYPE PID")

        # set PID mode
        self.server.command("LOOP 2:TYPE OFF")

        # set control temp
        self.set_control_temperature(self.control_temperature)

        # run custom initialization commands
        for cmd in self.init_commands:
            self.server.command(cmd)

        self.initialized = 1

        return

    def set_control_temperature(
        self, temperature: float = None, temperature_id: int = 0
    ):
        """
        Set control temperature in Celsius.

        :param temperature: temperature to set
        :param temperature_id: temperature ID number
          * 0 is TempA
          * 1 is TempB
        """

        if temperature is None:
            temperature = self.control_temperature
        else:
            self.control_temperature = float(temperature)

        if temperature_id == 0:
            # set loop 1
            self.server.command("Loop 1:SETPT %s;" % str(temperature))
            self.server.command("LOOP 1:TYPE PID")
        elif temperature_id == 1:
            # set loop 2
            self.server.command("Loop 2:SETPT %s;" % str(temperature))
            self.server.command("LOOP 2:TYPE PID")

        # turn on control loop
        self.server.command("CONTrol;")

        return

    def get_temperature(self, temperature_id: int = 0):
        """
        Reads temperatures from the tempcon controller.

        :param temperature_id: temperature ID number
        """

        if not self.enabled:
            # azcam.AzcamWarning("Tempcon not enabled")
            return -999.9

        if not self.initialized:
            # azcam.AzcamWarning("Tempcon not initialized")
            return -999.9

        if temperature_id == 0:
            tempstr = "INPUT? A;"
        elif temperature_id == 1:
            tempstr = "INPUT? B;"
        elif temperature_id == 2:
            tempstr = "INPUT? C;"
        elif temperature_id == 3:
            tempstr = "INPUT? D;"
        else:
            return "ERROR bad TemperatureID in ReadTemperature"

        reply = self.server.command(tempstr)
        try:
            temp = float(reply)
        except ValueError:
            temp = self.bad_temp_value
            # raise azcam.AzcamError("Could not convert temperature reading to a number")

        temp = self.apply_corrections(temp, temperature_id)

        return temp

    def get_temperatures(self):
        """
        Return temperatures in degrees C from temperature controller.
        CAMTEMP, DEWTEMP are first.
        """

        temp0 = self.get_temperature(0)
        temp1 = self.get_temperature(1)
        temp2 = self.get_temperature(2)
        temp3 = self.get_temperature(3)

        return [temp0, temp1, temp2, temp3]


# *** temperature control server interface ***
class TempconServerInterface(object):
    """
    Communicates with the CryoCon Model 24 builtin temperature server using a socket.
    """

    def __init__(self, host: str, port: int, name: str):

        self.host = host
        self.port = port
        self.connected = 0
        self.cmdstring = ""
        self.busy = 0
        self.timeout = 5.0

    def open(self):
        """
        Open a socket connection to an server.
        Creates the socket and makes a connection.
        """

        if not self.connected:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.socket.settimeout(self.timeout)

        return

    def close(self):
        """
        Close an open socket connection to an server.
        """

        self.socket.close()
        self.connected = 0
        self.busy = 0

        return

    def command(self, command: str):
        """
        Communicate with the remote server.
        Sends and command and returns reply.
        Returns the exact reply from the server.

        :param command: command string to send.
        """

        # multiple commands may come so wait
        loop = 0
        while self.busy:
            time.sleep(0.1)
            loop += 1
            if loop > 100:
                raise azcam.AzcamError("Tempcon is BUSY")

        self.busy = 1

        try:
            self.open()
            self.socket.sendto(
                str.encode(command), (self.host, self.port + 1)
            )  # UDP is TCP port + 1
            reply = self.socket.recvfrom(4000)
            self.close()
            reply = reply[0].decode()  # UDP return string is first element
            reply = reply[:-2]  # remove CR/LF
        except Exception:
            raise
        finally:
            self.busy = 0

        return reply
