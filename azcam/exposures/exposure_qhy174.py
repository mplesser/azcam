"""
Contains the ExposureQHY class.

(from ExposureMag)
"""

import os
import time

from azcam.fits import pyfits

import azcam
from azcam.exposures.exposure import Exposure


class ExposureQHY(Exposure):
    """
    Defines the exposure class for QHY174 camera which makes an exposure.
    """

    def __init__(self, *args):

        super().__init__(*args)

        self.id = "qhy"
        self.exp_start = 0
        self.readout_delay = 1

    def integrate(self):
        """
        Integration.
        """

        self.exposure_flag = azcam.db.exposureflags["EXPOSING"]
        imagetype = self.image_type.lower()

        try:
            shutterstate = self.shutter_dict[self.image_type.lower()]
        except KeyError:
            shutterstate = "open"  # other types are comps, so open shutter

        if shutterstate == "open":
            azcam.db.controller.set_shutter_state(1)
        else:
            azcam.db.controller.set_shutter_state(0)

        # start exposure
        if imagetype != "zero":
            azcam.log("Integration started")

        self.exp_start = time.time()
        self.dark_time_start = self.exp_start
        azcam.db.controller.start_exposure()

        # wait for integration
        time.sleep(self.exposure_time)

        # exposure finished
        if imagetype == "zero":
            self.exposure_time = self.exposure_time_saved
        self.exposure_time_remaining = 0
        if self.exposure_flag == azcam.db.exposureflags["ABORT"]:
            azcam.log("Integration aborted")
        else:
            self.exposure_flag = azcam.db.exposureflags["READ"]

        if self.image_type.lower() != "zero":
            azcam.log("integration finished", level=2)

        return

    def readout(self):
        """
        Exposure readout.
        """

        self.exposure_flag = azcam.db.exposureflags["READ"]

        # allow readout to complete
        time.sleep(self.readout_delay)
        self.image.valid = 1

        imagetype = self.image_type.lower()
        if imagetype == "ramp":
            azcam.db.controller.set_shutter_state(0)

        if self.exposure_flag == azcam.db.exposureflags["ABORT"]:
            azcam.log("Readout aborted")
            return
        else:
            azcam.log("Readout finished", level=2)
            self.exposure_flag = azcam.db.exposureflags["NONE"]
            return

    def end(self):
        """
        Completes an exposure by writing file and displaying image.
        """

        self.hdu = pyfits.PrimaryHDU(azcam.db.controller.camera.ImageArray)
        self.hdu.writeto(self.filename.get_name())

        self.exposure_flag = azcam.db.exposureflags["WRITING"]

        if self.image.remote_imageserver_flag:
            local_file = self.temp_image_file + "." + self.filename.get_extension(self.filetype)
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
        azcam.db.headers["exposure"].set_keyword("EXPTIME", et, "Exposure time (seconds)", float)
        azcam.db.headers["exposure"].set_keyword("DARKTIME", dt, "Dark time (seconds)", float)

        # write file(s) to disk
        if self.save_file:

            azcam.log("Writing %s" % local_file)

            # write the file to disk
            self.image.overwrite = self.filename.overwrite
            self.image.test_image = self.filename.test_image

            # hdu.writeto("test.fits")
            reply = self.image.write_file(local_file, self.filetype)

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
                azcam.db.display.display(self.image)
            except Exception:
                pass

        # increment file sequence number if image was written
        if self.save_file:
            self.filename.increment()

        self.exposure_flag = azcam.db.exposureflags["NONE"]

        return

    def get_exposuretime_remaining(self):
        """
        Return remaining exposure time (in seconds).
        """

        return self.controller.update_exposuretime_remaining()
