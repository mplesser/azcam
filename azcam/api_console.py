"""
API commands for console application.
"""

from typing import List, Optional, Union

import azcam
import azcam.sockets


class API(object):
    """
    API interface for console application.
    """

    def __init__(self):
        """Create instance."""

        super().__init__()

        self.controller = Controller(self)
        self.exposure = Exposure(self)
        self.instrument = Instrument(self)
        self.telescope = Telescope(self)
        self.tempcon = Tempcon(self)
        self.system = SystemHeader(self)

        self.server = ServerConnection()

        setattr(azcam.db, "api", self)
        azcam.db.cli_cmds["api"] = self

    def _get(self, name):
        """
        Returns an API object by name.
        Returns None if api.name is not defined.
        """

        try:
            obj = getattr(self, name)
        except AttributeError:
            obj = None

        return obj


class HeaderMethods(object):
    """
    Header methods used by other many client classes.
    """

    def __init__(self) -> None:
        pass

    def update_header(self):
        """
        Update the header of an object.
        This command usually reads hardware to get the lastest keyword values.
        """

        return self._parent.server.rcommand(f"{self.object_name}.update_header")

    def read_header(self):
        """
        Reads each keyword in the header and returns the keyword value.
        Returns a list of header lists: [[keyword, value, comment, type]].
        """

        return self._parent.server.rcommand(f"{self.object_name}.read_header")

    def set_keyword(
        self,
        keyword: str,
        key_value: str,
        key_comment: str = "",
        key_type: str = "str",
    ) -> Optional[str]:
        """
        Set a keyword value and comment.

        The keyword is set in the controller header by default.

        :param keyword: keyword name
        :param key_value: keyword value
        :param key_comment: comment string for keyword
        :param key_type: keyword type
        """

        if type(key_value) == str:
            if " " in key_value:
                key_value = f'"{key_value}"'

        if type(key_comment) == str:
            if " " in key_comment:
                key_comment = f'"{key_comment}"'

        s = f"{self.object_name}.set_keyword {keyword} {key_value} {key_comment} {key_type}"

        return self._parent.server.rcommand(s)

    def get_keyword(self, keyword: str) -> str:
        """
        Return a keyword value and its comment.
        The comment always returned in quotes, even if empty.
        Hardware is not usually read by this commands, use update_header first.

        :param keyword: keyword name
        :param key_object: object to which keyword belongs
        """

        return self._parent.server.rcommand(f"{self.object_name}.get_keyword {keyword}")

    def delete_keyword(self, keyword: str) -> Optional[str]:
        """
        Delete a keyword from a header.
        The keyword is set in the controller header by default.

        :param keyword: keyword name
        """

        return self._parent.server.rcommand(
            f"{self.object_name}.delete_keyword {keyword}"
        )

    def get_all_keywords(self):
        """
        Return a list of all keyword names.
        """

        reply = self._parent.server.rcommand(f"{self.object_name}.get_all_keywords")

        return reply

    def get_info(self):
        """
        Returns header info.
        Returns [Header[]]: Each element Header[i] contains the sublist (keyword, value, comment, and type).
        Example: Header[2][1] is the value of keyword 2 and Header[2][3] is its type.
        """

        header = []
        keywords = self.get_all_keywords()

        for key in keywords:
            reply = self.get_keyword(key)
            list1 = [key, reply[0], reply[1], reply[2]]
            header.append(list1)

        return header

    def get_string(self):
        """
        Returns the entire header as a single formatted string.
        """

        lines = ""

        header = self.get_info()
        for telem in header:
            line = telem[0] + " " + str(telem[1]) + " " + str(telem[2]) + "\n"
            lines += line

        return lines


class SystemHeader(HeaderMethods):
    """
    System header class, mainly for image header data.
    """

    def __init__(self, parent) -> None:
        self._parent = parent
        self.object_name = "system"


class Controller(HeaderMethods):
    """
    Controller class for client.
    """

    def __init__(self, parent) -> None:
        self._parent = parent
        self.object_name = "controller"

        super().__init__()

    def initialize(self):
        """
        Initialize controller.
        """

        return self._parent.server.rcommand(f"controller.initialize")

    def reset(self):
        """
        Reset controller using current attributes.
        May warn that the controller could not be reset.
        """

        return self._parent.server.rcommand(f"controller.reset")

    def set_shutter(self, state: int = 0) -> Optional[str]:
        """
        Open or close a shutter.

        :param state:

        """

        return self._parent.server.rcommand(f"controller.set_shutter {state}")


