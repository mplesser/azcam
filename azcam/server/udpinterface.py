"""
UDP interface class
Allows sending UDP register request to the Azcam Monitor application
Allows sending and receiving braodcast ID request
"""

import time
import socket

import azcam


class UDPinterface(object):
    def __init__(self):

        self.resp = []
        self.wait = 1

    def GetIP(self, hostName):
        """
        Sends UDP Get ID request and looks for a hostName, then returns IP address if found.
        """

        azcam.log("Resolving " + hostName + " IP Address")

        # create a ne wsocket for receiving IDs
        udp_socket_data = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        udp_socket_data.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        udp_socket_data.setblocking(0)
        udp_socket_data.bind(("", 2401))

        # ID request
        cmd = "0\r\n"

        # create a new socket for sending register command
        udp_socket_ctrl = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        udp_socket_ctrl.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        udp_socket_ctrl.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

        # send ID request
        udp_socket_ctrl.sendto(bytes(cmd, "utf-8"), ("255.255.255.255", 2400))

        # close socket
        udp_socket_ctrl.close()

        # wait self.wait time for the responses
        start = time.time()
        loop_ok = True

        while loop_ok:

            stop = time.time()
            if stop - start > self.Wait:
                loop_ok = False

            try:
                recv = udp_socket_data.recvfrom(1024)

                # store the whole response
                self.resp.append(recv)
            except Exception:
                pass

        # close socket
        udp_socket_data.close()

        # check IDs
        cnt = len(self.resp)
        ip_address = "0.0.0.0"

        if cnt > 0:
            for indx in self.resp:
                recv = str(indx).split(" ")
                try:
                    if recv[2] == hostName:
                        ip_address = recv[4]
                except Exception:
                    pass
        else:
            azcam.log("ERROR No IDs available")

        return ip_address

    def GetIDs(self):
        """
        Sends UDP Get ID request.
        """

        self.resp = []

        # create a new socket for receiving IDs
        udp_socket_data = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        udp_socket_data.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        udp_socket_data.setblocking(0)
        udp_socket_data.bind(("", 2401))

        # ID request
        cmd = "0\r\n"

        # create a new socket for sending register command
        udp_socket_ctrl = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        udp_socket_ctrl.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        udp_socket_ctrl.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

        # send ID request
        udp_socket_ctrl.sendto(bytes(cmd, "utf-8"), ("255.255.255.255", 2400))

        # close socket
        udp_socket_ctrl.close()

        # wait self.Wait time for the responses
        start = time.time()
        loop_ok = True

        while loop_ok:

            stop = time.time()
            if stop - start > self.Wait:
                loop_ok = False

            try:
                recv = udp_socket_data.recvfrom(1024)
                # store the whole response
                self.resp.append((recv[0].decode(), recv[1]))
            except Exception:
                pass

        # close socket
        udp_socket_data.close()

        return self.resp
