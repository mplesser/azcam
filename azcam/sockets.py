"""
*azcam.sockets* contains azcam's `SocketInterface` class used by many interfaces.
"""

import shlex
import socket
import time
import threading

import azcam
import azcam.exceptions


class SocketInterface(object):
    """
    The azcam socket server interface.
    """

    def __init__(self, host: str = "", port: int = 0) -> None:
        """
        Create socket connection instance.

        Args:
            host: host name of remote computer.
            port: port number of server on remote computer.
        """

        #: host name or IP address of remote server
        self.host: str = host
        #: port number of remote server
        self.port: int = port

        if host != "":
            self.host = host
        if port != 0:
            self.port = port

        #: true when connection is active
        self.connected: int = 0
        #: termination string for commands
        self.terminator = "\r\n"
        #: last response from server
        self.last_response = ""
        #: last command send to server
        self.last_command = ""
        #: true to try reopening socket a reset socket when trying to connect
        self.reopen = 0
        #: connection timeout in seconds
        self.timeout = 0

        #: socket instance
        self.socket: object = None

        #: thread lock
        self.lock = threading.Lock()

    def open(self) -> bool:
        """
        Open a socket connection to the server.
        Creates the socket and makes a connection.
        Returns:
            True if socket is already open or if it is opened here.
        """

        # check if socket is already open
        if self.socket is not None:
            return True

        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 0)
        try:
            self.socket.settimeout(0.1)
            self.socket.connect((self.host, int(self.port)))
            self.connected = True
        except Exception:
            self.close()
            self.connected = False
            return False

        # check if there is a welcome message
        self.set_timeout(0.2)
        try:
            welcome = self.recv()
        except socket.timeout:
            welcome = ""
        self.set_timeout(0)  # initally no timeout

        if len(welcome) > 0:
            azcam.log(welcome)

        return True

    def close(self) -> None:
        """
        Close the socket connection to the server.
        """

        if self.socket is not None:
            try:
                self.socket.close()
            except Exception:
                pass  # never error on close
        self.socket = None
        self.connected = False

        return

    def command(self, command: str, terminator: str = "\n") -> list:
        """
        Sends a command to the server and receives a reply back.

        Args:
            command: command string to send
            terminator: termination string to append the command
        Returns:
            tokenized list of the server's reply.
        """

        with self.lock:
            if not self.open():
                raise azcam.exceptions.AzcamError(
                    "could not open connection to server", error_code=2
                )

            self.send(command, terminator)
            reply = self.recv(-1, "\n")

        self.last_response = reply

        if command not in ["exposure.get_status"]:
            reply = shlex.split(reply)
        else:
            reply = [reply.strip()]

        return reply

    def send(self, command: str, terminator: str = "\n") -> None:
        """
        Send a command string to the server.
        Args:
            command: command string to send
            terminator: termination string to append the command
        """

        self.last_command = command
        try:
            self.socket.send(str.encode(command + terminator))
        except ConnectionResetError:
            if self.reopen:
                self.close()
                self.open()
                self.socket.send(str.encode(command + terminator))
            else:
                raise

        return

    def recv(self, length: int = -1, terminator: str = "\n") -> str:
        """
        Receives a reply from a server.
        Terminates socket read when length bytes are received or when the terminator is received.
        Args:
            length: number of bytes to receive. -1 means receive through terminator.
            terminator: terminator string.
        """

        # receive Length bytes
        if length != -1:
            reply = self.socket.recv(length).decode()
            return reply

        # read socket until Terminator found
        msg = ""
        loop = 0
        while True:
            try:
                msg += self.socket.recv(1024).decode()
            except ConnectionAbortedError:
                raise azcam.exceptions.AzcamError("Connection aborted")
            if len(msg) == 0:
                pass
            elif msg[-1] == terminator:  # found terminator at end
                break
            # check for infinite loop
            loop += 1
            if loop > 1024:
                raise azcam.exceptions.AzcamError("Socket recv loop max retry exceeded")
            time.sleep(0.005)

        if len(msg) < 2:
            raise azcam.exceptions.AzcamError("Invalid command response received")
        if msg[-2] == "r":
            reply = msg[:-2]  # remove CR/LF
        else:
            reply = msg[:-1]  # remove LF

        return reply

    def set_timeout(self, timeout: float = -1.0) -> None:
        """
        Set the receive timeout for socket connection.
        Args:
            timeout: timeout value in seconds. <0 means use current value, =0 means no timeout.
        """

        if timeout < 0:
            pass
        elif timeout == 0:
            self.timeout = None
        else:
            self.timeout = float(timeout)

        self.socket.settimeout(self.timeout)

        return

    def test(self) -> str:
        """
        Sends and receives a test message over the socket connection.
        """

        message = "this is a test message string"

        return self.command(f'Echo "{message}"')
