"""
Example server configuration script.
"""

import os

from azcam_ds9.ds9display import Ds9Display

import azcam
import azcam.server
import azcam.shortcuts_server
from azcam.cmdserver import CommandServer
from azcam.controller import Controller
from azcam.exposure import Exposure
from azcam.instrument import Instrument
from azcam.telescope import Telescope
from azcam.tempcon import TempCon

print("Loading example server configuration")

# ****************************************************************
# set some basic parameters
# ****************************************************************
azcam.db.systemname = "example"  # name or menu
azcam.db.datafolder = "/data/example"

# ****************************************************************
# define folders
# ****************************************************************
azcam.db.systemfolder = os.path.dirname(__file__)

# ****************************************************************
# enable logging
# ****************************************************************
azcam.db.logger.logfile = os.path.join(azcam.db.datafolder, "logs", "azcam.log")
azcam.db.logger.start_logging()
azcam.log(f"Configuring {azcam.db.systemname}")

# ****************************************************************
# define tools
# ****************************************************************
display = Ds9Display()
telescope = Telescope()
instrument = Instrument()
tempcon = TempCon()
controller = Controller()
exposure = Exposure()

# ****************************************************************
# read par file and set working directory
# ****************************************************************
parfile = os.path.join(azcam.db.datafolder, f"parameters_console_{azcam.db.systemname}.ini")
try:
    pardict = azcam.db.params.read_parfile(parfile)
    azcam.db.params.update_pars(0, pardict["azcamserver"])
except FileNotFoundError:
    azcam.log(f"Parameter file not found: {parfile}")

# ****************************************************************
# command server
# ****************************************************************
cmdserver = CommandServer()
cmdserver.port = 2402
azcam.log(f"Starting cmdserver - listening on port {cmdserver.port}")
cmdserver.welcome_message = "Welcome - connected to the azcam command server"
azcam.db.cmdserver.logcommands = 1
cmdserver.start()

# ****************************************************************
# finish
# ****************************************************************
azcam.log("Configuration complete")
