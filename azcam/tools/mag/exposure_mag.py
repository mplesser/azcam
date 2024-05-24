"""
Contains the ExposureMag class.
"""

import os
import time

import azcam
from azcam.tools.exposure import Exposure

from .receive_data import ReceiveData


class ExposureMag(Exposure):
    """
    Defines the exposure class for Magellan controllers which makes an exposure.
    """

    def __init__(self, tool_id="exposure", description=None):
        super().__init__(tool_id, description)

        self.receive_data = ReceiveData(self)
        self.exp_start = 0
        self.curr_delay = 0

    def integrate(self):
        """
        Integration.
        """

        # start integration
        self.exposure_flag = self.exposureflags["EXPOSING"]
        imagetype = self.image_type.lower()

        # do this as some DSP code not work right
        try:
            shutterstate = self.shutter_dict[self.image_type.lower()]
        except KeyError:
            shutterstate = 1  # other types are comps, so open shutter

        if shutterstate:
            azcam.db.tools["controller"].set_shutter(1)

        # start exposure
        if imagetype != "zero":
            azcam.log("Integration started")

        self.exp_start = time.time()
        azcam.db.tools["controller"].start_exposure()
        self.dark_time_start = time.time()

        # Mag controller pause/resume not supported but abort is
        if self.exposure_time >= 1.0:
            while self.exposure_time_remaining > 0.15:
                if self.exposure_flag == self.exposureflags["ABORT"]:
                    if self.is_exposure_sequence:
                        azcam.log("Stopping exposure sequence")
                        self.is_exposure_sequence = 0
                        self.exposure_sequence_number = 1
                        self.exposure_flag = self.exposureflags["EXPOSING"]
                    else:
                        azcam.db.tools["controller"].exposure_abort()
                    break
                time.sleep(0.1)
                self.exposure_time_remaining = self.exposure_time_remaining - 0.1
        else:
            time.sleep(self.exposure_time)

        azcam.db.tools["controller"].set_shutter(0)  # until shutter issue is solved

        # exposure finished
        if imagetype == "zero":
            self.exposure_time = self.exposure_time_saved
        self.exposure_time_remaining = 0
        if self.exposure_flag == self.exposureflags["ABORT"]:
            azcam.log("Integration aborted")
        else:
            self.exposure_flag = self.exposureflags["READ"]

        if shutterstate:
            azcam.db.tools["controller"].set_shutter(0)

        if self.image_type.lower() != "zero":
            azcam.log("integration finished", level=2)

        time.sleep(0.04)  # some bug on controller

        return

    def get_exposuretime_remaining(self):
        """
        Return remaining exposure time (in seconds).
        """

        return self.exposure_time_remaining

    def readout(self):
        """
        Exposure readout.
        """

        self.exposure_flag = self.exposureflags["READ"]

        imagetype = self.image_type.lower()

        if imagetype == "ramp":
            azcam.db.tools["controller"].set_shutter(1)

        # start readout
        azcam.log("Readout started")

        reply = azcam.db.tools["controller"].start_readout()

        # Wait for end of readout
        t_wait = (self.image.focalplane.numpix_image * 2) / 1000000 + 0.1

        t_wait = self.curr_delay
        time.sleep(t_wait)

        self.pixels_remaining = 0
        if self.exposure_flag != self.exposureflags["ABORT"]:
            self.exposure_flag = self.exposureflags["NONE"]

        # transfer image data already read from controller
        try:
            reply = self.receive_data.receive_image_data(
                self.image.focalplane.numpix_image * 2
            )
        except azcam.exceptions.AzcamError:
            self.exposure_flag = self.exposureflags["ABORT"]

        self.image.valid = 1  # new

        if imagetype == "ramp":
            azcam.db.tools["controller"].set_shutter(0)

        if self.exposure_flag == self.exposureflags["ABORT"]:
            azcam.log("Readout aborted")
            return ["ABORTED", "Readout aborted"]
        else:
            azcam.log("Readout finished", level=2)
            self.exposure_flag = self.exposureflags["NONE"]
            return

    def end(self):
        """
        Completes an exposure by writing file and displaying image.
        """

        self.exposure_flag = self.exposureflags["WRITING"]

        if self.send_image:
            local_file = self.temp_image_file + "." + self.get_extname(self.filetype)
            try:
                os.remove(local_file)
            except FileNotFoundError:
                pass
        else:
            local_file = self.get_filename()

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
            azcam.log("Writing %s" % local_file)

            # write the file to disk
            self.image.overwrite = self.overwrite
            self.image.test_image = self.test_image
            reply = self.image.write_file(local_file, self.filetype)
            azcam.log("Writing finished", level=2)

            # set flag that image now written to disk
            self.image.is_written = 1

            if self.send_image:
                azcam.log("Sending image")
                self.sendimage.send_image(local_file, self.get_filename())

        # image data and file are now ready
        self.image.toggle = 1

        # display image
        if self.display_image:
            try:
                azcam.log("Displaying image")
                azcam.db.tools["display"].display(self.image)
            except Exception:
                pass

        # increment file sequence number if image was written
        if self.save_file:
            self.increment_filenumber()

        self.exposure_flag = self.exposureflags["NONE"]

        return
