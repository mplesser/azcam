"""
*azcam.cmdserver* contains the CommandServer class for azcam's socket command interface.
"""

import os
import socket
import socketserver
import threading
import time
import json
from typing import Callable

import azcam
import azcam.utils
import azcam.exceptions


class CommandServer(socketserver.ThreadingTCPServer):
    """
    Main class for cmdserver tool.

    CommandServer class to receive and execute client commands over the socket interface.
    This is a socket server which receives command strings, executes them, and returns a reply string.
    The server normally runs in a thread so as to not block the command line. Each client which
    connects runs in its own thread (through the ThreadingTCPServer class) and so operates
    concurrently.  There is no global locking, so this process can be dangerous but it does allows
    multiple clients to interact simultaneously with azcam, which is important for operations
    like camera control, telescope movement, temperature readback, instrument control, etc.
    """

    def __init__(self, port=2402):
        self.welcome_message = None

        self.port = port  # listen port
        self.is_running = 0  # True when server is running
        self.server = 0  # server instance
        self.verbose = 0
        self.log_connections = 1  # log open and close connections
        self.monitorinterface = 0

        self.logcommands = 0

        self.socketnames = {}
        self.use_clientname = 1  # log client name with command

        self.currentclient = 0

        self.case_insensitive = 0

        azcam.db.cmdserver = self

    def begin(self, port=-1):
        """
        Start command server.
        """

        if port == -1:
            port = self.port
        else:
            self.port = port

        server_address = ("", port)  # '' better than localhost when no network

        try:
            self.server = ThreadedTCPServer(server_address, MyBaseRequestHandler)
            self.server.RequestHandlerClass.cmdserver = self

            self.is_running = 1
            self.server.serve_forever()  # waits here forever
        except Exception as message:
            self.is_running = 0
            azcam.log(
                f"ERROR in cmdserver:{repr(message)} Is it already running? Exiting..."
            )
            time.sleep(2)
            os._exit(1)

        # Exits here when server is aborted

        return

    def start(self, port=-1):
        """
        Starts command server in a thread.
        """

        cmdthread = threading.Thread(target=self.begin, name="cmdserver")
        cmdthread.daemon = True  # terminates when main process exits
        cmdthread.start()

        return

    def stop(self, port=-1):
        """
        Stops command server.
        """

        raise NotImplementedError

    def command(self, command: str):
        """
        Execute a command string received from a client over the command socket.
        Returns the reply string, always starting with OK or ERROR.
        """

        toolid, args, kwargs = self.parse_command_string(command, self.case_insensitive)

        reply = self.execute_command(toolid, args, kwargs)

        return reply

    def execute_command(self, tool: Callable, args: list, kwargs: dict = {}) -> str:
        """
        Executes a tool command which has been parsed into tool method and arguments and
        returns its reply string.

        Args:
            tool: tool object (not name)
            args: list of arguments
            kwargs: dictionary of keyword:value pairs for arguments

        Returns:
            reply: reply from command executed. Always starts with OK or ERROR.
        """

        if len(args) == 0 and len(kwargs) == 0:
            reply = tool()

        elif len(kwargs) == 0:
            reply = tool(*args)

        elif len(args) == 0:
            reply = tool(**kwargs)

        else:
            reply = tool(*args, **kwargs)

        reply = self._command_reply(reply)

        return reply

    def _command_reply(self, reply: str):
        """
        Create a reply string for a socket command.

        Args:
            reply (str): command reply

        Returns:
            [type]: formatted reply string
        """

        if reply is None or reply == "":
            s = ""

        elif type(reply) == str:
            s = reply

        elif type(reply) == list:
            s = ""
            for x in reply:
                if type(x) == str and " " in x:  # check if space in the string
                    s = s + " " + "'" + str(x) + "'"
                else:
                    s = s + " " + str(x)
            s = s.strip()

        elif type(reply) == dict:
            s = json.dumps(reply)

        else:
            s = repr(reply)

            if s != '""':
                s = s.strip()

        # add OK status if needed
        if not (s.startswith("OK") or s.startswith("ERROR") or s.startswith("WARNING")):
            s = "OK " + s

        s = s.strip()

        return s

    def parse_command_string(self, command: str, case_insensitive: int = 0):
        """
        Parse a command string into tool and arguments.
        If command does not start with a dotted object.method token, then
        assume it is the method of the default_tool.

        Returns (objid, args, kwargs)
        objid is a bound method of a class
        args is a list of strings
        kwargs is a dict of strings
        """

        # parse command string
        tokens = azcam.utils.parse(command, 0)
        cmd = tokens[0]

        if case_insensitive:
            cmd = cmd.lower()

        arglist = tokens[1:]
        args = []
        kwargs = {}
        if len(arglist) == 0:
            pass
        else:
            for token in arglist:
                if "=" in token:
                    keyname, value = token.split("=")
                    kwargs[keyname] = value
                else:
                    args.append(token)

        if "." not in cmd:
            # get method from db.default_tool
            if azcam.db.default_tool == "api":
                objid = getattr(azcam.db.api, cmd)
            elif azcam.db.default_tool is None:
                s = f"command not recognized: {cmd} "
                raise azcam.exceptions.AzcamError(s)
            else:
                objid = getattr(azcam.db.tools[azcam.db.default_tool], cmd)

        else:
            # get method from tool in db.tools
            objects = cmd.split(".")

            # special case temporarily for parameters
            if objects[0] == "parameters":
                if len(objects) == 1:
                    objid = azcam.db.parameters
                elif len(objects) == 2:
                    objid = getattr(azcam.db.parameters, objects[1])
                elif len(objects) == 3:
                    objid = getattr(
                        getattr(azcam.db.parameters, objects[1]), objects[2]
                    )
                elif len(objects) == 4:
                    objid = getattr(
                        getattr(getattr(azcam.db.parameters, objects[1]), objects[2]),
                        objects[3],
                    )
                else:
                    objid = None  # too complicated for now
                return objid, args, kwargs

            elif objects[0] == "api":
                objid = getattr(azcam.db.api, objects[1])
                return objid, args, kwargs

            elif objects[0] not in azcam.db.tools:
                raise azcam.exceptions.AzcamError(
                    f"remote call not allowed: {objects[0]}", 4
                )

            if len(objects) == 1:
                objid = azcam.db.tools[objects[0]]
            elif len(objects) == 2:
                objid = getattr(azcam.db.tools[objects[0]], objects[1])
            elif len(objects) == 3:
                objid = getattr(
                    getattr(azcam.db.tools[objects[0]], objects[1]), objects[2]
                )
            elif len(objects) == 4:
                objid = getattr(
                    getattr(
                        getattr(azcam.db.tools[objects[0]], objects[1]), objects[2]
                    ),
                    objects[3],
                )
            else:
                objid = None  # too complicated for now

            # kwargs = {}
            # l1 = len(tokens)
            # if l1 > 1:
            #     args = tokens[1:]
            #     if "=" in args[0]:
            #         # assume all keywords for now
            #         kwargs = {}
            #         for argtoken in args:
            #             keyword, value = argtoken.split("=")
            #             kwargs[keyword] = value
            #         args = []
            # else:
            #     args = []

        return objid, args, kwargs


