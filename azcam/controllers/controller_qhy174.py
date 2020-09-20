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

    def __init__(self, obj_id="controller", obj_name="Controller"):

        super().__init__(obj_id, obj_name)

        self.controller_class = "qhy"
        self.controller_type = "qhy174"

        #: video gain flag
        self.video_gain = 1

        #: True if image data from ControllserServer is binary (not a file)
        self.binary_image_data = 1

        self.shutter_state = 0

        # ASCOM
        self.driver = "ASCOM.QHYCCD.Camera"
        self.camera = None

        self.initialize()

    def initialize(self):
        """
        Initialize the controller interface.
        """

        if self.initialized:
            return

        # driver = "ASCOM.QHYCCD.Camera"
        # camera = win32com.client.Dispatch(driver)
        # camera.connected = True
        # camera.StartExposure(1, 1)
        # time.sleep(3)
        # flag = camera.ImageReady
        # print("ready", flag)

        # x = win32com.client.Dispatch("ASCOM.Utilities.Chooser")
        # x.DeviceType = "Camera"
        # self.driver = x.Choose(None)

        self.camera = win32com.client.Dispatch(self.driver)
        self.camera.connected = True

        # self.camera.NumX = 1920
        # self.camera.NumY = 1200
        # self.camera.BinX = 1
        # self.camera.BinY = 1

        self.initialized = 1

        return

    def reset(self):
        """
        Reset the controller.
        """

        # reset flag even is system has previously been reset
        self.is_reset = 0

        self.header.delete_all_keywords()

        self.is_reset = 1

        self.set_roi()

        self.set_exposuretime(azcam.db.exposure.exposure_time)

        return

    def set_roi(self):
        """
        Sets ROI parameters values in the controller based on focalplane parameters.
        """

        # self.camera.NumX = 1920
        # self.camera.NumY = 1200

        return

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

        # self.camera.NumX = 1920
        # self.camera.NumY = 1200

        self.camera.StartExposure(self.exposure_time, self.shutter_state)
        # time.sleep(3)
        # flag = self.camera.ImageReady
        flag = self.is_imageready(1)
        if flag:
            print("image ready")

        return

    def is_imageready(self, wait=0):
        """
        Return True if image is ready.
        """

        flag = self.camera.ImageReady

        if wait:
            while not flag:
                time.sleep(0.1)
                print("waiting...")
                flag = self.camera.ImageReady

        return flag

    def update_exposuretime_remaining(self):
        """
        Return remaining exposure time (in seconds).
        """

        return 0
