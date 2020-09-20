"""
Example server configuration script.
"""

import os

import azcam
import azcam.server
import azcam.shortcuts_server
from azcam.displays.ds9display import Ds9Display
from azcam.telescopes.telescope import Telescope
from azcam.instruments.instrument import Instrument
from azcam.controllers.controller import Controller
from azcam.tempcons.tempcon import TempCon
from azcam.exposures.exposure import Exposure
from azcam.cmdserver import CommandServer
from azcam.genpars import GenPars

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
azcam.db.logfile = os.path.join(azcam.db.datafolder, "logs", "azcam.log")
azcam.logging.start_logging(azcam.db.logfile, "123")
azcam.log(f"Configuring azcam for {azcam.db.systemname}")

# ****************************************************************
# define objects
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
parfile = os.path.join(azcam.db.datafolder, f"parameters_{azcam.db.systemname}.ini")
genpars = GenPars()

try:
    pardict = genpars.parfile_read(parfile)["azcamserver"]
    azcam.utils.update_pars(0, pardict)
    wd = genpars.get_par(pardict, "wd", "default")
    azcam.utils.curdir(wd)
except FileNotFoundError:
    azcam.log(f"Paramater file not found: {parfile}")

# ****************************************************************
# command server
# ****************************************************************
cmdserver = CommandServer()
cmdserver.port = 2402
azcam.log(f"Starting command server listening on port {cmdserver.port}")
cmdserver.welcome_message = "Welcome - connected to the azcam command server"
azcam.db.cmdserver.logcommands = 1
cmdserver.start()

# ****************************************************************
# define names to imported into namespace (for CLI)
# ****************************************************************
azcam.db.cli_cmds.update({"azcam": azcam, "db": azcam.db, "api": azcam.server.api})

# ****************************************************************
# finish
# ****************************************************************
azcam.log("Configuration complete")
