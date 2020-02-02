"""
Contains the CommandServer class for azcam's socket command interface.
"""

import threading
import socketserver
import os
import time
import socket

import azcam


class CommandServer(socketserver.ThreadingTCPServer):
    """
    CommandServer class to receive and execute client commands.

    This is a socket server which receives command strings, executes them, and returns a reply string.
    The server normally runs in a thread so as to not block the command line. Each client which
    connects runs in its own thread (through the ThreadingTCPServer class) and so operates
    concurrently.  There is no global locking, so this process can be dangerous but it does allows
    multiple clients to interact simultaneously with azcam, which is important for operations
    like camera control, telescope movement, temperature readback, instrument control, etc.

    Commands must be methods from instances in db['objects'], plus some special ones.
    """

    def __init__(self, port=2402):

        self.welcome_message = None

        self.port = port  # listen port
        self.is_running = 0  # True when server is running
        self.server = 0  # server instance
        self.verbose = 0
        self.log_connections = 1  # log open and close connections
        self.monitorinterface = 0

        self.socketnames = {}
        self.use_clientname = 1  # log client name with command

        azcam.db.cmdserver = self

        azcam.db.currentclient = 0

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
                "ERROR in cmdserver:%s Is it already running? Exiting..."
                % repr(message)
            )
            time.sleep(3)
            os._exit(1)

        # Exits here when server is aborted

        return

    def start(self, port=-1):
        """
        Starts command server in a thread.
        """

        cmdthread = threading.Thread(target=self.begin, name="cmdserver")
        cmdthread.start()

        return

    def stop(self):
        """
        Stops command server running in thread.
        """

        self.server.shutdown()
        self.is_running = 0

        return

    def rcommand(self, command: str, **kwargs) -> str:
        """
        Parse and execute a command string with optional arguments.
        Returns the reply string, always starting with OK or ERROR.
        """

        # parse command string
        tokens = azcam.utils.parse(command, 0)  # parse
        l1 = len(tokens)
        cmd = tokens[0]

        # command must be of form object.command or in default parser
        if "." in cmd:
            cmdobject, cmdcommand = cmd.split(".")
            if cmdobject in azcam.db.objects:
                cmd = azcam.objects[cmdobject]
                cmd = getattr(cmd, cmdcommand)
                kwargs = {}
                if l1 > 1:
                    args = tokens[1:]
                    if "=" in args[0]:
                        # assume all keywords for now
                        kwargs = {}
                        for argtoken in args:
                            keyword, value = argtoken.split("=")
                            kwargs[keyword] = value
                        args = []
                else:
                    args = []
                reply = cmd(*args, **kwargs)  # execute
            else:
                return "ERROR invalid object for remote command"
        else:
            if cmd == "get_par":
                reply = azcam.utils.get_par(tokens[1])
            elif cmd == "set_par":
                reply = azcam.utils.set_par(tokens[1], tokens[2])
            else:
                s = f"ERROR {cmd} not recognized"
                azcam.log(s)
                return s

        # process reply
        if reply is None or reply == "":
            s = ""

        elif type(reply) == str:
            s = reply

        elif type(reply) == list:
            s = ""
            for x in reply:
                if type(x) == str:
                    if " " in x:  # check if space in the string
                        s = s + " " + "'" + str(x) + "'"
                    else:
                        s = s + " " + str(x)
                else:
                    s = s + " " + str(x)
            s = s.strip()

        else:
            s = repr(reply)

            if s == '""':
                pass
            else:
                s = s.strip()

        # add OK status if needed
        if s.startswith("OK") or s.startswith("ERROR") or s.startswith("WARNING"):
            pass
        else:
            s = "OK " + s

        s = s.strip()

        return s


class ThreadedTCPServer(socketserver.ThreadingMixIn, socketserver.TCPServer):
    # allow_reuse_address = True
    allow_reuse_address = False


