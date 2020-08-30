"""
Example console configuration script.
"""

import os
import sys
import datetime
import threading

import azcam
import azcam.console
import azcam.logging
import azcam.shortcuts_console
from azcam.displays.ds9display import Ds9Display
from azcam.genpars import GenPars

print("Loading example console configuration")

# check command line
try:
    i = sys.argv.index("-system")
    azcam.db.systemname = sys.argv[i + 1]
except ValueError:
    azcam.db.systemname = "menu"
try:
    i = sys.argv.index("-datafolder")
    azcam.db.datafolder = sys.argv[i + 1]
except ValueError:
    azcam.db.datafolder = None

# optional menu to select system
menu_options = {
    "LSST": "LSST",
    "DESI": "DESI",
    "Example": "example",
}
if azcam.db.systemname == "menu":
    azcam.db.systemname = azcam.utils.show_menu(menu_options)

azcam.db.systemfolder = azcam.utils.fix_path(os.path.dirname(__file__))
if azcam.db.datafolder is None:
    azcam.db.datafolder = os.path.join("/data", azcam.db.systemname)

# allow top level only imports
azcam.utils.add_searchfolder(azcam.db.systemfolder, 0)

if azcam.db.systemname is not None:
    # system-specific folder, like DESI
    azcam.db.projectfolder = os.path.join(azcam.db.systemfolder, azcam.db.systemname)
    azcam.utils.add_searchfolder(azcam.db.projectfolder, 0)  # top level only
    parfile = f"{azcam.db.datafolder}/parameters_{azcam.db.systemname}.ini"
else:
    azcam.db.projectfolder = None
    parfile = None

# ****************************************************************
# start logging
# ****************************************************************
tt = datetime.datetime.strftime(datetime.datetime.now(), "%d%b%y_%H%M%S")
azcam.db.logfile = os.path.join(azcam.db.datafolder, "logs", f"console_{tt}.log")
azcam.logging.start_logging(azcam.db.logfile)
azcam.log(f"Configuring console for {azcam.db.systemname}")

# ****************************************************************
# display
# ****************************************************************
display = Ds9Display()
dthread = threading.Thread(target=display.initialize, args=[])
dthread.start()  # thread just for speed

# ****************************************************************
# try to connect to azcam
# ****************************************************************
connected = azcam.console.api.connect()  # default host and port
if connected:
    azcam.log("Connected to azcamserver")
else:
    azcam.log("Not connected to azcamserver")

# ****************************************************************
# system-specific
# ****************************************************************
if azcam.db.systemname == "DESI":
    from detchar_DESI import detchar

    if azcam.db.wd is None:
        azcam.db.wd = "/data/DESI"

if azcam.db.wd is None:
    azcam.db.wd = "/data"

# ****************************************************************
# read par file
# ****************************************************************
genpars = GenPars()
try:
    pardict = genpars.parfile_read(parfile)["azcamconsole"]
    azcam.utils.update_pars(0, pardict)
    wd = genpars.get_par(pardict, "wd", "default")
    azcam.utils.curdir(wd)
except FileNotFoundError:
    azcam.AzcamWarning("Parameter file not found")

# ****************************************************************
# add scripts to sys.path for Run
# ****************************************************************
azcam.utils.add_searchfolder(os.path.join(azcam.db.systemfolder, "scripts"))

# ****************************************************************
# define names to imported into namespace when using cli
# ****************************************************************
azcam.db.cli_cmds.update({"azcam": azcam, "db": azcam.db, "api": azcam.console.api})

# ****************************************************************
# clean namespace
# # ****************************************************************
del azcam.focalplane, azcam.displays, azcam.sockets, azcam.shortcuts_console
del azcam.header, azcam.image

# ****************************************************************
# finish
azcam.log("Configuration complete")
