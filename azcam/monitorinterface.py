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
        self.register_port = 2400

        # Get the AzCam Monitor host (local host)
        self.monitor_host = azcam.db.hostname
        # Command port
        self.command_port = azcam.db.cmdserver.port
        

        # Process fileds:
        # Process ID
        self.proc_id = 0
        # Default system name
        self.system_name = azcam.db.systemname
        # Process path
        self.proc_path = ""
        # Process flags
        self.proc_flags = 0
        # Process watchdog time
        self.watchdog = 1
        # Registration flag
        self.registered = 0
        
        self.debug = 1
        
           
    def register(self):
        """
        Sends UDP register requests.
        """
        
        self.proc_id = os.getpid()
        
        command_port = str(self.command_port)
        # register string: command = '1' 
        cmd = "1 " + str(self.proc_id) + " " + self.system_name + " " + command_port + " " + self.monitor_host + " " + self.proc_path + " " + str(self.proc_flags) + " " + str(self.watchdog) + "\r\n"
        azcam.log("Azcam monitor register: "  + cmd)
        # create a new socket for sending register command
        udp_socketReg = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        udp_socketReg.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)      
        
        udp_socketReg.sendto(bytes(cmd, "utf-8"), (self.monitor_host, self.register_port))
        
        udp_socketReg.close()    
        
        self.registered = 1

        return
        
            


