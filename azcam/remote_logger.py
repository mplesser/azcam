"""
Example logging server which receives and prints azcam log records.
"""

import socketserver
import pickle
import struct
import logging
import ctypes

from loguru import logger


class LoggingStreamHandler(socketserver.StreamRequestHandler):
    def handle(self):
        while True:
            try:
                chunk = self.connection.recv(4)
            except ConnectionResetError:
                break
            if len(chunk) < 4:
                break
            slen = struct.unpack(">L", chunk)[0]
            chunk = self.connection.recv(slen)
            while len(chunk) < slen:
                chunk = chunk + self.connection.recv(slen - len(chunk))
            record = pickle.loads(chunk)
            lrec = logging.makeLogRecord(record)
            outstring = lrec.msg
            # outstring = outstring.replace("| azcam.logger:log:68 - ", "")
            # outstring = outstring.replace(" | INFO   ", "")
            outstring = outstring[65:]

            print(outstring)
            # level, message = record["levelname"], record["msg"]
            # print(message)
            # logger.patch(lambda record: record.update(record)).log(level, message)


def start_and_serve_tcp(port: int = 2404):
    """
    Start logging server.
    """

    # optionally set window title
    try:
        ctypes.windll.kernel32.SetConsoleTitleW("azcamlogger")
    except Exception:
        pass
    print(f"Logging server started on port {port}")
    logging_server = socketserver.TCPServer(("localhost", port), LoggingStreamHandler)
    logging_server.serve_forever()


if __name__ == "__main__":
    start_and_serve_tcp()
