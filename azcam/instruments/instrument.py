"""
Contains the base Instrument class.
"""

import time

import azcam
from azcam.header import Header


class Instrument(object):
    """
    The base Instrument class.
    """

    def __init__(self, obj_id="instrument"):

        #: instrument name
        self.name = ""

        #: instrument ID
        self.obj_id = obj_id

        # True if instrument is initialized
        self.initialized = False

        # True if instrument is enabled
        self.enabled = True

        # active comparisons
        self.active_comps = []

        # True if shutter controls comps
        self.shutter_strobe = 0

        # keywords for header, list of [keyword, comment, type]
        self.keywords = {}

        # instrument header object
        self.header = Header("Instrument")
        self.header.set_header("instrument", 3)

        # save object
        setattr(azcam.db, obj_id, self)
        azcam.db.cmd_objects[obj_id] = self
        azcam.db.cli_cmds[obj_id] = self

        return

    def initialize(self):
        """
        Initialize the instrument.
        """

        if self.initialized:
            return

        if not self.enabled:
            azcam.AzcamWarning("Instrument is not enabled")
            return

        self.initialized = 1

        return

    def reset(self):
        """
        Reset instrument object.
        """

        return

    # ***************************************************************************
    # exposure
    # ***************************************************************************

    def exposure_start(self):
        """
        Optional call before exposure starts.
        """

        return

    def exposure_finish(self):
        """
        Optional tempcon.call after exposure finishes.
        """

        return

    # ***************************************************************************
    # header
    # ***************************************************************************
    def define_keywords(self):
        """
        Sets up instrument header keywords dictionary, if not already defined.
        """

        if len(self.header.keywords) != 0:
            return

        keywords = []

        # add keywords to header
        if keywords:
            for key in self.keywords:
                self.header.set_keyword(
                    key, "", self.header.comments[key], self.header.typestrings[key]
                )

        return

    def update_header(self):
        """
        Update the header, reading current data.
        Deletes all keywords if the Instrument is not enabled.
        """

        # delete all keywords if not enabled
        if not self.enabled:
            self.header.delete_all_keywords()
            return

        if not self.initialized:
            self.initialize()

        self.define_keywords()

        self.read_header()

        return

    def read_header(self):
        """
        Reads each keyword in the header and returns the header with the updated values.
        Returns a list of header lists: [[keyword, value, comment, type]].
        """

        header = []
        reply = self.header.get_all_keywords()

        for key in reply:
            reply = self.get_keyword(key)
            if reply is not None:
                list1 = [key, reply[0], reply[1], reply[2]]  # key, value, comment, type
                header.append(list1)

        return header

    def get_keyword(self, keyword):
        """
        Return a keyword value and its comment.
        Comment always returned in double quotes, even if empty.
        """

        return self.header.get_keyword(keyword)

    def set_keyword(self, keyword, value, comment=None, typestring=None):
        """
        Set a keyword value and comment.
        typestring is one of 'str', 'int', or 'float'.
        """

        self.header.set_keyword(keyword, value, comment, typestring)

        return

    def delete_keyword(self, keyword):
        """
        Delete a keyword.
        """

        self.header.delete_keyword(keyword)

        return

    # ***************************************************************************
    # comparisons
    # ***************************************************************************
    def get_all_comps(self, comp_id=0):
        """
        Return all valid comparison names.
        Useful for clients to determine which type of comparison exposures are supported.
        comp_id is the comparison mechanism ID.
        """

        raise NotImplementedError

    def get_active_comps(self, comp_id=0):
        """
        Return a list of the active comparison lamps.
        comp_id is the comparison mechanism ID.
        """

        return self.active_comps

    def set_active_comps(self, comp_names=None, comp_id=0):
        """
        Set comparisons which are to be turned on and off with comps_on() and comps_off().
        comp_names is a single string or a list of strings to be set as active.
        comp_id is the comparison mechanism ID.
        """

        if type(comp_names) == str:
            comp_names = list(comp_names)

        self.active_comps = comp_names

        return

    def comps_on(self, comp_id=0):
        """
        Turn on active comparisons.
        comp_id is the comparison mechanism ID.
        """

        return

    def comps_off(self, comp_id=0):
        """
        Turn off active comparisons.
        comp_id is the comparison mechanism ID.
        """

        return

    def comps_delay(self, delay_time=0, comp_id=0):
        """
        Delays for delay_time for comparison lamp warmup.
        May internally set delay based on comp selection.
        delay_time is in seconds.
        comp_id is the comparison mechanism ID.
        """

        time.sleep(delay_time)

        return

    # ***************************************************************************
    # filters
    # ***************************************************************************
    def get_all_filters(self, filter_id=0):
        """
        Return a list of all available/loaded filters.
        filter_id is the filter mechanism ID.
        """

        raise NotImplementedError

    def get_filter(self, filter_id=0):
        """
        Return the current/loaded filter, typically the filter in the beam.
        filter_id is the filter mechanism ID.
        """

        raise NotImplementedError

    def set_filter(self, filter_name, filter_id=0):
        """
        Set the current/loaded filter, typically the filter in the beam.
        filter_name is the filter name to set.
        filter_id is the filter mechanism ID.
        """

        raise NotImplementedError

    # ***************************************************************************
    # wavelengths
    # ***************************************************************************
    def get_all_wavelengths(self, wavelength_id=0):
        """
        Returns a list of valid wavelengths.
        Used for filter and LED based systems.
        wavelength_id is the wavelength mechanism ID.
        """

        raise NotImplementedError

    def get_wavelength(self, wavelength_id=0):
        """
        Returns the current wavelength.
        wavelength_id is the wavelength mechanism ID.
        """

        raise NotImplementedError

    def set_wavelength(self, wavelength, wavelength_id=0):
        """
        Set the current wavelength, typically for a filter or grating.
        wavelength is the wavelength value.
        wavelength_id is the wavelength mechanism ID.
        """

        raise NotImplementedError

    # ***************************************************************************
    # focus
    # ***************************************************************************
    def get_all_focus_positions(self):
        """
        Return a list of all focus positions.
        """

        raise NotImplementedError

    def get_focus(self, focus_id=0):
        """
        Return the current instrument focus position.
        focus_id is the focus mechanism ID.
        """

        raise NotImplementedError

    def set_focus(self, focus_position, focus_id=0, focus_type="absolute"):
        """
        Move (or step) the instrument focus.
        focus_position is the focus position or step size.
        focus_id is the focus mechanism ID.
        focus_type is "absolute" or "step".
        """

        raise NotImplementedError

    # ***************************************************************************
    # pressure
    # ***************************************************************************
    def get_all_pressures(self):
        """
        Return a list of all instrument pressures.
        """

        raise NotImplementedError

    def get_pressure(self, pressure_id=0):
        """
        Read an instrument pressure.
        """

        raise NotImplementedError

    def set_pressure(self, pressure, pressure_id=0):
        """
        Sets an instrument pressure.
        """

        raise NotImplementedError

    # ***************************************************************************
    # shutter
    # ***************************************************************************
    def set_shutter(self, state, shutter_id=0):
        """
        Open or close the instrument shutter.
        state is 1 for open and 0 for close.
        shutter_id is the shutter mechanism ID.
        """

        raise NotImplementedError

    # ***************************************************************************
    # electrometer
    # ***************************************************************************
    def get_current(self, current_id=0, shutter_state=1):
        """
        Read electrometer diode current in Amps.
        current_id = 0 is the sphere (Reference) diode.
        current_id = 1 is the calibrated diode or DUT.
        ShutterState is 0, 1 to close/open shutter during read or 2 unchanged.
        """

        raise NotImplementedError
