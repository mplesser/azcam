"""
Contains the ExposureArc class.
"""

import os
import threading
import time

import azcam
from azcam.server.exposures.exposure import Exposure, ReceiveData


class ExposureArc(Exposure):
    """
    Defines the exposure class for ARC controllers which makes an exposure.
    """

    def __init__(self, *args):

        super().__init__(*args)

        self.id = "arc"
        self.receive_data = ReceiveData(self)

    def integrate(self):
        """
        Integration.
        """

        # start integration
        self.exposure_flag = azcam.db.exposureflags["EXPOSING"]
        imagetype = self.image_type.lower()

        # flag to change OD voltages during integration > 1 second
        CHANGEVOLTAGES = (
            self.image_type.lower() != "zero"
            and azcam.db.objects["controller"].lower_voltages
            and self.exposure_time > 1.0
        )

        if CHANGEVOLTAGES:
            # lower OD's
            azcam.db.objects["controller"].board_command(
                "RMP", azcam.db.objects["controller"].TIMINGBOARD, 0
            )

        # start exposure
        if imagetype != "zero":
            azcam.log("Integration started")
        azcam.db.objects["controller"].start_exposure()

        """
        # do this for any return below
        if azcam.utils.check_reply(reply):
            if CHANGEVOLTAGES:  # return OD volatges
                azcam.db.objects["controller"].board_command("RMP", azcam.db.objects["controller"].TIMINGBOARD, 1)
            return reply
        """
        self.dark_time_start = time.time()

        reply = self.get_exposuretime_remaining()
        remtime = reply
        lasttime = remtime

        # countdown and check for async. ExposureFlag changes
        loopcount = 0

        while remtime > 0.6:
            if (
                self.exposure_flag == azcam.db.exposureflags["EXPOSING"]
            ):  # no EF changes
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
                self.exposure_flag = azcam.db.exposureflags["ABORT"]
                azcam.db.objects["controller"].exposure_abort()
                break
            elif (
                self.exposure_flag == azcam.db.exposureflags["ABORT"]
            ):  # AbortExposure received
                if self.is_exposure_sequence:
                    azcam.log("Stopping exposure sequence")
                    self.is_exposure_sequence = 0
                    self.exposure_sequence_number = 1
                    self.exposure_flag = azcam.db.exposureflags["EXPOSING"]
                else:
                    azcam.db.objects["controller"].exposure_abort()
                    break
            elif (
                self.exposure_flag == azcam.db.exposureflags["PAUSE"]
            ):  # PauseExposure received
                azcam.db.objects["controller"].exposure_pause()
                self.exposure_flag = azcam.db.exposureflags["PAUSED"]
                azcam.log("Integration paused")
            elif (
                self.exposure_flag == azcam.db.exposureflags["RESUME"]
            ):  # ResumeExposure received
                azcam.db.objects["controller"].exposure_resume()
                self.exposure_flag = azcam.db.exposureflags["EXPOSING"]
                reply = self.get_exposuretime_remaining()
                remtime = reply
                azcam.log("Integration resumed")
            elif (
                self.exposure_flag == azcam.db.exposureflags["READ"]
            ):  # ReadExposure received
                remtime = 0.0
                self.exposure_time_actual = (
                    self.exposure_time - self.exposure_time_remaining
                )
                break
            elif (
                self.exposure_flag == azcam.db.exposureflags["PAUSE"]
            ):  # already paused so just loop
                time.sleep(0.5)

        if (
            self.exposure_flag == azcam.db.exposureflags["ABORT"]
        ):  # abort in remaining time
            azcam.log("Integration aborted")
        else:
            time.sleep(remtime + 0.1)
            self.exposure_flag = azcam.db.exposureflags["READ"]  # set to readout

        self.dark_time = time.time() - self.dark_time_start

        # return OD voltages
        if CHANGEVOLTAGES:
            azcam.db.objects["controller"].board_command(
                "RMP", azcam.db.objects["controller"].TIMINGBOARD, 1
            )
            time.sleep(0.5)  # delay for voltages to come up

        # turn off comp lamps
        if not self.comp_sequence:
            if self.comp_exposure:
                if not azcam.db.objects["instrument"].shutter_strobe:
                    azcam.db.objects["instrument"].comps_off()
                azcam.db.objects["instrument"].set_active_comps("shutter")

        # extra close shutter command
        reply = azcam.db.objects["controller"].set_shutter(0)

        # set times
        self.exposure_time_remaining = 0
        if imagetype == "zero":
            self.exposure_time = self.exposure_time_saved

        if self.exposure_flag == azcam.db.exposureflags["ABORT"]:
            azcam.AzcamWarning("Integration aborted")
        else:
            azcam.log("Integration finished", level=2)

        return

    def readout(self):
        """
        Exposure readout.
        """

        self.exposure_flag = azcam.db.exposureflags["READ"]

        imagetype = self.image_type.lower()

        if imagetype == "ramp":
            azcam.db.objects["controller"].set_shutter(1)

        if self.tdi_mode:
            self.set_tdi_delay(True)

        # start readout
        azcam.db.objects["controller"].start_readout()
        self.exposure_flag = azcam.db.exposureflags["READOUT"]
        azcam.log("Readout started")

        # start data transfer, returns when all data is received
        try:
            self.receive_data.receive_image_data(self.image.focalplane.numpix_image * 2)
        except azcam.AzcamError as e:
            if e.error_code == 3:
                azcam.log("Exposure aborted")
            else:
                raise

        # check if aborted by user
        if azcam.db.abortflag:
            if self.is_exposure_sequence:  # stop exposure sequence
                azcam.log("User abort in exposure sequence")

        self.image.valid = 1

        if imagetype == "ramp":
            azcam.db.objects["controller"].set_shutter(0)

        if self.tdi_mode:
            self.set_tdi_delay(False)

        if self.exposure_flag == azcam.db.exposureflags["ABORT"]:
            # if aborted in a sequence, reset flags and let finish without error
            if self.is_exposure_sequence:
                azcam.log("Stopping exposure sequence in Exposure")
                self.is_exposure_sequence = 0
                self.exposure_sequence_number = 1
                self.exposure_flag = azcam.db.exposureflags["READ"]
            else:
                azcam.log("Readout aborted")
                raise azcam.AzcamError("Readout aborted", error_code=3)
        elif self.exposure_flag == azcam.db.exposureflags["ERROR"]:
            if self.is_exposure_sequence:
                self.exposure_flag = azcam.db.exposureflags["NONE"]
                raise azcam.AzcamError("Exposure sequence error occurred")
            else:
                self.exposure_flag = azcam.db.exposureflags["ABORT"]
                azcam.log("Readout aborted")
                raise azcam.AzcamError("Readout aborted", error_code=3)
        else:
            azcam.log("Readout finished", level=2)
            self.exposure_flag = azcam.db.exposureflags["NONE"]

        return

    def end(self):
        """
        Completes an exposure by writing file and displaying image.
        """

        self.exposure_flag = azcam.db.exposureflags["WRITING"]

        # if remote write, LocalFile is local temp file
        if self.image.remote_imageserver_flag:
            LocalFile = (
                self.temp_image_file + "." + self.filename.get_extension(self.filetype)
            )
            try:
                os.remove(LocalFile)
            except FileNotFoundError:
                pass
        else:
            LocalFile = self.filename.get_name()

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
            "EXPTIME", et, "Exposure time (seconds)", float
        )
        azcam.db.headers["exposure"].set_keyword(
            "DARKTIME", dt, "Dark time (seconds)", float
        )

        # write file(s) to disk
        if self.save_file:
            azcam.log("Writing %s" % LocalFile)

            # write the file to disk
            self.image.overwrite = self.filename.overwrite
            self.image.test_image = self.filename.test_image
            self.image.write_file(LocalFile, self.filetype)
            azcam.log("Writing finished", level=2)

            # set flag that image now written to disk
            self.image.written = 1

            # send image to guider software
            if self.guide_mode:
                self.image.send_image(LocalFile)

            # send image to remote DataServer
            elif self.image.remote_imageserver_flag:
                self.image.remote_imageserver_filename = self.get_filename()
                if self.write_async:
                    self.exposure_flag = azcam.db.exposureflags[
                        "NONE"
                    ]  # reset flag now so next exposure can start
                    azcam.log("Starting asynchronous image transfer to dataserver")
                    sendthread = threading.Thread(
                        target=self.image.send_image,
                        name="writeasync",
                        args=("dataserver"),
                    )
                    sendthread.start()

                    # increment file sequence number now and return
                    self.filename.increment()
                    self.exposure_flag = azcam.db.exposureflags["NONE"]
                    return

                else:
                    self.image.send_image(LocalFile)
                    azcam.log("Finished sending image")

        # image data and file are now ready
        self.image.toggle = 1

        # reset idle if no flush
        if not self.flush_array:
            azcam.db.objects["controller"].start_idle()

        # display image
        if self.display_image and not self.write_async:
            azcam.log("Displaying image")
            azcam.db.objects["display"].display(self.image)

        # increment file sequence number if image was written
        if self.save_file:
            self.filename.increment()

        self.exposure_flag = azcam.db.exposureflags["NONE"]

        return

    def abort(self):
        """
        Abort an exposure in progress.
        Really sets the ExposureFlag which is read in during the exposure.
        """

        if (
            azcam.db.objects["controller"].controller_type == "gen2"
            and self.exposure_flag == azcam.db.exposureflags["READ"]
        ):
            raise azcam.AzcamError("Abort readout not supported for this controller")

        if (
            azcam.db.objects["controller"].controller_type == "gen1"
            and self.exposure_flag == azcam.db.exposureflags["READ"]
        ):
            raise azcam.AzcamError("Abort readout not supported for this controller")

        if self.exposure_flag != azcam.db.exposureflags["NONE"]:
            self.exposure_flag = azcam.db.exposureflags["ABORT"]

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

        controller = azcam.db.objects["controller"]

        if Flag:
            Delay = self.tdi_delay
            controller.header.set_keyword(
                "TdiDelay", Delay, "TDI delay multiplier", int
            )
        else:
            Delay = self.par_delay
            controller.header.delete_keyword("TdiDelay")

        controller.write_memory("Y", controller.TIMINGBOARD, 0x20, Delay)

        return
