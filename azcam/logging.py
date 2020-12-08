import sys

import loguru
import azcam


class Logger(object):
    def __init__(self) -> None:

        self.logfile = "azcam.log"
        self.logger = loguru.logger
        self.use_logprefix = 1
        self._log_to_console = 1

    def log(self, message, *args, prefix="Log-> ", level=1, log_to_console=1):
        """
        Send a message to the logging system.
        :param str message: String message to be logged
        :param str args: Additional string message to be logged
        :param str prefix: Prefix to be prepended to logged message, ex: 'log> '
        :param int level: verbosity level for output
        :param bool log_to_console: set to False to not log to console
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

        if prefix != "" and self.use_logprefix:
            message = prefix + message

        if not log_to_console:
            self._log_to_console = 0
        self.logger.info(f"{message}")
        self._log_to_console = 1

        return

    def _logfilter(self, record):
        return self._log_to_console

    def start_logging(self, logtype="13", host="localhost", port=2406):
        """
        Start the azcam logger.

        :param str logfile: base filename of log file. If not absolute path, will use db.systemfolder. Use None for no log file.
        :param str logtype: code for loggers to start (1 console, 2 socket, 3 file, codes may be combined as '23')
        :param Port: socket port number
        """

        # remove default logger for customization
        try:
            self.logger.remove(0)
        except Exception:
            pass

        # console handler
        if "1" in logtype:
            self.logger.add(
                sys.stdout,
                colorize=False,
                filter=self._logfilter,
                format="{message}",
                enqueue=True,
            )

        # socket handler
        if "2" in logtype:
            pass

        # rotating file handler
        if "3" in logtype and (self.logfile is not None):
            self.logger.add(
                self.logfile,
                format="{time:DD-MMM-YY HH:mm:ss.SSS} | {level} | {message}",
                rotation="10 MB",
                retention="1 week",
            )

        return
