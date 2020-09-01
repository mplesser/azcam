"""
Contains the ControllerQHY class.
"""

import time
import win32com.client

import azcam
from azcam.controllers.controller import Controller


class ControllerQHY(Controller):
    """
    The controller class for QHY174 cameras using ASCOM.
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

        self.shutter_state = 0

        # ASCOM
        self.driver = "ASCOM.QHYCCD.Camera"
        self.camera = None

    def reset(self):
        """
        Reset controller.
        May warn that the controller could not be reset.
        """

        # reset flag even is system has previously been reset
        self.is_reset = 0

        self.header.delete_all_keywords()

        self.camera.connected = True

        self.is_reset = 1

        self.set_roi()

        self.set_exposuretime(azcam.db.exposure.exposure_time)

        return

    def initialize(self):
        """
        Initialize the controller interface.
        """

        # x = win32com.client.Dispatch("ASCOM.Utilities.Chooser")
        # x.DeviceType = "Camera"
        # self.driver = x.Choose(None)
        self.camera = win32com.client.Dispatch(self.driver)
        self.camera.connected = False

        return

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

    def set_shutter_state(self, state):
        """
        Open or close controller shutter.
        """

        if state:
            self.shutter_state = 1
        else:
            self.shutter_state = 0

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

        self.camera.StartExposure(self.exposure_time, self.shutter_state)

        return

    def update_exposuretime_remaining(self):
        """
        Return remaining exposure time (in seconds).
        """

        return 0
