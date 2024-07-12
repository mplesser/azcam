"""
Contains the CameraServerInterface class for Magelllan controllers.
"""

import azcam
import azcam.exceptions
import azcam.sockets


class CameraServerInterface(object):
    """
    The azcam controller server interface class for Magellan controllers.
    """

    def __init__(self, host: str = "", port: int = 0) -> bool:

        self.host = ""
        self.port = 0

        self.socketserver = azcam.sockets.SocketInterface(host, port)

        self.demo_mode = 0

    def set_server(self, host: str, port: int = 2405) -> None:
        """
        Set host and port of controller server.
        """

        self.host = host
        self.port = port

        self.socketserver.host = host
        self.socketserver.port = port

        return

    def command(self, command: str, terminator: str = "\n"):
        """
        Command method for controller server.
        """

        if self.demo_mode:
            reply = ["DEMO", 0]
        else:
            try:
                reply = self.socketserver.command(command, terminator)
                return reply
            except Exception as e:
                if e.error_code == 2:
                    raise azcam.exceptions.AzcamError("Could not connect to camserver")

    def test(self):
        """
        Echo a message string from controller server.
        """

        return self.echo()

    def echo(self, Message="This is a ControllerServer test message."):
        """
        Echo a message string from controller server.
        """

        return self.command('Echo "' + str(Message) + '"')

    def upload_file(self, fbuffer):
        """
        Sends a file as a binary buffer to the ControllerServer to be written to its file system.
        Returns the name of the file on the ControllerServer file system.
        """

        # send size
        size = len(fbuffer)
        self.command("cmd UploadFile " + str(size))

        # send file buffer
        if not self.demo_mode:
            self.socketserver.send(fbuffer)
            reply = self.socketserver.recv()
            csfilename = reply.split(" ")[1]
        else:
            csfilename = ""

        return csfilename.strip()

    def load_file(self, board, filename):
        """
        Send a a DSP code file to the controller server.
        """

        try:
            reply = self.command("LoadFile " + str(board) + " " + filename)
        finally:
            self.delete_file(filename)  # try and delete file even if error

        return

    def delete_file(self, filename):
        """
        Delete a file which wa uploaded to the controller server.
        """

        return self.command("cmd DeleteFile " + filename)

    def set(self, Parameter, value):
        """
        Set a parameter in the controller server.
        """

        return self.command("Set " + Parameter + " " + str(value))

    def get(self, Parameter):
        """
        Return a paramater from the controller server, as a string.
        """

        if self.demo_mode:
            if Parameter == "ExposureTimeRemaining":
                parval = azcam.db.tools["exposure"].exposure_time * 1000
                reply = ["OK", parval]
            else:
                reply = ["OK", 0]
        else:
            reply = self.command("Get " + Parameter)

        return reply

    def close_server(self):
        """
        Closes the ControllerServer.
        """

        return self.command("CloseServer")

    def restart_server(self):
        """
        Restarts the ControllerServer.
        """

        self.command("RestartServer")
        if not self.demo_mode:
            self.socketserver.close()  # close socket as it is reset in CS

        return

    def reset_server(self):
        """
        Resets the ControllerServer.
        """

        self.command("ResetServer")
        if not self.demo_mode:
            self.socketserver.close()  # close socket as it is reset in CS

        return
