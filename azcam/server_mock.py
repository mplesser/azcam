"""
azcamserver script for a mock system.

Command line options:
  -system azcam_mock
  -datafolder path_to_datafolder
  -cmdport azcamserver_port
"""

import os
import sys
import ctypes
from runpy import run_path

import azcam
import azcam.server
import azcam.shortcuts
from azcam.logger import check_for_remote_logger
import azcam.scripts

from azcam.cmdserver import CommandServer
from azcam.tools.controller import Controller
from azcam.tools.instrument import Instrument
from azcam.tools.tempcon import TempCon
from azcam.tools.display import Display
from azcam.tools.telescope import Telescope
from azcam.tools.exposure import Exposure
from azcam.tools.webserver.fastapi_server import WebServer
from azcam.tools.webtools.exptool.exptool import Exptool
from azcam.tools.webtools.status.status import Status
from azcam.tools.queue import Queue
from azcam.tools.observe.observe import Observe

# ****************************************************************
# parse command line arguments
# ****************************************************************
try:
    i = sys.argv.index("-system")
    systemname = sys.argv[i + 1]
except ValueError:
    systemname = "azcam_mock"
try:
    i = sys.argv.index("-datafolder")
    datafolder = sys.argv[i + 1]
except ValueError:
    datafolder = None
try:
    i = sys.argv.index("-cmdport")
    cmdport = int(sys.argv[i + 1])
except ValueError:
    cmdport = 2402

# ****************************************************************
# configuration
# ****************************************************************
azcam.db.systemname = systemname
azcam.db.systemfolder = os.path.dirname(__file__)
azcam.db.systemfolder = azcam.utils.fix_path(azcam.db.systemfolder)

if datafolder is None:
    droot = os.environ.get("AZCAM_DATAROOT")
    if droot is None:
        if os.name == "posix":
            droot = os.environ.get("HOME")
        else:
            droot = "/"
        azcam.db.datafolder = os.path.join(os.path.realpath(droot), "data", azcam.db.systemname)
    else:
        azcam.db.datafolder = os.path.join(os.path.realpath(droot), azcam.db.systemname)
else:
    azcam.db.datafolder = os.path.realpath(datafolder)

azcam.db.servermode = azcam.db.systemname
azcam.db.verbosity = 2

# ****************************************************************
# parameter file
# ****************************************************************
parfile = os.path.join(azcam.db.datafolder, "parameters", "parameters_server_mock.ini")
azcam.db.parameters.read_parfile(parfile)
azcam.db.parameters.update_pars(0, "azcamserver")

# ****************************************************************
# logging
# ****************************************************************
logfile = os.path.join(azcam.db.datafolder, "logs", "server.log")
if check_for_remote_logger():
    azcam.db.logger.start_logging(logtype="23", logfile=logfile)
else:
    azcam.db.logger.start_logging(logtype="1", logfile=logfile)

# message
azcam.log(f"Configuring {azcam.db.systemname}")

# define command server
cmdserver = CommandServer()
cmdserver.port = cmdport
cmdserver.logcommands = 0

# ****************************************************************
# tools
# ****************************************************************
controller = Controller()
instrument = Instrument()
instrument.enabled = 0
telescope = Telescope()
telescope.enabled = 0
tempcon = TempCon()
tempcon.enabled = 0
display = Display()
exposure = Exposure()
# queue = Queue()
# queue.initialize()
# queue.initialize()
observe = Observe()

# ****************************************************************
# scripts
# ****************************************************************
azcam.log("Loading scripts")
azcam.scripts.load("server")

# ****************************************************************
# web server
# ****************************************************************
if 1:
    webserver = WebServer()
    webserver.port = 2403
    webserver.logcommands = 0
    webserver.logstatus = 0
    webserver.return_json = 0
    webserver.index = os.path.join(azcam.db.systemfolder, "index.html")
    webserver.message = f"for host {azcam.db.hostname}"
    webserver.datafolder = azcam.db.datafolder
    webserver.start()

    webstatus = Status()
    webstatus.message = "for a mock system"
    webstatus.initialize()

    exptool = Exptool()
    exptool.initialize()

    # queue = Queue()
    # queue.initialize()

    azcam.log("Started web apps")

# ****************************************************************
# start command server
# ****************************************************************
azcam.log(f"Starting cmdserver - listening on port {cmdserver.port}")
cmdserver.start()

# cli commands
from azcam.cli import *

# try to change window title
try:
    ctypes.windll.kernel32.SetConsoleTitleW("azcamserver - mock")
except Exception:
    pass
