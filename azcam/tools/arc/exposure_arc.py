"""
Contains the ExposureArc class.
"""

import os
import threading
import time

import azcam
import azcam.exceptions
from azcam.tools.exposure import Exposure

from .receive_data import ReceiveData


class ExposureArc(Exposure):
    """
    Defines the exposure class for ARC controllers which makes an exposure.
    """

    def __init__(self, tool_id="exposure", description=None):
        super().__init__(tool_id, description)

        self.receive_data = ReceiveData(self)

    def integrate(self):
        """
        Integration.
        """

        # start integration
        self.exposure_flag = self.exposureflags["EXPOSING"]
        imagetype = self.image_type.lower()

        # start exposure
        if imagetype != "zero":
            azcam.log("Integration started")
        azcam.db.tools["controller"].start_exposure()
        self.dark_time_start = time.time()
        reply = self.get_exposuretime_remaining()
        remtime = reply
        lasttime = remtime

        # countdown and check for async. ExposureFlag changes
        loopcount = 0

        while remtime > 0.6:
            if self.exposure_flag == self.exposureflags["EXPOSING"]:  # no EF changes
                time.sleep(min(remtime, 0.5))
                reply = self.get_exposuretime_remaining()
                remtime = reply
                azcam.log(f"Integration: {remtime:0.3f} seconds remaining", level=3)
                if remtime == lasttime:
                    loopcount += 1
                else:
                    loopcount = 0
                    lasttime = remtime

            if loopcount > 20:
                azcam.log("ERROR Integration time stuck")
                self.exposure_flag = self.exposureflags["ABORT"]
                azcam.db.tools["controller"].exposure_abort()
                break
            elif (
                self.exposure_flag == self.exposureflags["ABORT"]
            ):  # AbortExposure received
                if self.is_exposure_sequence:
                    azcam.log("Stopping exposure sequence")
                    self.is_exposure_sequence = 0
                    self.exposure_sequence_number = 1
                    self.exposure_flag = self.exposureflags["EXPOSING"]
                else:
                    azcam.db.tools["controller"].exposure_abort()
                    break
            elif (
                self.exposure_flag == self.exposureflags["PAUSE"]
            ):  # PauseExposure received
                azcam.db.tools["controller"].exposure_pause()
                self.exposure_flag = self.exposureflags["PAUSED"]
                azcam.log("Integration paused")
            elif (
                self.exposure_flag == self.exposureflags["RESUME"]
            ):  # ResumeExposure received
                azcam.db.tools["controller"].exposure_resume()
                self.exposure_flag = self.exposureflags["EXPOSING"]
                reply = self.get_exposuretime_remaining()
                remtime = reply
                azcam.log("Integration resumed")
            elif (
                self.exposure_flag == self.exposureflags["READ"]
            ):  # ReadExposure received
                remtime = 0.0
                self.exposure_time_actual = (
                    self.exposure_time - self.exposure_time_remaining
                )
                self.set_exposuretime(self.exposure_time_saved)  # reset for sequence
                break
            elif (
                self.exposure_flag == self.exposureflags["PAUSE"]
            ):  # already paused so just loop
                time.sleep(0.5)

        if self.exposure_flag == self.exposureflags["ABORT"]:  # abort in remaining time
            azcam.log("Integration aborted")
        else:
            time.sleep(remtime + 0.1)
            self.exposure_flag = self.exposureflags["READ"]  # set to readout

        self.dark_time = time.time() - self.dark_time_start

        # turn off comp lamps
        if not self.comp_sequence:
            if self.comp_exposure:
                if not azcam.db.tools["instrument"].shutter_strobe:
                    azcam.db.tools["instrument"].comps_off()
                azcam.db.tools["instrument"].set_comps("shutter")

        # extra close shutter command
        reply = azcam.db.tools["controller"].set_shutter(0)

        # set times
        self.exposure_time_remaining = 0
        if imagetype == "zero":
            self.exposure_time = self.exposure_time_saved

        if self.exposure_flag == self.exposureflags["ABORT"]:
            azcam.exceptions.warning("Integration aborted")
        else:
            azcam.log("Integration finished", level=2)

        return

    def readout(self):
        """
        Exposure readout.
        """

        self.exposure_flag = self.exposureflags["READ"]

        imagetype = self.image_type.lower()

        if imagetype == "ramp":
            azcam.db.tools["controller"].set_shutter(1)

        if self.tdi_mode:
            self.set_tdi_delay(True)

        # start readout
        azcam.db.tools["controller"].start_readout()
        self.exposure_flag = self.exposureflags["READOUT"]
        azcam.log("Readout started")

        # start data transfer, returns when all data is received
        try:
            self.receive_data.receive_image_data(self.image.focalplane.numpix_image * 2)
        except azcam.exceptions.AzcamError as e:
            if e.error_code == 3:
                azcam.log("Exposure aborted")
            else:
                raise

        # check if aborted by user
        if azcam.db.abortflag and self.is_exposure_sequence:  # stop exposure sequence
            azcam.log("User abort in exposure sequence")

        self.image.valid = 1

        if imagetype == "ramp":
            azcam.db.tools["controller"].set_shutter(0)

        if self.tdi_mode:
            self.set_tdi_delay(False)

        if self.exposure_flag == self.exposureflags["ABORT"]:
            # if aborted in a sequence, reset flags and let finish without error
            if self.is_exposure_sequence:
                azcam.log("Stopping exposure sequence in Exposure")
                self.is_exposure_sequence = 0
                self.exposure_sequence_number = 1
                self.exposure_flag = self.exposureflags["READ"]
            else:
                azcam.log("Readout aborted")
                raise azcam.exceptions.AzcamError("Readout aborted", error_code=3)
        elif self.exposure_flag == self.exposureflags["ERROR"]:
            if self.is_exposure_sequence:
                self.exposure_flag = self.exposureflags["NONE"]
                raise azcam.exceptions.AzcamError("Exposure sequence error occurred")
            else:
                self.exposure_flag = self.exposureflags["ABORT"]
                azcam.log("Readout aborted")
                raise azcam.exceptions.AzcamError("Readout aborted", error_code=3)
        else:
            azcam.log("Readout finished", level=2)
            self.exposure_flag = self.exposureflags["NONE"]

        return

    def end(self):
        """
        Completes an exposure by writing file and displaying image.
        """

        self.exposure_flag = self.exposureflags["WRITING"]

        # if remote write, LocalFile is local temp file
        if self.send_image:
            LocalFile = self.temp_image_file + "." + self.get_extname(self.filetype)
            try:
                os.remove(LocalFile)
            except FileNotFoundError:
                pass
        else:
            LocalFile = self.get_filename()
        self.last_filename = LocalFile

        # wait for image data to be received
        loop = 0
        while not self.image.valid and loop < 100:
            loop += 1
            time.sleep(0.050)
            if loop >= 100:
                azcam.log("ERROR image data not received in time")

        # update controller header with keywords which might have changed
        et = float(int(self.exposure_time_actual * 1000.0) / 1000.0)
        dt = float(int(self.dark_time * 1000.0) / 1000.0)
        azcam.db.headers["exposure"].set_keyword(
            "EXPTIME", et, "Exposure time (seconds)", "float"
        )
        azcam.db.headers["exposure"].set_keyword(
            "DARKTIME", dt, "Dark time (seconds)", "float"
        )

        # write file(s) to disk
        if self.save_file:
            azcam.log("Writing %s" % LocalFile)

            # write the file to disk
            self.image.overwrite = self.overwrite
            self.image.test_image = self.test_image
            self.image.write_file(LocalFile, self.filetype)
            azcam.log("Writing finished", level=2)

            # set flag that image now written to disk
            self.image.is_written = 1

            # send image to guider software
            if self.guide_mode:
                self.sendimage.send_image(LocalFile)

            # send image to remote image server
            elif self.send_image:
                if self.write_async:
                    self.exposure_flag = self.exposureflags[
                        "NONE"
                    ]  # reset flag now so next exposure can start
                    azcam.log("Sending image asynchronously")
                    sendthread = threading.Thread(
                        target=self.sendimage.send_image,
                        name="writeasync",
                        args=(self.get_filename()),
                    )
                    sendthread.start()

                    # increment file sequence number now and return
                    self.increment_filenumber()
                    self.exposure_flag = self.exposureflags["NONE"]
                    return

                else:
                    azcam.log("Sending image")
                    self.sendimage.send_image(LocalFile, self.get_filename())

        # image data and file are now ready
        self.image.toggle = 1

        # reset idle if no flush
        if not self.flush_array:
            azcam.db.tools["controller"].start_idle()

        # display image
        if self.display_image and not self.write_async:
            azcam.log("Displaying image")
            azcam.db.tools["display"].display(self.image)

        # increment file sequence number if image was written
        if self.save_file:
            self.increment_filenumber()

        self.exposure_flag = self.exposureflags["NONE"]

        return

    def abort(self):
        """
        Abort an exposure in progress.
        Really sets the ExposureFlag which is read in during the exposure.
        """

        if (
            azcam.db.tools["controller"].controller_type == "gen2"
            and self.exposure_flag == self.exposureflags["READ"]
        ):
            raise azcam.exceptions.AzcamError(
                "Abort readout not supported for this controller"
            )

        if (
            azcam.db.tools["controller"].controller_type == "gen1"
            and self.exposure_flag == self.exposureflags["READ"]
        ):
            raise azcam.exceptions.AzcamError(
                "Abort readout not supported for this controller"
            )

        if self.exposure_flag != self.exposureflags["NONE"]:
            self.exposure_flag = self.exposureflags["ABORT"]

        return

    # **********************************************************************************************
    # TDI commands
    # **********************************************************************************************

    def set_tdi_delay(self, Flag):
        """
        Set TDI line delay On or Off.
        Flag==True sets delay to self.tdi_delay.
        Flag==Flase sets line delay to normal value, self.par_delay.
        """

        if Flag:
            Delay = self.tdi_delay
            azcam.db.tools["controller"].set_keyword(
                "TdiDelay", Delay, "TDI delay multiplier", "int"
            )
        else:
            Delay = self.par_delay
            azcam.db.tools["controller"].delete_keyword("TdiDelay")

        azcam.db.tools["controller"].write_memory(
            "Y", azcam.db.tools["controller"].TIMINGBOARD, 0x20, Delay
        )

        return