class Instrument(HeaderMethods):
    """
    Instrument class for client.
    """

    def __init__(self, parent) -> None:
        self._parent = parent
        self.object_name = "instrument"
        super().__init__()

    def set_filter(self, filter_name: str, filter_id: int = 0) -> Optional[str]:
        """
        Set instrument filter position.

        :param filter_name: filter value to set
        :param filter_id: filter ID flag
        """

        return self._parent.server.rcommand(
            f"instrument.set_filter {filter_name} {filter_id}"
        )

    def get_filter(self, filter_id: int = 0) -> str:
        """
        Get instrument filter position.

        :param filter_id: filter ID flag (use negative value for a list of all filters)
        """

        return self._parent.server.rcommand(f"instrument.get_filter {filter_id}")

    def get_current(
        self, diode_id: int = 0, shutter_state: int = 1
    ) -> Union[str, float]:
        """
        Returns a list of instrument diode currents.

        :param diode_id: diode ID flag (system dependent)
        :param shutter_state: open (1), close (0), unchanged (2) shutter during diode read
        """

        reply = self._parent.server.rcommand(
            f"instrument.get_current {diode_id} {shutter_state}"
        )

        return float(reply)

    def set_wavelength(
        self, wavelength: float, wavelength_id: int = 0, nd: int = -1
    ) -> Optional[str]:
        """
        Set wavelength, optionally changing neutral density.

        :param wavelength: wavelength value, may be a string such as 'clear' or 'dark'
        :param wavelength_id: wavelength ID flag
        :param nd: neutral density value to set
        """

        return self._parent.server.rcommand(
            f"instrument.set_wavelength {wavelength} {wavelength_id}"
        )

    def get_wavelength(self, wavelength_id: int = 0) -> float:
        """
        Get instrument wavelength.

        :param wavelength_id: wavelength ID flag  (use negative value for a list of all wavelengths)
        """

        reply = float(
            self._parent.server.rcommand(f"instrument.get_wavelength {wavelength_id}")
        )

        return reply

    def set_focus(
        self,
        focus_value: float,
        focus_id: int = 0,
        focus_type: str = "absolute",
    ) -> None:
        """
        Set instrument focus position. The focus value may be an absolute position
        or a relative step if supported by hardware.

        :param focus_value: focus position
        :param focus_id: focus sensor ID flag
        :param focus_type: focus type (absolute or step)
        """

        self._parent.server.rcommand(
            f"instrument.set_focus {focus_value} {focus_id} {focus_type}"
        )

        return

    def get_focus(
        self,
        focus_id: int = 0,
    ) -> float:
        """
        Get the current focus position.

        :param focus_id: focus sensor ID flag
        """

        reply = self._parent.server.rcommand(f"instrument.get_focus {focus_id}")

        return float(reply)

    def get_pressures(self, pressure_id: int = 0) -> List[float]:
        """
        Return a list of all system pressures.

        :param pressure_id: pressure sensor ID flag
        """

        reply = self._parent.server.rcommand(f"instrument.get_pressure {pressure_id}")

        return [float(x) for x in reply]

    def set_shutter(self, state: int = 0, shutter_id: int = 0) -> Optional[str]:
        """
        Open or close a shutter.

        :param state:
        :param shutter_id: Shutter ID flag

        """

        return self._parent.server.rcommand(
            f"instrument.set_shutter {state} {shutter_id}"
        )


class Telescope(HeaderMethods):
    """
    Telescope class for client.
    """

    def __init__(self, parent) -> None:
        self._parent = parent
        self.object_name = "telescope"
        super().__init__()

    def get_focus(self, focus_id: int = 0) -> float:
        """
        Get the current focus position.

        :param focus_id: focus sensor ID flag
        """

        reply = self._parent.server.rcommand(f"telescope.get_focus {focus_id}")

        return float(reply)

    def set_focus(
        self,
        focus_value: float,
        focus_id: int = 0,
        focus_type: str = "absolute",
    ) -> None:
        """
        Set instrument focus position. The focus value may be an absolute position
        or a relative step if supported by hardware.

        :param focus_value: focus position
        :param focus_id: focus sensor ID flag
        :param focus_type: focus type (absolute or step)
        """

        self._parent.server.rcommand(
            f"telescope.set_focus {focus_value} {focus_id} {focus_type}"
        )

        return

    def get_focus(self, focus_id: int = 0) -> float:
        """
        Get the current focus position.

        :param focus_id: focus sensor ID flag
        """

        reply = self._parent.server.rcommand(f"telescope.get_focus {focus_id}")

        return float(reply)


