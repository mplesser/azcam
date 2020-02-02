"""
Contains the ControllerArc class.
"""

import os

import azcam
from azcam.server.controllers.controller import Controller
from azcam.server.controllers.camera_server import CameraServerInterface


class ControllerArc(Controller):
    """
    Defines the ARC controller commands.
    This is used for Gen1, Gen2, and Gen3 ARC controllers.
    """

    def __init__(self, *args):

        super().__init__(*args)

        self.controller_class = "arc"

        # selected video channel(s) for switched systems
        self.video_select = 0
        # video gain flag
        self.video_gain = 1
        # True to generate fake data instead of real data
        self.synthetic_data = 0

        # True to lower voltages when integrating
        self.lower_voltages = 0

        # True if image data from ControllserServer is binary (not a file)
        self.binary_image_data = 1

        # boards
        self.timing_board = ""
        self.clock_boards = [""]
        self.video_boards = [""]
        self.utility_board = ""
        # True (1) if the PCI board is installed
        self.pci_board_installed = 1
        # PCI DSP code filename
        self.pci_file = ""
        # True (1) if the timing board is installed
        self.timing_board_installed = 1
        # timing DSP code filename
        self.timing_file = ""
        # True (1) if the utlity board is installed
        self.utility_board_installed = 1
        # utility DSP code filename
        self.utility_file = ""

        # video speed setting
        self.video_speed = 1

        # True to use read lock in ControllerServer
        self.use_read_lock = 0

        # controller server object communicates with ControllerServer
        self.camserver = CameraServerInterface()

        # DSP replies
        self.DON = 0x00444F4E
        self.RDR = 0x00524452
        self.ERR = 0x00455252
        self.SYR = 0x00535952
        self.TIMEOUT = 0x544F5554
        self.READOUT = 0x524F5554
        self.RDA = 0x00524441
        self.IIA = 0x00494941

        # DSP memory locations
        self.Y_CAMSTAT = 0x0  # not used GEN1
        self.Y_NSDATA = 0x1
        self.Y_NPDATA = 0x2
        self.Y_NSBIN = 0x3
        self.Y_NPBIN = 0x4
        self.Y_NSAMPS = 0x5  # not used anymore
        self.Y_NPAMPS = 0x6  # not used anymore
        self.Y_NSCLEAR = 0x7
        self.Y_NPCLEAR = 0x8
        self.Y_NSPRESKIP = 0x9
        self.Y_NSUNDERSCAN = 0xA
        self.Y_NSSKIP = 0xB
        self.Y_NSPOSTSKIP = 0xC
        self.Y_NSOVERSCAN = 0xD
        self.Y_NPPRESKIP = 0xE
        self.Y_NPUNDERSCAN = 0xF
        self.Y_NPSKIP = 0x10
        self.Y_NPPOSTSKIP = 0x11
        self.Y_NPOVERSCAN = 0x12
        self.Y_NPXSHIFT = 0x13
        self.Y_FRAMET = 0x15
        self.Y_PREFLASH = 0x16
        self.Y_NSIMAGE = 0x1B
        self.Y_NPIMAGE = 0x1C
        self.Y_NBOXES = 0x34
        self.Y_NSBIAS = 0x35
        self.Y_NSREAD = 0x36
        self.Y_NPREAD = 0x37
        self.X_STATUS = 0x0
        self.X_OPTIONS = 0x1

        # controller boards
        self.PCIBOARD = 1
        self.TIMINGBOARD = 2
        self.UTILITYBOARD = 3

    def set_boards(self):
        """
        Sets the boards installed in an ARC controller.
        If boards are not specified in this call then controller.timing_board, .clock_boards, .video_boards,
        and .utility_board values are used.

        Timing boards:  'gen1','gen2','arc22'
        Clock boards:   'gen1','gen2','arc32'          (gen1 -> analog combo board)
        Video boards:   'gen1','gen2','arc45','arc48'  (gen1 -> analog combo board)
        Utility boards: 'gen1','gen2','gen3'           (same board but different programming)
        """

        # timing board  (required, controller_type based on this board)
        self.timing_board_installed = 1
        if self.timing_board == "gen1":
            self.controller_type = "gen1"
            self.id = "ARC_gen1"
        elif self.timing_board == "gen2":
            self.controller_type = "gen2"
            self.id = "ARC_gen2"
        elif self.timing_board == "arc22":
            self.controller_type = "gen3"
            self.id = "ARC_gen3"
        else:
            raise azcam.AzcamError(f"Unrecognized timing board {self.timing_board}")

        # utility board - optional
        if self.utility_board == "":
            self.utility_board_installed = 0
        elif self.utility_board == "gen1":
            self.utility_board_installed = 1
        elif self.utility_board == "gen2":
            self.utility_board_installed = 1
        elif self.utility_board == "gen3":
            self.utility_board_installed = 1
        else:
            raise azcam.AzcamError(
                f"Unrecognized utility board name: {self.utility_board}"
            )

        return

    def initialize(self):
        """
        Initialize controller hardware, loading PCI code as needed.
        """

        self.set_boards()

        reply = self.camserver.get("ControllerType")
        if reply[0] == "OK":
            if reply[1] == "0" or reply[1] == 0 or reply[1].lower() == "demo":
                self.interface_type = 0
                self.initialized = True
                azcam.AzcamWarning("ControllerServer running in DEMO mode")
                return
            else:
                self.interface_type = int(reply[1])
                self.initialized = True
        elif reply[0] == "DEMO":
            azcam.AzcamWarning("ControllerServer running in DEMO mode")
            self.interface_type = 0
        else:
            raise azcam.AzcamError("Could not initialize controller interface")

        # do this only once
        if self.interface_type != 4:  # don't load PCIe DSP code
            azcam.log("Loading PCI file %s" % os.path.basename(self.pci_file))
            self.upload_dsp_file(1, self.pci_file)
            azcam.log("PCI file loaded.")

        return

    # *** reset ***

    def reset_controller(self):
        """
        Issues the ResetController command to the controller.
        """

        # SYR = 0x00535952

        reply = self.camserver.command("resetcontroller")

        # if error...
        if azcam.utils.check_reply(reply):
            if reply[0] == "135":
                raise azcam.AzcamError(
                    "Controller reset error - PCI bus error 135, try resetting PCI card"
                )
            else:
                raise azcam.AzcamError(
                    "Controller reset error, check power and fibers", error_code=1
                )

        return

    def reset(self):
        """
        Reset controller using current attributes.
        May warn that the controller could not be reset.
        """

        # reset flag even is system has previously been reset
        self.is_reset = 0

        if not self.initialized:
            self.initialize()

        try:
            self.reset_controller()
        except azcam.AzcamError as e:
            # warn about power and fiber
            if e.error_code == 1:
                raise azcam.AzcamError("Controller not reset: check power and fibers")

        # restore PCIFILE keyword
        self.header.set_keyword(
            "PCIFILE",
            os.path.basename(self.pci_file),
            "PCI board DSP code filename",
            str,
        )

        if self.timing_board_installed:
            azcam.log("Loading timing file %s" % os.path.basename(self.timing_file))
            self.upload_dsp_file(2, self.timing_file)
            azcam.log("Timing board file loaded.")

        if self.utility_board_installed:
            azcam.log("Loading utility file %s" % os.path.basename(self.utility_file))
            self.upload_dsp_file(3, self.utility_file)
            azcam.log("Utility board file loaded.")

        # once code is loaded, controller is "reset"
        self.is_reset = 1

        self.set_bias_voltages()
        self.set_shutter(0)
        self.power_on()
        self.start_idle()
        self.set_video_gain(self.video_gain)
        self.set_video_speed(self.video_speed)
        self.select_video_outputs()
        self.set_roi()
        self.set_exposuretime(0)  # new was .exposure_time

        return

    # *** ROI shifting parameters  ***

    def set_roi(self):
        """
        Sets the ROI parameters values in the controller based on focalplane parameters.
        Sends parameters to the controller.
        """

        # send parameters to controller in order to do all hardware communication here
        if self.is_reset:
            self._write_controller_roi()

        # update ControllerServer for image size
        if self.is_reset:
            self.camserver.set("NumberPixelsImage", self.detpars.numpix_image)

        return

    def _write_controller_roi(self):
        """
        Write clocking parameters to controller.
        """

        # number of total pixels in image for data transfer
        self.write_memory(
            "Y", self.TIMINGBOARD, self.Y_NSIMAGE, self.detpars.numcols_image
        )
        self.write_memory(
            "Y", self.TIMINGBOARD, self.Y_NPIMAGE, self.detpars.numrows_image
        )

        # frame transfer skip size
        self.write_memory("Y", self.TIMINGBOARD, self.Y_FRAMET, self.detpars.framet)

        # number of data pixels to shift
        self.write_memory("Y", self.TIMINGBOARD, self.Y_NSDATA, self.detpars.xdata)
        self.write_memory("Y", self.TIMINGBOARD, self.Y_NPDATA, self.detpars.ydata)

        # set binning
        self.write_memory("Y", self.TIMINGBOARD, self.Y_NSBIN, self.detpars.col_bin)
        self.write_memory("Y", self.TIMINGBOARD, self.Y_NPBIN, self.detpars.row_bin)

        # write number of pixels to flush
        self.write_memory("Y", self.TIMINGBOARD, self.Y_NSCLEAR, self.detpars.xflush)
        self.write_memory("Y", self.TIMINGBOARD, self.Y_NPCLEAR, self.detpars.yflush)

        # write skipping parameters
        self.write_memory(
            "Y", self.TIMINGBOARD, self.Y_NSPRESKIP, self.detpars.xpreskip
        )
        self.write_memory(
            "Y", self.TIMINGBOARD, self.Y_NSUNDERSCAN, self.detpars.xunderscan
        )
        self.write_memory("Y", self.TIMINGBOARD, self.Y_NSSKIP, self.detpars.xskip)
        self.write_memory(
            "Y", self.TIMINGBOARD, self.Y_NSPOSTSKIP, self.detpars.xpostskip
        )
        self.write_memory(
            "Y", self.TIMINGBOARD, self.Y_NSOVERSCAN, self.detpars.xoverscan
        )

        self.write_memory(
            "Y", self.TIMINGBOARD, self.Y_NPPRESKIP, self.detpars.ypreskip
        )
        self.write_memory(
            "Y", self.TIMINGBOARD, self.Y_NPUNDERSCAN, self.detpars.yunderscan
        )
        self.write_memory("Y", self.TIMINGBOARD, self.Y_NPSKIP, self.detpars.yskip)
        self.write_memory(
            "Y", self.TIMINGBOARD, self.Y_NPPOSTSKIP, self.detpars.ypostskip
        )
        self.write_memory(
            "Y", self.TIMINGBOARD, self.Y_NPOVERSCAN, self.detpars.yoverscan
        )

        return

    def set_synthetic_data(self, Flag="real"):
        """
        Set controller to create synthetic image data.
        Flag is:
        'real' -> normal, real data
        'fake' or 'synthetic' -> create a synthetic image
        """

        # gen1 not supported
        if self.controller_type == "gen1":
            return

        # timing board X:<STATUS
        value = self.read_memory("X", self.TIMINGBOARD, self.X_STATUS)

        if Flag.lower() == "real":
            flag = 0
        elif Flag.lower() == "fake" or Flag.lower() == "synthetic":
            flag = 1
        else:
            flag = 0

        # make a synthetic image by setting bit 10 in X:<STATUS
        bits = (value & 0xFFFBFF) | ((flag & 1) << 10)
        self.write_memory("X", self.TIMINGBOARD, self.X_STATUS, bits)

        return

    # *** header ***

    def read_header(self):
        """
        Returns the current controller header.
        Does not look up info as controller header should be updated as needed during exposure process.
        Returns [Header[]]: Each element Header[i] contains the sublist (keyword, value, comment, and type).
        Example: Header[2][1] is the value of keyword 2 and Header[2][3] is its type.
        """

        # get the header
        header = []
        reply = self.header.get_all_keywords()

        for key in reply:
            reply1 = self.header.get_keyword(key)
            list1 = [key, reply1[0], reply1[1], reply1[2]]
            header.append(list1)

        return header

    # *** video ***

    def select_video_outputs(self, video_select=-1):
        """
        Send command to utlity board to select output video channel.
        video_select is video select value.
        """

        if not self.utility_board_installed:
            return

        if video_select == -1:
            video_select = self.video_select

        self.video_select = video_select  # set global, used during exposure

        if self.utility_board_installed:
            return self.write_memory("Y", 3, 1, video_select)
        else:
            return

    def set_video_gain(self, Gain):
        """
        Set video processor gain.
        For gen2 and ARC45 boards:
        Allowed valid gains are 1,2,5,10
        Also resets video speed to its current value
        For gen1:
        Gain=1 is LOW and Gain=2 is HIGH.
        Gain is video gain value.
        """

        # if self.video_boards[0]=='arc48':
        # self.header.set_keyword('DETGAIN',Gain,'Video gain setting',int)
        # self.video_gain=Gain
        # status=self.Boardcommand('SGN',self.TIMINGBOARD,Gain)

        if self.video_boards[0] == "gen1":
            if Gain == 1:
                self.board_command("LGN", self.TIMINGBOARD)
            elif Gain == 2:
                self.board_command("HGN", self.TIMINGBOARD)
            else:
                raise ValueError("Gain must be 1 or 2")

            self.video_gain = Gain
            self.header.set_keyword(
                "DETGAIN", self.video_gain, "Video gain setting", int
            )
            self.header.set_keyword(
                "VIDGAIN", self.video_gain, "Video gain setting", int
            )

        elif self.video_boards[0] == "gen2" or self.video_boards[0] == "arc45":
            if Gain == 1 or Gain == 2 or Gain == 5 or Gain == 10:
                speed = self.video_speed - 1
                if speed == 0 or speed == 1:
                    self.board_command("SGN", self.TIMINGBOARD, Gain, speed)
                else:
                    raise azcam.AzcamError("Speed must be 1 or 2")
            else:
                raise azcam.AzcamError("Gain must be 1, 2, 5, or 10")

            self.video_gain = Gain
            self.header.set_keyword(
                "DETGAIN", self.video_gain, "Video gain setting", int
            )
            self.header.set_keyword(
                "VIDGAIN", self.video_gain, "Video gain setting", int
            )
            self.header.set_keyword(
                "VIDSPEED", self.video_speed, "Video speed setting", int
            )

        return

    def set_video_speed(self, Speed):
        """
        Sets video processor speed for gen2 and arc45 video boards.  Ignored for other boards.
        This command also resets video gain to current value.
        Speed is video speed value (1 slow, 2 fast).
        Speed 0 means no change.
        """

        if not (Speed == 0 or Speed == 1 or Speed == 2):
            raise azcam.AzcamError("Speed must be 0-2")

        # only used for gen2 and arc45 video boards
        if (
            self.video_boards[0] == "gen2"
            or self.video_boards[0] == "arc45"
            or self.video_boards[0] == "sdsu2"
        ):
            self.video_speed = Speed
            speed = self.video_speed - 1
            self.board_command("SGN", self.TIMINGBOARD, self.video_gain, speed)
            self.header.set_keyword(
                "VIDSPEED", self.video_speed, "Video speed setting", int
            )

        return

    def set_video_offset(self, BoardNumber, DAC, DacValue):
        """
        Sets a video offset value.
        BoardNumber is the controller board number.
        DAC is DAC number.
        DacValue is DAC value to set.
        """

        if self.video_boards[0] == "arc48":  # assume all board types are the same
            self.board_command("SVO", self.TIMINGBOARD, BoardNumber, DAC, DacValue)
        else:
            raise azcam.AzcamError(
                "Command set_video_offset not supported for this video board"
            )

        return

    # *** shutter ***

    def set_shutter_state(self, Flag="close"):
        """
        Sets the shutter state during an exposure.
        Flag is:
        open -> close shutter during exposure
        close -> open shutter during exposure
        """

        # timing board X:<STATUS for gen2/3
        # utility board X:<OPTIONS for gen 1

        if self.controller_type == "gen1":
            reg = self.X_OPTIONS
            board = self.UTILITYBOARD
        else:
            reg = self.X_STATUS
            board = self.TIMINGBOARD

        # note: this read may error with TIMEOUT or other status and we would not know...
        value = self.read_memory("X", board, reg)

        # bit 11 defines shutter state for gen2/3
        # bit 0 for gen1

        if Flag.lower() == "open":
            flag = 1
        elif Flag.lower() == "close" or Flag.lower() == "closed":
            flag = 0
        else:
            flag = 0

        if self.controller_type == "gen1":
            bits = (value & 0xFFFFFE) | ((flag & 1) << 0)
        else:
            bits = (value & 0xFFF7FF) | ((flag & 1) << 11)

        self.write_memory("X", board, reg, bits)

        return

    def set_shutter(self, state):
        """
        Open or close controller shutter.
        """

        if self.controller_type == "gen1":
            board = self.UTILITYBOARD
        else:
            board = self.TIMINGBOARD

        if state:
            self.board_command("OSH", board)
        else:
            self.board_command("CSH", board)

        return

    # *** board commands ***

    def board_command(self, Command, BoardNumber, Arg1=-1, Arg2=-1, Arg3=-1, Arg4=-1):
        """
        Send a specific command to an ARC controller board.
        The reply from the board is often 'DON' but could be data.
        Command is the board command to send.
        BoardNumber is controller board number.
        ArgN are arguments for command.
        """

        # change 3 char ascii string to integer
        cmdnum = (ord(Command[0]) << 16) + (ord(Command[1]) << 8) + (ord(Command[2]))

        reply = self.camserver.command(
            "BoardCommand "
            + str(cmdnum)
            + " "
            + str(BoardNumber)
            + " "
            + str(Arg1)
            + " "
            + str(Arg2)
            + " "
            + str(Arg3)
            + " "
            + str(Arg4)
        )

        # check for demo mode: ["DEMO", 0]
        if reply[0] == "DEMO":
            return reply

        # convert controller DSP codes
        try:
            rep = reply[1]
            if rep.startswith("0x"):
                rep = rep.lstrip("0x")
                irep = int(rep, 16)
            else:
                irep = int(rep, 10)
        except Exception:
            return reply

        if irep == self.DON:
            reply1 = "DON"
        elif irep == self.RDR:
            reply1 = "RDR"
        elif irep == self.ERR:
            reply1 = "ERR"
        elif irep == self.SYR:
            reply1 = "SYR"
        elif irep == self.TIMEOUT:
            reply1 = "TIMEOUT"
        elif irep == self.READOUT:
            reply1 = "READOUT"
        elif irep == self.RDA:
            reply1 = "RDA"
        else:
            return reply

        return ["OK", reply1]

    def load_application(self, BoardNumber, ApplicationNumber):
        """
        Load an ARC controller DSP application.
        BoardNumber is controller board number.
        ApplicationNumber is application number to load.
        """

        self.board_command("LDA", BoardNumber, ApplicationNumber)

        return

    def flush(self, Cycles=1):
        """
        Flush or clear out the detector.
        Returns after clearing is finished which could take many seconds.
        """

        for _ in range(Cycles):
            self.board_command("CLR", self.TIMINGBOARD)

        return

    def clear_switches(self):
        """
        Clear ARC controller switches.
        """

        self.board_command("CSW", self.TIMINGBOARD)

        return

    def power_off(self):
        """
        Turn off ARC controller internal power.
        """

        if self.controller_type == "gen1":
            board = self.UTILITYBOARD
        else:
            board = self.TIMINGBOARD

        self.board_command("POF", board)

        return

    def power_on(self):
        """
        Turn on ARC controller internal power.
        """

        if self.controller_type == "gen1":
            board = self.UTILITYBOARD
        else:
            board = self.TIMINGBOARD

        self.board_command("PON", board)

        return

    def parshift(self, NumRows=1):
        """
        Shift CCD detector NumRows rows.
        NumRows is number of rows to shift, positive toward and negative away from amplifier or origin.
        """

        Y_NPXSHIFT = 0x13

        self.write_memory("Y", self.TIMINGBOARD, Y_NPXSHIFT, abs(int(NumRows)))
        if NumRows > 0:
            self.board_command("FPX", self.TIMINGBOARD)
        else:
            self.board_command("RPX", self.TIMINGBOARD)

        return

    def set_bias_number(self, BoardNumber, DAC, Type, DacValue):
        """
        Sets a bias value.
        BoardNumber is the controller board number.
        DAC is DAC number.
        Type is 'VID' or 'CLK'.
        DacValue is DAC value for voltage.
        """

        if self.video_boards[0] == "gen1":
            raise azcam.AzcamError(
                "Command set_bias_number not supported for this controller"
            )
        elif self.video_boards[0] == "arc48":  # assume all board types are the same
            self.board_command(
                "SBN", self.TIMINGBOARD, BoardNumber, Type, DAC, DacValue
            )
        elif self.video_boards[0] == "arc47":  # assume all board types are the same
            self.board_command(
                "SBN", self.TIMINGBOARD, BoardNumber, Type, DAC, DacValue
            )
        else:
            self.board_command(
                "SBN", self.TIMINGBOARD, BoardNumber, DAC, Type, DacValue
            )

        return

    def set_bias_voltages(self):
        """
        Turns on all DC biases.
        """

        self.board_command("SBV", self.TIMINGBOARD)

        return

    def set_dc_mode(self, Mode):
        """
        Sets DC mode.
        Mode is value to set.
        """

        self.board_command("SDC", self.TIMINGBOARD, Mode)

        return

    def set_mux(self, BoardNumber, MUX1, MUX2):
        """
        Sets MUX values.
        BoardNumber is controller board number.
        MUX1 is MUX 1 value.
        MUX2 us MUX 2 value.
        """

        self.board_command("SMX", self.TIMINGBOARD, BoardNumber, MUX1, MUX2)

        return

    def start_idle(self):
        """
        Start idle clocking.
        """

        self.board_command("IDL", self.TIMINGBOARD)

        return

    def stop_idle(self):
        """
        Stop idle clocking.
        """

        self.board_command("STP", self.TIMINGBOARD)

        return

    def write_control(self, Word):
        """
        Writes the Control Word.
        Word is the data to write.
        """

        self.board_command("WRC", self.TIMINGBOARD, Word)

        return

    def write_memory(self, Type, BoardNumber, Address, value):
        """
        Write a word to a DSP memory location.
        Type is P, X, Y, or R memory space.
        BoardNumber is controller board number.
        Address is memory address to write.
        value is data to write.
        """

        if Type == "P":
            arg = 0x100000
        elif Type == "X":
            arg = 0x200000
        elif Type == "Y":
            arg = 0x400000
        elif Type == "R":
            arg = 0x800000
        else:
            raise azcam.AzcamError("Invalue write_memory type")

        self.board_command("WRM", BoardNumber, arg | Address, value)

        return

    def read_memory(self, Type, BoardNumber, Address):
        """
        Read from DSP memory.
        Type is P, X, Y, or R memory space.
        BoardNumber is controller board number.
        Address is memory address to read.
        """

        if Type == "P":
            arg = 0x100000
        elif Type == "X":
            arg = 0x200000
        elif Type == "Y":
            arg = 0x400000
        elif Type == "R":
            arg = 0x800000
        else:
            raise azcam.AzcamError("Invalue Type")

        BoardNumber = int(BoardNumber)
        Address = int(Address)

        reply = self.board_command("RDM", BoardNumber, arg | Address)

        return int(reply[1])

    # *** DSP files ***

    def upload_dsp_file(self, BoardNumber, filename):
        """
        Sends DSP a file to a controllercontaining DSP code to the PCI, timing, or utility boards.
        """

        if filename == "":
            return

        csfile = self.upload_file(filename)

        self.load_file(BoardNumber, csfile)

        # set keyword for file loaded
        if BoardNumber == 1:
            self.header.set_keyword(
                "PCIFILE",
                os.path.basename(filename),
                "PCI board DSP code filename",
                str,
            )
        elif BoardNumber == 2:
            self.header.set_keyword(
                "TIMFILE",
                os.path.basename(filename),
                "Timing board DSP code filename",
                str,
            )
        elif BoardNumber == 3:
            self.header.set_keyword(
                "UTILFILE",
                os.path.basename(filename),
                "Utility board DSP code filename",
                str,
            )

        return

    def load_file(self, BoardNumber, filename):
        """
        Write a file containing DSP code to the PCI, timing, or utility boards.
        The file must be on the ControllerServer file system.
        BoardNumber is controller board number.
        filename is file to load (.lod type).
        """

        if BoardNumber == 1:
            filename = os.path.normpath(filename)
            self.camserver.load_file(1, filename)
        elif BoardNumber == 2:
            filename = os.path.normpath(filename)
            self.camserver.load_file(2, filename)
        elif BoardNumber == 3:
            filename = os.path.normpath(filename)
            self.camserver.load_file(3, filename)
        else:
            raise azcam.AzcamError("Invalid board number")

        return

    # *** files ***

    def upload_file(self, filename):
        """
        Sends a local file to the controller server to be written to its file system.
        Returns uploaded filename on controller server.
        """

        f = open(filename, "r")

        fbuffer = f.read()
        f.close()

        # send file as binary, reply is filename on controller server
        reply = self.camserver.upload_file(fbuffer)

        return reply

    # *** readout ***

    def start_readout(self):
        """
        Start readout immediately.
        Returns imemdiately, does not wait for readout to finish.
        """

        return self.read_image()

    def get_pixels_remaining(self):
        """
        Return number of remaining pixels to be read (counts down).
        """

        reply = self.camserver.get("PixelCount")
        count = int(reply[1])
        pm = max(0, self.detpars.numpix_image - count)

        return pm

    # *** exposure time ***

    def set_exposuretime(self, ExposureTime):
        """
        Write the exposure time (in seconds) to the controller.
        """

        ExposureTime = float(ExposureTime)
        self.exposure_time = ExposureTime  # new

        et_msec = int(ExposureTime * 1000)

        self.camserver.set("ExposureTime", et_msec)

        return

    def get_exposuretime(self):
        """
        Return the exposure time from the controller (in seconds).
        """

        reply = self.camserver.get("ExposureTime")  # this in msec

        return float(reply[1]) / 1000.0

    # *** misc ***

    def start_exposure(self):
        """
        Start exposure (integration).
        Returns immediately, not waiting for exposure to finish.
        """

        self.camserver.command("StartExposure")

        return

    def ioctl(self, Command):
        """
        Issue a low-level ARC controller IO command on the controller server.
        """

        return self.camserver.command("ioctl " + str(Command))

    def exposure_abort(self):
        """
        Abort an integration.
        """
        # reply=self.Boardcommand('PEX',2)               # test 16Nov12
        # reply=self.Boardcommand('AEX',2)               # test 16Nov12
        # return reply

        return self.camserver.command("AbortExposure")

    def readout_abort(self):
        """
        Abort a readout in progress.
        """

        return self.camserver.command("AbortReadout")

    def exposure_pause(self):
        """
        Pause an integration which is in progress.
        """

        return self.camserver.command("PauseExposure")

    def read_image(self):
        """
        Start readout of detector.
        """

        return self.camserver.command("ReadImage")

    def exposure_resume(self):
        """
        Resume a paused integration.
        """

        return self.camserver.command("ResumeExposure")

    def update_exposuretime_remaining(self):
        """
        Return remaining exposure time (in seconds).
        """

        reply = self.camserver.get("ExposureTimeRemaining")  # returns elapsed

        elapsed = int(reply[1])  # milliseconds, was + 1

        if elapsed < 0:
            elapsed = 0

        ExposureTimeRemaining = max(0, self.exposure_time * 1000 - elapsed) / 1000.0

        return ExposureTimeRemaining

    # **************************************************************************
    # Test Commands
    # **************************************************************************

    def test_datalink(self, BoardNumber=0, value="counter", Loops=10):
        """
        Test comminications to one or more controller boards.
        BoardNumber is the board number (0=all boards, 1=PCI, 2=Timing, 3=Utility).
        value is an integer.
        Loops is the number of times to repeat command.
        """

        BoardNumber = int(BoardNumber)
        Loops = int(Loops)

        bmin = 1

        if BoardNumber == 0:
            if self.utility_board_installed:
                bmax = 4
            else:
                bmax = 3
        else:
            bmin = BoardNumber
            bmax = BoardNumber + 1

        for board in range(bmin, bmax):
            for loop in range(Loops):
                if value == "counter":
                    value = loop
                else:
                    value = value
                reply = self.board_command("TDL", board, value)
                if int(reply[1]) == value:
                    continue
                else:
                    raise azcam.AzcamError(
                        f"Communication to board {board} failed on loop {loop}"
                    )

        return
