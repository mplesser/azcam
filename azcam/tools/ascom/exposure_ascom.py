"""
Contains the ExposureASCOM class.
"""

import os
import time
import numpy

import azcam
from azcam.tools.exposure import Exposure


class ExposureASCOM(Exposure):
    """
    Defines the exposure class for cameras using ASCOM.
    """

    def __init__(self, tool_id="exposure", description=None):
        super().__init__(tool_id, description)

        self.exp_start = 0
        self.readout_delay = 0

    def integrate(self):
        """
        Integration.
        """

        self.exposure_flag = self.exposureflags["EXPOSING"]
        imagetype = self.image_type.lower()

        try:
            shutterstate = self.shutter_dict[self.image_type.lower()]
        except KeyError:
            shutterstate = 1  # other types are comps, so open shutter

        # close instrument shutter for darks and zeros
        if azcam.db.tools["instrument"].is_enabled:
            if shutterstate:
                azcam.db.tools["instrument"].comps_on()
            else:
                azcam.db.tools["instrument"].comps_off()

        # start exposure
        if imagetype != "zero":
            azcam.log("Integration started")

        self.exp_start = time.time()
        self.dark_time_start = self.exp_start
        azcam.db.tools["controller"].start_exposure()

        # wait for integration
        time.sleep(self.exposure_time)

        # exposure finished
        if imagetype == "zero":
            self.exposure_time = self.exposure_time_saved
        self.exposure_time_remaining = 0
        if self.exposure_flag == self.exposureflags["ABORT"]:
            azcam.log("Integration aborted")
        else:
            self.exposure_flag = self.exposureflags["READ"]

        if azcam.db.tools["instrument"].is_enabled:
            azcam.db.tools["instrument"].comps_off()

        if self.image_type.lower() != "zero":
            azcam.log("integration finished", level=2)

        return

    def readout(self):
        """
        Exposure readout.
        """

        self.exposure_flag = self.exposureflags["READOUT"]

        # wait for readout
        azcam.log("Readout started")

        try:
            azcam.db.tools["controller"].is_imageready(1)
        except azcam.exceptions.AzcamError:
            self.exposure_flag = self.exposureflags["ABORT"]
            return

        # allow readout to complete
        self.image.valid = 1

        imagetype = self.image_type.lower()
        if imagetype == "ramp":
            azcam.db.tools["controller"].set_shutter_state(0)

        if self.exposure_flag == self.exposureflags["ABORT"]:
            azcam.log("Readout aborted")
            return
        else:
            azcam.log("Readout finished", level=2)
            self.exposure_flag = self.exposureflags["NONE"]
            return

    def end(self):
        """
        Completes an exposure by writing file and displaying image.
        """

        # this can be slow for big image
        # ASCOM fills array Y then X do transpose
        self.image.transposed_image = 1
        # size = azcam.db.tools["controller"].camera.NumX * azcam.db.tools["controller"].camera.NumY  # can be wrong
        size = (
            azcam.db.tools["controller"].detpars.numcols_image
            * azcam.db.tools["controller"].detpars.numrows_image
        )
        self.image.data[0] = (
            numpy.array(azcam.db.tools["controller"].camera.ImageArray)
            .reshape(size)
            .astype("uint16")
        )

        self.exposure_flag = self.exposureflags["WRITING"]

        if self.send_image:
            local_file = self.temp_image_file + "." + self.get_extname(self.filetype)
            try:
                os.remove(local_file)
            except FileNotFoundError:
                pass
        else:
            local_file = self.get_filename()

        self.last_filename = local_file

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

            self.image.write_file(local_file, self.filetype)

            azcam.log("Writing finished", level=2)

            # set flag that image now written to disk
            self.image.is_written = 1

            if self.send_image:
                azcam.log("Sending image")
                self.sendimage.send_image()

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

    def get_exposuretime_remaining(self):
        """
        Return remaining exposure time (in seconds).
        """

        return azcam.db.tools["controller"].update_exposuretime_remaining()
