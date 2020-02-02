"""
Azcam configuration script example.

Usage:
  - import azcam.config_example
  - from azcam.config_example import *
  - call this from a startup script to begin a new application
"""

import os

import azcam
from azcam import db
from azcam.displays.ds9display import Ds9Display
from azcam.server.telescopes.telescope import Telescope
from azcam.server.instruments.instrument import Instrument
from azcam.server.controllers.controller import Controller
from azcam.server.tempcons.tempcon import TempCon
from azcam.server.exposures.exposure import Exposure
from azcam.cmdserver import CommandServer
from azcam.shortcuts_server import sav, p, sf, gf, bf

# ****************************************************************
# set some basic parameters
# ****************************************************************
db.systemname = "alpha"  # name or menu
db.datafolder = "/data/azcam"

# ****************************************************************
# define folders
# ****************************************************************
db.systemfolder = os.path.dirname(__file__)

# ****************************************************************
# enable logging
# ****************************************************************
db.logfile = os.path.join(db.datafolder, "logs", "azcam.log")
azcam.utils.start_logging(db.logfile, "123")
azcam.log(f"Configuring azcam for {db.systemname}")

# ****************************************************************
# define objects display
# ****************************************************************
display = Ds9Display()
telescope = Telescope()
instrument = Instrument()
tempcon = TempCon()
controller = Controller()
exposure = Exposure()

# ****************************************************************
# read par file
# ****************************************************************
db.parfile = os.path.join(db.datafolder, f"parameters_server_{db.systemname}.ini")
azcam.utils.curdir(azcam.db.parfile_dict["server"]["wd"])

# ****************************************************************
# command server
# ****************************************************************
cmdserver = CommandServer()
cmdserver.port = 2402
azcam.log(f"Starting command server listening on port {cmdserver.port}")
cmdserver.welcome_message = "Welcome - connected to the azcam command server"
db.cmdserver.logcommands = 1
cmdserver.start()

# ****************************************************************
# define names to imported into namespace when using cli
# # ****************************************************************
for name in db.objects:
    globals()[name] = db.objects[name]
__all__ = ["db", "sav", "p", "sf", "gf", "bf"] + [x for x in db.objects.keys()]

# ****************************************************************
# finish
# ****************************************************************
azcam.log("Configuration complete")
