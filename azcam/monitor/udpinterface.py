# UDP interface class
# Allows sending UDP register request to the AzCam Monitor application
# Allows sending and receiving braodcast ID request

# For broadcast???

import ipaddress
import multiprocessing
import os
import socket
import time


class UDPinterface(object):
    def __init__(self):
        self.Resp = []
        self.Wait = 3

    def GetIP(self, hostName):
        """
        Sends UDP Get ID request and looks for a hostName, then returns IP address if found.
        02Aug2019 last change GSZ
        """

        print("Resolving " + hostName + " IP Address")

        # create a ne wsocket for receiving IDs
        udp_socketData = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        udp_socketData.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        udp_socketData.setblocking(0)
        udp_socketData.bind(("", 2401))

        # ID request
        cmd = "0\r\n"

        # create a new socket for sending register command
        udp_socketCtrl = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        udp_socketCtrl.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        udp_socketCtrl.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

        # send ID request
        stat = udp_socketCtrl.sendto(bytes(cmd, "utf-8"), ("255.255.255.255", 2400))

        # close socket
        udp_socketCtrl.close()

        # wait self.Wait time for the responses
        start = time.time()
        loopOK = True

        while loopOK:
            stop = time.time()
            if stop - start > self.Wait:
                loopOK = False

            try:
                recv = udp_socketData.recvfrom(1024)

                # store the whole response
                self.Resp.append(recv)
            except Exception as message:
                pass

        # close socket
        udp_socketData.close()

        # check IDs
        cnt = len(self.Resp)
        found = 0
        IPAddress = "0.0.0.0"

        if cnt > 0:
            for indx in self.Resp:
                recv = str(indx).split(" ")
                try:
                    if recv[2] == hostName:
                        found = 1
                        IPAddress = recv[4]

                except Exception as e:
                    pass
        else:
            print("ERROR: No IDs available")

        if found == 1:
            print("IP Address: " + IPAddress)
        else:
            print("IP Address not found")

        return IPAddress

    def GetIDs(self):
        """
        Sends UDP Get ID request.
        10Sep2019 last change GSZ
        """

        print("Requesting IDs")

        self.Resp = []

        # create a ne wsocket for receiving IDs
        udp_socketData = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        udp_socketData.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        udp_socketData.setblocking(0)
        udp_socketData.bind(("", 2401))

        # ID request
        cmd = "0\r\n"

        # create a new socket for sending register command
        udp_socketCtrl = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        udp_socketCtrl.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        udp_socketCtrl.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

        # send ID request
        stat = udp_socketCtrl.sendto(bytes(cmd, "utf-8"), ("255.255.255.255", 2400))

        # close socket
        udp_socketCtrl.close()

        # wait self.Wait time for the responses
        start = time.time()
        loopOK = True

        while loopOK:
            stop = time.time()
            if stop - start > self.Wait:
                loopOK = False

            try:
                recv = udp_socketData.recvfrom(1024)
                print(recv[0])
                # store the whole response
                self.Resp.append(recv)
            except Exception as message:
                pass

        # close socket
        udp_socketData.close()

        print("")

        return self.Resp
