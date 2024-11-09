import datetime
import os
import sys
import logging.handlers
import threading
import socket
from typing import List

import azcam
import azcam.exceptions
import loguru

import azcam.utils


class AzCamLogger(object):
    """
    The azcam Logger class.
    """

    def __init__(self) -> None:
        self.logfile = "azcam.log"
        self.logger = loguru.logger
        self.use_logprefix = 1
        self.last_data = []  # data since last call to get_data
        self.last_data_max = 1024  # max entries in last_data buffer

    def log(self, message: str, *args: List[str], prefix: str = "", level: int = 1):
        """
        Send a message to the logging system.

        Message is output to logger if level > db.verbosity.
        Levels are:
        0 => silent
        1 => normal
        2 => extended info
        3 => debug

        Args:
            message: String message to be logged
            args: Additional string message to be logged
            prefix: Prefix to be prepended to logged message, ex: 'Log-> '
            level: verbosity level for output

        """

        # don't log if level > global verbosity
        if level > azcam.db.verbosity:
            return

        message = str(message)  # better for exceptions
        message = azcam.utils.dequote(message)

        # format message
        if len(args) == 1:
            message = message + " " + str(args[0])
        elif len(args) > 1:
            message = message + " " + " ".join(str(x) for x in args)

        if prefix != "" and self.use_logprefix:
            message = prefix + message

        # log eveything at INFO level
        self.logger.info(f"{message}")

        # append to last_data
        self.last_data.append(f'"{message}"')

        return

    def _logfilter(self, record):
        # do not send messages from threads to console
        thread_name = threading.currentThread().getName()
        if thread_name == "MainThread":
            return 1
        else:
            return 1  # was 0

    def info(self, message: str, *args, **kwargs):
        return self.logger.info(message, args, kwargs)

    def warning(self, message: str, *args, **kwargs):
        return self.logger.warning(message, args, kwargs)

    def error(self, message: str, *args, **kwargs):
        return self.logger.error(message, args, kwargs)

    def start_logging(
        self, logtype="13", host="localhost", port=2404, logfile=None, use_timestamp=1
    ):
        """
        Start the azcam logger.

        :param logtype: code for loggers to start (1 console, 2 socket, 3 file - combine as '23')
        :param host: hostname for logging over socket
        :param port: socket port number
        :param logfile: base filename of log file. If not absolute path, will use db.systemfolder.
        :param use_timestamp: append timestamp to logfile name.
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
                level="INFO",
                format="{message}",
                filter=self._logfilter,
                colorize=True,
                enqueue=True,
                # backtrace=True,
                # diagnose=True,
            )

        # socket handler
        if "2" in logtype:
            socket_handler = logging.handlers.SocketHandler(
                "localhost",
                port,
            )
            self.logger.add(socket_handler)
            azcam.log(f"Logging to logging server on port {port}")

        # rotating file handler
        if "3" in logtype:
            if logfile is None:
                if self.logfile is None:
                    raise azcam.exceptions.AzcamError("no logfile specified")
            else:
                self.logfile = logfile
            if use_timestamp:
                tt = datetime.datetime.strftime(
                    datetime.datetime.now(), "%d%b%y_%H%M%S"
                )
                s1, s2 = os.path.splitext(self.logfile)
                self.logfile = f"{s1}_{tt}{s2}"

            self.logger.add(
                self.logfile,
                format="{time:DD-MMM-YY HH:mm:ss.SSS} | {level} | {message}",
                rotation="10 MB",
                retention="1 week",
            )
            azcam.log(f"Logging to file {self.logfile}")

        return

    def get_logdata(self):
        """
        Returns log data.
        """

        buffer = self.last_data
        self.last_data = []

        return buffer


def check_for_remote_logger(host: str = "localhost", port: int = 2404):
    """
    Check if a remote logging server is running.
    """

    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 0)
    try:
        sock.settimeout(0.1)
        sock.connect((host, port))
        sock.close()
        return True
    except Exception:
        return False
