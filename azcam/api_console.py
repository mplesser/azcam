"""
API commands for console application.
"""

from typing import Optional, List, Union

import azcam
import azcam.sockets


class API(object):
    """
    Default API interface for console application.
    """

    def __init__(self):

        pass

    # *******************************************************
    # communications
    # *******************************************************
    def connect(self, host="localhost", port=2402):
        """
        Connect to azcamserver.
        """

        server = azcam.sockets.SocketInterface(host, port)
        azcam.db.server = server

        if server.open():
            connected = True
            self.rcommand("register console")
        else:
            connected = False

        azcam.db.connected = connected

        return connected

    def rcommand(self, command, **kwargs):
        """
        Send a command to a server process using the 'server' object in the database.
        This command traps all errors and returns exceptions and as error string.

        Returns None or a string.
        """

        # get tokenized reply - check for comm error
        try:
            reply = azcam.db.server.command(command, **kwargs)
        except azcam.AzcamError as e:
            if e.error_code == 2:
                raise azcam.AzcamError("could not connect to server")
            else:
                raise

        # status for socket communications is OK or ERROR
        if reply[0] == "ERROR":
            azcam.log(reply[1])
            raise azcam.AzcamError(f"rcommand error: {reply[1]}")
        elif reply[0] == "OK":
            if len(reply) == 1:
                return None
            elif len(reply) == 2:
                return reply[1]
            else:
                return reply[1:]
        else:
            raise azcam.AzcamError(f"invalid server response: {reply}")

        return  # can't get here

    # *******************************************************
    # exposures
    # *******************************************************

    def abort_exposure(self) -> Optional[str]:
        """
        Abort an exposure in progress.
        """

        return self.rcommand("exposure.abort")

    def initialize(self) -> None:
        """
        Initialize exposure.
        """

        return self.rcommand("exposure.initialize")

    def reset(self) -> None:
        """
        Reset exposure.
        """

        return self.rcommand("exposure.reset")

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

        return self.rcommand(f'exposure.expose {exposure_time} {image_type} "{image_title}"')

    def expose1(
        self, exposure_time: float = -1, image_type: str = "", image_title: str = ""
    ) -> Optional[str]:
        """
        Make a complete exposure with immediate return to caller.

        :param exposure_time: the exposure time in seconds
        :param image_type: type of exposure ('zero', 'object', 'flat', ...)
        :param image_title: image title, usually surrounded by double quotes
        """

        return self.rcommand(f'exposure.expose1 {exposure_time} {image_type} "{image_title}"')

    def begin_exposure(
        self, exposure_time: float = -1, image_type: str = "", image_title: str = ""
    ) -> Optional[str]:
        """
        Initiates the first part of an exposure, through image flushing.
        This is an advanced function.

        :param exposure_time: the exposure time in seconds
        :param image_type: type of exposure ('zero', 'object', 'flat', ...)
        :param image_title: image title, usually surrounded by double quotes
        """

        return self.rcommand(f'exposure.begin {exposure_time} {image_type} "{image_title}"')

    def integrate_exposure(self) -> None:
        """
        Integrate exposure.
        This is an advanced function.
        """

        return self.rcommand("exposure.integrate")

    def readout_exposure(self) -> None:
        """
        Readout the exposure.
        This is an advanced function.
        """

        return self.rcommand("exposure.readout")

    def end_exposure(self) -> None:
        """
        Completes an exposure by writing file and displaying image.
        This is an advanced function.
        """

        return self.rcommand("exposure.end")

    def sequence(self, number_exposures: int = 1, flush_array: int = -1, delay=-1) -> Optional[str]:
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

        return self.rcommand(f"exposure.sequence {number_exposures} {flush_array} {delay}")

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

        return self.rcommand(f"exposure.sequence1 {number_exposures} {flush_array} {delay}")

    def guide(self, number_exposures: int = 1) -> Optional[str]:
        """
        Make a complete guider exposure sequence.

        :param number_exposures: number of exposures to make, -1 loop forever
        """

        return self.rcommand(f"exposure.guide {number_exposures}")

    def guide1(self, number_exposures: int = 1) -> Optional[str]:
        """
        guide() with immediate return.

        :param number_exposures: number of exposures to make, -1 loop forever
        """

        return self.rcommand(f"exposure.guide1 {number_exposures}")

    def flush(self, cycles: int = 1) -> Optional[str]:
        """
        Flush/clear detector.

        :param cycles:  number of times to flush the detector.
        """

        return self.rcommand(f"exposure.flush {cycles}")

    def start_readout(self):
        """
        Start immediate readout of an exposing image.
        Returns immediately, not waiting for readout to finish.
        """

        return self.rcommand("exposure.start_readout")

    def get_image_types(self) -> List[str]:
        """
        Return a list of valid image types.
        """

        return self.rcommand("exposure.get_image_types")

    def roi_reset(self) -> Optional[str]:
        """
        Resets detector ROI values to full frame, current binning.
        """

        return self.rcommand("exposure.roi_reset")

    def get_exposuretime(self) -> Union[str, float]:
        """
        Return current exposure time in seconds.
        """

        reply = self.rcommand("exposure.get_exposuretime")

        return float(reply)

    def get_exposuretime_remaining(self) -> Union[str, float]:
        """
        Return current exposure time in seconds.
        """

        reply = self.rcommand("exposure.get_exposuretime_remaining")

        return float(reply)

    def set_exposuretime(self, exposure_time: float) -> Optional[str]:
        """
        Set current exposure time in seconds.

        :param exposure_time: exposure time in seconds.
        """

        return self.rcommand(f"exposure.set_exposuretime {exposure_time}")

    def get_pixels_remaining(self) -> Union[str, int]:
        """
        Return current number of pixels remaing in readout.
        """

        reply = self.rcommand("exposure.get_pixels_remaining")

        return int(reply)

    def parshift(self, number_rows: int) -> Optional[str]:
        """
        Shift detector by number_rows.

        :param number_rows: number of rows to shift (positive is toward readout, negative is away)
        """

        return self.rcommand(f"exposure.parshift {number_rows}")

    def tests(
        self, number_exposures: int = 1, exposure_time: float = 1.0, image_type: str = "zero",
    ) -> Optional[str]:
        """
        Make test exposures, which overwrite previous test images.

        :param number_exposures: number of exposures to take
        :param exposure_time: exposure time in seconds
        :param image_type: image type
        """

        testflag = self.get_par("imagetest")
        self.set_par("imagetest", 1)
        reply = "OK"

        for _ in range(int(number_exposures)):
            try:
                reply = self.rcommand(f'exposure.expose {exposure_time} {image_type} "test image"')
            except Exception as e:
                self.set_par("imagetest", testflag)
                raise (e)

        self.set_par("imagetest", testflag)

        return reply

    def pause_exposure(self) -> Optional[str]:
        """
        Pause an exposure in progress (integration only).
        """

        return self.rcommand("exposure.pause_exposure")

    def resume_exposure(self) -> Optional[str]:
        """
        Resume a paused exposure.
        """

        return self.rcommand("exposure.resume_exposure")

    def get_image_filename(self) -> str:
        """
        Return the current exposure image filename.
        :returns: imaeg filename
        """

        return self.rcommand("exposure.get_filename")

    def set_image_filename(self, filename: str) -> Optional[str]:
        """
        Set the filename of the exposure image.
        Always use forward slashes.
        Not fully functional.

        :param filename: image filename
        """

        return self.rcommand(f"exposure.set_filename {filename}")

    # *******************************************************
    # shutter
    # *******************************************************

    def set_shutter(self, state: int = 0, shutter_id: int = 0) -> Optional[str]:
        """
        Open or close a shutter.

        :param state:
        :param shutter_id: Shutter ID flag

        * 0 => controller shutter.
        * 1 => instrument shutter.
        """

        return self.rcommand(f"exposure.set_shutter {state} {shutter_id}")

    # *******************************************************
    # instrument
    # *******************************************************

    def set_filter(self, filter_name: str, filter_id: int = 0) -> Optional[str]:
        """
        Set instrument filter position.

        :param filter_name: filter value to set
        :param filter_id: filter ID flag
        """

        return self.rcommand(f"instrument.set_filter {filter_name} {filter_id}")

    def get_filter(self, filter_id: int = 0) -> str:
        """
        Get instrument filter position.

        :param filter_id: filter ID flag (use negative value for a list of all filters)
        """

        return self.rcommand(f"instrument.get_filter {filter_id}")

    def get_current(self, diode_id: int = 0, shutter_state: int = 1) -> Union[str, float]:
        """
        Returns a list of instrument diode currents.

        :param diode_id: diode ID flag (system dependent)
        :param shutter_state: open (1), close (0), unchanged (2) shutter during diode read
        """

        reply = self.rcommand(f"instrument.get_current {diode_id} {shutter_state}")

        return float(reply)

    # *******************************************************
    # wavelengths
    # *******************************************************

    def set_wavelength(
        self, wavelength: float, wavelength_id: int = 0, nd: int = -1
    ) -> Optional[str]:
        """
        Set wavelength, optionally changing neutral density.

        :param wavelength: wavelength value, may be a string such as 'clear' or 'dark'
        :param wavelength_id: wavelength ID flag
        :param nd: neutral density value to set
        """

        return self.rcommand(f"instrument.set_wavelength {wavelength} {wavelength_id}")

    def get_wavelength(self, wavelength_id: int = 0) -> int:
        """
        Get instrument wavelength.

        :param wavelength_id: wavelength ID flag  (use negative value for a list of all wavelengths)
        """

        return self.rcommand(f"instrument.get_wavelength {wavelength_id}")

    # *******************************************************
    # focus
    # *******************************************************
    # TODO: step_focus

    def set_focus(
        self,
        focus_value: float,
        focus_id: int = 0,
        focus_component: str = "instrument",
        focus_type: str = "absolute",
    ) -> None:
        """
        Set instrument focus position. The focus value may be an absolute position
        or a relative step if supported by hardware.

        :param focus_value: focus position
        :param focus_id: focus sensor ID flag
        :param focus_component: focus type (typically instrument or telecope)
        :param focus_type: focus type (absolute or step)
        """

        if focus_component == "instrument":
            self.rcommand(
            f"instrument.set_focus {focus_value} {focus_id} {focus_type}"
        )
        elif focus_component == "telescope":
            self.rcommand(
            f"telescope.set_focus {focus_value} {focus_id} {focus_type}"
        )

        return

    def get_focus(self, focus_id: int = 0, focus_component: str = "instrument") -> float:
        """
        Get the current focus position.

        :param focus_id: focus sensor ID flag
        :param focus_component: focus type (typically instrument or telecope)
        """

        if focus_component == "instrument":
            reply = self.rcommand(f"instrument.get_focus {focus_id}")
        elif focus_component == "telescope":
            reply = self.rcommand(f"telescope.get_focus {focus_id}")

        return float(reply)

    # *******************************************************
    # pressure
    # *******************************************************

    def get_pressure(self, pressure_id: int = 0) -> List[float]:
        """
        Return a list of all system pressures.

        :param pressure_id: pressure sensor ID flag
        """

        reply = self.rcommand(f"instrument.get_pressure {pressure_id}")

        return [float(x) for x in reply]

    # *******************************************************
    # temperature
    # *******************************************************

    def get_temperature(self) -> Union[str, List[float]]:
        """
        Return a list of all system temperatures as defined in configuration setup.
        Values are in degrees Celsius and may be formatted for display.
        If temperatures cannot be read, then a list of -999.99 is returned.
        """

        reply = self.rcommand("tempcon.get_temperatures")

        return [float(x) for x in reply]

    def set_control_temperature(
        self, control_temperature: float, temperature_id: int = 0
    ) -> Optional[str]:
        """
        Set control temperature.

        :param control_temperature: control (set) temperature in Celsius
        :param temperature_id: temperature sensor ID flag
        """

        return self.rcommand(
            f"tempcon.set_control_temperature {control_temperature} {temperature_id}"
        )

    def get_control_temperature(self, temperature_id: int = 0) -> Union[str, float]:
        """
        Get control temperature in degress Celsius.

        :param temperature_id: temperature ID flag
        """

        reply = self.rcommand(f"tempcon.get_control_temperature {temperature_id}")

        return float(reply)

    # *******************************************************
    # keywords
    # *******************************************************

    def set_keyword(
        self,
        keyword: str,
        key_value: str,
        key_comment: str = "",
        key_type: str = "str",
        key_object: str = "controller",
    ) -> Optional[str]:
        """
        Set a keyword value and comment.

        The keyword is set in the controller header by default.

        :param keyword: keyword name
        :param key_value: keyword value
        :param key_comment: comment string for keyword
        :param key_type: keyword type
        :param key_object: object to which keyword belongs
        """

        return self.rcommand(
            f'{key_object}.set_keyword {keyword} {key_value} "{key_comment}" {key_type}'
        )

    def get_keyword(self, keyword: str, key_object: str = "controller") -> str:
        """
        Return a keyword value and its comment.
        The comment always returned in quotes, even if empty.

        :param keyword: keyword name
        :param key_object: object to which keyword belongs
        """

        return self.rcommand(f"{key_object}.get_keyword {keyword}")

    def delete_keyword(self, keyword: str, key_object: str = "controller") -> Optional[str]:
        """
        Delete a keyword from a header.
        The keyword is set in the controller header by default.

        :param keyword: keyword name
        :param key_object: object to which keyword belongs
        """

        return self.rcommand(f"{key_object}.delete_keyword {keyword}")

    # *******************************************************
    # focalplane
    # *******************************************************

    def get_roi(self) -> List:
        """
        Return detector ROI.
        """

        return self.rcommand("exposure.get_roi")

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

        return self.rcommand(
            f"exposure.set_roi {first_col} {last_col} {first_row} {last_row} {col_bin} {row_bin} {roi_number}"
        )

    def get_focalplane(self) -> List:
        """
        Returns the current focal plane configuration.
        """

        return self.rcommand("exposure.get_focalplane")

    def set_focalplane(
        self,
        numdet_x: int = -1,
        numdet_y: int = -1,
        numamps_x: int = -1,
        numamps_y: int = -1,
        amp_config: str = "",
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
        amp_config defines each amplifier's orientation (ex: '1223').
        0 - normal
        1 - flip x
        2 - flip y
        3 - flip x and y
        """

        return self.rcommand(
            f"exposure.set_focalplane {numdet_x} {numdet_y} {numamps_x} {numamps_y} {amp_config}"
        )

    def get_format(self) -> List:
        """
        Return the current detector format parameters.
        """

        return self.rcommand("exposure.get_format")

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

        return self.rcommand(
            (
                f"exposure.set_format {ns_total} {ns_predark} {ns_underscan} {ns_overscan} "
                f"{np_total} {np_predark} {np_underscan} {np_overscan} {np_frametransfer}"
            )
        )

    def abort(self):
        """
        Sets the global exposure abort flag and tries to abort a remote server exposure.
            """

        azcam.db.abortflag = 1

        # send abort to server, error OK
        try:
            self.rcommand("abort")
        except Exception as e:
            azcam.log(f"abort error: {e}")

        return

    def get_par(self, parameter):
        """
        Return the value of a parameter from remote server.
        Returns None on error.
        """

        parameter = parameter.lower()
        value = None

        reply = self.rcommand(f"get_par {parameter}")
        _, value = azcam.utils.get_datatype(reply)

        return value

    def set_par(self, parameter, value):
        """
        Set the value of a parameter in the remote server.
        Returns None on error.
        """

        if parameter == "":
            return None

        parameter = parameter.lower()

        self.rcommand(f"set_par {parameter} {value}")

        return

    def get_attr(self, obj, attribute):
        """
        Get the value of an object's attribute on remote server.
        Advanced Use only!
        """

        command_string = f"get_attr {obj} {attribute}"

        return self.rcommand(command_string)

    # ************************************************************************************************
    # image parameter commands
    # ************************************************************************************************
    def save_imagepars(self, imagepars={}):
        """
        Save current image parameters.
        imagepars is a dictionary.
        """

        for par in azcam.db.imageparnames:
            imagepars[par] = self.get_par(par)

        return

    def restore_imagepars(self, imagepars, folder=""):
        """
        Restore image parameters from dictionary.
        imagepars is a dictionary set with save_imagepars().
        """

        for par in azcam.db.imageparnames:
            impar = imagepars[par]
            if impar == "":
                impar = '""'
            imagepars[par] = impar
            if par == "imagetitle":
                impar = f'"{impar}"'
            self.set_par(par, impar)

        # return to folder
        if folder != "":
            azcam.utils.curdir(folder)

        return
