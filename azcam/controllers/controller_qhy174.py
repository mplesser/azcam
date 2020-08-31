"""
Contains the ControllerQHY class.
"""

import time
import os
import win32com.client

import azcam
from azcam.fits import pyfits
from azcam.controllers.controller import Controller


class ControllerQHY(Controller):
    """
    Defines the QHY174 controller commands.
    """

    def __init__(self, *args):

        super().__init__(*args)

        self.name = "qhy174"

        #: video gain flag
        self.video_gain = 1

        #: True if image data from ControllserServer is binary (not a file)
        self.binary_image_data = 1

        self.controller_class = "qhy"
        self.controller_type = "qhy174"

        # DSP code filename
        self.timing_file = ""

    def reset(self):
        """
        Reset controller.
        May warn that the controller could not be reset.
        """

        # reset flag even is system has previously been reset
        self.is_reset = 0

        self.header.delete_all_keywords()

        self.is_reset = 1

        self.set_roi()

        self.set_exposuretime(azcam.db.exposure.exposure_time)

        return

    def initialize(self):
        """
        Initialize the controller interface.
        """

        x = win32com.client.Dispatch("ASCOM.Utilities.Chooser")
        x.DeviceType = "Camera"
        self.driver = x.Choose(None)
        self.camera = win32com.client.Dispatch(self.driver)
        self.camera.connected = True

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

    def set_shutter(self, state):
        """
        Open or close controller shutter.
        """

        if state:
            self.set_shutter_state = 1
        else:
            self.set_shutter_state = 0

        return

    def set_exposuretime(self, exposure_time):
        """
        Write the exposure time (in seconds) to the controller.
        """

        exposure_time = float(exposure_time)

        self.exposure_time = exposure_time

        return

    def get_exposuretime(self):

        return self.exposure_time

    def start_exposure(self):
        """
        Start exposure (integration).
        """

        self.camera.StartExposure(self.exposure_time, self.set_shutter_state)
        time.sleep(1)
        image = self.camera.ImageArray
        self.hdu = pyfits.PrimaryHDU(image)

        return
