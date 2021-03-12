"""
Remote command interface for a console tools.
This is the interface to azcamserver using the
socket-based command server.
"""

from typing import Optional, Any

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
        azcam.db.cli_tools[self.objname] = self
        setattr(azcam.db, self.objname, self)

    def initialize(self) -> None:
        """
        Initialize this tool.
        """

        return azcam.db.server.command(f"{self.objname}.initialize")

    def reset(self) -> None:
        """
        Reset this tool.
        """

        return azcam.db.server.command(f"{self.objname}.reset")

    def get(self, name: str) -> Any:
        """
        Returns an attribute of this tool by name.

        Returns:
            attribute or None if not available
        """

        reply = azcam.db.server.command(f"{self.objname}.get {name}")

        return reply

    def update_header(self):
        """
        Update the header of a tool.
        This command usually reads hardware to get the lastest keyword values.
        """

        return azcam.db.server.command(f"{self.objname}.update_header")

    def read_header(self):
        """
        Returns the current header.

        Returns:
            list of header lines: [Header[]]: Each element Header[i] contains the sublist (keyword, value, comment, and type).
        """

        return azcam.db.server.command(f"{self.objname}.read_header")

    def set_keyword(
        self,
        keyword: str,
        value: str,
        comment: str = "no_comment",
        typestring: str = "str",
    ) -> Optional[str]:
        """
        Set a keyword value, comment, and type.
        Args:
            keyword: keyword
            value: value of keyword
            comment: comment string
            typestring: one of 'str', 'int', or 'float'
        """

        if type(value) == str:
            if " " in value:
                value = f'"{value}"'

        s = f"{self.objname}.set_keyword {keyword} {value} {comment} {typestring}"

        return azcam.db.server.command(s)

    def get_keyword(self, keyword: str) -> str:
        """
        Return a keyword value, its comment string, and type.
        Comment always returned in double quotes, even if empty.

        Args:
            keyword: name of keyword
        Returns:
            list of [keyword, comment, type]
        """

        return azcam.db.server.command(f"{self.objname}.get_keyword {keyword}")

    def delete_keyword(self, keyword: str) -> Optional[str]:
        """
        Delete a keyword from a header.

        Args:
            keyword: name of keyword
        """

        return azcam.db.server.command(f"{self.objname}.delete_keyword {keyword}")

    def get_keywords(self) -> list:
        """
        Return a list of all keyword names.

        Returns:
            list of all keywords
        """

        reply = azcam.db.server.command(f"{self.objname}.get_keywords")

        return reply

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
        azcam.db.cli_tools["server"] = self
        setattr(azcam.db, "server", self)

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

        # status for socket communications is OK or ERROR
        if reply[0] == "ERROR":
            raise azcam.AzcamError(f"command error: {' '.join(reply[1:])}")
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


def load(tools="all"):
    """
    Load console tools.

    Args:
        tools (str or list[str]): tool name or list of names
    """

    from azcam.system import SystemConsole
    from azcam.exposure import ExposureConsole
    from azcam.controller import ControllerConsole
    from azcam.instrument import InstrumentConsole
    from azcam.tempcon import TempconConsole
    from azcam.telescope import TelescopeConsole

    if tools == "all":
        server = ServerConnection()
        system = SystemConsole()
        exposure = ExposureConsole()
        controller = ControllerConsole()
        instrument = InstrumentConsole()
        tempcon = TempconConsole()
        telescope = TelescopeConsole()

    return
