import os
import datetime

from azcam.console import azcam
from azcam.testers.report import Report


class DetChar(Report):
    """
    Base DetChar class.
    """

    def __init__(self, obj_id="detchar"):

        super().__init__()

        self.obj_id = obj_id
        self.name = ""

        self.is_setup = 0
        self.create_html = True

        setattr(azcam.api, obj_id, self)
        azcam.db.cli_cmds[obj_id] = self

    def initdata(self, serial_number=-1):
        """
        Initialize data taking for new sensor.
        """

        if serial_number != -1:
            sn = serial_number
        else:
            sn = azcam.utils.prompt("Enter sensor serial number")
            if sn.startswith("sn"):
                sn = sn.lstrip("sn")
            elif sn.startswith("s"):
                sn = sn.lstrip("s")

        newfolder = f"sn{sn}"
        newfolder = os.path.join(azcam.db.datafolder, newfolder)
        try:
            os.mkdir(newfolder)
        except FileExistsError as e:
            print(e)
            pass
        azcam.utils.curdir(newfolder)

        datestring = datetime.datetime.strftime(
            datetime.datetime.now(), "%d%b%y"
        ).lower()
        try:
            os.mkdir(datestring)
        except FileExistsError:
            pass
        azcam.utils.curdir(datestring)

        imagefolder = azcam.utils.curdir()
        azcam.api.set_par("imagefolder", imagefolder)

        return

    def write_report(self, report_file, lines=[]):
        """
        Create report file.
        """

        # Make report file
        self.make_mdfile(report_file, lines)
        self.md2pdf(report_file, create_html=self.create_html)

        return