class Tempcon(HeaderMethods):
    """
    Temperature controller (tempcon) class for client.
    """

    def __init__(self, parent) -> None:
        self._parent = parent
        self.object_name = "tempcon"
        super().__init__()

    def get_temperatures(self) -> Union[str, List[float]]:
        """
        Return a list of all system temperatures as defined in configuration setup.
        Values are in degrees Celsius and may be formatted for display.
        If temperatures cannot be read, then a list of -999.99 is returned.
        """

        reply = self._parent.server.rcommand("tempcon.get_temperatures")

        return [float(x) for x in reply]

    def set_control_temperature(
        self, control_temperature: float, temperature_id: int = 0
    ) -> Optional[str]:
        """
        Set control temperature.

        :param control_temperature: control (set) temperature in Celsius
        :param temperature_id: temperature sensor ID flag
        """

        return self._parent.server.rcommand(
            f"tempcon.set_control_temperature {control_temperature} {temperature_id}"
        )

    def get_control_temperature(self, temperature_id: int = 0) -> Union[str, float]:
        """
        Get control temperature in degress Celsius.

        :param temperature_id: temperature ID flag
        """

        reply = self._parent.server.rcommand(
            f"tempcon.get_control_temperature {temperature_id}"
        )

        return float(reply)


class Exposure(HeaderMethods):
    """
    Exposure class for client.
    """

    def __init__(self, parent) -> None:
        self._parent = parent
        self.object_name = "exposure"
        super().__init__()

    def set_shutter(self, state: int = 0, shutter_id: int = 0) -> Optional[str]:
        """
        Open or close a shutter.

        :param state:
        :param shutter_id: Shutter ID flag

        * 0 => controller shutter.
        * 1 => instrument shutter.
        """

        return self._parent.server.rcommand(
            f"exposure.set_shutter {state} {shutter_id}"
        )

    def abort_exposure(self) -> Optional[str]:
        """
        Abort an exposure in progress.
        """

        return self._parent.server.rcommand("exposure.abort")

    def initialize(self) -> None:
        """
        Initialize exposure.
        """

        return self._parent.server.rcommand("exposure.initialize")

    def reset(self) -> None:
        """
        Reset exposure.
        """

        return self._parent.server.rcommand("exposure.reset")

    def test(self, exposure_time: float = -1, shutter_state: int = 0) -> Optional[str]:

        return self._parent.server.rcommand(
            f"exposure.test {exposure_time} {shutter_state}"
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

        return self._parent.server.rcommand(
            f'exposure.expose {exposure_time} {image_type} "{image_title}"'
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

        return self._parent.server.rcommand(
            f'exposure.expose1 {exposure_time} {image_type} "{image_title}"'
        )

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

        return self._parent.server.rcommand(
            f'exposure.begin {exposure_time} {image_type} "{image_title}"'
        )

    def integrate_exposure(self) -> None:
        """
        Integrate exposure.
        This is an advanced function.
        """

        return self._parent.server.rcommand("exposure.integrate")

    def readout_exposure(self) -> None:
        """
        Readout the exposure.
        This is an advanced function.
        """

        return self._parent.server.rcommand("exposure.readout")

    def end_exposure(self) -> None:
        """
        Completes an exposure by writing file and displaying image.
        This is an advanced function.
        """

        return self._parent.server.rcommand("exposure.end")

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

        return self._parent.server.rcommand(
            f"exposure.sequence {number_exposures} {flush_array} {delay}"
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

        return self._parent.server.rcommand(
            f"exposure.sequence1 {number_exposures} {flush_array} {delay}"
        )

    def guide(self, number_exposures: int = 1) -> Optional[str]:
        """
        Make a complete guider exposure sequence.

        :param number_exposures: number of exposures to make, -1 loop forever
        """

        return self._parent.server.rcommand(f"exposure.guide {number_exposures}")

    def guide1(self, number_exposures: int = 1) -> Optional[str]:
        """
        guide() with immediate return.

        :param number_exposures: number of exposures to make, -1 loop forever
        """

        return self._parent.server.rcommand(f"exposure.guide1 {number_exposures}")

    def flush(self, cycles: int = 1) -> Optional[str]:
        """
        Flush/clear detector.

        :param cycles:  number of times to flush the detector.
        """

        return self._parent.server.rcommand(f"exposure.flush {cycles}")

    def start_readout(self):
        """
        Start immediate readout of an exposing image.
        Returns immediately, not waiting for readout to finish.
        """

        return self._parent.server.rcommand("exposure.start_readout")

    def get_image_types(self) -> List[str]:
        """
        Return a list of valid image types.
        """

        return self._parent.server.rcommand("exposure.get_image_types")

    def roi_reset(self) -> Optional[str]:
        """
        Resets detector ROI values to full frame, current binning.
        """

        return self._parent.server.rcommand("exposure.roi_reset")

    def get_exposuretime(self) -> Union[str, float]:
        """
        Return current exposure time in seconds.
        """

        reply = self._parent.server.rcommand("exposure.get_exposuretime")

        return float(reply)

    def get_exposuretime_remaining(self) -> Union[str, float]:
        """
        Return current exposure time in seconds.
        """

        reply = self._parent.server.rcommand("exposure.get_exposuretime_remaining")

        return float(reply)

    def set_exposuretime(self, exposure_time: float) -> Optional[str]:
        """
        Set current exposure time in seconds.

        :param exposure_time: exposure time in seconds.
        """

        return self._parent.server.rcommand(
            f"exposure.set_exposuretime {exposure_time}"
        )

    def get_pixels_remaining(self) -> Union[str, int]:
        """
        Return current number of pixels remaing in readout.
        """

        reply = self._parent.server.rcommand("exposure.get_pixels_remaining")

        return int(reply)

    def parshift(self, number_rows: int) -> Optional[str]:
        """
        Shift detector by number_rows.

        :param number_rows: number of rows to shift (positive is toward readout, negative is away)
        """

        return self._parent.server.rcommand(f"exposure.parshift {number_rows}")

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

        testflag = self.get_par("imagetest")
        self.set_par("imagetest", 1)
        reply = "OK"

        for _ in range(int(number_exposures)):
            try:
                reply = self._parent.server.rcommand(
                    f'exposure.expose {exposure_time} {image_type} "test image"'
                )
            except Exception as e:
                self.set_par("imagetest", testflag)
                raise (e)

        self.set_par("imagetest", testflag)

        return reply

    def pause_exposure(self) -> Optional[str]:
        """
        Pause an exposure in progress (integration only).
        """

        return self._parent.server.rcommand("exposure.pause_exposure")

    def resume_exposure(self) -> Optional[str]:
        """
        Resume a paused exposure.
        """

        return self._parent.server.rcommand("exposure.resume_exposure")

    def get_image_filename(self) -> str:
        """
        Return the current exposure image filename.
        :returns: imaeg filename
        """

        return self._parent.server.rcommand("exposure.get_filename")

    def set_image_filename(self, filename: str) -> Optional[str]:
        """
        Set the filename of the exposure image.
        Always use forward slashes.
        Not fully functional.

        :param filename: image filename
        """

        return self._parent.server.rcommand(f"exposure.set_filename {filename}")

    def get_roi(self) -> List:
        """
        Return detector ROI.
        """

        return self._parent.server.rcommand("exposure.get_roi")

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

        return self._parent.server.rcommand(
            f"exposure.set_roi {first_col} {last_col} {first_row} {last_row} {col_bin} {row_bin} {roi_number}"
        )

    def get_focalplane(self) -> List:
        """
        Returns the current focal plane configuration.
        """

        return self._parent.server.rcommand("exposure.get_focalplane")

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

        return self._parent.server.rcommand(
            f"exposure.set_focalplane {numdet_x} {numdet_y} {numamps_x} {numamps_y} {amp_config}"
        )

    def get_format(self) -> List:
        """
        Return the current detector format parameters.
        """

        return self._parent.server.rcommand("exposure.get_format")

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

        return self._parent.server.rcommand(
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
            self._parent.server.rcommand("exposure.abort")
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

        reply = self._parent.server.rcommand(f"exposure.get_par {parameter}")
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

        self._parent.server.rcommand(f"exposure.set_par {parameter} {value}")

        return


class ServerConnection(azcam.sockets.SocketInterface):
    """
    Server connection class for client to azcamserver.
    """

    def __init__(self) -> None:

        azcam.sockets.SocketInterface.__init__(self)
        self.connected = False

    def connect(self, host="localhost", port=2402):
        """
        Connect to azcamserver.
        """

        self.host = host
        self.port = port

        if self.open():
            connected = True
            self.rcommand("register console")
        else:
            connected = False

        self.connected = connected

        return connected

    def rcommand(self, command):
        """
        Send a command to a server process using the 'server' object in the database.
        This command traps all errors and returns exceptions and as error string.

        Returns None or a string.
        """

        # get tokenized reply - check for comm error
        try:
            reply = self.command(command)
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
