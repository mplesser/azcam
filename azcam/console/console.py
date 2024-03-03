"""
*azcam.console* is imported to define console mode, create the azcamconsole parameters dictionary, and define a logger.
"""

import azcam
from azcam.logger import AzCamLogger
from azcam.console.parameters_console import ParametersConsole
from azcam.console.database_console import AzcamDatabaseConsole


def setup_console():
    azcam.db = AzcamDatabaseConsole()  # overwrite default db

    # parameters
    azcam.db.parameters = ParametersConsole()

    # logging
    azcam.db.logger = AzCamLogger()
    azcam.log = azcam.db.logger.log  # to allow azcam.log()


setup_console()
