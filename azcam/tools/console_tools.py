"""
*azcam.tools.console_tools* contains the `ConsoleTools` base tool class.
"""

from typing import Any, Optional

import azcam
import azcam.sockets


class ConsoleTools(object):
    """
    Common methods included in most console tools.
    """

    def __init__(self, name: str) -> None:
        """
        Args:
            name (str): name of this tool.
        """

        self.objname = name
        azcam.db.tools[self.objname] = self

        #: verbosity for debug, > 0 is more verbose
        self.verbosity = 0

    def initialize(self) -> None:
        """
        Initialize this tool.
        """

        return azcam.db.tools["server"].command(f"{self.objname}.initialize")

    def reset(self) -> None:
        """
        Reset this tool.
        """

        return azcam.db.tools["server"].command(f"{self.objname}.reset")

    def update_header(self):
        """
        Update the header of a tool.
        This command usually reads hardware to get the lastest keyword values.
        """

        return azcam.db.tools["server"].command(f"{self.objname}.update_header")

    def read_header(self):
        """
        Returns the current header.

        Returns:
            list of header lines: [Header[]]: Each element Header[i] contains the sublist (keyword, value, comment, and type).
        """

        return azcam.db.tools["server"].command(f"{self.objname}.read_header")

    def set_keyword(
        self,
        keyword: str,
        value: str,
        comment: str = "none",
        typestring: str = "none",
    ) -> Optional[str]:
        """
        Set a keyword value, comment, and type.
        Args:
            keyword: keyword
            value: value of keyword
            comment: comment string
            typestring: one of 'str', 'int', 'float,  'none'
        """

        if type(value) == str and " " in value:
            value = f'"{value}"'

        if " " in comment:
            comment = f'"{comment}"'

        s = f"{self.objname}.set_keyword {keyword} {value} {comment} {typestring}"

        return azcam.db.tools["server"].command(s)

    def get_keyword(self, keyword: str) -> str:
        """
        Return a keyword value, its comment string, and type.
        Comment always returned in double quotes, even if empty.

        Args:
            keyword: name of keyword
        Returns:
            list of [keyword, comment, type]
        """

        return azcam.db.tools["server"].command(f"{self.objname}.get_keyword {keyword}")

    def delete_keyword(self, keyword: str) -> Optional[str]:
        """
        Delete a keyword from a header.

        Args:
            keyword: name of keyword
        """

        return azcam.db.tools["server"].command(f"{self.objname}.delete_keyword {keyword}")

    def get_keywords(self) -> list:
        """
        Return a list of all keyword names.

        Returns:
            list of all keywords
        """

        return azcam.db.tools["server"].command(f"{self.objname}.get_keywords")

    def get_string(self) -> str:
        """
        Returns the entire header as a formatted string.

        Returns:
            single formatted string of keywords, values, and comments.
        """

        lines = ""

        header = self.read_header()
        for telem in header:
            line = telem[0] + " " + str(telem[1]) + " " + str(telem[2]) + "\n"
            lines += line

        return lines


class ServerConnection(object):
    """
    Server connection tool for consoles.
    Usually implemented as the "server" tool.
    """

    def __init__(self) -> None:
        self.remserver = azcam.sockets.SocketInterface()
        self.connected = False
        azcam.db.tools["server"] = self

    def connect(self, host="localhost", port=2402):
        """
        Connect to azcamserver.
        """

        self.host = host
        self.port = port

        self.remserver.host = host
        self.remserver.port = port

        if self.remserver.open():
            connected = True
            self.remserver.command("register console")
        else:
            connected = False

        self.connected = connected

        return connected

    def command(self, command):
        """
        Send a command to a server process using the 'server' object in the database.
        This command traps all errors and returns exceptions and as error string.

        Returns None or a string.
        """

        # get tokenized reply - check for comm error
        try:
            reply = self.remserver.command(command)
        except azcam.AzcamError as e:
            if e.error_code == 2:
                raise
                # raise azcam.AzcamError("could not connect to server")
            else:
                raise

        if command in ["exposure.get_status"]:
            return reply[0][3:]

        # status for socket communications is OK or ERROR
        if reply[0] == "ERROR":
            # raise azcam.AzcamError(f"command error: {' '.join(reply[1:])}")
            raise azcam.AzcamError(f"command error: {reply}")
        elif reply[0] == "OK":
            if len(reply) == 1:
                return None
            elif len(reply) == 2:
                return reply[1]
            else:
                return reply[1:]
        else:
            raise azcam.AzcamError(f"invalid server response: { ' '.join(reply)}")

        return  # can't get here


def create_console_tools() -> None:
    """
    Creates the console tools.
    """

    from azcam.tools.controller import ControllerConsole
    from azcam.tools.exposure import ExposureConsole
    from azcam.tools.instrument import InstrumentConsole
    from azcam.tools.telescope import TelescopeConsole
    from azcam.tools.tempcon import TempconConsole
    from azcam.tools.observe.observe import ObserveConsole

    server = ServerConnection()
    exposure = ExposureConsole()
    controller = ControllerConsole()
    instrument = InstrumentConsole()
    tempcon = TempconConsole()
    telescope = TelescopeConsole()
    observe = ObserveConsole()

    return