class ThreadedTCPServer(socketserver.ThreadingMixIn, socketserver.TCPServer):
    # allow_reuse_address = True
    allow_reuse_address = False


class MyBaseRequestHandler(socketserver.BaseRequestHandler):
    def __init__(self, request, client_address, server):
        azcam.db.cmdserver.currentclient += 1
        self.currentclient = azcam.db.cmdserver.currentclient

        socketserver.BaseRequestHandler.__init__(self, request, client_address, server)

    def handle(self):
        """
        Called when a connection is made from a client.
        Starts an infinite loop waiting for new commands.
        Commands are executed sequentially.
        """

        if azcam.db.cmdserver.welcome_message is not None:
            self.request.send(str.encode(azcam.db.cmdserver.welcome_message + "\r\n"))

        while True:
            try:
                prefix_in = f"Rcv{self.currentclient:01}> "
                prefix_out = f"Out{self.currentclient:01}>  "  # extra space for indent

                # ************************************************************************
                # receive command from the network socket
                # ************************************************************************
                try:
                    command_string = self.receive_command()
                except ConnectionResetError:
                    azcam.log(
                        f"Client {azcam.db.tools['cmdserver'].socketnames[self.currentclient]} disconnected",
                        prefix=prefix_in,
                    )
                    break
                except Exception as e:
                    azcam.log(f"ERROR in handle: {e}", prefix="Err-> ")
                    break

                # ************************************************************************
                # disconnect on empty string - important
                # ************************************************************************
                if command_string.strip() == "":
                    try:
                        self.request.send(str.encode("OK\r\n"))
                    except OSError:
                        pass
                    except Exception as e:
                        azcam.log(
                            f"Null command send error for client {self.currentclient}: {e}"
                        )
                    break

                # ************************************************************************
                # log received command
                # ************************************************************************
                try:
                    self.cmdserver.socketnames[self.currentclient]
                except Exception:
                    azcam.db.cmdserver.socketnames[self.currentclient] = (
                        f"unknown_{self.currentclient}"
                    )
                if azcam.db.cmdserver.logcommands:
                    azcam.log(command_string, prefix=prefix_in)

                # ************************************************************************
                # check special cases which do not leave cmdserver
                # ************************************************************************

                # close socket connection to client
                if command_string.lower().startswith("closeconnection"):
                    azcam.log(
                        f"closing connection to {azcam.db.tools['cmdserver'].socketnames[self.currentclient]}",
                        prefix=prefix_in,
                    )
                    self.request.send(str.encode("OK\r\n"))
                    self.request.close()
                    break

                # register - register a client name, example: register console
                elif command_string.lower().startswith("register"):
                    x = command_string.split(" ")
                    azcam.db.cmdserver.socketnames[self.currentclient] = (
                        f"{x[1]}_{int(self.currentclient)}"
                    )
                    self.request.send(str.encode("OK\r\n"))
                    azcam.log(
                        f"OK client {self.currentclient}", prefix=prefix_out
                    )  # log reply
                    command_string = ""

                # echo - for polling as "echo hello" or just "echo"
                elif command_string.lower().startswith("echo"):
                    s = command_string.split(" ")
                    if len(s) == 1:
                        reply = "OK"
                    elif len(s) == 2:
                        reply = "OK %s" % s[1]
                    else:
                        reply = "OK %s" % " ".join(s[1:])
                    self.request.send(str.encode(reply + "\r\n"))
                    if azcam.db.cmdserver.logcommands:
                        azcam.log("%s" % reply, prefix=prefix_out)
                    command_string = ""

                # update - azcammonitor
                elif command_string.lower().startswith("updatemonitor"):
                    azcam.db.monitor.register()
                    azcam.log("%s" % "OK", prefix=prefix_out)
                    reply = "OK"

                    self.request.send(str.encode(reply + "\r\n"))
                    command_string = ""

                # exit - send reply for handshake before closing socket and shutting down
                elif command_string.lower().startswith("exit"):
                    self.request.send(str.encode("OK\r\n"))
                    azcam.log("%s" % "OK", prefix=prefix_out)  # log reply
                    self.request.close()
                    os._exit(0)  # kill python

                # ************************************************************************
                # process all other command_strings
                # ************************************************************************
                if command_string != "":
                    # execute command
                    try:
                        reply = azcam.db.cmdserver.command(command_string)
                    except Exception as e:
                        reply = f"ERROR {repr(e)}"

                    # log reply
                    if azcam.db.cmdserver.logcommands:
                        azcam.log(reply, prefix=prefix_out)

                    # send reply to socket
                    self.request.send(str.encode(reply + "\r\n"))

                else:
                    time.sleep(0.10)  # for telnet

            except Exception as message:  # catch everything so cmdserver never crashes
                azcam.log(f"ERROR in cmdserver: {command_string}: {message}")
                # try to reply but this may not work
                try:
                    self.request.send(str.encode(f"ERROR {repr(message)}\r\n"))
                except Exception as e:
                    print(e)
                    pass  # OK to do nothing

        return

    def setup(self):
        """
        Called when new connection made.
        """

        if azcam.db.cmdserver.log_connections and azcam.db.cmdserver.verbose:
            azcam.log(
                f"Client connection made from {str(self.client_address)}",
                prefix="cmd> ",
            )

        return socketserver.BaseRequestHandler.setup(self)

    def finish(self):
        """
        Called when existing connection is closed.
        """

        if azcam.db.cmdserver.log_connections and azcam.db.cmdserver.verbose:
            azcam.log(f"Connection closed to {str(self.client_address)}")

        return socketserver.BaseRequestHandler.finish(self)

    def receive_command(self):
        """
        Receive a string from socket until terminator is found.
        Returns a string.
        Returns empty string on error.
        """

        terminator = "\n"  # likely ends with \r\n

        # read socket until terminator found
        msg = ""
        msg1 = ""
        while True:
            try:
                msg1 = self.request.recv(1024).decode()
                if msg1 == "":
                    return ""
                if msg1[-1] == terminator:  # found terminator
                    msg += msg1[:-1]
                    break
                msg += msg1
            except socket.error as e:
                if e.errno == 10054:  # connection closed
                    pass
                else:
                    azcam.log(f"receive_command: {e}", prefix="Err-> ")
                break

        if len(msg) == 0:
            msg = ""

        if msg is None:
            msg = ""

        return msg
