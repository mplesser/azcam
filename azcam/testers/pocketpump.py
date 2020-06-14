import os

import azcam
from azcam.console import api
import azcam.testers
from azcam.testers.testerbase import TesterBase


class PocketPump(TesterBase):
    """
    Pocket pumping (trap) acquisition and analysis.
    """

    def __init__(self):

        super().__init__("pocketpump")

        self.exposure_type = "flat"
        self.exposure_time = 1.0
        self.exposure_level = -1
        self.number_cycles = 1000
        self.shift_rows = 1
        self.wavelength = 600.0

        self.data_file = "traps.txt"
        self.report_file = "traps"

        self.total_traps = 0  # should be -1

        self.means = []
        self.sdev = []
        self.temperatures = []
        self.pocketpump_timing_file = "STA3800C_config1.lod"  # example

    def acquire(self):
        """
        Make a pocket pump image sequence.
        """

        return self.acquire_archon()

    def acquire_arc(self):
        """
        Make a pocket pump image sequence.
        """

        azcam.log("Acquiring PocketPump sequence")

        # save pars to be changed
        impars = {}
        api.save_imagepars(impars)

        api.set_par("imageroot", "pocketpump.")  # for automatic data analysis
        api.set_par("imageincludesequencenumber", 1)  # use sequence numbers
        api.set_par("imageautoname", 0)  # manually set name
        api.set_par("imageautoincrementsequencenumber", 1)  # inc sequence numbers
        api.set_par("imagetest", 0)

        # create and move to new subfolder
        currentfolder, newfolder = azcam.utils.make_file_folder("pocketpump")
        api.set_par("imagefolder", newfolder)

        # set wavelength so exposure time is correct
        azcam.log(f"Setting wavelength to {self.wavelength}")
        api.set_wavelength(self.wavelength)

        # set proper timing code, reset, and clear device
        timingfile_org = api.get_par("TimingFile")
        timcode = os.path.dirname(timingfile_org)
        timcode = os.path.join(timcode, self.pocketpump_timing_file)
        timcode = timcode.replace("\\", "/")
        azcam.log("PocketPump timing code will be: %s" % timcode)
        api.set_par("TimingFile", timcode)
        api.reset()
        api.tests(2)

        # take a bias
        azcam.log("Taking first pocketpump bias")
        try:
            api.expose(0, "zero", "pocketpump first bias")
        except Exception as message:
            api.set_par("TimingFile", timingfile_org)
            api.reset()
            api.restore_imagepars(impars, currentfolder)
            raise message

        # setup exposure
        azcam.log("Pocketpump setup")
        api.begin_exposure(self.exposure_time, self.exposure_type, "pocket pump")

        # integrate
        azcam.log("Pocketpump integration")
        api.integrate_exposure()

        # pocket pump
        azcam.log("Pocket pumping...")
        for _ in range(self.number_cycles):
            api.parshift(-1 * self.shift_rows)  # reverse par shift is a complete cycle

        # readout
        azcam.log("Readout")
        api.readout_exposure()

        # write image and display
        api.end_exposure()
        azcam.log("Pocket pumped exposure completed")

        # take a bias
        azcam.log("Taking second pocketpump bias")
        try:
            api.expose(0, "zero", "pocketpump second bias")
        except Exception as message:
            api.set_par("TimingFile", timingfile_org)
            api.reset()
            api.restore_imagepars(impars, currentfolder)
            return message

        # take a reference flat of same time
        azcam.log("Taking non-pumped reference exposure")
        try:
            api.expose(
                self.exposure_time, self.exposure_type, "pocket pump reference flat"
            )

        except Exception as message:
            api.set_par("TimingFile", timingfile_org)
            api.reset()
            api.restore_imagepars(impars, currentfolder)
            raise message

        # finish
        api.set_par("TimingFile", timingfile_org)
        api.reset()
        api.restore_imagepars(impars, currentfolder)
        azcam.log("PocketPump sequence finished")

        return

    def acquire_archon(self):
        """
        Make a pocket pump image sequence.
        """

        azcam.log("Acquiring PocketPump sequence")

        # save pars to be changed
        impars = {}
        api.save_imagepars(impars)

        api.set_par("imageroot", "pocketpump.")  # for automatic data analysis
        api.set_par("imageincludesequencenumber", 1)  # use sequence numbers
        api.set_par("imageautoname", 0)  # manually set name
        api.set_par("imageautoincrementsequencenumber", 1)  # inc sequence numbers
        api.set_par("imagetest", 0)

        # create and move to new subfolder
        currentfolder, newfolder = azcam.utils.make_file_folder("pocketpump")
        api.set_par("imagefolder", newfolder)

        # set wavelength so exposure time is correct
        azcam.log(f"Setting wavelength to {self.wavelength}")
        api.set_wavelength(self.wavelength)

        # Get exposure time
        binning = 1
        if azcam.testers.detcal.valid and self.exposure_level != -1:
            azcam.log("Using exposure_level")

            meanelectrons = azcam.testers.detcal.mean_electrons

            et = self.exposure_level / meanelectrons[self.wavelength] / binning
        elif self.exposure_time != -1:
            azcam.log("Using ExposureTime")
            et = self.exposure_time
        else:
            raise azcam.AzcamError("could not determine exposure times")

        # flush well
        azcam.log("Flushing")
        api.tests(2)

        # take a bias
        azcam.log("Taking first pocketpump bias")
        try:
            api.expose(0, "zero", "pocketpump first bias")
        except Exception as message:
            api.restore_imagepars(impars, currentfolder)
            raise message

        # turn on pocketpumping
        api.rcommand("controller.set_pocket_pumping 1")

        # expose
        azcam.log("Taking pocketpump flat")
        api.expose(et, "flat", "pocketpump flat")

        # turn off pocketpumping
        api.rcommand("controller.set_pocket_pumping 0")

        # take a bias
        azcam.log("Taking second pocketpump bias")
        try:
            api.expose(0, "zero", "pocketpump second bias")
        except Exception as message:
            api.restore_imagepars(impars, currentfolder)
            raise message

        # take a reference flat of same time
        azcam.log("Taking non-pumped reference exposure")
        try:
            api.expose(et, self.exposure_type, "pocket pump reference flat")

        except Exception as message:
            api.restore_imagepars(impars, currentfolder)
            raise message

        # finish
        api.restore_imagepars(impars, currentfolder)
        azcam.log("PocketPump sequence finished")

        return

    def analyze(self):
        """
        Analys a pocket pump image sequence.
        Not yet supported.
        """

        self.total_traps = 0
        # self.grade='UNDEFINED'
        self.grade = "PASS"

        # define dataset
        self.dataset = {
            "data_file": self.data_file,
            "grade": self.grade,
            "total_traps": self.total_traps,
        }

        # write output files
        self.write_datafile()
        if self.create_reports:
            self.report()

        return
