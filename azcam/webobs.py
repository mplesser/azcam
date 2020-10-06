"""
Webobs commands for webobs application.
"""

import os
import time
import datetime
import urllib
import azcam


class WebObs(object):
    """
    API interface for server application.
    """

    def __init__(self):

        self.debug = 1  #: True to NOT execute commands
        self.number_cycles = 1  #: Number of times to run the script.
        self.move_telescope_during_readout = 0  #: True to move the telescope during camera readout
        self.increment_status = 0  #: True to increment status count if command in completed

        self.script_file = ""  #: filename of observing commands cript file

        self.lines = []
        self.commands = []  # list of dictionaries for each command to be executed
        self.current_line = -1  # current line being executed

        self.current_filter = ""  # current filter

        self._abort_script = 0  #: internal abort flag to stop scipt
        self._abort_gui = 0  #: internal abort flag to stop GUI
        self._paused = 0  #: internal pause flag
        self._do_highlight = 1  #: internal highlight row flag
        self.message = ""

        self.upload_folder = "/data/uploads"

        self.data = []  # list of dictionaries for each command to be executed

        setattr(azcam.db, "webobs", self)
        azcam.db.cmd_objects["webobs"] = self
        azcam.db.cli_cmds["webobs"] = self

    def initialize(self):
        """
        Initialize webobs.
        """

        # set defaults from parfile
        self.script_file = azcam.db.genpars.get_par(
            "webobs", "script_file", "default", "", "observing_script.txt"
        )

        number_cycles = azcam.db.genpars.get_par("webobs", "number_cycles", "default", "", 1)
        self.number_cycles = int(number_cycles)

        self.column_order = [
            "cmdnumber",
            "status",
            "command",
            "argument",
            "exptime",
            "type",
            "title",
            "numexp",
            "filter",
            "ra",
            "dec",
            "epoch",
            "expose_flag",
            "movetel_flag",
            "steptel_flag",
            "movefilter_flag",
            "movefocus_flag",
        ]

        self.column_number = {}
        for i, x in enumerate(self.column_order):
            self.column_number[i] = x

        return

    def test(self):
        """
        Just a test method.
        """

        return "I do nothing"

    def watchdog(self):
        """
        Update timestamp indicating GUI in running and highlight current table row.
        """

        precision = 0

        dateTimeObj = datetime.datetime.now()
        timestamp = str(dateTimeObj)

        if precision >= 6:
            pass
        elif precision == 0:
            timestamp = timestamp[:-7]
        else:
            tosecs = timestamp[:-7]
            frac = str(round(float(timestamp[-7:]), precision))
            timestamp = tosecs + frac

        # check abort
        if self._abort_gui:
            self.status("Aborting GUI")
            print("Aborting observe GUI")
            return

        if self._paused:
            self.status("Script PAUSED")

        # highlights
        if self._do_highlight:
            row = self.current_line  # no race condition
            if row != -1:
                if self._paused:
                    self.highlight_row(row, 2)
                elif self._abort_script:
                    self.highlight_row(row, 3)
                else:
                    self.highlight_row(row, 1)
                # clear previous row
                if row > 0:
                    self.highlight_row(row - 1, 0)
            self._do_highlight = 0

        # print(f"watchdog on line {self.current_line}")
        data = {
            "timestamp": timestamp,
            "currentrow": self.current_line,
            "message": self.message,
        }

        return data

    def load_script(self, scriptname):
        """
        Load script into table.
        """

        scriptname = urllib.parse.unquote(scriptname)
        scriptfile = os.path.join(self.upload_folder, os.path.basename(scriptname))
        scriptfile = os.path.normpath(scriptfile)

        self.read_file(scriptfile)
        self.parse()

        table_list = []
        for row in self.commands:
            l1 = list(row.values())
            table_list.append(l1[1:-3])  # ignore some cols

        return table_list

    def read_file(self, script_file):
        """
        Read an observing script file.

        :param script_file: full path name of script file.
        :return: None
        """

        self.script_file = script_file

        # read file
        with open(self.script_file, "r") as sfile:
            all_lines = sfile.readlines()

        # save all lines
        self.lines = []
        self.commands = []  # list of dictionaries, one for each line
        for line in all_lines:
            if line == "\n":
                continue
            line = line.strip()
            self.lines.append(line)

        return

    def parse(self):
        """
        Parse current line set into self.commands dictionary.
        The script file must have already been read using read_file().

        :return: None
        """

        for linenumber, line in enumerate(self.lines):

            expose_flag = 0
            movetel_flag = 0
            steptel_flag = 0
            movefilter_flag = 0
            movefocus_flag = 0
            wave = ""
            focus = ""
            ra = ""
            dec = ""
            raNext = ""
            decNext = ""
            epoch = ""
            exptime = 0.0
            imagetype = ""
            arg = ""
            title = ""
            numexposures = 0
            status = 0

            tokens = azcam.utils.parse(line)

            # comment line, special case
            if line.startswith("#") or line.startswith("!") or line.startswith("comment"):
                cmd = "comment"
                arg = line[1:].strip()

            # if the first token is a number, it is a status flag - save and remove from parsing
            elif tokens[0].isdigit():
                status = int(tokens[0])
                line = line.lstrip(tokens[0]).strip()
                tokens = tokens[1:]  # reset tokens to not include status
                cmd = tokens[0].lower()
            else:
                status = -1  # indicates no status value
                cmd = tokens[0].lower()

            # comment
            if cmd == "comment":
                pass

            # prompt, use quotes for string
            elif cmd == "prompt":
                arg = tokens[1]

            # print
            elif cmd == "print":
                arg = tokens[1]

            elif cmd == "prompt":
                arg = tokens[1]

            # take a normal observation
            elif cmd == "obs":
                # obs 10.5 object "M31 field F" 1 U 00:36:00 40:30:00 2000.0
                exptime = float(tokens[1])
                imagetype = tokens[2]
                title = tokens[3].strip('"')  # remove double quotes
                numexposures = int(tokens[4])
                expose_flag = 1
                movetel_flag = 0
                if len(tokens) > 5:
                    wave = tokens[5].strip('"')
                    movefilter_flag = 1
                if len(tokens) > 6:
                    ra = tokens[6]
                    dec = tokens[7]
                    if len(tokens) > 8:
                        epoch = tokens[8]
                    else:
                        epoch = 2000.0
                    movetel_flag = 1

            # take test images
            elif cmd == "test":
                # test 10.5 object "M31 field F" 1 U 00:36:00 40:30:00 2000.0
                exptime = float(tokens[1])
                imagetype = tokens[2]
                title = tokens[3].strip('"')
                numexposures = int(tokens[4])
                expose_flag = 1
                movetel_flag = 0
                if len(tokens) > 5:
                    wave = tokens[5].strip('"')
                    movefilter_flag = 1
                if len(tokens) > 6:
                    ra = tokens[6]
                    dec = tokens[7]
                    if len(tokens) > 8:
                        epoch = tokens[8]
                    else:
                        epoch = 2000.0
                    movetel_flag = 1

            # move focus position in relative steps from current position
            elif cmd == "stepfocus":
                # stepfocus RelativeSteps
                focus = float(tokens[1])
                # reply=step_focus(focus)
                movefocus_flag = 1

            # move filter
            elif cmd == "movefilter":
                # movefilter FilterName
                wave = tokens[1]
                movefilter_flag = 1

            # move telescope to absolute RA DEC EPOCH
            elif cmd == "movetel":
                # movetel ra dec
                ra = tokens[1]
                dec = tokens[2]
                epoch = tokens[3]
                movetel_flag = 1

            # slew telescope to absolute RA DEC EPOCH
            elif cmd == "slewtel":
                # slewtel ra dec
                ra = tokens[1]
                dec = tokens[2]
                epoch = tokens[3]
                movetel_flag = 1

            # move telescope relative RA DEC
            elif cmd == "steptel":
                # steptel raoffset decoffset
                raoffset = tokens[1]
                decoffset = tokens[2]
                ra = raoffset
                dec = decoffset
                movetel_flag = 1

            # delay N seconds
            elif cmd == "delay":
                delay = float(tokens[1])
                arg = delay

            # quit script
            elif cmd == "quit":
                pass

            else:
                azcam.log("command not recognized on line %03d: %s" % (linenumber, cmd))

            # get next RA and DEC if next line is obs command
            raNext = ""
            decNext = ""
            epochNext = ""
            if linenumber == len(self.lines) - 1:  # last line
                pass
            else:
                lineNext = self.lines[linenumber + 1]
                tokensNext = azcam.utils.parse(lineNext)
                lentokNext = len(tokensNext)
                if lentokNext != 0:
                    cmdNext = tokensNext[0].lower()
                    if cmdNext == "obs" and lentokNext > 6:
                        raNext = tokensNext[6]
                        decNext = tokensNext[7]
                        epochNext = tokensNext[8]
                    else:
                        pass

            data1 = {}
            data1["line"] = line
            data1["cmdnumber"] = linenumber
            data1["status"] = status
            data1["command"] = cmd
            data1["argument"] = arg
            data1["exptime"] = exptime
            data1["type"] = imagetype
            data1["title"] = title
            data1["numexp"] = numexposures
            data1["filter"] = wave
            data1["ra"] = ra
            data1["dec"] = dec
            data1["epoch"] = epoch
            data1["expose_flag"] = expose_flag
            data1["movetel_flag"] = movetel_flag
            data1["steptel_flag"] = steptel_flag
            data1["movefilter_flag"] = movefilter_flag
            data1["movefocus_flag"] = movefocus_flag
            data1["focus"] = focus
            data1["ra_next"] = raNext
            data1["dec_next"] = decNext
            self.commands.append(data1)

        return

    def run(self):
        """
        Execute the commands in the script command dictionary.

        :return: None
        """
        self._abort_script = 0

        # save pars to be changed
        # impars = {}

        # log start info
        s = time.strftime("%Y-%m-%d %H:%M:%S")
        azcam.log("Observing script started: %s" % s)

        # begin execution loop
        offsets = []
        for loop in range(self.number_cycles):

            if self.number_cycles > 1:
                azcam.log("*** Script cycle %d of %d ***" % (loop + 1, self.number_cycles))

            for linenumber, command in enumerate(self.commands):

                stop = 0

                line = command["line"]
                status = command["status"]

                azcam.log("Command %03d/%03d: %s" % (linenumber, len(self.commands), line))

                # execute the command
                try:
                    reply = self.execute_command(linenumber)
                except Exception as e:
                    azcam.log(e)
                    pass

                keyhit = azcam.utils.check_keyboard(0)
                if keyhit == "q":
                    reply = "QUIT"
                    stop = 1

                if reply == "STOP":
                    azcam.log("STOP after line %d" % linenumber)
                    stop = 1
                elif reply == "QUIT":
                    stop = 1
                    azcam.log("QUIT after line %d" % linenumber)
                else:
                    azcam.log("Reply %03d: %s" % (linenumber, reply))

                if stop or self._abort_script:
                    break

                # check for pause
                while self._paused:
                    self.wait4highlight()
                    time.sleep(1)

        # finish
        self.current_line = 0
        # azcam.api.restore_imagepars(impars)
        self._abort_script = 0  # clear abort status

        return

    def execute_command(self, linenumber):
        """
        Execute one command.

        :param linenumber: Line number to execute, from command buffer.
        """

        # wait for highlighting of current row
        self.current_line = linenumber

        command = self.commands[linenumber]
        if self.debug:
            print(f"mock executing line {self.current_line}")
            time.sleep(2)
            return "OK"

        reply = "OK"

        expose_flag = 0
        movetel_flag = 0
        steptel_flag = 0
        movefilter_flag = 0
        movefocus_flag = 0
        wave = ""
        ra = ""
        dec = ""
        epoch = ""
        exptime = ""
        imagetype = ""
        arg = ""
        title = ""
        numexposures = ""
        status = 0

        # get command and all parameters
        line = command["line"]
        cmd = command["command"]

        status = command["status"]
        arg = command["argument"]
        exptime = command["exptime"]
        imagetype = command["type"]
        title = command["title"]
        numexposures = command["numexp"]
        wave = command["filter"]
        ra = command["ra"]
        dec = command["dec"]
        raNext = command["ra_next"]
        decNext = command["dec_next"]
        epoch = command["epoch"]
        epochNext = command["epoch"]  # debug
        expose_flag = command["expose_flag"]
        movetel_flag = command["movetel_flag"]
        steptel_flag = command["steptel_flag"]
        movefilter_flag = command["movefilter_flag"]
        movefocus_flag = command["movefocus_flag"]

        exptime = float(exptime)
        numexposures = int(numexposures)
        expose_flag = int(expose_flag)
        movetel_flag = int(movetel_flag)
        steptel_flag = int(steptel_flag)
        movefilter_flag = int(movefilter_flag)
        movefocus_flag = int(movefocus_flag)

        # perform some immediate actions

        # comment
        if cmd == "comment":  # do nothing
            return "OK"

        elif cmd == "obs":
            pass

        elif cmd == "test":
            pass

        elif cmd == "offset":
            pass

        elif cmd == "stepfocus":
            reply = azcam.api.step_focus(arg)

        elif cmd == "movefilter":
            pass

        elif cmd == "movetel":
            pass

        # display message and then change command, for now
        elif cmd == "slewtel":
            cmd = "movetel"
            azcam.log("Enable slew for next telescope motion")
            reply = azcam.utils.prompt("Waiting...")
            return "OK"

        elif cmd == "steptel":
            azcam.log("offsetting telescope in arcsecs - RA: %s, DEC: %s" % (raoffset, decoffset))
            try:
                reply = azcam.api.telescope.offset(raoffset, decoffset)
                return "OK"
            except azcam.AzcamError as e:
                return f"ERROR {e}"

        elif cmd == "delay":
            time.sleep(float(arg))
            return "OK"

        elif cmd == "print":
            azcam.log(arg)
            return "OK"

        elif cmd == "prompt":
            azcam.log("prompt not available: %s" % arg)
            return "OK"

        elif cmd == "quit":
            azcam.log("quitting...")
            return "QUIT"

        else:
            azcam.log("script command %s not recognized" % cmd)

        # perform actions based on flags

        # move focus
        if movefocus_flag:
            azcam.log("Moving to focus: %s" % focus)
            if not self.DummyMode:
                reply = azcam.api.set_focus(focus)
                # reply, stop = check_exit(reply, 1)
                stop = self._abort_gui
                if stop:
                    return "STOP"
                reply = azcam.api.get_focus()
                azcam.log("Focus reply:: %s" % repr(reply))
                # reply, stop = check_exit(reply, 1)
                stop = self._abort_gui
                if stop:
                    return "STOP"

        # set filter
        if movefilter_flag:
            if wave != self.current_filter:
                azcam.log("Moving to filter: %s" % wave)
                if not self.debug:
                    azcam.api.set_filter(wave)
                    reply = azcam.api.get_filter()
                    self.current_filter = reply
            else:
                azcam.log("Filter %s already in beam" % self.current_filter)

        # move telescope to RA and DEC
        if movetel_flag:
            azcam.log("Moving telescope now to RA: %s, DEC: %s" % (ra, dec))
            if not self.debug:
                try:
                    reply = azcam.api.telescope.move(ra, dec, epoch)
                except azcam.AzcamError as e:
                    return f"ERROR {e}"

        # make exposure
        if expose_flag:
            for i in range(numexposures):
                if steptel_flag:
                    azcam.log(
                        "Offsetting telescope in RA: %s, DEC: %s"
                        % (offsets[i * 2], offsets[i * 2 + 1])
                    )
                    if not self.debug:
                        reply = TelescopeOffset(offsets[i * 2], offsets[i * 2 + 1])
                        # reply, stop = check_exit(reply, 1)
                        stop = self._abort_gui
                        if stop:
                            return "STOP"

                if cmd != "test":
                    azcam.api.set_par("imagetest", 0)
                else:
                    azcam.api.set_par("imagetest", 1)
                filename = azcam.api.get_image_filename()

                if cmd == "test":
                    azcam.log(
                        "test %s: %d of %d: %.3f sec: %s"
                        % (imagetype, i + 1, numexposures, exptime, filename)
                    )
                else:
                    azcam.log(
                        "%s: %d of %d: %.3f sec: %s"
                        % (imagetype, i + 1, numexposures, exptime, filename)
                    )

                if self.move_telescope_during_readout and (raNext != ""):

                    if i == numexposures - 1:  # Apr15
                        doMove = 1
                    else:
                        doMove = 0

                    if 1:
                        # if not self.debug:
                        reply = azcam.api.expose1(exptime, imagetype, title)  # immediate return
                        time.sleep(2)  # wait for Expose process to start
                        cycle = 1
                        while 1:
                            flag = azcam.api.get_par("ExposureFlag")
                            if flag is None:
                                azcam.log("Could not get exposure status, quitting...")
                                stop = 1
                                return "STOP"
                            if (
                                flag == azcam.db.exposureflags["EXPOSING"]
                                or flag == azcam.db.exposureflags["SETUP"]
                            ):
                                flagstring = "Exposing"
                            elif flag == azcam.db.exposureflags["READOUT"]:
                                flagstring = "Reading"
                                if doMove:
                                    check_header = 1
                                    while check_header:
                                        header_updating = int(
                                            azcam.api.get_par("exposureupdatingheader")
                                        )
                                        if header_updating:
                                            azcam.log("Waiting for header to finish updating...")
                                            time.sleep(0.5)
                                        else:
                                            check_header = 0
                                    azcam.log(
                                        "Moving telescope to next field - RA: %s, DEC: %s"
                                        % (raNext, decNext)
                                    )
                                    try:
                                        reply = azcam.api.telescope.move_start(
                                            raNext, decNext, epochNext
                                        )
                                    except azcam.AzcamError as e:
                                        return f"ERROR {e}"
                                    doMove = 0
                            elif flag == azcam.db.exposureflags["WRITING"]:
                                flagstring = "Writing"
                            elif flag == azcam.db.exposureflags["NONE"]:
                                flagstring = "Finished"
                                break
                            # azcam.log('Checking Exposure Status (%03d): %10s\r' % (cycle,flagstring))
                            time.sleep(0.1)
                            cycle += 1
                else:
                    if not self.debug:
                        azcam.api.expose(exptime, imagetype, title)

                # reply, stop = check_exit(reply)
                stop = self._abort_gui
                if stop:
                    return "STOP"

                keyhit = azcam.utils.check_keyboard(0)
                if keyhit == "q":
                    return "QUIT"

        return "OK"

    def edit_script(self):
        """
        Edit the select a script file.
        """

        filename = str(self.ui.plainTextEdit_filename.toPlainText())

        os.startfile(filename)  # opens notepad for .txt files

        return

    def cell_changed(self, item):
        """
        Called when a table cell is changed.
        """

        row = item.row()
        col = item.column()
        newvalue = item.text()

        colnum = self.column_number[col]

        self.commands[row][colnum] = newvalue

        return

    def highlight_row(self, row_number, flag):
        """
        Highlight or unhighlight a row of the GUI table during execution.
        """

        numcols = self.ui.tableWidget_script.columnCount()

        # higlight row being executed
        if flag == 0:
            # uncolor row
            for col in range(numcols):
                item = self.ui.tableWidget_script.item(row_number, col)
                item.setBackground(QtGui.QColor(QtCore.Qt.transparent))
                self.ui.tableWidget_script.repaint()

        elif flag == 1:
            # green
            for col in range(numcols):
                item = self.ui.tableWidget_script.item(row_number, col)
                item.setBackground(QtGui.QColor(0, 255, 0))
                self.ui.tableWidget_script.repaint()

        elif flag == 2:
            # alt color for pause
            for col in range(numcols):
                item = self.ui.tableWidget_script.item(row_number, col)
                item.setBackground(QtGui.QColor(255, 255, 153))
                self.ui.tableWidget_script.repaint()

        elif flag == 3:
            # alt color for abort
            for col in range(numcols):
                item = self.ui.tableWidget_script.item(row_number, col)
                item.setBackground(QtGui.QColor(255, 100, 100))
                self.ui.tableWidget_script.repaint()

        return

    def wait4highlight(self):
        """
        Wait for row to highlight.
        """

        time.sleep(1.0)

        return

    def status(self, message):
        """
        Display text in status field.
        """

        self.message = message

        return

    def abort_script(self):
        """
        Abort a running script as soon as possible.
        """

        self._abort_script = 1
        self.status("Abort detected")

        # self.wait4highlight()
        self._do_highlight = 1

        return

    def pause_script(self):
        """
        Pause a running script as soon as possible.
        """

        self._paused = not self._paused
        if self._paused:
            s = "Pause detected"
        else:
            s = "Running..."
        self.status(s)

        # self.wait4highlight()
        self._do_highlight = 1

        return

    def start(self):
        """
        Show the GUI.
        """

        self.initialize()

        # show GUI
        self.show()
        self.status("ready...")

        # set window location
        self.move(50, 50)

        return

    def stop(self):
        """
        Stop the GUI for the Observe class.
        """

        self._abort_gui = 1

        return


webobs = WebObs()