class MyBaseRequestHandler(socketserver.BaseRequestHandler):
    def __init__(self, request, client_address, server):

        azcam.db.currentclient += 1
        self.currentclient = azcam.db.currentclient

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
                    command_string = self.receive_command(self.currentclient)
                except ConnectionResetError:
                    azcam.log(
                        f"Client {self.cmdserver.socketnames[self.currentclient]} disconnected",
                        prefix=prefix_in,
                    )
                    break
                except Exception as e:
                    azcam.log(f"ERROR in handle: {e}", prefix="Err-> ")

                # ************************************************************************
                # disconnect on empty string - important
                # ************************************************************************
                if command_string.strip() == "":
                    try:
                        self.request.send(
                            str.encode("OK\r\n")
                        )  # reply 'OK' to empty string
                    except OSError:
                        pass
                    except Exception as e:
                        azcam.log(
                            f"Null command send error for client {self.currentclient}: {e}"
                        )
                        pass
                    # azcam.log(f"closing connection to client {self.currentclient}")
                    break

                # ************************************************************************
                # log received command
                # ************************************************************************
                try:
                    self.cmdserver.socketnames[self.currentclient]
                except Exception:
                    self.cmdserver.socketnames[
                        self.currentclient
                    ] = f"unknown_{self.currentclient}"
                if azcam.db.cmdserver.logcommands:
                    azcam.log(command_string, prefix=prefix_in)

                # ************************************************************************
                # check special cases which do not leave cmdserver
                # ************************************************************************

                # close socket connection
                if command_string.lower().startswith("closeconnection"):
                    azcam.log(
                        f"closing connection to {self.cmdserver.socketnames[self.currentclient]}",
                        prefix=prefix_in,
                    )
                    self.request.send(str.encode("OK\r\n"))
                    self.request.close()
                    break

                # register - register a client name
                elif command_string.lower().startswith("register"):
                    x = command_string.split(" ")
                    self.cmdserver.socketnames[
                        self.currentclient
                    ] = f"{x[1]}_{int(self.currentclient)}"
                    self.request.send(str.encode("OK\r\n"))
                    azcam.log(
                        f"OK client {self.currentclient}", prefix=prefix_out
                    )  # log reply
                    command_string = ""

                # exit - send reply for handshake before closing socket and shutting down
                elif command_string.lower().startswith("exit"):
                    self.request.send(str.encode("OK\r\n"))
                    azcam.log("%s" % "OK", prefix=prefix_out)  # log reply
                    self.request.close()
                    os._exit(0)  # kill python

                # echo - for polling
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
                        azcam.log("%s" % reply, prefix=prefix_out)  # log reply
                    command_string = ""

                # update monitor
                elif command_string.lower().startswith("update"):
                    if self.cmdserver.monitorinterface == 0:
                        azcam.log("%s" % "ERROR", prefix=prefix_out)  # log reply
                        reply = "ERROR Register Process"
                    else:
                        self.cmdserver.monitorinterface.Register()
                        azcam.log("%s" % "OK", prefix=prefix_out)  # log reply
                        reply = "OK"

                    self.request.send(str.encode(reply + "\r\n"))
                    command_string = ""

                # ************************************************************************
                # process all other command_strings
                # ************************************************************************
                if command_string != "":

                    # execute command, catching all errors so server does not crash
                    reply = azcam.db.cmdserver.rcommand(command_string)

                    # log reply
                    if azcam.db.cmdserver.logcommands:
                        azcam.log(reply, prefix=prefix_out)

                    # send reply to socket
                    self.request.send(str.encode(reply + "\r\n"))

                else:
                    time.sleep(0.10)  # for telnet

            except Exception as message:  # catch everything so cmdserver never crashes
                azcam.log(f"ERROR in cmdserver: {message}")
                # try to reply but this may not work
                try:
                    self.request.send(str.encode(f"ERROR {repr(message)}\r\n"))
                except Exception:
                    pass  # OK to do nothing
                finally:
                    self.request.close()
                    break

        return

    def setup(self):
        """
        Called when new connection made.
        """

        if self.cmdserver.log_connections and self.cmdserver.verbose:
            azcam.log(
                f"Client connection made from {str(self.client_address)}",
                prefix="cmd> ",
            )

        return socketserver.BaseRequestHandler.setup(self)

    def finish(self):
        """
        Called when existing connection is closed.
        """

        if self.cmdserver.log_connections and self.cmdserver.verbose:
            azcam.log(f"Connection closed to {str(self.client_address)}")

        return socketserver.BaseRequestHandler.finish(self)

    def receive_command(self, currentclient):
        """
        Receive a string from socket until terminator is found.
        Returns a string.
        Returns empty string on error.
        :param currentclient: client ID for socket ID
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
                    msg += msg1
                    break
                msg += msg1
            except socket.error as e:
                if e.errno == 10054:  # connection closed
                    pass
                else:
                    azcam.log(f"receive_command: {e}", prefix="Err-> ")
                break

        reply = msg[:-1]  # \n
        if len(reply) == 0:
            return ""

        if reply[-1] == "\r":
            reply = msg[:-1]  # \r

        if reply is None:
            reply = ""

        return reply
