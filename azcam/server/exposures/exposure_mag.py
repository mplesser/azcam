"""
Contains the ExposureMag class.
"""

import os
import time

import azcam
from azcam.server.exposures.exposure import Exposure, ReceiveData


class ExposureMag(Exposure):
    """
    Defines the exposure class for Magellan controllers which makes an exposure.
    """

    def __init__(self, *args):

        super().__init__(*args)

        self.id = "mag"
        self.receive_data = ReceiveData(self)
        self.exp_start = 0
        self.curr_delay = 0

    def integrate(self):
        """
        Integration.
        """

        # start integration
        self.exposure_flag = azcam.db.exposureflags["EXPOSING"]
        imagetype = self.image_type.lower()

        # do this as some DSP code not work right
        try:
            shutterstate = self.shutter_dict[self.image_type.lower()]
        except KeyError:
            shutterstate = "open"  # other types are comps, so open shutter

        if shutterstate == "open":
            azcam.db.objects["controller"].set_shutter(1)

        # start exposure
        if imagetype != "zero":
            azcam.log("Integration started")

        self.exp_start = time.time()
        azcam.db.objects["controller"].start_exposure()
        self.dark_time_start = time.time()

        # Mag controller pause/resume not supported but abort is
        if self.exposure_time >= 1.0:
            while self.exposure_time_remaining > 0:
                if (
                    self.exposure_flag == azcam.db.exposureflags["ABORT"]
                ):  # AbortExposure received
                    if self.is_exposure_sequence:
                        azcam.log("Stopping exposure sequence")  # new 05nov12
                        self.is_exposure_sequence = 0
                        self.exposure_sequence_number = 1
                        self.exposure_flag = azcam.db.exposureflags["EXPOSING"]
                    else:
                        azcam.db.objects["controller"].exposure_abort()
                    break
                time.sleep(0.1)
                self.exposure_time_remaining = self.exposure_time_remaining - 0.1
        else:
            time.sleep(self.exposure_time)

        azcam.db.objects["controller"].set_shutter(0)  # until shutter issue is solved

        # exposure finished
        if imagetype == "zero":
            self.exposure_time = self.exposure_time_saved
        self.exposure_time_remaining = 0
        if self.exposure_flag == azcam.db.exposureflags["ABORT"]:
            azcam.log("Integration aborted")
        else:
            self.exposure_flag = azcam.db.exposureflags["READ"]

        if shutterstate == "open":
            azcam.db.objects["controller"].set_shutter(0)

        if self.image_type.lower() != "zero":
            azcam.log("integration finished", level=2)

        time.sleep(0.04)  # some bug on controller

        return

    def readout(self):
        """
        Exposure readout.
        """

        self.exposure_flag = azcam.db.exposureflags["READ"]

        imagetype = self.image_type.lower()

        if imagetype == "ramp":
            azcam.db.objects["controller"].set_shutter(1)

        # start readout
        azcam.log("Readout started")

        reply = azcam.db.objects["controller"].start_readout()
        if azcam.utils.check_reply(reply):
            return reply

        # Wait for end of readout
        t_wait = (self.image.focalplane.numpix_image * 2) / 1000000 + 0.1

        t_wait = self.curr_delay
        time.sleep(t_wait)

        self.pixels_remaining = 0
        if self.exposure_flag != azcam.db.exposureflags["ABORT"]:
            self.exposure_flag = azcam.db.exposureflags["NONE"]

        # transfer image data already read from controller
        reply = self.receive_data.receive_image_data(
            self.image.focalplane.numpix_image * 2
        )
        if azcam.utils.check_reply(reply):
            self.exposure_flag = azcam.db.exposureflags["ABORT"]

        self.image.valid = 1  # new

        if imagetype == "ramp":
            azcam.db.objects["controller"].set_shutter(0)

        if self.exposure_flag == azcam.db.exposureflags["ABORT"]:
            azcam.log("Readout aborted")
            return ["ABORTED", "Readout aborted"]
        else:
            azcam.log("Readout finished", level=2)
            self.exposure_flag = azcam.db.exposureflags["NONE"]
            return

    def end(self):
        """
        Completes an exposure by writing file and displaying image.
        """

        self.exposure_flag = azcam.db.exposureflags["WRITING"]

        if self.image.remote_imageserver_flag:
            local_file = (
                self.temp_image_file + "." + self.filename.get_extension(self.filetype)
            )
            try:
                os.remove(local_file)
            except FileNotFoundError:
                pass
        else:
            local_file = self.filename.get_name()

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

            azcam.log("Writing %s" % local_file)

            # write the file to disk
            self.image.overwrite = self.filename.overwrite
            self.image.test_image = self.filename.test_image
            reply = self.image.write_file(local_file, self.filetype)
            if azcam.utils.check_reply(reply):
                return reply
            azcam.log("Writing finished", level=2)

            # set flag that image now written to disk
            self.image.written = 1

            if self.image.remote_imageserver_flag:
                self.image.send_image(local_file)

        # image data and file are now ready
        self.image.toggle = 1

        # display image
        if self.display_image:
            try:
                azcam.log("Displaying image")
                azcam.db.objects["display"].display(self.image)
            except Exception:
                pass

        # increment file sequence number if image was written
        if self.save_file:
            self.filename.increment()

        self.exposure_flag = azcam.db.exposureflags["NONE"]

        return
