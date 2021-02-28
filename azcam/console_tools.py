"""
Remote command interface for a console tools.
This is the interface to azcamserver using the
socket-based command server.
"""

from typing import Optional

import azcam
import azcam.sockets


class ConsoleTools(object):
    """
    Common methods used by all console tools.
    """

    def __init__(self, name) -> None:
        self.objname = name
        azcam.db.cli_objects[self.objname] = self
        setattr(azcam.db, self.objname, self)

    def initialize(self) -> None:
        """
        Initialize tool.
        """

        return azcam.db.server.rcommand(f"{self.objname}.initialize")

    def reset(self) -> None:
        """
        Reset tool.
        """

        return azcam.db.server.rcommand(f"{self.objname}.reset")

    def get(self, name):
        """
        Returns an object attribute by name.
        Returns None if not available.
        """

        reply = azcam.db.server.rcommand(f"{self.objname}.get {name}")

        return reply

    def update_header(self):
        """
        Update the header of an object.
        This command usually reads hardware to get the lastest keyword values.
        """

        return azcam.db.server.rcommand(f"{self.objname}.update_header")

    def read_header(self):
        """
        Returns the current header.
        Returns:
            list of header lines: [Header[]]: Each element Header[i] contains the sublist (keyword, value, comment, and type).
        """

        return azcam.db.server.rcommand(f"{self.objname}.read_header")

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

        return azcam.db.server.rcommand(s)

    def get_keyword(self, keyword: str) -> str:
        """
        Return a keyword value, its comment string, and type.
        Comment always returned in double quotes, even if empty.
        Args:
            keyword: name of keyword
        Returns:
            list of [keyword, comment, type]
        """

        return azcam.db.server.rcommand(f"{self.objname}.get_keyword {keyword}")

    def delete_keyword(self, keyword: str) -> Optional[str]:
        """
        Delete a keyword from a header.
        The keyword is set in the controller header by default.

        :param keyword: keyword name
        """

        return azcam.db.server.rcommand(f"{self.objname}.delete_keyword {keyword}")

    def get_all_keywords(self):
        """
        Return a list of all keyword names.
        Returns:
            keywords: list of all keywords
        """

        reply = azcam.db.server.rcommand(f"{self.objname}.get_all_keywords")

        return reply

    def get_string(self):
        """
        Returns the entire header as a single formatted string.
        """

        lines = ""

        header = self.read_header()
        for telem in header:
            line = telem[0] + " " + str(telem[1]) + " " + str(telem[2]) + "\n"
            lines += line

        return lines


class ServerConnection(azcam.sockets.SocketInterface):
    """
    Server connection class for console tools to azcamserver.
    """

    def __init__(self) -> None:

        azcam.sockets.SocketInterface.__init__(self)
        self.connected = False
        azcam.db.cli_objects["server"] = self
        setattr(azcam.db, "server", self)

    def connect(self, host="localhost", port=2402):
        """
        Connect to azcamserver.
        """

        self.host = host
        self.port = port

        if self.open():
            connected = True
            self.rcommand("register console")
        else:
            connected = False

        self.connected = connected

        return connected

    def rcommand(self, command):
        """
        Send a command to a server process using the 'server' object in the database.
        This command traps all errors and returns exceptions and as error string.

        Returns None or a string.
        """

        # get tokenized reply - check for comm error
        try:
            reply = self.command(command)
        except azcam.AzcamError as e:
            if e.error_code == 2:
                raise
                # raise azcam.AzcamError("could not connect to server")
            else:
                raise

        # status for socket communications is OK or ERROR
        if reply[0] == "ERROR":
            azcam.log(reply[1])
            raise azcam.AzcamError(f"rcommand error: {reply[1]}")
        elif reply[0] == "OK":
            if len(reply) == 1:
                return None
            elif len(reply) == 2:
                return reply[1]
            else:
                return reply[1:]
        else:
            raise azcam.AzcamError(f"invalid server response: {reply}")

        return  # can't get here


def load(tools="all"):
    """Load console tools

    Args:
        tools ([type]): [description]
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
