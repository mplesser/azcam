"""
# database_console.py

Contains the azcam database class for azcamconsole.

There is only one instance of this class which is referenced as `azcam.db` and contains
temporary data for this current process.
"""

from azcam.database import AzcamDatabase
from azcam.console.parameters_console import ParametersConsole


class AzcamDatabaseConsole(AzcamDatabase):
    """
    The azcam database class.
    """

    parameters: ParametersConsole
