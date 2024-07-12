import psutil
import subprocess
import time
import socket


class DataItem(object):
    def __init__(self):
        self.number = 0
        self.type = 0
        self.pid = 0
        self.name = ""
        self.cmd_port = 0
        self.host = ""
        self.path = ""
        self.flags = 0
        self.watchdog = 0
        self.count = 0


class MonitorProcesses(object):
    # *************************************************************************
    # Process methods
    # *************************************************************************

    def __init__(self):
        self.debug = 1
        pass

    def register_process(self):
        """
        Register process.
        """

        self.MonitorDataSemafor.acquire()

        cnt = len(self.MonitorData)
        found = 0
        cmd_port = int(self.Recv[3])
        procPos = 0
        retVal = ""

        # Check if the process is already registerd and running in the MonitorData list
        for indx in range(cnt):
            if self.MonitorData[indx].cmd_port == cmd_port:
                if self.MonitorData[indx].pid > 0:
                    # Entry the MonitorData list found and process is probably running
                    found = 1
                    procPos = indx
                else:
                    # Entry the MonitorData list found and process is probably not running
                    found = 2
                    procPos = indx

        if found == 1:
            # Entry the MonitorData list found and process is probably running
            running = 0
            for procItem in psutil.process_iter():
                # Check if process with current ID is running
                if procItem.pid == self.MonitorData[procPos].pid:
                    running = 1

            # if running:
            if 0:
                pass
            else:
                # Data entry in the MonitorData struct should be updated
                self.MonitorData[procPos].pid = int(self.Recv[1])
                self.MonitorData[procPos].name = self.Recv[2]
                self.MonitorData[procPos].cmd_port = int(self.Recv[3])
                self.MonitorData[procPos].host = self.Recv[4]
                if self.Recv[5] != "default":
                    self.MonitorData[procPos].path = self.Recv[5]
                self.MonitorData[procPos].flags = self.Recv[6]
                self.MonitorData[procPos].watchdog = self.Recv[7]

                retVal = (
                    "Process "
                    + self.MonitorData[procPos].name
                    + " was running on port "
                    + str(self.MonitorData[procPos].cmd_port)
                )

        elif found == 2:
            # Re-register process (process was previously registered then stopped)
            retVal = (
                "Process "
                + self.MonitorData[procPos].name
                + " is running on port "
                + str(self.NewDataItem.cmd_port)
            )
            # Update pid and watchdog time
            self.MonitorData[procPos].pid = int(self.Recv[1])
            self.MonitorData[procPos].watchdog = self.Recv[7]

        elif found == 0:
            # Register new process

            self.NewDataItem = DataItem()
            recvCnt = len(self.Recv)
            try:
                if recvCnt == 8:
                    self.NewDataItem.number = self.process_number + 1
                    self.process_number += 1

                    self.NewDataItem.type = 0
                    self.NewDataItem.pid = int(self.Recv[1])
                    self.NewDataItem.name = self.Recv[2]
                    self.NewDataItem.cmd_port = int(self.Recv[3])
                    self.NewDataItem.host = self.Recv[4]
                    self.MonitorData[procPos].path = self.Recv[5]
                    self.NewDataItem.flags = self.Recv[6]
                    self.NewDataItem.watchdog = self.Recv[7]

                    # Append new DataItem
                    self.MonitorData.append(self.NewDataItem)

                    retVal = (
                        "Process "
                        + self.NewDataItem.name
                        + " is running on port "
                        + str(self.NewDataItem.cmd_port)
                    )
                else:
                    # ERROR - registration string
                    retVal = "ERROR: Process Registration string error"

            except Exception as message:
                retVal = "ERROR: Register Process " % repr(message)

        self.MonitorDataSemafor.release()

        if self.debug:
            print(retVal)

        return

    def add_process(self, addStr):
        """
        Add new process to the MonitorData struct.
        """

        self.MonitorDataSemafor.acquire()

        recvCnt = len(addStr)

        try:
            if recvCnt == 6:
                self.NewDataItem = DataItem()
                self.NewDataItem.number = self.process_number + 1
                self.process_number += 1

                self.NewDataItem.type = 0
                self.NewDataItem.pid = 0
                self.NewDataItem.name = addStr[1]
                self.NewDataItem.cmd_port = int(addStr[2])
                self.NewDataItem.host = addStr[3]
                self.NewDataItem.path = addStr[4]
                self.NewDataItem.flags = addStr[5]
                self.NewDataItem.watchdog = addStr[6]
                self.NewDataItem.count = 0

                # Append new DataItem
                self.MonitorData.append(self.NewDataItem)

                # Start the process -> the process will register itself

                path = self.NewDataItem.path

                subprocess.Popen(path, creationflags=subprocess.CREATE_NEW_CONSOLE)
                time.sleep(0.2)
                if self.debug:
                    print("Process: " + self.NewDataItem.name + " is added/registered")
        except Exception as message:
            if self.debug:
                print(f"ERROR Add/Register: {message}")

        self.MonitorDataSemafor.release()

        return

    def remove_process(self, Proccmd_port):
        """
        Remove process. Stop the process if running then remove.
        """
        cmd_port = int(Proccmd_port)

        # Check if the process is running
        if self.debug:
            print("Removing process on cmd_port " + str(cmd_port))

        self.MonitorDataSemafor.acquire()

        cnt = len(self.MonitorData)
        sleepT = 0

        pos = 0
        for indx in range(cnt):
            if self.MonitorData[indx].cmd_port == cmd_port:
                pos = indx
                procName = self.MonitorData[indx].name
                pID = self.MonitorData[indx].pid
                if pID == 0:
                    # Set sleep time in case the process is running but not updated in the DataItem list
                    sleepT = 1.0

        if pos > 0:
            update = "update\r\n"
            # Process entry found -> check if process is running
            try:
                testSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                testSocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                testSocket.settimeout(1)

                testSocket.connect((self.cmd_host, self.MonitorData[pos].cmd_port))

                retVal = testSocket.send(str.encode(update))
                testSocket.recv(1024)
                testSocket.close()

                # Wait for the process to send update to the monitor (if the process is running)
                time.sleep(sleepT)
                # Close the process
                subprocess.Popen("taskkill /F /T /pid " + str(pID))
                time.sleep(0.1)
                self.MonitorData[pos].pid = 0
                if self.debug:
                    print("Process: " + procName + " has been removed")
            except Exception:
                # Time out -> process not running
                if self.debug:
                    print("Process: " + procName + " is not responding")

        else:
            if self.debug:
                print("Process: " + procName + " not found")

        # Remove the process from the DataItem list
        del self.MonitorData[pos]

        self.MonitorDataSemafor.release()

        return

    def start_process(self, name=None, cmd_port=None):
        """
        Start process by name or command port.
        Do nothing if process is running.
        """

        if cmd_port is not None:
            cmd_port = int(cmd_port)

        self.MonitorDataSemafor.acquire()

        cnt = len(self.MonitorData)
        found = 0

        # Find the process in the MonitorData struct
        for indx in range(cnt):
            if (name is None and self.MonitorData[indx].cmd_port == cmd_port) or (
                cmd_port is None and self.MonitorData[indx].name == name
            ):
                found = 1
                if self.MonitorData[indx].pid == 0:

                    cmd = f"python {self.MonitorData[indx].path}"
                    p = subprocess.Popen(
                        cmd,
                        creationflags=subprocess.CREATE_NEW_CONSOLE,
                    )
                    p.wait()
                    # self.MonitorData[indx].pid = int(p.pid)
                    if self.debug:
                        print(
                            f"Process: {self.MonitorData[indx].name} has been started"
                        )
                else:
                    # Check if process is running
                    try:
                        testSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                        testSocket.settimeout(1)
                        testSocket.connect(
                            (self.cmd_host, self.MonitorData[indx].cmd_port)
                        )
                        testSocket.close()
                        if self.debug:
                            print(
                                f"Process: {self.MonitorData[indx].name} is already running"
                            )
                    except Exception as e:
                        # Process is not running
                        cmd = f"python {self.MonitorData[indx].path}"
                        p = subprocess.Popen(
                            cmd,
                            creationflags=subprocess.CREATE_NEW_CONSOLE,
                        )
                        p.wait()
                        # self.MonitorData[indx].pid = int(p.pid)
                        if self.debug:
                            print(
                                f"Process: {self.MonitorData[indx].name} has been started"
                            )

        if found == 0:
            if self.debug:
                print(f"Process on port {str(cmd_port)}not found")

        self.MonitorDataSemafor.release()

        return

    def stop_process(self, name=None, cmd_port=None):
        """
        Stop running process by name or command port.
        """

        if cmd_port is not None:
            cmd_port = int(cmd_port)

        self.MonitorDataSemafor.acquire()

        cnt = len(self.MonitorData)
        found = 0

        for indx in range(cnt):
            if (name is None and self.MonitorData[indx].cmd_port == cmd_port) or (
                cmd_port is None and self.MonitorData[indx].name == name
            ):
                found = 1
                if self.MonitorData[indx].pid == 0:
                    # Process ID = 0 -> process not running
                    retVal = (
                        "Process: " + self.MonitorData[indx].name + " is not running"
                    )
                else:
                    # Process ID != 0 -> process is running
                    self.MonitorData[indx].watchdog = 0
                    p = subprocess.Popen(
                        "taskkill /F /T /pid " + str(self.MonitorData[indx].pid)
                    )
                    p.wait()
                    self.MonitorData[indx].pid = 0
                    retVal = (
                        "Process: " + self.MonitorData[indx].name + " has been stopped"
                    )

        if found == 0:
            retVal = "Process: " + self.MonitorData[indx].name + " not found"
            if self.debug:
                print(retVal)

        self.MonitorDataSemafor.release()

        return

    def stop_all_processes(self):
        """
        Stop all running processes.
        """

        self.MonitorDataSemafor.acquire()

        cnt = len(self.MonitorData)
        stopCnt = 0

        for indx in range(1, cnt):
            # Check if the process is running
            if self.MonitorData[indx].pid != 0:
                # Stop the watchdog so the process will not be restarted
                self.MonitorData[indx].watchdog = 0
                self.MonitorData[indx].count = 0
                # Stop the process
                p = subprocess.Popen(
                    "taskkill /F /T /pid " + str(self.MonitorData[indx].pid)
                )
                p.wait()
                self.MonitorData[indx].pid = 0
                stopCnt += 1

        retVal = "Stopped: " + str(stopCnt) + " processes"

        self.MonitorDataSemafor.release()

        return

    def start_all_processes(self):
        """
        Start all processes previously registerd.
        """

        self.MonitorDataSemafor.acquire()

        cnt = len(self.MonitorData)
        startCnt = 0

        for indx in range(1, cnt):
            if self.MonitorData[indx].pid == 0:
                p = subprocess.Popen(
                    self.MonitorData[indx].path,
                    creationflags=subprocess.CREATE_NEW_CONSOLE,
                )
                # p.wait()
                startCnt += 1
                # The process will register itself
                if self.debug:
                    print("Starting : " + str(self.MonitorData[indx].name) + " process")

        self.MonitorDataSemafor.release()

        if self.debug:
            print("Started: " + str(startCnt) + " processes")

        return

    def restart_process(self, procNum):
        """
        Restart process. Stop it and then start.
        Use process number as the reference.
        """

        self.MonitorDataSemafor.acquire()

        cnt = len(self.MonitorData)
        procPos = 0

        for indx in range(1, cnt):
            if int(self.MonitorData[indx].number) == procNum:
                procPos = indx

        if procPos > 0:
            # Check if the process is running
            cmd_port = self.MonitorData[procPos].cmd_port
            echo = "echo\r\n"
            try:
                testSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                testSocket.settimeout(1)
                testSocket.connect((self.cmd_host, cmd_port))

                retVal = testSocket.send(str.encode(echo))
                testSocket.recv(1024)
                testSocket.close()

                # Process is running -> close it

                p = subprocess.Popen(
                    "taskkill /F /T /pid " + str(self.MonitorData[procPos].pid)
                )
                p.wait()
                self.MonitorData[procPos].pid = 0
            except Exception:
                if self.MonitorData[procPos].pid > 0:
                    self.MonitorData[procPos].pid = 0

            # Here process should be closed -> start it
            path = self.MonitorData[procPos].path
            p = subprocess.Popen(path, creationflags=subprocess.CREATE_NEW_CONSOLE)
            p.wait()
            # Give the process some time to register itself
            # time.sleep(0.3)

        else:
            pass

        self.MonitorDataSemafor.release()

        return

    def refresh_processes(self):
        """
        Refresh process. Sets PID to 0 if process does not respond.
        """

        cnt = len(self.MonitorData)

        update = "echo test\r\n"
        for indx in range(1, cnt):
            # Check if the process is running
            cmd_port = self.MonitorData[indx].cmd_port
            host = self.MonitorData[indx].host

            try:
                testSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                testSocket.settimeout(0.1)
                testSocket.connect((host, cmd_port))

                retVal = testSocket.send(str.encode(update))
                testSocket.recv(1024)
                testSocket.close()

                # Process is running -> it should update its entry in the DataItem list
                # time.sleep(0.2)
            except Exception:
                self.MonitorData[indx].pid = 0

        return

    def get_ids(self):
        """
        Return IDs of all processes.
        """

        self.MonitorDataSemafor.acquire()

        self.refresh_processes()  # validates process (PIDs)

        cnt = len(self.MonitorData)

        msg = ""
        self.process_list = []
        data_list = []
        for indx in range(cnt):
            data_list = [
                str(self.MonitorData[indx].number),
                str(self.MonitorData[indx].pid),
                self.MonitorData[indx].name,
                str(self.MonitorData[indx].cmd_port),
                self.MonitorData[indx].host,
                self.MonitorData[indx].path,
                str(self.MonitorData[indx].flags),
                str(self.MonitorData[indx].watchdog),
            ]
            msg = " ".join(data_list)
            self.process_list.append(data_list)

        self.MonitorDataSemafor.release()

        return

    def get_status(self):
        """
        Return process status.
        """

        self.refresh_processes()

        response = {}

        cnt = len(self.MonitorData)
        for indx in range(cnt):
            rsp = {}
            rsp["procnum"] = str(self.MonitorData[indx].number)
            rsp["pid"] = str(self.MonitorData[indx].pid)
            rsp["name"] = self.MonitorData[indx].name
            rsp["cmd_port"] = str(self.MonitorData[indx].cmd_port)
            rsp["host"] = self.MonitorData[indx].host
            rsp["path"] = self.MonitorData[indx].path
            rsp["flags"] = str(self.MonitorData[indx].flags)
            rsp["watchdog"] = str(self.MonitorData[indx].watchdog)

            response[f"process{indx}"] = rsp

        return response
