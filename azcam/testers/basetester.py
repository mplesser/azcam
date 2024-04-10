import json

import azcam
import azcam.console
from azcam.tools import Tools
from azcam.testers.report import Report


class Tester(Tools, Report):
    """
    Base class inherited by all tester classes.
    """

    def __init__(self, tool_id, description=None):
        Tools.__init__(self, tool_id, description)

        Report.__init__(self)

        self.itl_id = ""

        self.number_images_acquire = 1
        """number of images to acquire"""

        self.rootname = "tester."
        """root for data filenames"""

        # analysis
        self.grade = "UNDEFINED"
        """final grade"""

        self.grade_sensor = True
        """True to produce a grade"""

        self.valid = False
        """True if analysis results are valid"""

        self.data_file = "base.txt"
        """output data file"""

        self.dataset = {}
        """output 3D cube of image data"""

        #: output report file
        self.report_file = "base"
        """no extension, will be pdf or md"""

        self.create_reports = True
        """True to generate reports during analysis"""

        self.create_plots = True
        """True to generate plots during analysis"""

        self.create_html = False
        """True to create HTML analysis reports"""

        # all testers are initialized and reset at creation
        self.initialize()
        self.reset()

    def acquire(self):
        """
        Acquire data.
        """

        raise NotImplementedError("acquire() not defined")

    def analyze(self):
        """
        Analyze data.
        """

        raise NotImplementedError("analyze() not defined")

    def write_datafile(self):
        """
        Write data file as a json dump.

        Note: numpy.array(x).tolist() may be useful for dataset.
        """

        with open(self.data_file, "w") as datafile:
            json.dump(self.dataset, datafile)

        return

    def read_datafile(self, filename="default"):
        """
        Read an existing data file and set tool as valid.
        """

        if filename == "prompt":
            f = azcam.console.utils.file_browser(
                self.data_file, [("data files", ("*.txt"))], Label="Select data file"
            )
            if f is not None and f != "":
                self.data_file = f[0]
        elif filename == "default":
            filename = self.data_file

        # read file
        with open(filename, "r") as datafile:
            dataline = datafile.readlines()

        self.dataset = json.loads(dataline[0])

        for data in self.dataset:
            setattr(self, data, self.dataset[data])

        self.valid = True

        return

    def report(self):
        """
        Generate a report.
        """

        raise NotImplementedError("report() not defined")
