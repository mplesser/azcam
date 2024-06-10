"""
Contains the ControllerASCOM class.
"""

import time
from datetime import datetime

try:
    import win32com.client
except Exception as e:
    print(e)

import azcam
import azcam.exceptions
from azcam.tools.controller import Controller


class ControllerASCOM(Controller):
    """
    The controller class for cameras using ASCOM.
    """

    def __init__(self, tool_id="controller", description=None):
        super().__init__(tool_id, description)

        self.controller_class = "ASCOM"

        # video gain flag
        self.video_gain = 1

        # True if image data from ControllserServer is binary (not a file)
        self.binary_image_data = 1

        self.shutter_state = 0

        # ASCOM
        self.driver = ""
        self.camera = None

    def initialize(self):
        """
        Initialize the controller interface.
        """

        if self.is_initialized:
            return

        azcam.log("initializing camera")

        """
        import win32com
        driver = "ASCOM.ASICamera2.Camera"
        camera = win32com.client.Dispatch(driver)
        camera.connected = True
        camera.NumX = self.nx
        camera.NumY = self.ny
        camera.BinX = 1
        camera.BinY = 1
        camera.StartExposure(1, 1)
        time.sleep(3)
        flag = camera.ImageReady
        print("ready", flag)
        x = win32com.client.Dispatch("ASCOM.Utilities.Chooser")
        x.DeviceType = "Camera"
        driver = x.Choose(None)
        """

        self.camera = win32com.client.Dispatch(self.driver)
        self.camera.connected = True

        """
        self.camera.NumX = self.nx
        self.camera.NumY = self.ny
        self.camera.BinX = 1
        self.camera.BinY = 1
        """

        self.is_initialized = 1

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

        self.set_exposuretime(azcam.db.tools["exposure"].exposure_time)

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
        et = max(0.000001, exposure_time)

        self.exposure_time = et

        return

    def get_exposuretime(self):
        return self.exposure_time

    def start_exposure(self):
        """
        Start exposure (integration).
        """

        self.start_time = datetime.now()

        try:
            self.camera.StartExposure(self.exposure_time, self.shutter_state)
        except Exception as e:
            print(f"Camera error starting exposure: {e}")

        return

    def is_imageready(self, wait=0):
        """
        Return True if image is ready.
        """

        flag = self.camera.ImageReady

        count = 0
        if wait:
            while not flag:
                if count > 200:
                    raise azcam.exceptions.AzcamError("Camera timeout reading image")
                time.sleep(0.05)
                count += 1
                # print("waiting...")
                flag = self.camera.ImageReady
            # print("ready")

        return flag

    def update_exposuretime_remaining(self):
        """
        Return remaining exposure time (in seconds).
        """

        et = datetime.now() - self.start_time
        et = self.exposure_time - et.seconds
        if et < 0:
            et = 0

        return et

    def get_pixels_remaining(self):
        """
        Return number of remaining pixels to be read (counts down).
        """

        return 0

    def set_roi(self):
        self.camera.BinX = min(self.detpars.col_bin, self.camera.MaxBinX)
        self.camera.BinY = min(self.detpars.row_bin, self.camera.MaxBinY)

        # binned pixels
        self.camera.NumX = min(self.detpars.numcols_image, self.camera.CameraXSize)
        self.camera.NumY = min(self.detpars.numrows_image, self.camera.CameraYSize)

        # zero based
        self.camera.StartX = self.detpars.first_col / self.detpars.col_bin - 1
        self.camera.StartY = self.detpars.first_row / self.detpars.row_bin - 1

        return
