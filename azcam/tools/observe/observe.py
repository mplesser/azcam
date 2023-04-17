"""
AzCam observing scripts.
"""


import os
import time
import typing
import azcam
from azcam.tools.tools import Tools
from azcam.tools.console_tools import ConsoleTools


class Observe(Tools):
    """
    Defines the azcam observing script class.
    """

    def __init__(self, tool_id="observe", description="azcam observing scripts"):
        super().__init__(tool_id, description)

        # these parameters can be set remotely
        self.mock = 1  # True to not  execute actual commands
        self.verbose = 1  # True to print extended info during execution
        self.number_cycles = 1  # number of times to run the script
        self.move_telescope_during_readout = 0  # True to move the telescope during camera readout

        self.increment_status = 0  # True to increment status count if command in completed
        self._abort_gui = 0  # internal abort flag to stop
        self._paused = 0  # internal pause flag
        self._do_highlight = 0  # internal highlight row flag

        self.script_file = ""  # filename of observing commands script file

        self.lines = []
        self.commands = []  # list of dictionaries for each command to be executed
        self.current_line = -1  # current line being executed

        self.current_filter = ""  # current filter

        self._abort_script = 0  # internal abort flag to stop scipt

        self.data = []  # list of dictionaries for each command to be executed

        #: focus tool for motion - usually "instrument" or "telescope"
        self.focus_component = "instrument"

        self.gui_mode = 0

    def _get_coord_mode(self, ra, dec, az, alt):
        """
        Return coordinate mode.
        """

        # determine ra/dec or az/alt mode
        mode = 0  # 0 do nothing, 1 radec, 2 azalt
        if ra is None and dec is None:
            if az is None and alt is None:
                mode = 0  # all 0 do nothing
            else:
                mode = 2  # azalt mode
        else:
            if az is not None or alt is not None:
                raise azcam.AzcamError("conflicting radec/azalt parameters")
            else:
                mode = 1  # radec mode

        return mode

    def obs(
        self,
        et: float = None,
        imagetype: str = None,
        title: str = None,
        numexposures: int = 1,
        filter: float = None,
        az: str = None,
        alt: str = None,
        ra: str = None,
        dec: str = None,
        epoch: str = 2000.0,
    ):
        """
        Take an observation.
        """

        mode = self._get_coord_mode(ra, dec, az, alt)

        if self.mock:
            print("obs")
            return

        return

    def test(
        self,
        et: float = None,
        imagetype: str = None,
        title: str = None,
        numexposures: int = 1,
        filter: float = None,
        az: str = None,
        alt: str = None,
        ra: str = None,
        dec: str = None,
        epoch: str = 2000.0,
    ):
        """
        Take a test observation.
        """

        mode = self._get_coord_mode(ra, dec, az, alt)

        if self.mock:
            print("test")
            return

        return

    def stepfocus(self, step: float = 1.0):
        """
        Step the focus in relative units.
        """

        focusstep = float(step)

        if self.mock:
            print(f"stepfocus: {focusstep}")
            return

        return

    def steptel(
        self,
        rastep: float = None,
        decstep: float = None,
        azstep: float = None,
        altstep: float = None,
    ):
        """
        Step the telesocpe in relative arcseconds in either ra/dec or az/alt.
        Specify only ra/dec or az/alt values.
        """

        mode = self._get_coord_mode(rastep, decstep, azstep, altstep)

        ra_telstep = float(rastep)
        dec_telstep = float(decstep)
        az_telstep = float(azstep)
        alt_telstep = float(altstep)

        if self.mock:
            if mode == 0:
                print(f"steptel 0 0")
            elif mode == 1:
                print(f"steptel: ra: {ra_telstep} dec: {dec_telstep}")
            elif mode == 2:
                print(f"steptel: az {az_telstep} alt: {alt_telstep}")
            return

        if mode == 0:
            return
        elif mode == 1:
            pass  # do radec command
        elif mode == 2:
            pass  # do azalt command

        return

    def movetel(
        self, ra: str = None, dec: str = None, az: str = None, alt: str = None, epoch: str = 2000.0
    ):
        """
        Move the teleccope in either ra/dec or az/alt.
        Specify only ra/dec or az/alt values.
        """

        mode = self._get_coord_mode(ra, dec, az, alt)

        # change this to time strings
        if mode == 0:
            pass
        elif mode == 1:
            telra = float(ra) if ra is not None else 0.0
            teldec = float(dec) if dec is not None else 0.0
        elif mode == 2:
            telaz = float(az) if az is not None else 0.0
            telalt = float(alt) if alt is not None else 0.0

        if self.mock:
            if mode == 0:
                print(f"movetel 0 0")
                return
            elif mode == 1:
                print(f"movetel: ra: {telra} dec: {teldec} epoch:{epoch}")
            elif mode == 2:
                print(f"movetel: az: {telaz} alt: {telalt} epoch:{epoch}")

        return

    def movefilter(self, name: str = None):
        """
        Move the filter.
        """

        if self.mock:
            print(f"movefilter: {filter}")
            return

        return

    def delay(self, seconds: float = None):
        """
        Delay by a number of seconds.
        """

        deltime = float(seconds) if seconds is not None else 0.0

        if self.mock:
            print(f"delay: {deltime} seconds")
        else:
            time.sleep(deltime)

        return

    def message(self, message: str = None):
        """
        Display a message.
        """

        print(f"message: {message}")

        return

    def set(self, parameter: str = None, value: typing.Any = None):
        """
        Set a paramater.
        """

        if self.mock:
            print("set")
            return

        if parameter not in [
            "mock",
            "verbose",
            "azalt_mode",
            "move_telescope_during_readout",
            "number_cycles",
        ]:
            azcam.AzcamError(f"parameter {parameter} for set not recognized")

        if parameter == "mock":
            self.mock = int(value)
        elif parameter == "verbose":
            self.verbose = int(value)
        elif parameter == "move_telescope_during_readout":
            self.move_telescope_during_readout = int(value)
        elif parameter == "number_cycles":
            self.number_cycles = int(value)

        return

    def quit(self):
        """
        Quit script execution as soon as possible.
        """

        if self.mock:
            print("quit")
            return

        return

    # ##############################################################################

    def _get_focus(
        self,
        focus_id: int = 0,
    ):
        if self.focus_component == "instrument":
            return azcam.db.tools["instrument"].get_focus(focus_id)
        elif self.focus_component == "telescope":
            return azcam.db.tools["telescope"].get_focus(focus_id)

    def _set_focus(self, focus_value: float, focus_id: int = 0, focus_type: str = "absolute"):
        if self.focus_component == "instrument":
            return azcam.db.tools["instrument"].set_focus(focus_value, focus_id, focus_type)
        elif self.focus_component == "telescope":
            return azcam.db.tools["telescope"].set_focus(focus_value, focus_id, focus_type)

    def read_file(self, script_file):
        """
        Read an observing script file into the .lines list.

        Args:
            script_file: full path name of script file.
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

    def _parse(self):
        """
        Parse current line set into self.commands dictionary.
        The script file must have already been read using read_file().
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

            # immediately set a value
            elif cmd == "set":
                attribute = tokens[1]
                value = tokens[2]
                arg = " ".join(tokens[1:])

                if attribute == "mock":
                    self.mock = int(value)
                elif attribute == "azalt_mode":
                    self.azalt_mode = int(value)
                    if self.gui_mode:
                        self.ui.checkBox_azalt.setChecked(self.azalt_mode)
                elif attribute == "move_telescope_during_readout":
                    self.move_telescope_during_readout = int(value)
                elif attribute == "number_cycles":
                    self.number_cycles = int(value)
                    if self.gui_mode:
                        self.ui.spinBox_loops.setValue(self.number_cycles)
                continue

            # print
            elif cmd == "print":
                arg = tokens[1]

            # issue a raw server which should be in single quotes
            elif cmd == "azcam":
                arg = tokens[1]

            # take a normal observation
            elif cmd == "obs":
                # obs 10.5 object "M31 field F" 1 U 00:36:00 40:30:00 2000.0
                exptime = float(tokens[1])
                imagetype = tokens[2]
                title = tokens[3].strip('"')  # remove double quotes
                numexposures = int(tokens[4])
                expose_flag = 1
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
                else:
                    ra = ""
                    dec = ""
                    epoch = ""
                    movetel_flag = 0

            # take test images
            elif cmd == "test":
                # test 10.5 object "M31 field F" 1 U 00:36:00 40:30:00 2000.0
                exptime = float(tokens[1])
                imagetype = tokens[2]
                title = tokens[3].strip('"')
                numexposures = int(tokens[4])
                expose_flag = 1
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
                else:
                    ra = ""
                    dec = ""
                    epoch = ""
                    movetel_flag = 0

            # move focus position in relative steps from current position
            elif cmd == "stepfocus":
                # stepfocus RelativeSteps
                focus = float(tokens[1])
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
                ra = tokens[1]
                dec = tokens[2]
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
                        try:
                            raNext = tokensNext[6]
                            decNext = tokensNext[7]
                            epochNext = tokensNext[8]
                        except Exception:
                            raNext = ""
                            decNext = ""
                            epochNext = ""
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
            data1["focus"] = focus
            data1["ra"] = ra
            data1["dec"] = dec
            data1["ra_next"] = raNext
            data1["dec_next"] = decNext
            data1["epoch"] = epoch
            data1["epoch_next"] = epochNext
            data1["expose_flag"] = expose_flag
            data1["movetel_flag"] = movetel_flag
            data1["steptel_flag"] = steptel_flag
            data1["movefilter_flag"] = movefilter_flag
            data1["movefocus_flag"] = movefocus_flag
            self.commands.append(data1)

        return

    def log(self, message):
        """
        Log a message.

        Args:
            message: string to be logged.
        """

        azcam.log(message)

        return

    def run(self):
        """
        Execute the commands in the script command dictionary.
        """

        self._abort_script = 0

        # save pars to be changed
        impars = {}
        azcam.utils.save_imagepars(impars)

        # log start info
        s = time.strftime("%Y-%m-%d %H:%M:%S")
        self.log("Observing script started: %s" % s)

        # begin execution loop
        for loop in range(self.number_cycles):
            if self.number_cycles > 1:
                self.log("*** Script cycle %d of %d ***" % (loop + 1, self.number_cycles))

            for linenumber, command in enumerate(self.commands):
                stop = 0

                line = command["line"]
                status = command["status"]

                self.log("Command %03d/%03d: %s" % (linenumber, len(self.commands), line))

                # execute the command
                reply = self.execute_command(linenumber)

                keyhit = azcam.utils.check_keyboard(0)
                if keyhit == "q":
                    reply = "QUIT"
                    stop = 1

                if reply == "STOP":
                    self.log("STOP after line %d" % linenumber)
                    stop = 1
                elif reply == "QUIT":
                    stop = 1
                    self.log("QUIT after line %d" % linenumber)
                else:
                    self.log("Reply %03d: %s" % (linenumber, reply))

                if stop or self._abort_script:
                    break

                # check for pause
                if self.gui_mode:
                    while self._paused:
                        self.wait4highlight()
                        time.sleep(1)

        # finish
        azcam.utils.restore_imagepars(impars)
        self._abort_script = 0  # clear abort status

        return

    def execute_command(self, linenumber):
        """
        Execute one command.

        Args:
            linenumber: Line number to execute, from command buffer.
        """

        # wait for highlighting of current row
        if self.gui_mode:
            self.current_line = linenumber
            self.wait4highlight()

        command = self.commands[linenumber]

        # if self.mock:
        #     time.sleep(0.5)
        #     return "OK"

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

        # get command and all parameters
        cmd = command["command"]

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
        epochNext = command["epoch_next"]
        expose_flag = command["expose_flag"]
        movetel_flag = command["movetel_flag"]
        steptel_flag = command["steptel_flag"]
        movefilter_flag = command["movefilter_flag"]
        movefocus_flag = command["movefocus_flag"]

        focus = command["focus"]

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

        elif cmd == "stepfocus":
            reply = self._step_focus(arg)

        elif cmd == "movefilter":
            pass

        elif cmd == "movetel":
            pass

        # display message and then change command, for now
        elif cmd == "slewtel":
            cmd = "movetel"
            self.log("Enable slew for next telescope motion")
            reply = azcam.utils.prompt("Waiting...")
            return "OK"

        elif cmd == "steptel":
            self.log("offsetting telescope in arcsecs - RA: %s, DEC: %s" % (ra, dec))
            try:
                reply = azcam.db.tools["server"].command(f"telescope.offset {ra} {dec}")
                return "OK"
            except azcam.AzcamError as e:
                return f"ERROR {e}"

        elif cmd == "delay":
            time.sleep(float(arg))
            return "OK"

        elif cmd == "azcam":
            try:
                reply = azcam.db.tools["server"].command(arg)
                return reply
            except azcam.AzcamError as e:
                return f"ERROR {e}"

        elif cmd == "print":
            self.log(arg)
            return "OK"

        elif cmd == "prompt":
            self.log("prompt not available: %s" % arg)
            return "OK"

        elif cmd == "quit":
            self.log("quitting...")
            return "QUIT"

        else:
            self.log("script command %s not recognized" % cmd)

        # perform actions based on flags

        # move focus
        if movefocus_flag:
            self.log("Moving to focus: %s" % focus)
            if not self.mock:
                reply = self._set_focus(focus)
                stop = self._abort_gui
                if stop:
                    return "STOP"
                reply = self._get_focus()
                self.log("Focus reply:: %s" % repr(reply))
                stop = self._abort_gui
                if stop:
                    return "STOP"

        # set filter
        if movefilter_flag:
            if wave != self.current_filter:
                self.log("Moving to filter: %s" % wave)
                if not self.mock:
                    azcam.db.tools["instrument"].set_filter(wave)
                    reply = azcam.db.tools["instrument"].get_filter()
                    self.current_filter = reply
            else:
                self.log("Filter %s already in beam" % self.current_filter)

        # move telescope
        if movetel_flag:
            if not self.mock:
                try:
                    if self.azalt_mode:
                        self.log("Moving telescope now to Az: %s, Alt: %s" % (ra, dec))
                        reply = azcam.db.tools["server"].command(f"telescope.move_azalt {ra} {dec}")
                    else:
                        self.log("Moving telescope now to RA: %s, DEC: %s" % (ra, dec))
                        reply = azcam.db.tools["server"].command(f"telescope.move {ra} {dec}")
                except azcam.AzcamError as e:
                    return f"ERROR {e}"
            else:
                if self.azalt_mode:
                    self.log("Moving telescope now to Az: %s, Alt: %s" % (ra, dec))
                else:
                    self.log("Moving telescope now to RA: %s, DEC: %s" % (ra, dec))

        # make exposure
        if expose_flag:
            for i in range(numexposures):
                if cmd != "test":
                    azcam.db.parameters.set_par("imagetest", 0)
                else:
                    azcam.db.parameters.set_par("imagetest", 1)
                filename = azcam.db.tools["exposure"].get_filename()

                if cmd == "test":
                    self.log(
                        "test %s: %d of %d: %.3f sec: %s"
                        % (imagetype, i + 1, numexposures, exptime, filename)
                    )
                else:
                    self.log(
                        "%s: %d of %d: %.3f sec: %s"
                        % (imagetype, i + 1, numexposures, exptime, filename)
                    )

                if self.move_telescope_during_readout and (raNext != ""):
                    if i == numexposures - 1:  # Apr15
                        doMove = 1
                    else:
                        doMove = 0

                    if 1:
                        reply = azcam.db.tools["exposure"].expose1(
                            exptime, imagetype, title
                        )  # immediate return
                        time.sleep(2)  # wait for Expose process to start
                        cycle = 1
                        while 1:
                            flag = azcam.db.parameters.get_par("ExposureFlag")
                            if flag is None:
                                self.log("Could not get exposure status, quitting...")
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
                                            azcam.db.parameters.get_par("exposureupdatingheader")
                                        )
                                        if header_updating:
                                            self.log("Waiting for header to finish updating...")
                                            time.sleep(0.5)
                                        else:
                                            check_header = 0
                                    self.log(
                                        "Moving telescope to next field - RA: %s, DEC: %s"
                                        % (raNext, decNext)
                                    )
                                    try:
                                        reply = azcam.db.tools["server"].command(
                                            "telescope.move_start %s %s %s"
                                            % (raNext, decNext, epochNext)
                                        )
                                    except azcam.AzcamError as e:
                                        return f"ERROR {e}"
                                    doMove = 0
                            elif flag == azcam.db.exposureflags["WRITING"]:
                                flagstring = "Writing"
                            elif flag == azcam.db.exposureflags["NONE"]:
                                flagstring = "Finished"
                                break
                            time.sleep(0.1)
                            cycle += 1
                else:
                    if not self.mock:
                        azcam.db.tools["exposure"].expose(exptime, imagetype, title)

                # reply, stop = check_exit(reply)
                stop = self._abort_gui
                if stop:
                    return "STOP"

                keyhit = azcam.utils.check_keyboard(0)
                if keyhit == "q":
                    return "QUIT"

        return "OK"


class ObserveConsole(ConsoleTools):
    """
    Observe tool for consoles.
    Usually implemented as the "observe" tool.
    """

    def __init__(self) -> None:
        super().__init__("observe")

    def delay(self, seconds: float = None):
        """
        Delay by a number of seconds.

        :param seconds:

        """

        return azcam.db.tools["server"].command(f"{self.objname}.delay {seconds}")
