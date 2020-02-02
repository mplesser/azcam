import os
import socket

import azcam
import time


class SendImage(object):
    """
    Class to send image to a remote image server.
    """

    def __init__(self):

        self.timeout = 10.0

    def azcam_imageserver(self, filename, remote_imageserver_host, remote_imageserver_port):
        """
        Send image to azcam image server.
        """

        # open image file on disk
        dfile = open(filename, "rb")

        # get file size
        lSize = os.path.getsize(filename)

        # read the file into the buffer
        buff = dfile.read()

        # close the file
        dfile.close()

        # open socket to DataServer
        dataserver_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        dataserver_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 0)
        dataserver_socket.settimeout(self.timeout)
        dataserver_socket.connect((remote_imageserver_host, int(remote_imageserver_port)))

        if self.remote_imageserver_filename != "":
            remotefile = self.remote_imageserver_filename
        else:
            remotefile = filename
        if self.overwrite or self.test_image:
            remotefile = "!" + remotefile

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
            raise azcam.AzcamError("Could not send image header to remote image server")

        # get 16 char ASCII header return status from image server
        # reply = dataserver_socket.recv(16)
        # if len(reply) != 16:
        #    raise azcam.AzcamError("Did not receive header return status from remote image server")
        # retstat=int(reply[:1])
        # retstat=int(reply)
        retstat = 0

        # check header return status codes
        if retstat != 0:
            if retstat == -1:
                raise azcam.AzcamError("Bad reply from remote image server")
            elif retstat == -2:
                raise azcam.AzcamError("Remote ImageServer not create image filename")
            elif retstat == -3:  #
                raise azcam.AzcamError("Folder does not exist on remote machine")
            else:
                raise azcam.AzcamError("Unknown error from remote image server")

        # send file data
        reply = dataserver_socket.send(buff)

        if reply != len(buff):
            raise azcam.AzcamError("Did not send entire image file data to remote image server")

        # get 16 char ASCII final return status from image server
        reply = dataserver_socket.recv(16).decode()

        # if len(reply) != 2:
        #    raise AzcamError("did not receive entire return status from remote image server")

        retstat = int(reply[:1])

        # check final return status error codes
        if retstat != 0:
            raise azcam.AzcamError("Bad final return status from remote image server")

        # close socket
        # time.sleep()
        dataserver_socket.close()

        return

    def dataserver(self, filename, remote_imageserver_host, remote_imageserver_port):
        """
        Send image to dataserver.
        """

        ImageSendBufferSize = 1024 * 32

        # open image file on disk
        dfile = open(filename, "rb")

        # get file size
        lSize = os.path.getsize(filename)

        # read the file into the buffer
        buff = dfile.read()

        # close the file
        dfile.close()

        # open socket to DataServer
        dataserver_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        dataserver_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 0)
        dataserver_socket.settimeout(self.timeout)
        dataserver_socket.connect((remote_imageserver_host, int(remote_imageserver_port)))

        if self.remote_imageserver_filename != "":
            remotefile = self.remote_imageserver_filename
            if self.overwrite or self.test_image:
                remotefile = "!" + remotefile
        else:
            remotefile = filename
            if self.overwrite or self.test_image:
                remotefile = "!" + remotefile

        azcam.log("Sending image to %s as %s" % (self.remote_imageserver_host, remotefile))

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
            raise azcam.AzcamError("Could not send image header to remote DataServer")

        # get 16 char ASCII header return status from image server
        # reply = dataserver_socket.recv(16)
        # if len(reply) != 16:
        #    raise azcam.AzcamError("Did not receive header return status from remote image server")
        # retstat=int(reply[:1])
        # retstat=int(reply)
        retstat = 0

        # check header return status codes (updated 14jul11)
        if retstat != 0:
            if retstat == 1:  # overwrite existing name wihtout flag
                raise azcam.AzcamError("Remote image server could not create image filename")
            elif retstat == 2:  # not enough space
                raise azcam.AzcamError("Remote image server does not have enough disk space")
            elif retstat == 3:  #
                raise azcam.AzcamError("Remote image server reports folder does not exist")
            else:
                raise azcam.AzcamError("Unknown error from remote image server")

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
                raise azcam.AzcamError(
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
            raise azcam.AzcamError("Did not send image file data to remote image server: %s" % message)

        if reply!=len(buff):
            raise azcam.AzcamError("Did not send entire image file data to remote image server")
        """

        # get 16 char ASCII final return status from image server
        """
        try:
            reply = dataserver_socket.recv(16)
        except:
            raise azcam.AzcamError("Did not receive return status from remote image server")

        if len(reply) != 2:
            raise azcam.AzcamError("Did not receive entire return status from remote image server")
        retstat=int(reply[:1])

        # check final return status error codes
        if retstat != 0:
            raise azcam.AzcamError("Bad final return status from remote image server")
        """

        # close socket
        time.sleep(1)  # 3
        dataserver_socket.close()

        return

    def lbtguider(self, filename, GuideHost, GuidePort):
        """
        Send image to an LBT guider image server.
        """

        # open image file on disk
        gfile = open(filename, "rb")
        if not gfile:
            return ["ERROR", "Could not open local image file"]

        # get file size
        lSize = os.path.getsize(filename)

        # read the file into the buffer and close
        buff = gfile.read()
        gfile.close()

        # open socket to LBT image server
        GuideSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        GuideSocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 0)

        try:
            GuideSocket.connect((GuideHost, GuidePort))
        except Exception as message:
            GuideSocket.close()
            return ["ERROR", "LBT guider ImageServer not opened: %s" % message]

        # send filesize in bytes, \r\n terminated
        sockBuf = "%d\r\n" % lSize
        if GuideSocket.send(str.encode(sockBuf)) != len(sockBuf):
            return ["ERROR", "GuideSocket send error"]

        # send file data
        if GuideSocket.send(str.encode(buff)) != len(buff):
            return ["ERROR", "Could not send all image file data to LBT ImageServer"]

        # close socket
        GuideSocket.close()

        return
