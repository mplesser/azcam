"""
Contains the Focus class.
"""

import time

import azcam
import azcam.utils
import azcam.exceptions
from azcam.tools.tools import Tools


class Focus(Tools):
    """
    Class for focusing a camera.

    Either the telescope or instrument may be moved for focus adjustment.
    The focus sequence performed is:

    - integrate
    - move focus
    - shift detector (2x last time)
    - (repeat above steps)
    - readout
    - return to starting focus position
    - save image
    """

    def __init__(self, tool_id="focus", description=None):
        """
        Create focus tool.
        """

        super().__init__(tool_id, description)

        #: Number of exposures in focus sequence
        self.number_exposures = 7
        #: Number of focus steps between each exposure in a frame
        self.focus_step = 30
        #: Number of rows to shift detector for each focus step
        self.detector_shift = 10
        #: current focus position
        self.focus_position = 0
        #: exposure time
        self.exposure_time = 1.0
        #: focus component for motion - instrument or telescope
        self.focus_component = "instrument"
        #: focus type, absolute or step
        self.focus_type = "absolute"
        #: flag to not prompt when set_pars already called
        self.set_pars_called = 0
        #: delay in seconds between exposures
        self.move_delay = 3

    def initialize(self):
        """
        Initialize focus routine.
        """

        self.exposure = azcam.db.tools["exposure"]
        try:
            self.instrument = azcam.db.tools["instrument"]
        except Exception:
            self.instrument = None
        try:
            self.telescope = azcam.db.tools["telescope"]
        except Exception:
            self.telescope = None
            pass

        self.is_initialized = 1

        return

    def abort(self):
        """
        Abort focus exposure.
        """

        self.exposure.abort()

        return

    def set_pars(
        self,
        exposure_time: float,
        number_exposures: int = 7,
        focus_step: float = 30,
        detector_shift: int = 10,
    ):
        """
        Set focus related parameters.
        Args:
            number_exposures: Number of exposures in focus sequence.
            focus_step: Number of focus steps between each exposure in a frame.
            detector_shift: Number of rows to shift detector for each focus step.
            exposuretime: Exposure time i seconds.

        """

        self.exposure_time = float(exposure_time)
        self.number_exposures = int(number_exposures)
        self.focus_step = float(focus_step)
        self.detector_shift = int(detector_shift)

        self.set_pars_called = 1

        return

    def _get_focus(self) -> float:
        """
        Get focus using default focus_id.
        """

        if self.focus_component == "instrument":
            return self.instrument.get_focus()
        elif self.focus_component == "telescope":
            return self.telescope.get_focus()

    def _set_focus(self, focus_value: float):
        """
        Set focus using default focus_id and focus_type
        """

        if self.focus_component == "instrument":
            return self.instrument.set_focus(focus_value, focus_type=self.focus_type)
        elif self.focus_component == "telescope":
            return self.telescope.set_focus(focus_value, focus_type=self.focus_type)

    def save_keywords(self):
        """
        Save focus related keywords for image header.
        """

        if self.focus_component == "instrument":
            reply = self.instrument.get_focus()
            self.instrument.set_keyword(
                "FOCSTART", reply, "starting focus value", "str"
            )
            self.instrument.set_keyword(
                "FOCSTEP", self.focus_step, "focus step size", "float"
            )
            self.instrument.set_keyword(
                "FOCSHIFT", self.detector_shift, "focus detector shift pixels", "int"
            )
            self.instrument.set_keyword(
                "FOCSTEPS", self.number_exposures, "focus number of exposures", "int"
            )
        elif self.focus_component == "telescope":
            reply = self.telescope.get_focus()
            self.telescope.set_keyword("FOCSTART", reply, "starting focus value", "str")
            self.telescope.set_keyword(
                "FOCSTEP", self.focus_step, "focus step size", "float"
            )
            self.telescope.set_keyword(
                "FOCSHIFT", self.detector_shift, "focus detector shift pixels", "int"
            )
            self.telescope.set_keyword(
                "FOCSTEPS", self.number_exposures, "focus number of exposures", "int"
            )

        return

    def run(
        self,
        exposure_time: float,
        number_exposures: int = 7,
        focus_step: float = 30,
        detector_shift: int = 10,
    ):
        """
        Execute the focus sequence.
        If focus.set_pars() was previously called then those values are used and input here is ignored.
        Args:
            number_exposures: Number of exposures in focus sequence.
            focus_step: Number of focus steps between each exposure in a frame.
            detector_shift: Number of rows to shift detector for each focus step.
            exposuretime: Exposure time in seconds.
        """

        if self.set_pars_called:
            pass

        else:
            self.exposure_time = float(exposure_time)
            self.number_exposures = int(number_exposures)
            self.focus_step = int(focus_step)
            self.detector_shift = int(detector_shift)

        abort_flag = 0

        # exposure time - zero not allowed for focus
        self.exposure.set_exposuretime(self.exposure_time)
        ExpTime = self.exposure.get_exposuretime()
        if ExpTime < 0.001:
            azcam.exceptions.warning("do not focus with zero exposure time")
            return
        self.exposure.set_exposuretime(self.exposure_time)

        # save parameters to be changed
        root = azcam.db.parameters.get_par("imageroot")
        includesequencenumber = azcam.db.parameters.get_par(
            "imageincludesequencenumber"
        )
        autoname = azcam.db.parameters.get_par("imageautoname")
        autoincrementsequencenumber = azcam.db.parameters.get_par(
            "imageautoincrementsequencenumber"
        )
        title = azcam.db.parameters.get_par("imagetitle")
        testimage = azcam.db.parameters.get_par("imagetest")
        imagetype = azcam.db.parameters.get_par("imagetype")

        azcam.db.parameters.set_par("imageroot", "focus.")
        azcam.db.parameters.set_par("imageincludesequencenumber", 1)
        azcam.db.parameters.set_par("imageautoname", 0)
        azcam.db.parameters.set_par("imageautoincrementsequencenumber", 1)
        azcam.db.parameters.set_par("imagetest", 0)
        azcam.db.parameters.set_par("imageoverwrite", 1)

        # set header keywords
        self.save_keywords()

        # start
        self.exposure.begin(self.exposure_time, "object", "Focus")

        # loop over FocusNumber integrations
        current_exposure = 1

        # get starting focus
        current_focus_position = self._get_focus()
        starting_focus_value = current_focus_position

        nsteps = 0  # total number of focus steps
        while current_exposure <= self.number_exposures:
            # check for abort
            k = azcam.utils.check_keyboard(0)
            ab = azcam.db.abortflag
            if k == "q" or ab:
                abort_flag = 1
                break

            if current_exposure > 1:
                if self.focus_type == "step":
                    self._set_focus(self.focus_step)
                    nsteps += self.focus_step
                elif self.focus_type == "absolute":
                    self._set_focus(
                        current_focus_position + self.focus_step,
                    )
                time.sleep(self.move_delay)
                reply = self._get_focus()
                current_focus_position = reply
                current_focus_position = float(current_focus_position)

                # shift detector
                self.exposure.parshift(self.detector_shift)
                if current_exposure == self.number_exposures:
                    azcam.log("Last exposure, double shifting")
                    self.exposure.parshift(self.detector_shift)

            azcam.log(
                "Next exposure is %d of %d at focus position %.3f"
                % (current_exposure, self.number_exposures, current_focus_position)
            )

            # integrate
            azcam.log("Integrating")
            try:
                self.exposure.integrate()
            except azcam.exceptions.AzcamError:
                azcam.log("Focus exposure aborted")
                self._set_focus(starting_focus_value)
                azcam.db.parameters.set_par("imageroot", root)
                azcam.db.parameters.set_par(
                    "imageincludesequencenumber", includesequencenumber
                )
                azcam.db.parameters.set_par("imageautoname", autoname)
                azcam.db.parameters.set_par(
                    "imageautoincrementsequencenumber", autoincrementsequencenumber
                )
                azcam.db.parameters.set_par("imagetest", testimage)
                azcam.db.parameters.set_par("imagetitle", title)
                azcam.db.parameters.set_par("imagetype", imagetype)
                fp = self._get_focus()
                azcam.log("Current focus: %.3f" % fp)
                return

            # increment focus number
            current_exposure += 1

        # set focus back to starting position
        azcam.log("Returning focus to starting value %.3f" % starting_focus_value)
        if self.focus_type == "step":
            steps = -1 * nsteps
            self._set_focus(steps)
        elif self.focus_type == "absolute":
            self._set_focus(starting_focus_value)
        time.sleep(self.move_delay)
        fp = self._get_focus()
        azcam.log("Current focus: %.3f" % fp)

        if not abort_flag:
            # readout and finish
            azcam.log("Reading out")
            self.exposure.readout()
            self.exposure.end()
        else:
            azcam.db.parameters.set_par("ExposureFlag", azcam.db.exposureflags["NONE"])

        # finish
        azcam.db.parameters.set_par("imageroot", root)
        azcam.db.parameters.set_par("imageincludesequencenumber", includesequencenumber)
        azcam.db.parameters.set_par("imageautoname", autoname)
        azcam.db.parameters.set_par(
            "imageautoincrementsequencenumber", autoincrementsequencenumber
        )
        azcam.db.parameters.set_par("imagetest", testimage)
        azcam.db.parameters.set_par("imagetitle", title)
        azcam.db.parameters.set_par("imagetype", imagetype)

        return
