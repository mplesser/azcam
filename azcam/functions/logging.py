import sys

from loguru import logger

import azcam


def log(message, *args, prefix="Log-> ", level=1, logconsole=1):
    """
    Send a message to the logging system.
    :param str message: String message to be logged
    :param str args: Additional string message to be logged
    :param str prefix: Prefix to be prepended to logged message, ex: 'log> '
    :param int level: verbosity level for output
    :param bool logconsole: set to False to not log to console
    :return None:

    Message is output to logger if level > db.verbosity.
    Levels are:
    0 => silent
    1 => normal
    2 => extended info
    3 => debug
    """

    # don't log if level > global verbosity
    if level > azcam.db.verbosity:
        return

    message = str(message)  # better for exceptions

    if len(args) == 1:
        message = message + " " + str(args[0])
    elif len(args) > 1:
        message = message + " " + " ".join(str(x) for x in args)

    if message.startswith("'") or message.startswith('"'):
        message = message[1:]

    if prefix != "" and azcam.db.use_logprefix:
        message = prefix + message

    if azcam.db.logger is None:
        if logconsole:
            print(message)
    else:
        azcam.db._logconsole = logconsole
        azcam.db.logger.info(f"{message}")
        azcam.db._logconsole = 1

    return


def _logfilter(record):
    return azcam.db._logconsole


def start_logging(logfile="azcam.log", logtype="13", host="localhost", port=2406):
    """
    Start the azcam logger.

    :param str logfile: base filename of log file. If not absolute path, will use db.systemfolder. Use None for no log file.
    :param str logtype: code for loggers to start (1 console, 2 socket, 3 file, codes may be combined as '23')
    :param Port: socket port number
    """

    azcam.db.logger = logger

    # remove default logger for customization
    try:
        azcam.db.logger.remove(0)
    except Exception:
        pass

    # console handler
    if "1" in logtype:
        azcam.db.logger.add(
            sys.stdout,
            colorize=False,
            filter=_logfilter,
            format="{message}",
            enqueue=True,
        )

    # socket handler
    if "2" in logtype:
        pass

    # rotating file handler
    if "3" in logtype and (logfile is not None):
        azcam.db.logger.add(
            logfile,
            format="{time:DD-MMM-YY HH:mm:ss.SSS} | {level} | {message}",
            rotation="10 MB",
            retention="1 week",
        )

    return
