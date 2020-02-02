"""
Contains the SocketInterface class.
"""

import socket
import shlex
import time
import azcam


class SocketInterface(object):
    """
    The azcam socket server interface.
    """

    def __init__(self, host: str = "", port: int = 0) -> None:
        """
        Create socket connection instance.

        :param str host: host name of remote computer.
        :param int port: port number of server on remote computer.
        """

        if host != "":
            self.host = host
        if port != 0:
            self.port = port

        self.socket = 0
        self.connected = 0
        self.terminator = "\r\n"
        self.last_response = ""
        self.last_command = ""

        #: default is no timeout
        self.timeout = 0

        self.busy = False

    def open(self):
        """
        Open a socket connection to the server.
        Creates the socket and makes a connection.
        Returns True if socket is already open or if it is opened.
        """

        # don't reopen
        if self.socket != 0:
            return True

        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 0)
        try:
            self.socket.connect((self.host, self.port))
            self.connected = 1
        except Exception:
            self.close()
            self.connected = 0
            return False

        # check if there is a welcome message
        self.set_timeout(0.5)
        try:
            welcome = self.recv()
        except socket.timeout:
            welcome = ""
        self.set_timeout(0)  # initally no timeout

        if len(welcome) > 0:
            azcam.log(welcome)

        return True

    def close(self):
        """
        Close the socket connection to the controller server.
        """

        if self.socket != 0:
            try:
                self.socket.close()
            except Exception:
                pass  # never error on close
        self.socket = 0
        self.connected = 0

        return

    def command(self, Command: str, terminator: str = "\n"):
        """
        Communicate with the controller server.
        Opens and closes the socket each time.
        Always returns reply string as a tokenized list
        """

        # try a simple queue
        i = 0
        while self.busy:
            time.sleep(0.010)
            i += 1
            if i > 1000:
                self.busy = False
                raise azcam.AzcamError("Timeout error in socket BUSY loop")
        self.busy = True

        if not self.open():
            self.busy = False
            raise azcam.AzcamError(
                "Could not open connection to server", error_code=2
            )

        try:
            self.send(Command, terminator)
            reply = self.recv(-1, "\n")
        except Exception:
            raise
        finally:
            self.busy = False

        # tokenize
        self.last_response = reply
        reply = shlex.split(reply)

        return reply

    def send(self, Command, terminator="\n"):
        """
        Send a command string to a socket controller.
        Appends the terminator.
        """

        self.last_command = Command
        self.socket.send(str.encode(Command + terminator))

        return

    def recv(self, Length=-1, terminator="\n"):
        """
        Receives a reply from a socket controller as a string.
        Terminates the socket read when Length bytes are received or when the Terminator is received.
        Length is the number of bytes to receive.  -1 means receive through Terminator character.
        terminator is the terminator character.
        """

        # receive Length bytes
        if Length != -1:
            reply = self.socket.recv(Length).decode()
            return reply

        # read socket until Terminator found
        msg = ""
        loop = 0
        while True:
            try:
                msg += self.socket.recv(1024).decode()
            except ConnectionAbortedError:
                raise azcam.AzcamError("Connection aborted")
            if msg[-1] == terminator:  # found terminator at end
                break
            # check for infinite loop
            loop += 1
            if loop > 1024:
                raise azcam.AzcamError("Socket recv loop max retry exceeded")
            time.sleep(0.005)

        if len(msg) < 2:
            raise azcam.AzcamError("Invalid command response received")
        if msg[-2] == "r":
            reply = msg[:-2]  # remove CR/LF
        else:
            reply = msg[:-1]  # remove LF

        return reply

    def set_timeout(self, timeout: float = -1):
        """
        Set the receive timeout for this socket connection.
        -1 timeout means use current value
        """

        if timeout < 0:
            pass
        elif timeout == 0:
            self.timeout = None
        else:
            self.timeout = float(timeout)

        self.socket.settimeout(self.timeout)

        return

    def test(self):
        """
        Echo a message string from controller server.
        """

        return self.echo()

    def echo(self, Message="This is a server test message."):
        """
        Echo a message string from controller server.
        """

        return self.command(f'Echo "{str(Message)}"')
