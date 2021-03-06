"""
Contains custom exceptions and warnings for azcam.

AzcamError codes:
 "controller reset error, check power and fibers", error_code=1
 "could not open connection to server", error_code=2
 "receive image data abort", error_code=3
 "remote call not allowed", error_code=4
"""

import warnings

import azcam

# ERRORS
class AzcamError(Exception):
    def __init__(self, message, error_code=None):
        """
        Custom error exception for azcam.

        # Usage:  raise azcam.AzcamError(message)
        :param: int Error code: flag for code, from list below:
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

        if azcam.db.logger is not None:
            azcam.db.logger.logger.warning(f"ERR-> {message}")
        else:
            print(f"AzcamError: {message}")


# WARNINGS
def azcam_formatwarning(msg, *a, **kargs) -> str:
    # only print the message
    return "AzcamWarning: " + str(msg) + "\n"


warnings.formatwarning = azcam_formatwarning
del azcam_formatwarning


def AzcamWarning(message):
    """
    AzcamWarning attempts to print a message and exit the call stack without displaying a traceback.
    """

    # warnings.warn(message)
    # print(f"AzcamWarning: {message}")

    try:
        azcam.db.logger.logger.warning(f"Warn> {message}")
    except Exception:
        print(f"AzcamWarning: {message}")

    return
