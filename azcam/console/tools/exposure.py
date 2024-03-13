"""
Contains the ExposureConsole class.
"""

from typing import Union, List, Optional

import azcam
from azcam.console.tools.console_tools import ConsoleTools


class ExposureConsole(ConsoleTools):
    """
    Exposure tool for consoles.
    Usually implemented as the "exposure" tool.
    """

    def __init__(self) -> None:
        super().__init__("exposure")

    def set_shutter(self, state: int = 0, shutter_id: int = 0) -> Optional[str]:
        """
        Open or close a shutter.

        :param state:
        :param shutter_id: Shutter ID flag

        * 0 => controller shutter.
        * 1 => instrument shutter.
        """

        return azcam.db.tools["server"].command(
            f"{self.objname}.set_shutter {state} {shutter_id}"
        )

    def abort(self) -> None:
        """
        Sets the global exposure abort flag and tries to abort a remote server exposure.
        """

        azcam.db.abortflag = 1

        # send abort to server, error OK
        try:
            azcam.db.tools["server"].command(f"{self.objname}.abort")
        except Exception as e:
            azcam.log(f"abort error: {e}")

        return

    def initialize(self) -> None:
        """
        Initialize exposure.
        Usually implemented as the "exposure" tool.
        """

        return azcam.db.tools["server"].command(f"{self.objname}.initialize")

    def reset(self) -> None:
        """
        Reset exposure.
        """

        return azcam.db.tools["server"].command(f"{self.objname}.reset")

    def test(self, exposure_time: float = -1, shutter_state: int = 0) -> Optional[str]:
        return azcam.db.tools["server"].command(
            f"{self.objname}.test {exposure_time} {shutter_state}"
        )

    def expose(
        self, exposure_time: float = -1, image_type: str = "", image_title: str = ""
    ) -> Optional[str]:
        """
        Make a complete exposure.
        If arguments are not specified, then previous exposure_time and imagetype values are used.

        :param exposure_time: the exposure time in seconds
        :param image_type: type of exposure ('zero', 'object', 'flat', ...)
        :param image_title: image title, usually surrounded by double quotes
        """

        return azcam.db.tools["server"].command(
            f'{self.objname}.expose {exposure_time} {image_type} "{image_title}"'
        )

    def expose1(
        self, exposure_time: float = -1, image_type: str = "", image_title: str = ""
    ) -> Optional[str]:
        """
        Make a complete exposure with immediate return to caller.

        :param exposure_time: the exposure time in seconds
        :param image_type: type of exposure ('zero', 'object', 'flat', ...)
        :param image_title: image title, usually surrounded by double quotes
        """

        return azcam.db.tools["server"].command(
            f'{self.objname}.expose1 {exposure_time} {image_type} "{image_title}"'
        )

    def begin(
        self, exposure_time: float = -1, image_type: str = "", image_title: str = ""
    ) -> Optional[str]:
        """
        Initiates the first part of an exposure, through image flushing.
        This is an advanced function.

        :param exposure_time: the exposure time in seconds
        :param image_type: type of exposure ('zero', 'object', 'flat', ...)
        :param image_title: image title, usually surrounded by double quotes
        """

        return azcam.db.tools["server"].command(
            f'{self.objname}.begin {exposure_time} {image_type} "{image_title}"'
        )

    def integrate(self) -> None:
        """
        Integrate exposure.
        This is an advanced function.
        """

        return azcam.db.tools["server"].command(f"{self.objname}.integrate")

    def readout(self) -> None:
        """
        Readout the exposure.
        This is an advanced function.
        """

        return azcam.db.tools["server"].command(f"{self.objname}.readout")

    def end(self) -> None:
        """
        Completes an exposure by writing file and displaying image.
        This is an advanced function.
        """

        return azcam.db.tools["server"].command(f"{self.objname}.end")

    def sequence(
        self, number_exposures: int = 1, flush_array: int = -1, delay=-1
    ) -> Optional[str]:
        """
        Take an exposure sequence.

        :param number_exposures:  number of exposures to make
        :param flush_array:  flag defining detector flushing

        * -1 => current value defined by exposure.exposure_sequence_flush [default]
        * 0 => flush for each exposure
        * 1 => flush after first exposure only
        * 2 => no flush

        :param delay: delay between exposures in seconds (-1 => no change)
        """

        return azcam.db.tools["server"].command(
            f"{self.objname}.sequence {number_exposures} {flush_array} {delay}"
        )

    def sequence1(
        self, number_exposures: int = 1, flush_array: int = -1, delay=-1
    ) -> Optional[str]:
        """
        Take an exposure sequence with immediate return.

        :param number_exposures:  number of exposures to make.
        :param flush_array:  flag defining detector flushing

        * -1 => current value defined by exposure.exposure_sequence_flush [default]
        * 0 => flush for each exposure
        * 1 => flush after first exposure only
        * 2 => no flush

        :param delay: delay between exposures in seconds (-1 => no change)
        """

        return azcam.db.tools["server"].command(
            f"{self.objname}.sequence1 {number_exposures} {flush_array} {delay}"
        )

    def guide(self, number_exposures: int = 1) -> Optional[str]:
        """
        Make a complete guider exposure sequence.

        :param number_exposures: number of exposures to make, -1 loop forever
        """

        return azcam.db.tools["server"].command(
            f"{self.objname}.guide {number_exposures}"
        )

    def guide1(self, number_exposures: int = 1) -> Optional[str]:
        """
        guide() with immediate return.

        :param number_exposures: number of exposures to make, -1 loop forever
        """

        return azcam.db.tools["server"].command(
            f"{self.objname}.guide1 {number_exposures}"
        )

    def flush(self, cycles: int = 1) -> Optional[str]:
        """
        Flush/clear detector.

        :param cycles:  number of times to flush the detector.
        """

        return azcam.db.tools["server"].command(f"{self.objname}.flush {cycles}")

    def start_readout(self):
        """
        Start immediate readout of an exposing image.
        Returns immediately, not waiting for readout to finish.
        """

        return azcam.db.tools["server"].command(f"{self.objname}.start_readout")

    def get_image_types(self) -> List[str]:
        """
        Return a list of valid image types.
        """

        return azcam.db.tools["server"].command(f"{self.objname}.get_image_types")

    def roi_reset(self) -> Optional[str]:
        """
        Resets detector ROI values to full frame, current binning.
        """

        return azcam.db.tools["server"].command(f"{self.objname}.roi_reset")

    def get_exposuretime(self) -> Union[str, float]:
        """
        Return current exposure time in seconds.
        """

        reply = azcam.db.tools["server"].command(f"{self.objname}.get_exposuretime")

        return float(reply)

    def get_exposuretime_remaining(self) -> Union[str, float]:
        """
        Return current exposure time in seconds.
        """

        reply = azcam.db.tools["server"].command(
            f"{self.objname}.get_exposuretime_remaining"
        )

        return float(reply)

    def set_exposuretime(self, exposure_time: float) -> Optional[str]:
        """
        Set current exposure time in seconds.

        :param exposure_time: exposure time in seconds.
        """

        return azcam.db.tools["server"].command(
            f"{self.objname}.set_exposuretime {exposure_time}"
        )

    def get_pixels_remaining(self) -> Union[str, int]:
        """
        Return current number of pixels remaing in readout.
        """

        reply = azcam.db.tools["server"].command(f"{self.objname}.get_pixels_remaining")

        return int(reply)

    def parshift(self, number_rows: int) -> Optional[str]:
        """
        Shift detector by number_rows.

        :param number_rows: number of rows to shift (positive is toward readout, negative is away)
        """

        return azcam.db.tools["server"].command(
            f"{self.objname}.parshift {number_rows}"
        )

    def tests(
        self,
        number_exposures: int = 1,
        exposure_time: float = 1.0,
        image_type: str = "zero",
    ) -> Optional[str]:
        """
        Make test exposures, which overwrite previous test images.

        :param number_exposures: number of exposures to take
        :param exposure_time: exposure time in seconds
        :param image_type: image type
        """

        testflag = self.test_image
        self.test_image = 1
        reply = "OK"

        for _ in range(int(number_exposures)):
            try:
                reply = azcam.db.tools["server"].command(
                    f'{self.objname}.expose {exposure_time} {image_type} "test image"'
                )
            except Exception as e:
                self.test_image = testflag
                raise (e)

        self.test_image = testflag

        return reply

    def pause_exposure(self) -> Optional[str]:
        """
        Pause an exposure in progress (integration only).
        """

        return azcam.db.tools["server"].command(f"{self.objname}.pause_exposure")

    def resume_exposure(self) -> Optional[str]:
        """
        Resume a paused exposure.
        """

        return azcam.db.tools["server"].command(f"{self.objname}.resume_exposure")

    def get_filename(self) -> str:
        """
        Return the current exposure image filename.
        :returns: imaeg filename
        """

        return azcam.db.tools["server"].command(f"{self.objname}.get_filename")

    def set_image_filename(self, filename: str) -> Optional[str]:
        """
        Set the filename of the exposure image.
        Always use forward slashes.
        Not fully functional.

        :param filename: image filename
        """

        return azcam.db.tools["server"].command(
            f"{self.objname}.set_filename {filename}"
        )

    def get_image_title(self) -> str:
        """
        Get the current image title.
        """

        return azcam.db.tools["server"].command(f"{self.objname}.get_image_title")

    def set_image_title(self, title: str) -> Optional[str]:
        """
        Set the image title.
        """

        if len(title.split(" ")) > 1:
            title = f'"{title}"'

        return azcam.db.tools["server"].command(
            f"{self.objname}.set_image_title {title}"
        )

    def get_roi(self) -> List:
        """
        Return detector ROI.
        """

        reply = azcam.db.tools["server"].command(f"{self.objname}.get_roi")
        reply_ints = [int(x) for x in reply]

        return reply_ints

    def set_roi(
        self,
        first_col: int = -1,
        last_col: int = -1,
        first_row: int = -1,
        last_row: int = -1,
        col_bin: int = -1,
        row_bin: int = -1,
        roi_number: int = 0,
    ):
        """
        Sets the ROI values for subsequent exposures.
        Currently only one ROI (0) is supported.
        These values are for the entire focal plane, not just one detector.
        """

        return azcam.db.tools["server"].command(
            f"{self.objname}.set_roi {first_col} {last_col} {first_row} {last_row} {col_bin} {row_bin} {roi_number}"
        )

    def get_focalplane(self) -> List:
        """
        Returns the current focal plane configuration.
        """

        return azcam.db.tools["server"].command(f"{self.objname}.get_focalplane")

    def set_focalplane(
        self,
        numdet_x: int = -1,
        numdet_y: int = -1,
        numamps_x: int = -1,
        numamps_y: int = -1,
        amp_cfg: list = [0],
    ) -> None:
        """
        Sets focal plane configuration for subsequent exposures. Use after set_format().
        Must call set_roi() after using this command and before starting exposure.
        This command replaces SetConfiguration.
        Default focalplane values are set here.
        numdet_x defines number of detectors in Column direction.
        numdet_y defines number of detectors in Row direction.
        numamps_x defines number of amplifiers in Column direction.
        numamps_y defines number of amplifiers in Row direction.
        amp_cfg defines each amplifier's orientation (ex: [1,2,2,3]).
        0 - normal
        1 - flip x
        2 - flip y
        3 - flip x and y
        """

        return azcam.db.tools["server"].command(
            f"{self.objname}.set_focalplane {numdet_x} {numdet_y} {numamps_x} {numamps_y} '{amp_cfg}'"
        )

    def get_format(self) -> List:
        """
        Return the current detector format parameters.
        """

        return azcam.db.tools["server"].command(f"{self.objname}.get_format")

    def set_format(
        self,
        ns_total: int = -1,
        ns_predark: int = -1,
        ns_underscan: int = -1,
        ns_overscan: int = -1,
        np_total: int = -1,
        np_predark: int = -1,
        np_underscan: int = -1,
        np_overscan: int = -1,
        np_frametransfer: int = -1,
    ) -> None:
        """
        Set the detector format for subsequent exposures.
        Must call set_roi() after using this command and before starting exposure.
        ns_total is the number of visible columns.
        ns_predark is the number of physical dark underscan columns.
        ns_underscan is the desired number of desired dark underscan columns.
        ns_overscan is the number of dark overscan columns.
        np_total is the number of visible rows.
        np_predark is the number of physical dark underscan rows.
        np_underscan is the number of desired dark underscan rows.
        np_overscan is the number of desired dark overscan rows.
        np_frametransfer is the rows to frame transfer shift.
        """

        return azcam.db.tools["server"].command(
            (
                f"{self.objname}.set_format {ns_total} {ns_predark} {ns_underscan} {ns_overscan} "
                f"{np_total} {np_predark} {np_underscan} {np_overscan} {np_frametransfer}"
            )
        )

    def get_exposureflag(self):
        return azcam.db.tools["server"].command(f"{self.objname}.get_exposureflag")

    def get_status(self):
        """
        Return JSON dictionary of a variety of system status data in one dictionary.
        """

        status = azcam.db.tools["server"].command(f"{self.objname}.get_status")

        return json.loads(status)
