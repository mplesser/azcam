"""
*azcam.server* is imported to define server mode, create azcamserver 
parameters dictionary, define a logger, and get local network information.
"""

import socket

import azcam
from azcam.logger import Logger
from azcam.parameters import Parameters

# server mode
azcam.mode = "server"
azcam.db.servermode = ""

# parameters
parameters = Parameters("azcamserver")

# logging
azcam.db.logger = Logger()
azcam.log = azcam.db.logger.log  # to allow azcam.log()

# save this machine's hostname and ip address
hostname = socket.gethostname()
azcam.db.set("hostname", hostname)
azcam.db.set("hostip", socket.gethostbyname(hostname))

# tool_id's which are reset or initialized with exposure
azcam.db.set("tools_reset", {})
azcam.db.set("tools_init", {})
