import json

import azcam.testers.report
import azcam


class TesterBase(object):
    """
    Base class inherited by all detchar classes.
    """

    def __init__(self, obj_id=None):

        #: tester name
        self.name = ""

        #: tester ID
        self.obj_id = obj_id

        # acquistion
        self.number_images_acquire = 1  # number of images to acquire

        # analysis
        self.grade = "UNDEFINED"  # final grade
        self.grade_sensor = True  # True to produce a grade

        self.valid = False  # flag True if analysis results are valid

        # data and reports
        self.data_file = "base.txt"
        self.dataset = {}

        self.report_file = "base"  # no extension, will be pdf, md, or rst
        self.create_reports = True  # True to generate reports during analysis

        self.create_plots = True  # True to generate plots during analysis

        self.create_html = True

        setattr(azcam.db, obj_id, self)
        azcam.db.cli_cmds[obj_id] = self

    def acquire(self):
        """
        Acquire data.
        """

        return "not supported"

    def analyze(self):
        """
        Analyze data.
        """

        return "not supported"

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
        Read data file and set object as valid.
        """

        if filename == "prompt":
            f = azcam.utils.file_browser(
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

        lines = []

        return lines

    def write_report(self, report_file, lines=[]):
        """
        Create report file.
        """

        # Make report file
        azcam.testers.report.make_mdfile(report_file, lines)
        azcam.testers.report.md2pdf(report_file, create_html=self.create_html)

        return
