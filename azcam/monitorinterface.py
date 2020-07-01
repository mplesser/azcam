# AzCam Monitor interface class
# Allows sending UDP register request to the AzCam Monitor application
# After registration the communication with the AzCam Monitor is based on TCP/IP.

import socket
import multiprocessing
import time, ipaddress
import os

import azcam


class MonitorInterface(object):

    def __init__(self):

        # Registration port (UDP)
        self.RegisterPort = 2400

        # Get the AzCam Monitor host (local host)
        self.MonitorHost = azcam.db.hostname
        # Command port
        self.CommandPort = azcam.db.cmdserver.port
        

        # Process fileds:
        # Process ID
        self.ProcID = 0
        # Default system name
        self.SysName = azcam.db.systemname
        # Process path
        self.ProcPath = ""
        # Process flags
        self.ProcFlags = 0
        # Process watchdog time
        self.Watchdog = 1
        # Registration flag
        self.Registered = 0
        
        self.Debug = 1
        
           
    def Register(self):
        """
        Sends UDP Register requests.
        Last change: 26Jul2019 GSZ
        """
        
        self.ProcID = os.getpid()
        
        CommandPort = str(self.CommandPort)
        # Register string: command = '1' 
        cmd = "1 " + str(self.ProcID) + " " + self.SysName + " " + CommandPort + " " + self.MonitorHost + " " + self.ProcPath + " " + str(self.ProcFlags) + " " + str(self.Watchdog) + "\r\n"
        print("Register process: "  + cmd)
        # create a new socket for sending register command
        udp_socketReg = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        udp_socketReg.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)      
        
        udp_socketReg.sendto(bytes(cmd, "utf-8"), (self.MonitorHost, self.RegisterPort))
        
        udp_socketReg.close()    
        
        self.Registered = 1
        
            


