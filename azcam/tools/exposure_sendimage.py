import os
import socket
import time

import azcam
import azcam.exceptions
from azcam.tools.tools import Tools


class SendImage(object):
    """
    Class to send image to a remote image server.
    """

    def __init__(self):

        self.remote_imageserver_host = ""
        self.remote_imageserver_port = 0
        self.remote_imageserver_type = ""
        self.remote_imageserver_filename = ""

        self.timeout = 10.0
        self.overwrite = 0
        self.test_image = 0
        self.display_image = 0
        self.filetype = 0
        self.size_x = 0
        self.size_y = 0

        # new - imageserver call method, may be overridden
        self.imageserver_send = self.dataserver

    def set_remote_imageserver(
        self,
        remote_imageserver_host="",
        remote_imageserver_port=6543,
        remote_imageserver_type="dataserver",
        remote_imageserver_filename="image",
    ):
        """
        Set parameters so image files are sent to a remote image server.
        """

        self.remote_imageserver_host = remote_imageserver_host
        self.remote_imageserver_port = remote_imageserver_port
        self.remote_imageserver_type = remote_imageserver_type
        self.remote_imageserver_filename = remote_imageserver_filename

        if self.remote_imageserver_type == "dataserver":
            self.imageserver_send = self.dataserver
        elif self.remote_imageserver_type == "azcam":
            self.imageserver_send = self.azcam_imageserver

        return

    def get_remote_imageserver(self):
        """
        Get remote image server parameters.
        Returns:
            remote_imageserver_host:
            remote_imageserver_port:
            remote_imageserver_type:
            remote_imageserver_filename:
        """

        return [
            self.remote_imageserver_host,
            self.remote_imageserver_port,
            self.remote_imageserver_type,
            self.remote_imageserver_filename,
        ]

    def send_image(self, localfile=None, remotefile=None):
        """
        Send image to remote image server.
        """

        if localfile is None:
            localfile = f"{azcam.db.tools['exposure'].temp_image_file}.{azcam.db.tools['exposure'].get_extname(self.filetype)}"

        if remotefile is None:
            remotefile = f"{self.remote_imageserver_filename}.{azcam.db.tools['exposure'].get_extname(self.filetype)}"

        self.overwrite = azcam.db.tools["exposure"].overwrite
        self.test_image = azcam.db.tools["exposure"].test_image
        self.display_image = azcam.db.tools["exposure"].display_image
        self.filetype = azcam.db.tools["exposure"].filetype
        self.size_x = azcam.db.tools["exposure"].size_x
        self.size_y = azcam.db.tools["exposure"].size_y

        self.imageserver_send(localfile, remotefile)

        # if self.remote_imageserver_type == "azcam":
        #     self.azcam_imageserver(localfile, remotefile)
        # elif self.remote_imageserver_type == "lbtguider":
        #     self.lbtguider_imageserver(localfile, remotefile)
        # elif self.remote_imageserver_type == "dataserver":
        #     self.dataserver(localfile, remotefile)
        # elif self.remote_imageserver_type == "ccdacq":
        #     self.ccdacq_imageserver(localfile, remotefile)
        # else:
        #     raise azcam.exceptions.AzcamError("Unknown remote image server type")

    def azcam_imageserver(self, localfile, remotefile=None):
        """
        Send image to azcam image server.
        """

        if remotefile is None:
            remotefile = self.remote_imageserver_filename

        # open image file on disk
        with open(localfile, "rb") as dfile:
            lSize = os.path.getsize(localfile)
            buff = dfile.read()

        # open socket to DataServer
        dataserver_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        dataserver_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 0)
        dataserver_socket.settimeout(self.timeout)
        dataserver_socket.connect(
            (self.remote_imageserver_host, int(self.remote_imageserver_port))
        )

        if self.overwrite or self.test_image:
            remotefile = "!" + remotefile

        print(remotefile)

        # send header
        # file types: 0 FITS, 1 MEF, 2 binary
        s1 = "%16d %s %d %d %d %d" % (
            lSize,
            remotefile,
            self.filetype,
            self.size_x,
            self.size_y,
            self.display_image,
        )
        s1 = "%-256s" % s1
        status = dataserver_socket.send(str.encode(s1))
        if status != 256:
            raise azcam.exceptions.AzcamError(
                "Could not send image header to remote image server"
            )

        # get 16 char ASCII header return status from image server
        # reply = dataserver_socket.recv(16)
        # if len(reply) != 16:
        #    raise azcam.exceptions.AzcamError("Did not receive header return status from remote image server")
        # retstat=int(reply[:1])
        # retstat=int(reply)
        retstat = 0

        # check header return status codes
        if retstat != 0:
            if retstat == -1:
                raise azcam.exceptions.AzcamError("Bad reply from remote image server")
            elif retstat == -2:
                raise azcam.exceptions.AzcamError(
                    "Remote ImageServer not create image filename"
                )
            elif retstat == -3:  #
                raise azcam.exceptions.AzcamError(
                    "Folder does not exist on remote machine"
                )
            else:
                raise azcam.exceptions.AzcamError(
                    "Unknown error from remote image server"
                )

        # send file data
        reply = dataserver_socket.send(buff)

        if reply != len(buff):
            raise azcam.exceptions.AzcamError(
                "Did not send entire image file data to remote image server"
            )

        # get 16 char ASCII final return status from image server
        reply = dataserver_socket.recv(16).decode()

        # if len(reply) != 2:
        #    raise AzcamError("did not receive entire return status from remote image server")

        retstat = int(reply[:1])

        # check final return status error codes
        if retstat != 0:
            raise azcam.exceptions.AzcamError(
                "Bad final return status from remote image server"
            )

        # close socket
        # time.sleep()
        dataserver_socket.close()

        return

    def dataserver(self, localfile, remotefile):
        """
        Send image to dataserver.
        """

        ImageSendBufferSize = 1024 * 32

        # open image file on disk
        with open(localfile, "rb") as dfile:
            lSize = os.path.getsize(localfile)
            buff = dfile.read()

        # open socket to DataServer
        dataserver_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        dataserver_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 0)

        print("timeout", self.timeout)

        connected = 0
        for i in range(10):
            print("attempting to connect...")
            try:
                dataserver_socket.settimeout(self.timeout)
                dataserver_socket.connect(
                    (self.remote_imageserver_host, int(self.remote_imageserver_port))
                )
                connected = 1
            except Exception as e:
                azcam.log(e)
                # raise azcam.exceptions.AzcamError(
                #     f"Could not connect to imageserver {self.remote_imageserver_host}:{int(self.remote_imageserver_port)}"
                # )
                time.sleep(1.0)
        if not connected:
            raise azcam.exceptions.AzcamError(
                f"Could not connect to imageserver {self.remote_imageserver_host}:{int(self.remote_imageserver_port)}"
            )

        if self.overwrite or self.test_image:
            remotefile = "!" + remotefile

        azcam.log(f"Sending image to {self.remote_imageserver_host} as {remotefile}")

        # send header
        # file types: 0 FITS, 1 MEF, 2 binary
        s1 = "%16d %s %d %d %d %d" % (
            lSize,
            remotefile,
            self.filetype,
            self.size_x,
            self.size_y,
            self.display_image,
        )
        s1 = "%-256s" % s1
        status = dataserver_socket.send(str.encode(s1))
        if status != 256:
            raise azcam.exceptions.AzcamError(
                "Could not send image header to remote DataServer"
            )

        # get 16 char ASCII header return status from image server
        # reply = dataserver_socket.recv(16)
        # if len(reply) != 16:
        #    raise azcam.exceptions.AzcamError("Did not receive header return status from remote image server")
        # retstat=int(reply[:1])
        # retstat=int(reply)
        retstat = 0

        # check header return status codes (updated 14jul11)
        if retstat != 0:
            if retstat == 1:  # overwrite existing name wihtout flag
                raise azcam.exceptions.AzcamError(
                    "Remote image server could not create image filename"
                )
            elif retstat == 2:  # not enough space
                raise azcam.exceptions.AzcamError(
                    "Remote image server does not have enough disk space"
                )
            elif retstat == 3:  #
                raise azcam.exceptions.AzcamError(
                    "Remote image server reports folder does not exist"
                )
            else:
                raise azcam.exceptions.AzcamError(
                    "Unknown error from remote image server"
                )

        # send file data, new 10Sep13
        numchunks = int(lSize / ImageSendBufferSize)
        if lSize - (numchunks * ImageSendBufferSize) != 0:
            remainder = lSize - (numchunks * ImageSendBufferSize)
        else:
            remainder = 0

        if numchunks == 0:
            size = remainder
        else:
            size = ImageSendBufferSize

        end = 0
        for _ in range(numchunks):
            start = end
            end = start + size
            try:
                # dataserver_socket.send(str.encode(buff[start:end]))
                dataserver_socket.send(buff[start:end])
            except Exception as message:
                raise azcam.exceptions.AzcamError(
                    f"Did not send image file data to remote image server: {message}"
                )
        if remainder > 0:
            # dataserver_socket.send(str.encode(buff[end:]))
            dataserver_socket.send(buff[end:])

        """
        # send file data
        try:
            reply=dataserver_socket.send(str.encode(buff))
        except Exception as message:
            raise azcam.exceptions.AzcamError("Did not send image file data to remote image server: %s" % message)

        if reply!=len(buff):
            raise azcam.exceptions.AzcamError("Did not send entire image file data to remote image server")
        """

        # get 16 char ASCII final return status from image server
        """
        try:
            reply = dataserver_socket.recv(16)
        except:
            raise azcam.exceptions.AzcamError("Did not receive return status from remote image server")

        if len(reply) != 2:
            raise azcam.exceptions.AzcamError("Did not receive entire return status from remote image server")
        retstat=int(reply[:1])

        # check final return status error codes
        if retstat != 0:
            raise azcam.exceptions.AzcamError("Bad final return status from remote image server")
        """

        # close socket
        time.sleep(1)  # 3
        dataserver_socket.close()

        return
