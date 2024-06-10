"""
Contains the base TempConCryoCon24 class.
"""

import socket
import threading

import azcam
import azcam.exceptions
from azcam.tools.tempcon import TempCon

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


class TempConCryoCon24(TempCon):
    """
    Cryogenic Control Systems Model 24 temperature control class.
    """

    def __init__(self, tool_id="tempcon", description=None):
        super().__init__(tool_id, description)

        self.host = ""
        self.port = 5000

        self.temperature_ids = [0, 1]  # camtemp, dewtemp

        self.init_commands = []

    def define_keywords(self):
        """
        Defines and resets instrument keywords.
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

        # recreate in case host/port changed
        self.server = TempconServerInterface(self.host, self.port, self.description)

        # query ID
        try:
            self.server.command("*IDN?;")
        except socket.timeout as e:
            azcam.exceptions.warning("Could not query temperature controller: {e}")
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

        self.is_initialized = 1

        return

    def set_control_temperature(
        self, temperature: float = None, temperature_id: int = 0
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

        if temperature_id == 0:
            # set loop 1
            self.server.command(f"Loop 1:SETPT {temperature};")
            self.server.command(f"LOOP 1:TYPE PID")
        elif temperature_id == 1:
            # set loop 2
            self.server.command(f"Loop 2:SETPT {temperature};")
            self.server.command(f"LOOP 2:TYPE PID")

        # turn on control loop
        self.server.command("CONTrol;")

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
            tempstr = "INPUT? A;"
        elif temperature_id == 1:
            tempstr = "INPUT? B;"
        elif temperature_id == 2:
            tempstr = "INPUT? C;"
        elif temperature_id == 3:
            tempstr = "INPUT? D;"
        else:
            raise azcam.exceptions.AzcamError("bad temperature_id in get_temperature")

        reply = self.server.command(tempstr)
        try:
            temp = float(reply)
        except ValueError:
            temp = self.bad_temp_value

        temp = self.apply_corrections(temp, temperature_id)

        return temp


class TempconServerInterface(object):
    """
    Communicates with the CryoCon Model 24 builtin temperature server using a socket.
    """

    def __init__(self, host: str, port: int, name: str):
        self.host = host
        self.port = port
        self.connected = 0
        self.cmdstring = ""
        self.timeout = 5.0

        self.lock = threading.Lock()

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

        return

    def command(self, command: str):
        """
        Communicate with the remote server.
        Sends and command and returns reply.
        Returns the exact reply from the server.
        Args:
            command: command string to send.
        Returns:
            reply: commands reply
        """

        with self.lock:
            self.open()
            self.socket.sendto(
                str.encode(command), (self.host, self.port + 1)
            )  # UDP is TCP port + 1
            reply = self.socket.recvfrom(4000)
            self.close()
            reply = reply[0].decode()  # UDP return string is first element
            reply = reply[:-2]  # remove CR/LF

        return reply
