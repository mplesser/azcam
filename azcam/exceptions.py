"""
Contains custom exceptions and warnings used throughout azcam.
"""

import azcam

import warnings

warnings.filterwarnings("ignore")


def warning(message: str) -> None:
    """
    Print and log a warning message.
    """

    # warnings.warn(message)
    # print(f"Warning: {message}")

    try:
        azcam.logger.warning(f"Warning: {message}")
    except Exception:
        print(f"Warning: {message}")

    return


class AzcamError(Exception):
    """
    Base custom error class for azcam.
    """

    def __init__(self, message: str, error_code: int = 0):
        """
        Custom error exception for azcam.

        Usage:  raise azcam.exceptions.AzcamError(message)

        Args:
          message: string message to display when error is raised
          error_code: flag for code, from list below
          - 0 - no error
          - 1 - controller reset error, check power and fibers
          - 2 - could not open connection to server
          - 3 - receive image data abort
          - 4 - remote call not allowed
        """

        super().__init__(message)

        self.error_code = 0

        # Now for your custom code...
        if error_code is not None:
            self.error_code = error_code
            # Original error was self.errors.message

        if azcam.logger is not None:
            azcam.logger.error(message)
        else:
            print(f"AzcamError: {message}")
