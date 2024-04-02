"""
azcamconsole config for mock system

Command line options:
  -system azcam_mock
  -datafolder path_to_datafolder
  -cmdport azcamserver_port
  -observe flag to load observe
"""

import os
import sys

import azcam
import azcam.utils
from azcam.scripts import loadscripts

import azcam.console
import azcam.console.shortcuts
import azcam.console.tools.console_tools
from azcam.console.tools.focus import FocusConsole
from azcam.console.tools.ds9display import Ds9Display

# parse command line arguments
try:
    i = sys.argv.index("-datafolder")
    datafolder = sys.argv[i + 1]
except ValueError:
    datafolder = None
try:
    i = sys.argv.index("-observe")
    load_observe = 1
except ValueError:
    load_observe = 0
try:
    i = sys.argv.index("-cmdport")
    cmdport = int(sys.argv[i + 1])
except ValueError:
    cmdport = 2402


def setup():
    global datafolder, load_observe, cmdport

    azcam.db.systemfolder = azcam.utils.fix_path(os.path.dirname(__file__))

    if datafolder is None:
        droot = os.environ.get("AZCAM_DATAROOT")
        if droot is None:
            if os.name == "posix":
                droot = os.environ.get("HOME")
            else:
                droot = "/"
            azcam.db.datafolder = os.path.join(
                os.path.realpath(droot), "data", azcam.db.systemname
            )
        else:
            azcam.db.datafolder = os.path.join(
                os.path.realpath(droot), azcam.db.systemname
            )
    else:
        azcam.db.datafolder = os.path.realpath(datafolder)

    # ****************************************************************
    # parameter file
    # ****************************************************************
    parfile = os.path.join(
        azcam.db.datafolder, "parameters", f"parameters_console_mock.ini"
    )
    azcam.db.parameters.read_parfile(parfile)
    azcam.db.parameters.update_pars()

    # logging
    logfile = os.path.join(azcam.db.datafolder, "logs", "console.log")
    azcam.db.logger.start_logging(logfile=logfile)
    azcam.log(f"Configuring console for {azcam.db.systemname}")

    # display
    display = Ds9Display()

    # console tools
    from azcam.console.tools import create_console_tools

    create_console_tools()
    focus = FocusConsole()

    # ****************************************************************
    # scripts
    # ****************************************************************
    azcam.log("Loading azcam.console.scripts")
    loadscripts(["azcam.console.scripts"])

    # ****************************************************************
    # observe
    # ****************************************************************
    # azcam.log("Loading observe")
    # from azcam.observe.observe_cli.observe_cli import ObserveCli
    # observe = ObserveCli()

    # try to connect to azcamserver
    connected = azcam.db.tools["server"].connect(port=cmdport)  # default host and port
    if connected:
        azcam.log("Connected to azcamserver")
    else:
        azcam.log("Not connected to azcamserver")

    # system-specific
    if azcam.db.systemname == "azcam_mock":
        pass

    if azcam.db.wd is None:
        azcam.db.wd = azcam.db.datafolder

    # par file
    azcam.db.parameters.read_parfile(parfile)
    azcam.db.parameters.update_pars()


setup()
from azcam.cli import *
