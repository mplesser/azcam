import threading
import time


class MonitorWatchdog(object):
    # *************************************************************************
    # Watchdog methods
    # *************************************************************************

    def start_watchdog(self):
        """
        Starts watchdog server in a separate thread.
        """
        watchdogthread = threading.Thread(target=self.init_watchdog)
        watchdogthread.start()

        return

    def stop_watchdog(self):
        """
        Stops watchdog loop running in separate thread.
        """

        # self.timer_server.shutdown()
        self.timer_server_running = 0

        return

    def init_watchdog(self):
        """
        Start Timer/watchdog server.
        """

        self.timer_server = self.watchdog_loop()
        self.timer_server.MonData = self.MonitorData
        self.timer_server.MonDataSemafor = self.MonitorDataSemafor

        try:
            self.timer_server_running = 1
            self.timer_server.serve_forever()  # blocking loop
        except Exception as message:
            self.timer_server_running = 0
            print(
                "ERROR init_watchdog: %s Is it already running? Exiting..."
                % repr(message)
            )
        return

    def watchdog_loop(self):
        """
        watchdog main loop.
        """

        while True:
            # Check the counter regularly
            time.sleep(0.5)

            self.MonitorDataSemafor.acquire()

            # Get the total count of MonitorData items
            cnt = len(self.MonitorData)

            # Check if all active processes are running
            for indx in range(1, cnt):
                # Check the watchdog value
                watchdog = int(self.MonitorData[indx].watchdog)
                if watchdog > 0:
                    # Check if the process is running
                    self.MonitorData[indx].count = int(self.MonitorData[indx].count) + 1

                    if int(self.MonitorData[indx].count) > watchdog * 2:
                        self.MonitorData[indx].count = 0

                        pid = self.MonitorData[indx].pid
                        running = 0
                        for procItem in psutil.process_iter():
                            # Check if process with current ID is running
                            if procItem.pid == pid:
                                running = 1

                        if running == 0:
                            # Process is not running -> restart the process
                            path = self.MonitorData[indx].path
                            print(
                                "Process "
                                + self.MonitorData[indx].name
                                + " on port "
                                + self.MonitorData[indx].cmd_port
                                + " is not responding. Restarting process..."
                            )
                            subprocess.Popen(
                                path, creationflags=subprocess.CREATE_NEW_CONSOLE
                            )

                        else:
                            # Check if the process is responding (use TCP connection)
                            cmd_port = self.MonitorData[indx].cmd_port
                            try:
                                testSocket = socket.socket(
                                    socket.AF_INET, socket.SOCK_STREAM
                                )
                                testSocket.settimeout(1)
                                testSocket.connect((self.cmd_host, cmd_port))

                                echo = "echo\r\n"

                                testSocket.send(str.encode(echo))
                                testSocket.recv(1024)
                                testSocket.close()
                                # Process is responding -> do nothing
                            except Exception:
                                # Keep the path to the process
                                path = self.MonitorData[indx].path

                                print(
                                    "Process "
                                    + self.MonitorData[indx].name
                                    + " on port "
                                    + self.MonitorData[indx].cmd_port
                                    + " is not responding. Terminating process..."
                                )
                                # Process is not responding -> stop it and start again
                                subprocess.Popen(
                                    "taskkill /F /T /pid "
                                    + str(self.MonitorData[indx].pid)
                                )
                                time.sleep(0.1)

                                # Start the process. Process should register itself and it will keep the same spot in the MonitorData struct.
                                subprocess.Popen(
                                    path, creationflags=subprocess.CREATE_NEW_CONSOLE
                                )

            self.MonitorDataSemafor.release()

        return
