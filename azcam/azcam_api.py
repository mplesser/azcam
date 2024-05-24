"""
API for azcam
"""

import azcam


class API(object):
    """
    AzCam API class.
    """

    def __init__(self) -> None:
        pass

        self.exposure = ExposureAPI()
        self.parameters = ParametersAPI()
        self.tempcon = TempConAPI()

        pass


class ParametersAPI(object):
    """
    Paramaters API.
    """

    def __init__(self) -> None:
        pass

    def get_par(self):
        return

    def set_par(self):
        return


class ExposureAPI(object):
    """
    Exposure API.
    """

    def __init__(self) -> None:
        pass

    def expose(self):
        return

    def expose1(self):
        return

    def flush(self):
        return

    def set_filename(self):
        return

    def reset(self):
        return

    def get_roi(self):
        return

    def get_format(self):
        return

    def set_roi(self):
        return

    def get_temperatures(self):
        return

    def abort(self):
        return

    def pause(self):
        return

    def resume(self):
        return

    def read_header_file(self):
        return

    def set_exposuretime(self):
        return

    def get_exposuretime_remaining(self):
        return

    def sequence(self):
        return

    def sequence1(self):
        return

    def get_pixels_remaining(self):
        return

    def get_status(self):
        return


class TempConAPI(object):
    """
    Temperature controller API.
    """

    def get_temperatures(self):
        return

    def set_control_temperature(
        self, temperature: float = None, temperature_id: int = 0
    ):
        return
