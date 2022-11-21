"""
Report generation class.
"""

import os
import subprocess

import pdfkit
from markdown import markdown
from PyPDF2 import PdfFileMerger, PdfFileReader


class Report(object):
    """
    Report generation methods.
    """

    def __init__(self):

        self.report_css = os.path.join(
            os.path.dirname(os.path.abspath(__file__)), "report.css"
        )

    def make_rstfile(self, rst_file, lines=[]):
        """
        Create an RST file from lines.
        """

        basefile, ext = os.path.splitext(rst_file)
        if ext == "":
            rst_file = f"{basefile}.rst"

        # Write RSTfile
        with open(rst_file, "w") as f:
            for line in lines:
                f.write(line + "\n")

        return

    def make_mdfile(self, md_file, lines=[]):
        """
        Create a markdown file from lines.
        """

        basefile, ext = os.path.splitext(md_file)
        if ext == "":
            md_file = f"{basefile}.md"

        with open(md_file, "w") as f:
            for line in lines:
                f.write(line + "\n")

        return

    def merge_pdf(self, input_files=[], output_file="combined.pdf"):
        """
        Merge multiple PDF files into one.
        """

        merger = PdfFileMerger()
        for filename in input_files:
            f = str(filename)  # no unicode
            merger.append(PdfFileReader(open(f, "rb")), import_bookmarks=False)

        merger.write(str(output_file))

        return

    def rst2pdf(self, filename, options=[]):
        """
        Create a PDF from an RST file.
        Filename extension is optional.
        Also create an html file (currently required).
        """

        basefile, ext = os.path.splitext(filename)
        html_file = f"{basefile}.html"
        pdf_file = f"{basefile}.pdf"
        if ext == "":
            rst_file = f"{filename}.rst"
        else:
            rst_file = filename

        # make PDF report, html first
        with open(os.devnull, "w") as fnull:
            folder = os.path.abspath(os.path.curdir)
            s = "rst2html.py < %s > %s" % (rst_file, html_file)
            p1 = subprocess.Popen(s, shell=True, cwd=folder, stdout=fnull, stderr=fnull)
            p1.wait()

        # options = "-b 1 -s letter,twelvepoint"
        options = {
            "quiet": "",
            "page-size": "Letter",
            "margin-top": "0.5in",
            "margin-right": "0.75in",
            "margin-bottom": "0.5in",
            "margin-left": "0.75in",
            "encoding": "UTF-8",
            "no-outline": None,
        }
        pdfkit.from_file(html_file, pdf_file, options=options, css=self.report_css)

        return

    def md2pdf(self, filename, options=[], create_html=False):
        """
        Create a PDF from a markdown file.
        Filename extension is optional.
        Optionally also create an html file.
        """

        basefile, ext = os.path.splitext(filename)
        pdf_file = f"{basefile}.pdf"
        if ext == "":
            md_file = f"{filename}.md"
        else:
            md_file = filename

        with open(md_file, "r") as f:
            html_text = markdown(
                f.read(),
                extensions=["tables"],
                output_format="html",
                css=self.report_css,
            )

        if create_html:
            html_file = f"{basefile}.html"
            with open(html_file, "w") as f:
                f.writelines(html_text)

        if options == []:
            options = {
                "quiet": "",
                "page-size": "Letter",
                "margin-top": "0.5in",
                "margin-right": "0.75in",
                "margin-bottom": "0.5in",
                "margin-left": "0.75in",
                "encoding": "UTF-8",
                "no-outline": None,
                "enable-local-file-access": None,
            }
        pdfkit.from_string(html_text, pdf_file, options, css=self.report_css)

        return
