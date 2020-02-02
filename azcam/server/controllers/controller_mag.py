"""
Contains the ControllerMag class.
"""

import time
import os

import azcam
from azcam.server.controllers.controller import Controller
from azcam.server.controllers.camera_server import CameraServerInterface

"""
FPGA system: Fill image buffer command

fillbuffer 0 val	-> fill buffer with fixed val
fillbuffer 1 		-> fill buffer with ramp 0-65535
fillbuffer 2 		-> fill buffer with ramp 0-lastcol
fillbuffer 3 		-> fill buffer with random values
"""


class ControllerMag(Controller):
    """
    Defines the Magellan controller commands.
    """

    def __init__(self, *args):

        super().__init__(*args)

        self.id = "mag1"

        #: selected video channel(s) for switched systems
        self.video_select = 0
        #: video gain flag
        self.video_gain = 1
        #: True to generate fake ramp data instead of real data
        self.synthetic_data = 0

        #: True to lower voltages when integrating
        self.lower_voltages = 0

        #: True if image data from ControllserServer is binary (not a file)
        self.binary_image_data = 1

        #: True to use read lock in ControllerServer
        self.use_read_lock = 0

        self.controller_class = "mag"
        self.controller_type = "mag1"

        # DSP code filename
        self.timing_file = ""

        self.camserver = CameraServerInterface()

        # new for Arduino
        # self.power = WebPowerController()

    # *** reset ***

    def reset(self):
        """
        Reset controller.
        May warn that the controller could not be reset.
        """

        # reset flag even is system has previously been reset
        self.is_reset = 0

        # close and open PCI interface every time
        self.camserver.command("CloseInterface")  # don't stop if error here

        azcam.log("Resetting interface")
        self.camserver.command("OpenInterface mag1")

        self.header.delete_all_keywords()

        azcam.log("Waiting for DSP reset")
        time.sleep(1.6)

        azcam.log("Loading DSP file %s" % self.timing_file)

        try:
            self.upload_dsp_file(2, self.timing_file)
        except azcam.AzcamError as e:
            # warn about reset
            if e.error_code == 1:
                azcam.AzcamWarning("Controller not reset: check power")
                return

        self.remove_read_lock()

        # wait for FPGA reset (104 ms)
        time.sleep(0.1)

        self.is_reset = 1

        self.set_roi()

        self.set_exposuretime(azcam.db.objects["exposure"].exposure_time)

        self.set_read_lock()

        try:
            self.camserver.command("set debug 0")
        except Exception:
            pass

        return

    def initialize(self):
        """
        Initialize the controller interface.
        """

        reply = self.camserver.get("ControllerType")
        if reply[0] == "OK":
            if reply[1] == "0" or reply[1].lower() == "demo":
                self.initialized = True
                azcam.log("ControllerServer running in DEMO mode")
                return
            else:
                self.initialized = True
                return
        else:
            raise azcam.AzcamError("Could not initialize controller")

        return

    def set_read_lock(self, Flag=-1):
        """
        Set the read lock in the ControllerServer.
        If not specified then the default value is used.
        """

        if Flag == -1:
            Flag = self.use_read_lock
        else:
            self.use_read_lock = Flag  # save for future resets

        self.camserver.set("UseReadLock", Flag)

        return

    def get_read_lock(self):
        """
        Returns the read lock value in the ControllerServer.
        """

        reply = self.camserver.get("UseReadLock")
        flag = int(reply[1])

        return flag

    def remove_read_lock(self):
        """
        Removes the read lock value in the ControllerServer.
        Should not be required.
        """

        self.camserver.command("RemoveReadLock")

        return

    # *** ROI shifting parameters  ***

    def set_roi(self):
        """
        Sets the ROI parameters values in the controller based on focalplane parameters.
        Sends parameters to the controller.
        """
        # send parameters to controller in order to do all hardware communication here
        if self.is_reset:
            cmd = (
                "SetFormat "
                + str(self.detpars.ns_total)
                + " "
                + str(self.detpars.ns_predark)
                + " "
                + str(self.detpars.ns_underscan)
                + " "
                + str(self.detpars.ns_overscan)
                + " "
                + str(self.detpars.np_total)
                + " "
                + str(self.detpars.np_predark)
                + " "
                + str(self.detpars.np_underscan)
                + " "
                + str(self.detpars.np_overscan)
                + " "
                + str(self.detpars.np_frametransfer)
            )
            self.camserver.command(cmd)

            self.camserver.command(
                "SetRoi "
                + str(self.detpars.first_col)
                + " "
                + str(self.detpars.last_col)
                + " "
                + str(self.detpars.first_row)
                + " "
                + str(self.detpars.last_row)
                + " "
                + str(self.detpars.col_bin)
                + " "
                + str(self.detpars.row_bin)
            )

        # update ControllerServer for image size
        if self.is_reset:
            self.camserver.set("NumberPixelsImage", self.detpars.numpix_image)

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

    def flush(self, Cycles=1):
        """
        Flush or clear out the detector 'Cycles' times.
        Returns after clearing is finished which could take many seconds.
        """

        for _ in range(Cycles):
            reply = self.magio("flush_ccd", 0)
            if azcam.utils.check_reply(reply):
                return reply

        return

    def set_shutter_state(self, Flag="close"):
        """
        Sets the shutter state during an exposure.
        Flag is:
        open -> close shutter during exposure
        close -> open shutter during exposure
        """

        self.camserver.set("ShutterState", Flag)

        return

    # *** testing ***

    def test(self, Loops=10):
        """
        Perform MAG controller tests.
        Loops is the number of times the test cycle is executed.
        """

        # reset
        azcam.log("Resetting controller")
        self.reset()

        # communications
        azcam.log("Testing communication")
        for loop in range(Loops):
            azcam.log("Loop %d" % loop)
            self.test_datalink(2, 98, 25)

        return

    def test_datalink(self, BoardNumber=2, value=999, Loops=1):
        """
        Test communications to controller.
        BoardNumber - board number to test - ignored!
        value - integer number to send to board.
        Loops is the number of times to repeat command.
        """

        for _ in range(Loops):
            status = self.magio("dsp_echo", value)
            if status[0] != "OK":
                raise azcam.AzcamError("Comminication with controller failed")

        return

    # *** shutter *

    def set_shutter(self, state):
        """
        Open or close controller shutter.
        """

        if state:
            self.magio("set_shutter", 1)
        else:
            self.magio("set_shutter", 0)

        return

    # *** files ***

    def upload_dsp_file(self, BoardNumber, filename):
        """
        Sends DSP a file to a controllercontaining DSP code to the PCI, timing, or utility boards.
        """

        csfile = self.upload_file(filename)

        # wait for reset
        time.sleep(1)

        self.load_file(BoardNumber, csfile)

        # set keyword for file loaded
        if BoardNumber == 2:
            self.header.set_keyword(
                "DSPFILE",
                os.path.basename(filename),
                "Timing board DSP code filename",
                str,
            )

        return

    def load_file(self, BoardNumber, filename):
        """
        Write a file containing DSP code to the controller board.
        BoardNumber - board number - ignored!
        filename - filename on server of DSP code.  S-record.
        """

        self.camserver.load_file(BoardNumber, filename)
        self.header.set_keyword(
            "DSPFILE", os.path.basename(filename), "DSP code filename", str
        )

        return

    # *** exposure time ***

    def set_exposuretime(self, ExposureTime):
        """
        Write the exposure time (in seconds) to the controller.
        """

        ExposureTime = float(ExposureTime)

        et_msec = int(ExposureTime * 1000)

        return self.camserver.set("ExposureTime", et_msec)

    def get_exposuretime(self):
        """
        Return the exposure time from the controller (in seconds).
        """

        reply = self.camserver.get("ExposureTime")  # this in msec

        return float(reply[1]) / 1000.0

    def update_exposuretime_remaining(self):
        """
        Return remaining exposure time (in seconds).
        """

        reply = self.camserver.get("ExposureTimeRemaining")
        elapsed = int(reply[1])  # milliseconds
        ExposureTimeRemaining = (
            max(0, azcam.db.objects["exposure"].exposure_time * 1000 - elapsed)
            / 1000.0
        )

        return ExposureTimeRemaining

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

    # *** misc ***

    def magio(self, Command, Parameter):
        """
        Issue a low-level MAG controller IO on the controller server.
        """
        return self.camserver.command("MagIO " + str(Command) + " " + str(Parameter))

    def start_exposure(self):
        """
        Start exposure (integration).
        Returns immediately, not waiting for exposure to finish.
        """

        return self.camserver.command("StartExposure")

    def exposure_abort(self):
        """
        Abort an integration.
        """
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

    def write_image(self, flag, file):
        """
        Write image to local disk on controller server.
        """

        return self.camserver.command("WriteImage " + str(flag) + " " + file)

    def set_configuration(self, Flag, Splits, numdet_x, numdet_y, amp_config):
        """
        Set detector configuration.
        """

        return self.camserver.command(
            "SetConfiguration "
            + str(Flag)
            + " "
            + str(Splits)
            + " "
            + str(numdet_x)
            + " "
            + str(numdet_y)
            + " "
            + str(amp_config)
        )

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
