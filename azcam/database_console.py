"""
*azcam.database* contains the main azcam database class.

There is only one instance of this class which is referenced as `azcam.db` and contains
temporary data for this current process.
"""

from typing import Any, Union, List, Dict

from azcam.logger import Logger
from azcam.parameters import Parameters
from azcam.cmdserver import CommandServer
from azcam.system import System


class AzcamConsoleDatabase(object):
    """
    The azcam database class.
    """

    wd: Union[str, None] = None
    """the current working directory"""

    verbosity: int = 1
    """verbosity level for messages"""

    mode: str = ""
    """operating mode (server or console)"""

    abortflag: int = 0
    """abort flag, 1 (true) if an abort has occurred"""

    datafolder: str = ""
    """system datafolder"""

    tools: dict = {}
    """dict of tools"""

    shortcuts: dict = {}
    """dict of shortcuts"""

    scripts: dict = {}
    """dict of scripts"""

    logger: Logger = Logger()
    """logger object"""

    parameters: Parameters
    """parameters object"""

    # *************************************************************************
    # db methods
    # *************************************************************************

    def __init__(self) -> None:
        pass

    def get(self, name: str) -> Any:
        """
        Returns a database attribute by name.
        Args:
          name: name of attribute to return
        Returns:
          value or None if *name* is not defined
        """

        try:
            obj = getattr(self, name)
        except AttributeError:
            obj = None

        return obj

    def set(self, name: str, value: Any) -> None:
        """
        Sets a database attribute value.
        Args:
          name: name of attribute to set
          value: value of attribute to be set
        """

        # if not hasattr(self, name):
        #    return

        setattr(self, name, value)

        return
