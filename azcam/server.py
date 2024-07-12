"""
*azcam.server* is imported to define server mode, create azcamserver 
parameters dictionary, define a logger, and get local network information.
"""

import socket

import azcam
from azcam.logger import AzCamLogger
from azcam.parameters_server import ParametersServer
from azcam.database_server import AzcamDatabaseServer
from azcam.cmdserver import CommandServer
from azcam.api import API

from azcam.monitor.monitorinterface import AzCamMonitorInterface


def setup_server():
    azcam.db = AzcamDatabaseServer()  # overwrite default db

    # server mode
    azcam.db.set("servermode", "")

    # parameters
    azcam.db.parameters = ParametersServer()

    # logging
    azcam.db.logger = AzCamLogger()
    azcam.log = azcam.db.logger.log  # to allow azcam.log()

    # save this machine's hostname and ip address
    hostname = socket.gethostname()
    azcam.db.set("hostname", hostname)
    azcam.db.set("hostip", socket.gethostbyname(hostname))

    # tool_id's which are reset or initialized with exposure
    azcam.db.set("tools_reset", {})
    azcam.db.set("tools_init", {})

    # command server
    azcam.db.cmdserver = CommandServer()

    # azcammonitor
    azcam.db.monitor = AzCamMonitorInterface()
    # azcam.db.monitor.proc_path = ""
    # azcam.db.monitor.register()

    # define API tool
    _ = API()

    return


setup_server()
