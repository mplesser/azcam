"""
AzCamMonitor class
"""

import configparser
import os
import socket
import socketserver
import subprocess
import sys
import threading
import time

import azcam
from azcam.monitor.webserver.monitor_webserver import WebServer
from azcam.monitor.monitor_udp import UDP_aux
from azcam.monitor.monitor_watchdog import MonitorWatchdog
from azcam.monitor.monitor_processes import MonitorProcesses


class DataItem(object):
    def __init__(self):
        self.number = 0
        self.type = 0
        self.pid = 0
        self.name = ""
        self.cmd_port = 0
        self.host = ""
        self.path = "default"  # dafault means use existing path
        self.flags = 0
        self.watchdog = 0
        self.count = 0


class AzCamMonitor(
    socketserver.ThreadingTCPServer,
    socketserver.ThreadingUDPServer,
    UDP_aux,
    MonitorWatchdog,
    MonitorProcesses,
):
    def __init__(self):

        self.debug = 1

        MonitorWatchdog.__init__(self)
        MonitorProcesses.__init__(self)

        # UDP port used for receiving register_process requests
        self.port_reg = 2400
        self.port_udp = 2400
        self.port_data = 2401
        self.remote_ip = 0

        self.UDPServer = 0
        self.UDPServer_running = 0

        self.timer_server = 0
        self.timer_server_running = 0

        self.RegServer = 0
        self.RegServer_running = 0

        # self.cmd_host = socket.gethostbyname(socket.gethostname())
        self.cmd_host = "localhost"
        self.cmd_port = 0

        self.udp_socket = 0

        self.IDs = []
        self.Resp = []

        # Registered processes - use Lock() to access current data
        self.MonitorData = []

        self.MonitorDataSemafor = threading.Lock()

        self.process_number = 0

        # Create first entry in the MonitorData list
        self.NewDataItem = DataItem()
        self.NewDataItem.type = 1
        self.NewDataItem.pid = os.getpid()
        self.NewDataItem.name = "azcam-monitor"
        self.NewDataItem.cmd_port = self.port_reg
        self.NewDataItem.host = self.cmd_host
        self.NewDataItem.path = "default"
        self.NewDataItem.flags = 0
        self.MonitorData.append(self.NewDataItem)

        self.process_list = []

        azcam.db.monitor = self
        azcam.db.monitor.process_list = self.process_list

        # command line args
        try:
            i = sys.argv.index("-configfile")
            self.config_file = sys.argv[i + 1]
        except ValueError:
            self.config_file = None

    def load_configfile(self, config_file=None):
        """
        Load configuration file with list of processes that should be automatically started.
        """

        if config_file is None:
            config_file = self.config_file
        else:
            self.config_file = config_file

        if self.config_file is None:
            return

        config_file = os.path.abspath(self.config_file)

        update = "updatemonitor\r\n"

        print(f"Loading monitor config file: {config_file}")

        self.MonitorConfig = configparser.ConfigParser()

        self.MonitorConfig.read(config_file)
        # Load all processes
        # This happens only when the AzCam Monitor starts -> there are no processes already registered
        for process_section in self.MonitorConfig.sections():
            cmd_port = int(self.MonitorConfig.get(process_section, "cmd_port"))

            # Create new Data Item
            self.NewDataItem = DataItem()

            # Set process number - unique
            self.NewDataItem.number = self.process_number + 1
            self.process_number += 1

            self.NewDataItem.pid = 0
            self.NewDataItem.name = self.MonitorConfig.get(process_section, "name")
            self.NewDataItem.cmd_port = int(
                self.MonitorConfig.get(process_section, "cmd_port")
            )
            self.NewDataItem.host = self.cmd_host
            self.NewDataItem.path = self.MonitorConfig.get(process_section, "path")
            self.NewDataItem.flags = self.MonitorConfig.get(process_section, "flags")

            # Append new DataItem
            self.MonitorData.append(self.NewDataItem)

        for process_section in self.MonitorConfig.sections():
            cmd_port = int(self.MonitorConfig.get(process_section, "cmd_port"))
            try:
                testSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                testSocket.settimeout(0.1)
                testSocket.connect((self.cmd_host, cmd_port))
                testSocket.send(str.encode(update))
                reply = testSocket.recv(1024)
                testSocket.close()

                # print(
                #     f"Found process running on port {cmd_port}: {self.MonitorConfig.get(process_section, 'name')}"
                # )

            except Exception as e:
                start = int(self.MonitorConfig.get(process_section, "start"))
                if start == 1:
                    # Start the process -> the process will register itself
                    if self.debug:
                        print(
                            f"Process {self.MonitorConfig.get(process_section, 'name')} is not running"
                        )
                    path = self.MonitorConfig.get(process_section, "path")
                    if self.debug:
                        print(
                            f"Starting {self.MonitorConfig.get(process_section, 'name')} on port {str(cmd_port)}"
                        )
                    subprocess.Popen(path, creationflags=subprocess.CREATE_NEW_CONSOLE)
                    time.sleep(0.2)

        return

    #   ***********************************************************************
    #   webserver
    #   ***********************************************************************
    def start_webserver(self):
        self.webserver = WebServer()
        self.webserver.azcammonitor = self
        self.webserver.start()
