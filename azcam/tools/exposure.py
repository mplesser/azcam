"""
Contains the base Exposure class.
"""

import datetime
import os
import threading
import time
import ast
from typing import Union, List, Optional

import numpy

import azcam
import azcam.exceptions
from azcam.tools.exposure_filename import Filename
from azcam.tools.exposure_sendimage import SendImage
from azcam.tools.exposure_obstime import ObsTime
from azcam.header import Header, ObjectHeaderMethods
from azcam.image import Image
from azcam.tools.tools import Tools


class Exposure(Tools, Filename, ObjectHeaderMethods):
    """
    The base exposure tool.
    Usually implemented as the "exposure" tool.
    Only required attributes and stub methods are defined here. Additional
    methods and attributes are added as needed in exposure-specific classes
    which should inherit this class.
    """

    def __init__(self, tool_id="exposure", description=None):
        Tools.__init__(self, tool_id, description)
        Filename.__init__(self)

        self.sendimage = SendImage()
        self.obstime = ObsTime()
        self.image = Image()

        # exposure flags, may be used anywhere
        self.exposureflags = {
            "NONE": 0,
            "EXPOSING": 1,
            "ABORT": 2,
            "PAUSE": 3,
            "RESUME": 4,
            "READ": 5,
            "PAUSED": 6,
            "READOUT": 7,
            "SETUP": 8,
            "WRITING": 9,
            "GUIDEERROR": 10,
            "ERROR": 11,
        }

        azcam.db.exposureflags = self.exposureflags

        self.exposureflags_rev = {v: k for k, v in self.exposureflags.items()}

        # exposure flag defining state of current exposure
        self.exposure_flag = self.exposureflags["NONE"]

        # current image type, 'zero', 'object', 'dark', 'flat', 'ramp', etc
        self.image_type = "zero"
        # default imagetypes
        self.image_types = ["zero", "object", "flat", "dark"]
        # dictionary of shutter states for imagetypes {imagetype:ShutterState}
        self.shutter_dict = {
            "zero": 0,
            "object": 1,
            "flat": 1,
            "dark": 0,
            "ramp": 1,
        }
        # True to flush detector before exposures
        self.flush_array = 1
        # True to display an image after readout
        self.display_image = 1
        # True to send image to remote image server after readout
        self.send_image = 0

        self.message = ""  # exposure status message
        self.guide_status = 0
        self.guide_image_copy = 0

        # TdiMode flag, 0=not in TDI mode, 1=TDI mode
        self.tdi_mode = 0
        # TdiDelay mode
        self.tdi_delay = 5
        # ParDelay mode
        self.par_delay = 5

        # guide mode
        self.guide_mode = 0

        # True when exposure type is a comparision, to turn on comp lamps
        self.comp_exposure = 0
        # True when in a comparision exposure sequence so lamps stay on
        self.comp_sequence = 0

        # True when exposure is completed, then toggled off
        self.completed = 0

        # requested exposure time in seconds
        self.exposure_time = 1.0
        # remaining exposure time in seconds for an exposure in progress
        self.exposure_time_remaining = 0.0
        # actual elapsed exposure time in seconds of last/current exposure
        self.exposure_time_actual = 0.0
        # exposure time saved for each exposure, used for zeros
        self.exposure_time_saved = 0.0
        # total time in seconds an exposure was paused
        self.paused_time = 0.0
        # starting clock paused time of exposure
        self.paused_time_start = 0.0
        # actual elapsed dark time of last/current exposure
        self.dark_time = 0.0
        # starting clock dark time of exposure
        self.dark_time_start = 0.0

        # True when in an exposure sequence
        self.is_exposure_sequence = 0
        # current exposure sequence number
        self.exposure_sequence_number = 1
        # total number of exposures in sequence
        self.exposure_sequence_total = 1
        # delay between sequence exposures in seconds
        self.exposure_sequence_delay = 0.0
        # sequence flush flag: -1=> use FlushArray, 0==> flush all, 1=> flush only first exposure, 2=> no flush
        self.exposure_sequence_flush = 0

        # remaining number of pixels to read for an exposure in progress
        self.pixels_remaining = 0

        # True to update headers in a thread to save time
        self.update_headers_in_background = 0
        self.updating_header = 0

        # True to save image file after exposure
        self.save_file = 1

        # file types
        self.filetypes = {"FITS": 0, "MEF": 1, "BIN": 2, "ASM": 6}
        self.filetype = self.filetypes["MEF"]

        # Exposure title
        self.title = ""

        # True to make image title the same as image type
        self.auto_title = 0

        # deinterlace mode; 1 = generic mode; x = ODI mode
        self.deinterlace_mode = 1

        # temporary image files
        self.temp_image_file = ""

        # filename of current image
        self.last_filename = ""

        # write data asynchronously
        self.write_async = 0

        # create the exposure header
        self.header = Header("Exposure")

        # flag indicating ROI has been changed
        self.new_roi = 0
        self.header.set_header("exposure", 1)

        # data order
        self.data_order = []

        self.imageheaderfile = ""

        self.pgress = 0  # debug

    def initialize(self):
        """
        Initialize exposure.
        """

        # call initialize() method on other tools
        for tool in azcam.db.tools_init:
            azcam.db.tools[tool].initialize()

        self.is_initialized = 1

        return

    def reset(self):
        """
        Reset exposure tool.
        """

        # initialize only once
        if not self.is_initialized:
            self.initialize()

        # set temporary filenames
        self.set_temp_files()

        # setup for exposures
        self.is_exposure_sequence = 0
        self.exposure_sequence_number = 1
        self.set_auto_title()
        azcam.db.abortflag = 0
        self.save_file = 1
        self.exposure_flag = self.exposureflags["NONE"]

        # call reset() method on other tools
        for tool in azcam.db.tools_reset:
            try:
                azcam.db.tools[tool].reset()
            except Exception as e:
                raise azcam.exceptions.AzcamError(f"Could not reset {tool}: {e}")

        return

    # **********************************************************************************************
    # Exposure control
    # **********************************************************************************************

    def start(self):
        """
        Allow custom operations at start of exposure.
        """

        try:
            azcam.db.tools["instrument"].exposure_start()
        except KeyError:
            pass
        try:
            azcam.db.tools["telescope"].exposure_start()
        except KeyError:
            pass

        return

    def finish(self):
        """
        Allow custom operations at end of exposure.
        """

        try:
            azcam.db.tools["instrument"].exposure_finish()
        except KeyError:
            pass
        try:
            azcam.db.tools["telescope"].exposure_finish()
        except KeyError:
            pass

        return

    def finished(self):
        if self.completed:
            return 1
        else:
            return 0

    def get_exposureflag(self):
        return [self.exposure_flag, self.exposureflags_rev[self.exposure_flag]]

    def test(self, exposure_time=0.0, shutter=0):
        """
        Make a test exposure.
        exposure_time is the exposure time in seconds
        shutter is 0 for closed and 1 for open
        title is the image title.
        """

        old_testimage = self.test_image
        old_imagetype = self.image_type
        old_exposuretime = self.exposure_time
        self.test_image = 1

        if shutter:
            shutter_state = "object"
        else:
            shutter_state = "dark"

        self.expose(exposure_time, shutter_state, "test image")

        self.test_image = old_testimage
        self.image_type = old_imagetype
        self.exposure_time = old_exposuretime

        return

    def expose(self, exposure_time=-1, imagetype="", title=""):
        """
        Make a complete exposure.
        exposure_time is the exposure time in seconds
        imagetype is the type of exposure ('zero', 'object', 'flat', ...)
        title is the image title.
        """

        azcam.db.abortflag = 0

        # allow custom operations
        self.start()

        azcam.log("Exposure started")

        # if last exposure was aborted, warn before clearing flag
        if self.exposure_flag == self.exposureflags["ABORT"]:
            azcam.exceptions.warning("Previous exposure was aborted")

        # begin
        if self.exposure_flag != self.exposureflags["ABORT"]:
            self.begin(exposure_time, imagetype, title)

        # integrate
        if self.exposure_flag != self.exposureflags["ABORT"]:
            self.integrate()

        # readout
        if (
            self.exposure_flag != self.exposureflags["ABORT"]
            and self.exposure_flag == self.exposureflags["READ"]
        ):
            try:
                self.readout()
            except azcam.exceptions.AzcamError:
                pass
        # end
        if self.exposure_flag != self.exposureflags["ABORT"]:
            self.end()

        self.exposure_flag = self.exposureflags["NONE"]
        self.completed = 1
        azcam.log("Exposure finished")

        # allow custom operations
        self.finish()

        return

    def expose1(
        self, exposure_time: float = -1, image_type: str = "", image_title: str = ""
    ):
        """
        Make a complete exposure with immediate return to caller.

        :param exposure_time: the exposure time in seconds
        :param image_type: type of exposure ('zero', 'object', 'flat', ...)
        :param image_title: image title, usually surrounded by double quotes
        """

        arglist = [exposure_time, image_type, image_title]
        thread = threading.Thread(target=self.expose, name="expose1", args=arglist)
        thread.start()

        return

    def guide(self, number_exposures=1):
        """
        Make a complete guider exposure sequence.
        NumberExposures is the number of exposures to make, -1 loop forever
        """

        AbortFlag = 0

        number_exposures = int(number_exposures)

        # system must be reset once before an exposure can be made
        if not azcam.db.tools["controller"].is_reset:
            azcam.db.tools["controller"].reset()

        # parameters for faster operation
        flusharray = self.flush_array
        azcam.log("Guide started")

        # this loop continues even for errors since data is sent to a seperate client receiving images
        LoopCount = 0
        while True:
            if 0:
                self.begin(exposure_time=-1, imagetype="object", title="guide image")

                # integrate
                self.integrate()

                # readout
                if self.exposure_flag == self.exposureflags["READ"]:
                    try:
                        self.readout()
                        self.guide_status = 1  # image read OK
                        self.guide_image_copy = self.image
                    except Exception:
                        self.guide_status = (
                            2  # image not read OK, but don't stop guide loop
                        )
                        self.image = self.guide_image_copy

                # image writing
                self.end()
                self.exposure_flag = self.exposureflags["NONE"]
            else:
                self.expose(-1, "object", "guide image")

            AbortFlag = azcam.db.abortflag
            if AbortFlag:
                break

            if number_exposures == -1:
                continue
            else:
                LoopCount += 1

            if LoopCount >= number_exposures:
                break

        # finish
        self.guide_status = 0
        self.flush_array = flusharray

        if AbortFlag:
            azcam.exceptions.warning("Guide aborted")
        else:
            azcam.log("Guide finished")

        return

    def guide1(self, number_exposures=1):
        """
        Make a complete guider exposure with an immediate return.
        NumberExposures is the number of exposures to make, -1 loop forever
        """

        arglist = [number_exposures]
        thread = threading.Thread(target=self.guide, name="guide1", args=arglist)
        thread.start()

        return

    def begin(self, exposure_time=-1, imagetype="", title=""):
        """
        Initiates the first part of an exposure, through image flushing.
        exposure_time is in seconds.
        imagetype is one of zero, object, flat, dark, ramp, ...
        """

        # system must be reset once before an exposure can be made
        x = self.is_exposure_sequence  # save this flag which is lost by reset
        if not azcam.db.tools["controller"].is_reset:
            self.reset()
            self.is_exposure_sequence = x

        # set exposure flag
        self.exposure_flag = self.exposureflags["SETUP"]

        # reset flags as new data coming
        self.image.valid = 0
        self.image.is_written = 0
        self.image.toggle = 0
        self.image.assembled = 0

        # clear the image header
        self.image.header.delete_all_items()
        self.image.header.delete_all_keywords()

        # update image size
        try:
            self.set_roi()  # bug?
        except Exception:
            pass

        if self.new_roi:
            self.image.data = numpy.empty(
                shape=[
                    self.image.focalplane.numamps_image,
                    self.image.focalplane.numpix_amp,
                ],
                dtype="<u2",
            )
            self.new_roi = 0

        # imagetype
        if imagetype != "":
            self.image_type = imagetype
        self.image.image_type = self.image_type
        imagetype = self.image_type.lower()

        # exposure times
        exposure_time = float(exposure_time)
        self.exposure_time_saved = self.exposure_time
        if exposure_time >= 0:
            self.exposure_time = float(exposure_time)
        if imagetype == "zero":
            self.exposure_time = 0.0
        self.paused_time = 0.0  # reset paused time
        self.paused_time_start = 0.0  # reset paused start time
        self.exposure_time_remaining = self.exposure_time

        # update title and set OBJECT keyword using title
        self.set_image_title(title)

        # send exposure time to controller
        self.set_exposuretime(self.exposure_time)

        # set total number of pixels to readout
        self.pixels_remaining = self.image.focalplane.numpix_image

        # set CompExposure flag for any undefined image types (comp names)
        if imagetype not in self.image_types:
            self.comp_exposure = 1
        else:
            self.comp_exposure = 0

        if not self.guide_mode:  # for speed
            try:
                shutterstate = self.shutter_dict[imagetype]
            except KeyError:
                shutterstate = 1  # other types are comps, so open shutter
            azcam.db.tools["controller"].set_shutter_state(shutterstate)

        self.delete_keyword("COMPLAMP")

        # set comp lamps, turn on, set keyword
        if self.comp_exposure and azcam.db.tools["instrument"].is_enabled:
            if self.comp_sequence:  # lamps already on
                pass
            else:
                azcam.db.tools["instrument"].set_comps(imagetype)
                if not azcam.db.tools["instrument"].shutter_strobe:
                    azcam.db.tools["instrument"].comps_on()
            lampnames = " ".join(azcam.db.tools["instrument"].get_comps())
            self.set_keyword("COMPLAMP", lampnames, "Comp lamp names", "str")
            self.set_keyword("IMAGETYP", "comp", "Image type", "str")
            azcam.db.tools["instrument"].comps_delay()  # delay for lamp warmup
        else:
            if not self.guide_mode:
                try:
                    if (azcam.db.tools["instrument"] is not None) and azcam.db.tools[
                        "instrument"
                    ].is_enabled:
                        azcam.db.tools["instrument"].set_comps()  # reset
                except KeyError:
                    pass
                self.set_keyword("IMAGETYP", imagetype, "Image type", "str")

        # update all headers with current data
        if self.update_headers_in_background:
            headerthread = threading.Thread(
                target=self.update_headers, name="updateheaders", args=[]
            )
            headerthread.start()
        else:
            self.update_headers()

        # flush detector
        if self.flush_array:
            self.flush()
        else:
            azcam.db.tools["controller"].stop_idle()

        # record current time and date in header
        self.record_current_times()

        return

    def integrate(self):
        """
        Integration.
        """

        return

    def readout(self):
        """
        Exposure readout.
        """

        return

    def end(self):
        """
        Completes an exposure by writing file and displaying image.
        """

        return

    def start_readout(self):
        """
        Start immediate readout of an exposing image.
        Returns immediately, not waiting for readout to finish.
        Really sets a flag which is read in expose().
        """

        if self.exposure_flag != self.exposureflags["NONE"]:
            self.exposure_flag = self.exposureflags["READ"]

        return

    def flush(self, Cycles=1):
        """
        Flush/clear detector.
        Cycles is the number of times to flush the detector.
        """

        azcam.log("Flushing")

        return azcam.db.tools["controller"].flush(int(Cycles))

    def sequence(self, number_exposures=1, flush_array_flag=-1, delay=-1):
        """
        Take an exposure sequence.
        Uses pre-set exposure time, image type and image title.
        NumberExposures is the number of exposures to make.
        FlushArrayFlag defines detector flushing:
        -1 => current value defined by exposure.exposure_sequence_flush [default]
        0 => flush for each exposure
        1 => flush after first exposure only
        2 => no flush
        Delay => delay between exposures in seconds
        -1 => no change
        """

        AbortFlag = 0
        self.is_exposure_sequence = 1
        self.exposure_sequence_number = 1
        self.exposure_sequence_total = number_exposures

        number_exposures = int(number_exposures)
        flush_array_flag = int(flush_array_flag)
        if delay != -1 and delay != "-1":
            self.exposure_sequence_delay = float(delay)

        # set flushing
        currentflush = self.flush_array
        if flush_array_flag == -1:
            flush_array_flag = self.exposure_sequence_flush

        if flush_array_flag == 0 or flush_array_flag == 1:
            FlushArray = True
        else:
            FlushArray = False
        self.flush_array = FlushArray

        self.comp_sequence = (
            self.check_comparison_imagetype()
            and azcam.db.tools["instrument"].is_enabled
        )

        if self.comp_sequence:
            azcam.log("Starting comparison sequence")
            azcam.db.tools["instrument"].set_comps(self.image_type)
            if azcam.db.tools["instrument"].shutter_strobe:
                pass  # these instruments use shutter to turn on comps
            else:
                azcam.db.tools["instrument"].comps_on()
            azcam.db.tools[
                "instrument"
            ].comps_delay()  # delay for lamp warmup if needed

        for i in range(number_exposures):
            if i > 0:
                time.sleep(self.exposure_sequence_delay)

            if i > 0 and flush_array_flag == 1:
                self.flush_array = False

            self.expose(self.exposure_time, self.image_type, self.title)

            # check
            if azcam.db.abortflag:
                break

            # sequence may have been stopped
            if not self.is_exposure_sequence:
                break

            self.exposure_sequence_number += 1

        # turn off comps
        if self.comp_sequence:
            azcam.db.tools["instrument"].comps_off()
            self.comp_sequence = 0

        self.flush_array = currentflush
        self.is_exposure_sequence = 0
        self.exposure_sequence_number = 1

        azcam.db.abortflag = 0

        return

    def sequence1(self, number_exposures=1, flush_array_flag=-1, delay=-1):
        """
        Take an exposure sequence.
        Uses pre-set exposure time, image type and image title.
        number_exposures is the number of exposures to make.
        flush_array_flag defines detector flushing:
        -1 => current value defined by exposure.exposure_sequence_flush [default]
        0 => flush for each exposure
        1 => flush after first exposure only
        2 => no flush
        Delay => delay between exposures in seconds
        -1 => no change
        """

        arglist = [number_exposures, flush_array_flag, delay]
        thread = threading.Thread(target=self.sequence, name="sequence1", args=arglist)
        thread.start()

        return

    def pause(self):
        """
        Pause an exposure in progress (integration only).
        Really sets a flag which is read in expose().
        """

        self.paused_time_start = time.time()  # save paused clock time

        if self.exposure_flag != self.exposureflags["NONE"]:
            self.exposure_flag = self.exposureflags["PAUSE"]

        return

    def resume(self):
        """
        Resume a paused exposure.
        Really sets a flag which is read in expose().
        """

        self.paused_time = (
            time.time() - self.paused_time_start
        ) + self.paused_time  # total paused time in seconds

        if self.exposure_flag != self.exposureflags["NONE"]:
            self.exposure_flag = self.exposureflags["RESUME"]

        return

    def abort(self):
        """
        Abort an exposure in progress.
        Really sets a flag which is read in expose().
        """

        if self.exposure_flag != self.exposureflags["NONE"]:
            self.exposure_flag = self.exposureflags["ABORT"]

        return

    def set_shutter(self, state: int = 0, shutter_id: int = 0):
        """
        Open or close a shutter.

        :param state:
        :param shutter_id: Shutter ID flag

          * 0 => controller default shutter.
          * 1 => instrument default shutter.
        """

        if shutter_id == 0:
            azcam.db.tools["controller"].set_shutter(state)
        elif shutter_id == 1:
            azcam.db.tools["instrument"].set_shutter(state)

        return

    def parshift(self, number_rows: int):
        """
        Shift sensor by number_rows.

        :param number_rows: number of rows to shift (positive is toward readout, negative is away)
        """

        number_rows = int(float(number_rows))

        azcam.db.tools["controller"].parshift(number_rows)

        return

    # ***************************************************************************
    # pixel counter
    # ***************************************************************************

    def get_pixels_remaining(self):
        """
        Return number of remaining pixels to be read (counts down).
        """

        reply = azcam.db.tools["controller"].get_pixels_remaining()
        self.pixels_remaining = reply

        return reply

    # ***************************************************************************
    # exposure time
    # ***************************************************************************

    def get_exposuretime(self):
        """
        Return current exposure time in seconds.
        """

        if azcam.db.tools["controller"].is_reset:
            self.exposure_time = azcam.db.tools["controller"].get_exposuretime()

        return self.exposure_time

    def set_exposuretime(self, exposure_time: float):
        """
        Set current exposure time in seconds.
        """

        self.exposure_time = float(exposure_time)
        self.exposure_time_actual = self.exposure_time  # may be changed later

        azcam.db.tools["controller"].set_exposuretime(self.exposure_time)

        self.header.set_keyword(
            "EXPREQ", exposure_time, "Exposure time requested (seconds)", "float"
        )
        self.header.set_keyword(
            "EXPTIME", exposure_time, "Exposure time (seconds)", "float"
        )

        return

    def get_exposuretime_remaining(self):
        """
        Return remaining exposure time (in seconds).
        """

        if azcam.db.tools["controller"].is_reset:
            self.exposure_time_remaining = azcam.db.tools[
                "controller"
            ].update_exposuretime_remaining()

        return self.exposure_time_remaining

    # **********************************************************************************************
    # header
    # **********************************************************************************************
    def record_current_times(self):
        """
        Record the current times and data info in the header.
        """

        # get current time and date
        self.obstime.update(0)

        # format should be YYYY-MM-DDThh:mm:ss.sss  ISO 8601
        self.header.set_keyword(
            "DATE-OBS", self.obstime.date[0], "UTC shutter opened", "str"
        )
        self.header.set_keyword(
            "DATE", self.obstime.date[0], "UTC date and time file writtten", "str"
        )  # OLD
        self.header.set_keyword(
            "TIME-OBS", self.obstime.ut[0], "UTC at start of exposure", "str"
        )
        self.header.set_keyword(
            "UTC-OBS", self.obstime.ut[0], "UTC at start of exposure", "str"
        )
        self.header.set_keyword(
            "UT", self.obstime.ut[0], "UTC at start of exposure", "str"
        )
        self.header.set_keyword(
            "TIMESYS", self.obstime.time_system[0], "Time system", "str"
        )
        self.header.set_keyword(
            "TIMEZONE", self.obstime.time_zone[0], "Local time zone", "str"
        )
        self.header.set_keyword(
            "LOCTIME",
            self.obstime.local_time[0],
            "Local time at start of exposure",
            "str",
        )

        return

    def update_headers(self):
        """
        Update all headers, reading current data.
        """

        # set flag that update is in progress
        self.updating_header = 1

        # all headers to be updated must be in azcam.db['headers']
        for objectname in azcam.db.headers:
            if (
                objectname == "controller"
                or objectname == "system"
                or objectname == "exposure"
                or objectname == "focalplane"
            ):
                continue
            try:
                azcam.db.tools[
                    objectname
                ].update_header()  # dont crash so all headers get updated
            except Exception as e:
                azcam.log(f"could not get {objectname} header: {e}")

        # update focalplane header which is not in db
        self.image.focalplane.update_header()

        # try to update system header last
        if "system" in azcam.db.headers:
            try:
                azcam.db.headers["system"].update_header()
            except Exception:
                pass

        # set flag that update is finished
        self.updating_header = 0

        return

    # ***************************************************************************
    # misc
    # ***************************************************************************

    def set_auto_title(self, flag=-1):
        """
        Set the AutoTitle flag so that image title matches lowercase imagetype.
        """

        if flag != -1:
            self.auto_title = flag
            self.set_image_title()

        if flag != 0:
            self.set_image_title()

        return

    def set_image_title(self, title=""):
        """
        Set the image title.
        Allows for AutoTitle.
        """

        if self.auto_title:
            if (
                self.image_type.lower() == "object"
            ):  # don't change object title in AutoTitle mode
                pass
            else:
                if title == "":
                    title = self.image_type.lower()

        # set OBJECT keyword to title or autotitle value
        self.set_keyword("OBJECT", title, "", "str")
        self.title = title
        self.image.title = title

        return

    def get_image_title(self):
        """
        Get the current image title.
        Allows for AutoTitle.
        """

        return self.title

    def set_image_type(self, imagetype="zero"):
        """
        Set image type for an exposure.
        imagetype is system defined, and typically includes:
        zero, object, dark, flat.
        """

        self.image_type = imagetype

        return

    def check_image_ready(self):
        """
        Returns True (1) if exposure image is ready and then toggles the flag off
        so that image is not detected multiple times.  Used only for clients which need to know
        when an image is ready.
        An image is ready when written to disk if SaveFile is true, or when valid if SaveFile is false.
        """

        if self.image.toggle:
            self.image.toggle = 0
            return 1
        else:
            return 0

    def get_image_type(self):
        """
        Get current image type for an exposure.
        imagetype is system defines, and typically includes:
        zero, object, dark, flat.
        """

        return self.image_type

    def get_image_types(self):
        """
        Return a list of valid imagetypes.
        Gets imagetypes and comparisons.
        """

        l1 = self.image_types

        try:
            l2 = azcam.db.tools["instrument"].get_all_comps()
        except Exception:
            return l1

        return l1 + l2 if len(l2) > 0 else l1

    def check_comparison_imagetype(self, imagetype=""):
        """
        Returns 1 if imagetype is a comparision, 0 if not.
        If imagetype is not specified, checks the current type.
        """

        if imagetype == "":
            imagetype = self.image_type  # if not specified use previous (global)

        # any undefined image types are comps
        if imagetype in self.image_types:
            return 0
        else:
            return 1

    def set_temp_files(self):
        """
        Update TempImageFile and TempDisplayFile file names based on CommandServer port.
        """

        if not os.path.isabs(self.temp_image_file):
            self.temp_image_file = os.path.join(azcam.db.datafolder, "TempImage")
            self.temp_image_file = os.path.normpath(self.temp_image_file)
            self.temp_image_file = "%s%d" % (
                self.temp_image_file,
                azcam.db.cmdserver.port,
            )  # make unique for multiple processes

        return

    def set_test_image(self, flag):
        """
        Sets TestImage flag is True, clears if False.
        """

        self.test_image = flag

        return

    def get_test_image(self):
        """
        Returns TestImage flag.
        """

        return self.test_image

    # **********************************************************************************************
    # detector parameters
    # **********************************************************************************************

    def set_detpars(self, sensor_data):
        """
        Set detector parameters from sensor data dictionary.
        """

        detpars = sensor_data

        if detpars.get("ref_pixel"):
            self.set_ref_pixel(detpars["ref_pixel"])
        if detpars.get("format"):
            self.set_format(*detpars["format"])
        if detpars.get("focalplane"):
            self.set_focalplane(*detpars["focalplane"])
        if detpars.get("roi"):
            self.set_roi(*detpars["roi"])
        if detpars.get("ext_position"):
            self.set_extension_position(detpars["ext_position"])
        if detpars.get("jpg_order"):
            self.set_jpg_order(detpars["jpg_order"])
        if detpars.get("det_number"):
            self.set_detnum(detpars["det_number"])
        if detpars.get("det_position"):
            self.set_detpos(detpars["det_position"])
        if detpars.get("det_gap"):
            self.set_detgap(detpars["det_gap"])
        if detpars.get("ext_name"):
            self.set_extname(detpars["ext_name"])
        if detpars.get("ext_number"):
            self.set_extnum(detpars["ext_number"])

        if detpars.get("ctype"):
            self.image.focalplane.wcs.ctype1 = detpars["ctype"][0]
            self.image.focalplane.wcs.ctype2 = detpars["ctype"][1]

        return

    def set_format(
        self,
        ns_total=-1,
        ns_predark=-1,
        ns_underscan=-1,
        ns_overscan=-1,
        np_total=-1,
        np_predark=-1,
        np_underscan=-1,
        np_overscan=-1,
        np_frametransfer=-1,
    ):
        """
        Set the detector format for subsequent exposures.
        Must call set_roi() after using this command and before starting exposure.
        ns_total is the number of visible columns.
        ns_predark is the number of physical dark underscan columns.
        ns_underscan is the desired number of desired dark underscan columns.
        ns_overscan is the number of dark overscan columns.
        np_total is the number of visible rows.
        np_predark is the number of physical dark underscan rows.
        np_underscan is the number of desired dark underscan rows.
        np_overscan is the number of desired dark overscan rows.
        np_frametransfer is the rows to frame transfer shift.
        """

        # update image.focalplane
        self.image.focalplane.set_format(
            ns_total,
            ns_predark,
            ns_underscan,
            ns_overscan,
            np_total,
            np_predark,
            np_underscan,
            np_overscan,
            np_frametransfer,
        )

        # update controller parameters
        controller = azcam.db.tools["controller"]
        controller.detpars.ns_total = self.image.focalplane.ns_total
        controller.detpars.ns_predark = self.image.focalplane.ns_predark
        controller.detpars.ns_underscan = self.image.focalplane.ns_underscan
        controller.detpars.ns_overscan = self.image.focalplane.ns_overscan
        controller.detpars.np_total = self.image.focalplane.np_total
        controller.detpars.np_predark = self.image.focalplane.np_predark
        controller.detpars.np_underscan = self.image.focalplane.np_underscan
        controller.detpars.np_overscan = self.image.focalplane.np_overscan
        controller.detpars.np_frametransfer = self.image.focalplane.np_frametransfer
        controller.detpars.coltotal = self.image.focalplane.ns_total
        controller.detpars.colusct = self.image.focalplane.ns_predark
        controller.detpars.coluscw = self.image.focalplane.ns_underscan
        controller.detpars.coluscm = 0
        controller.detpars.coloscw = self.image.focalplane.ns_overscan
        controller.detpars.coloscm = 0
        controller.detpars.rowtotal = self.image.focalplane.np_total
        controller.detpars.rowusct = self.image.focalplane.np_predark
        controller.detpars.rowuscw = self.image.focalplane.np_underscan
        controller.detpars.rowuscm = 0
        controller.detpars.rowoscw = self.image.focalplane.np_overscan
        controller.detpars.rowoscm = 0
        controller.detpars.framet = self.image.focalplane.np_frametransfer

        return

    def get_format(self):
        """
        Return the current detector format parameters.
        """

        return self.image.focalplane.get_format()

    def set_focalplane(
        self, numdet_x=-1, numdet_y=-1, numamps_x=-1, numamps_y=-1, amp_cfg=[0]
    ):
        """
        Sets focal plane configuration for subsequent exposures. Use after set_format().
        Must call set_roi() after using this command and before starting exposure.
        This command replaces SetConfiguration.
        Default focalplane values are set here.
        numdet_x defines number of detectors in Column direction.
        numdet_y defines number of detectors in Row direction.
        numamps_x defines number of amplifiers in Column direction.
        numamps_y defines number of amplifiers in Row direction.
        amp_cfg defines each amplifier's orientation (ex: [1,2,2,3]).
        0 - normal
        1 - flip x
        2 - flip y
        3 - flip x and y
        """

        # set type as could have some from socket string
        numdet_x = int(numdet_x)
        numdet_y = int(numdet_y)
        numamps_x = int(numamps_x)
        numamps_y = int(numamps_y)
        if type(amp_cfg) == str:
            amp_cfg = ast.literal_eval(amp_cfg)

        # update image.focalplane
        reply = self.image.focalplane.set_focalplane(
            numdet_x, numdet_y, numamps_x, numamps_y, amp_cfg
        )

        # update controller parameters
        controller = azcam.db.tools["controller"]
        controller.detpars.numdet_x = self.image.focalplane.numdet_x
        controller.detpars.numdet_y = self.image.focalplane.numdet_y
        controller.detpars.numamps_x = self.image.focalplane.numamps_x
        controller.detpars.numamps_y = self.image.focalplane.numamps_y
        controller.detpars.amp_cfg = self.image.focalplane.amp_cfg
        controller.detpars.num_detectors = self.image.focalplane.num_detectors
        controller.detpars.num_ser_amps_det = self.image.focalplane.num_ser_amps_det
        controller.detpars.num_par_amps_det = self.image.focalplane.num_par_amps_det
        controller.detpars.num_amps_det = self.image.focalplane.num_amps_det
        controller.detpars.numamps_image = self.image.focalplane.numamps_image
        controller.detpars.ampvispix_x = self.image.focalplane.ampvispix_x
        controller.detpars.ampvispix_y = self.image.focalplane.ampvispix_y

        self.image.set_scaling()

        return reply

    def get_focalplane(self):
        """
        Returns the current focal plane configuration.
        """

        return self.image.focalplane.get_focalplane()

    def set_data_order(self, dataOrder):
        """
        Sets data order
        """

        self.data_order = []
        if len(dataOrder) > 0:
            for item in dataOrder:
                self.data_order.append(int(item))

        return

    def set_roi(
        self,
        first_col=-1,
        last_col=-1,
        first_row=-1,
        last_row=-1,
        col_bin=-1,
        row_bin=-1,
        roi_num=0,
    ):
        """
        Sets the ROI values for subsequent exposures.
        Currently only one ROI (0) is supported.
        These values are for the entire focal plane, not just one detector.
        """

        # update image.focalplane
        first_col = int(first_col)
        last_col = int(last_col)
        first_row = int(first_row)
        last_row = int(last_row)
        col_bin = int(col_bin)
        row_bin = int(row_bin)
        roi_num = int(roi_num)
        self.image.focalplane.set_roi(
            first_col, last_col, first_row, last_row, col_bin, row_bin, roi_num
        )

        # update controller parameters
        controller = azcam.db.tools["controller"]
        controller.detpars.first_col = self.image.focalplane.first_col
        controller.detpars.last_col = self.image.focalplane.last_col
        controller.detpars.first_row = self.image.focalplane.first_row
        controller.detpars.last_row = self.image.focalplane.last_row
        controller.detpars.col_bin = self.image.focalplane.col_bin
        controller.detpars.row_bin = self.image.focalplane.row_bin

        controller.detpars.xunderscan = self.image.focalplane.xunderscan
        controller.detpars.xskip = self.image.focalplane.xskip
        controller.detpars.xpreskip = self.image.focalplane.xpreskip
        controller.detpars.xdata = self.image.focalplane.xdata
        controller.detpars.xpostskip = self.image.focalplane.xpostskip
        controller.detpars.xoverscan = self.image.focalplane.xoverscan
        controller.detpars.yunderscan = self.image.focalplane.yunderscan
        controller.detpars.yskip = self.image.focalplane.yskip
        controller.detpars.ypreskip = self.image.focalplane.ypreskip
        controller.detpars.ydata = self.image.focalplane.ydata
        controller.detpars.ypostskip = self.image.focalplane.ypostskip
        controller.detpars.yoverscan = self.image.focalplane.yoverscan

        controller.detpars.numcols_amp = self.image.focalplane.numcols_amp
        controller.detpars.numcols_overscan = self.image.focalplane.numcols_overscan
        controller.detpars.numviscols_amp = self.image.focalplane.numviscols_amp
        controller.detpars.numviscols_image = self.image.focalplane.numviscols_image
        controller.detpars.numrows_amp = self.image.focalplane.numrows_amp
        controller.detpars.numrows_overscan = self.image.focalplane.numrows_overscan
        controller.detpars.numvisrows_amp = self.image.focalplane.numvisrows_amp
        controller.detpars.numvisrows_image = self.image.focalplane.numvisrows_image
        controller.detpars.numpix_amp = self.image.focalplane.numpix_amp
        controller.detpars.numcols_det = self.image.focalplane.numcols_det
        controller.detpars.numrows_det = self.image.focalplane.numrows_det
        controller.detpars.numpix_det = self.image.focalplane.numpix_det
        controller.detpars.numpix_image = self.image.focalplane.numpix_image
        controller.detpars.numcols_image = self.image.focalplane.numcols_image
        controller.detpars.numrows_image = self.image.focalplane.numrows_image
        controller.detpars.numbytes_image = self.image.focalplane.numbytes_image
        controller.detpars.xflush = self.image.focalplane.xflush
        controller.detpars.yflush = self.image.focalplane.yflush

        # update controller
        controller.set_roi()

        # update image size
        self.size_x = self.image.focalplane.numcols_image
        self.size_y = self.image.focalplane.numrows_image

        self.image.size_x = self.image.focalplane.numcols_image
        self.image.size_y = self.image.focalplane.numrows_image

        # indicate that ROI has changed for next exposure
        self.new_roi = 1

        return

    def get_roi(self, roi_num=0):
        """
        Returns a list of the ROI parameters for the roi_num specified.
        Currently only one ROI (0) is supported.
        Returned list format is (first_col,last_col,first_row,last_row,col_bin,row_bin).
        """

        return self.image.focalplane.get_roi(roi_num)

    def roi_reset(self):
        """
        Resets detector ROI values to full frame, current binning.
        """

        self.image.focalplane.roi_reset()

        return

    def set_ref_pixel(self, XY):
        """
        Set the reference pixel.
        XY is [X,Y] in pixels.
        """

        self.image.focalplane.set_ref_pixel(XY)

        return

    def set_extension_position(self, XY):
        """
        Set the extension position of each amplifier.
        XY is [[X,Y]] in index numbers, starting at [1,1].
        """

        self.image.focalplane.set_extension_position(XY)

        return

    def set_detnum(self, det_number):
        """
        Set the detector numbers.
        """

        self.image.focalplane.det_number = det_number

        return

    def set_detgap(self, det_gap):
        """
        Set the detector gaps in pixels.
        """

        for i, gap in enumerate(det_gap):
            self.image.focalplane.gapx[i] = gap[0]
            self.image.focalplane.gapy[i] = gap[1]

        return

    def set_detpos(self, det_position):
        """
        Set the detector positions.
        """

        for i, pos in enumerate(det_position):
            self.image.focalplane.detpos_x[i] = pos[0]
            self.image.focalplane.detpos_y[i] = pos[1]

        return

    def set_jpg_order(self, Indices):
        """
        Set JPG image positions.
        """

        self.image.focalplane.set_jpg_order(Indices)

        return

    def set_tdi_delay(self, flag):
        """
        Set TDI line delay On or Off.
        flag==True sets delay to self.tdi_delay.
        flag==Flase sets line delay to normal value, self.par_delay.
        """

        return

    def set_extname(self, ext_name):
        """
        Set image extension names.
        """

        self.image.focalplane.set_extension_name(ext_name)

        return

    def set_extnum(self, ext_number):
        """
        Set image extension numbers.
        """

        self.image.focalplane.set_extension_extnum(ext_number)

        return

    def get_status(self):
        """
        Return a variety of system status data in one dictionary.
        """

        progress = 0

        filename = self.get_filename()
        et = self.get_exposuretime()
        if self.is_exposure_sequence:
            self.exposure_sequence_number
            seqcount = self.exposure_sequence_number
            seqtotal = self.exposure_sequence_total
        else:
            seqcount = 0
            seqtotal = 0

        ef = self.exposure_flag
        expstate = self.exposureflags_rev.get(ef, "")

        if azcam.db.tools["tempcon"].is_enabled:
            try:
                camtemp, dewtemp = azcam.db.tools["tempcon"].get_temperatures()[0:2]
                camtemp = f"{camtemp:.1f}"
                dewtemp = f"{dewtemp:.1f}"
            except Exception as e:
                azcam.log(e)
                camtemp = -999.9  # error reading temperature
                dewtemp = -666.6
        else:
            camtemp = -999.9
            dewtemp = -666.6
            # camtemp = f"{camtemp:8.3f}"
            # dewtemp = f"{dewtemp:8.3f}"

        if ef == 1:
            expcolor = "green"
            et = self.get_exposuretime()
            if et == 0:
                progress = 0.0
                explabel = ""
            else:
                etr = self.get_exposuretime_remaining()
                explabel = f"{etr:.1f} sec remaining"
                progress = float(100.0 * (etr / et))
        elif ef == 7:
            expcolor = "red"
            progress = int(
                100.0
                * (self.get_pixels_remaining() / self.image.focalplane.numpix_image)
            )
            explabel = f"{progress}% readout"
        elif ef == 8:
            expcolor = "cyan"
            explabel = "exposure setup"
        else:
            expcolor = "transparent"
            progress = 0.0
            explabel = ""
            expstate = ""

        if self.message == "" and expstate != "":
            message = expstate
            if self.is_exposure_sequence:
                message = f"{message} - {self.exposure_sequence_number} of {self.exposure_sequence_total}"
        else:
            message = self.message

        # debug
        if 0:
            self.pgress += 5.0
            if self.pgress > 100:
                self.pgress = 0
            progress = self.pgress

        response = {
            "message": message,
            "exposurelabel": explabel,
            "exposurecolor": expcolor,
            "exposurestate": expstate,
            "progressbar": progress,
            "camtemp": camtemp,
            "dewtemp": dewtemp,
            "filename": filename,
            "seqcount": seqcount,
            "seqtotal": seqtotal,
            "timestamp": self._timestamp(0),
            "imagetitle": self.get_image_title(),
            "imagetype": self.get_image_type(),
            "imagetest": self.test_image,
            "exposuretime": self.get_exposuretime(),
            "colbin": self.image.focalplane.col_bin,
            "rowbin": self.image.focalplane.row_bin,
            "systemname": azcam.db.systemname,
            "mode": azcam.db.servermode,
        }

        return response

    def _timestamp(self, precision=0):
        """
        Return a timestamp string.
        precision is number of fractional seconds.
        """

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

        return timestamp

    def read_header_file(self, filename):
        """
        Read header template file.
        """

        return azcam.db.headers["system"].read_file(filename)
