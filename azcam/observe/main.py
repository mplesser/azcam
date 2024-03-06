"""
Starts the observe Qt application.
This runs from a dedicated azcamconsole.
"""

import sys
import os

from PySide6.QtCore import QCoreApplication
from PySide6.QtWidgets import QApplication

import azcam
import azcam.utils
import azcam.console
from azcam.console.tools import create_console_tools
from azcam.observe.observe_qt.observe_qt import ObserveQt


def main():
    """
    Start observe GUI as a command.
    Usage examples:
      python -m azcam.observe
      ipython -m azcam.observe --
    """

    # app setup
    azcam.db.systemname = "azcamobserve"
    azcam.db.systemfolder = f"{os.path.dirname(__file__)}"

    try:
        i = sys.argv.index("-datafolder")
        datafolder = sys.argv[i + 1]
    except ValueError:
        datafolder = None

    try:
        i = sys.argv.index("-port")
        port = int(sys.argv[i + 1])
    except ValueError:
        port = 2402

    azcam.db.datafolder = azcam.utils.get_datafolder(datafolder)

    parfile = os.path.join(
        azcam.db.datafolder, "parameters", f"parameters_{azcam.db.systemname}.ini"
    )
    azcam.db.parameters.read_parfile(parfile)

    create_console_tools()
    server = azcam.db.tools["server"]
    server.connect(port=port)

    logfile = os.path.join(azcam.db.datafolder, "logs", "console.log")
    azcam.db.logger.start_logging(logfile=logfile)

    if azcam.db.get("qtapp") is None:
        app = QCoreApplication.instance()
        if app is None:
            app = QApplication(sys.argv)
        azcam.db.qtapp = app

    observe = ObserveQt()
    observe.start()

    sys.exit(azcam.db.qtapp.exec())


if __name__ == "__main__":
    main()
