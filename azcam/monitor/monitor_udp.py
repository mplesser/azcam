# UDP server classes for azcammonitor

import socket
import socketserver
import time
import threading


class UDP_aux:
    """
    Aux UDP functions for azcammonitor.
    """

    def start_udp_server(self):
        """
        Starts UDP server in a separate thread.
        """

        print(f"Starting UDP server - listening on port {self.port_udp}/udp")
        regthread = threading.Thread(target=self.init_udp_server)
        regthread.start()

        return

    def stop_udp_server(self):
        """
        Stops UDP server running in separate thread.
        """

        self.UDPServer.shutdown()
        self.UDPServer_running = 0

        return

    def init_udp_server(self, port=-1):
        """
        Start UDP (ID and Register) process server.
        """
        if port == -1:
            port = self.port_udp
        else:
            self.port_udp = port

        server_address = ("", port)  # '' better than localhost when no network
        self.saddr = server_address
        self.UDPServer = ThreadedUDPServer(server_address, GetUDPRequestHandler)
        self.UDPServer.MonData = self.MonitorData
        self.UDPServer.MonDataSemafor = self.MonitorDataSemafor
        self.UDPServer.CallParser = self.udp_command_parser
        self.UDPServer.port_data = self.port_data
        self.UDPServer.Debug = self.debug
        # self.RegServer.PtrIDs = self.MonitorID

        try:
            self.UDPServer_running = 1
            self.UDPServer.serve_forever()  # blocking loop
        except Exception as message:
            self.UDPServer_running = 0
            print(
                "ERROR init_server: %s Is it already running? Exiting..."
                % repr(message)
            )

        # Exits here when server is aborted

        return

    def udp_command_parser(self, RegData):
        """
        Called when a request is received.
        """

        # Command codes:
        # 0 - send IDs
        # 1 - register process - add process to the MonitorData struct
        # 2 - add process - add a process to the MonitorData struct and start it (process will register itself)
        # 3 - remove process - remove process with given command port number
        # 4 - start process - start process with given command port number
        # 5 - stop process - stop process with given command port number
        # 6 - restart process - restart process with given command port number
        # 7 - stop all processes - stop all currently running processes
        # 8 - start all processes - start all processes with start flag set to 1
        # 9 - refresh all processes - check which processes are running (try to connect to all processes listed in the MonitorData struct)
        # 10 - start a process based on name not command port

        # Get the command code
        self.Recv = RegData.split(" ")
        cmd = int(self.Recv[0])

        if cmd == 0:
            # Send back IDs of all running processes
            self.get_ids()

        elif cmd == 1:
            # Register process
            self.register_process()

        elif cmd == 2:
            # Add process to the MonitorData struct
            self.add_process(self.Recv)

        elif cmd == 3:
            # Remove process
            if len(self.Recv) == 2:
                if int(self.Recv[1]) > 0:
                    self.remove_process(int(self.Recv[1]))
                else:
                    if self.debug:
                        print("ERROR: Can't remove AzCam Monitor process (s)")
            else:
                if self.debug:
                    print("ERROR: Wrong parameter(s)")

        elif cmd == 4:
            # Start process
            self.start_process(int(self.Recv[1]))

        elif cmd == 5:
            # Stop process
            self.stop_process(int(self.Recv[1]))

        elif cmd == 6:
            # Restart process
            self.restart_process(int(self.Recv[1]))

        elif cmd == 7:
            # Stop all processes
            self.stop_all_processes()

        elif cmd == 8:
            # Start all processes
            self.start_all_processes()

        elif cmd == 9:
            # Refresh processes
            self.refresh_processes()

        else:
            if self.debug:
                print("ERROR: Unsupported command")

        return


class ThreadedUDPServer(socketserver.ThreadingMixIn, socketserver.UDPServer):
    allow_reuse_address = True


class GetUDPRequestHandler(socketserver.BaseRequestHandler):
    def __init__(self, request, client_address, server):
        self.cmdVal = 0
        self.Resp = ""
        socketserver.BaseRequestHandler.__init__(self, request, client_address, server)

    def setup(self):
        return socketserver.BaseRequestHandler.setup(self)

    def handle(self):
        """
        Responses to the UDP reqests.
        """

        # Get remote IP address
        remote_ip = self.client_address[0]
        self.server.remote_ip = remote_ip

        try:
            # The UDP packet is already received -> get the first token (message-command)

            cmd = self.request[0].decode("utf-8")
            # First character is the command code. For now '0' - ID request, '1' - Register request
            self.cmdVal = cmd[0]

            # Call command parser
            self.Resp = self.server.CallParser(cmd)

        except Exception as message:
            print(message)

        return

    def finish(self):
        """
        Send response to the UDP request.
        """

        # Wait [100 + random] ms delay before sending response
        tm = str(time.time()).split(".")[1][0:3]
        tm = (int(tm) / 2 + 100) / 1000
        time.sleep(tm)

        # Create socket and send back ID strings
        udp_socketData = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        udp_socketData.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

        if self.Resp is None:
            self.Resp = ""

        udp_socketData.sendto(
            bytes(self.Resp, "utf-8"), (self.client_address[0], self.server.port_data)
        )
        udp_socketData.close()

        return socketserver.BaseRequestHandler.finish(self)
