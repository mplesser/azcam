import os
import shlex
import pathlib

import matplotlib.pylab as pylab
import numpy
import scipy.optimize
from matplotlib.ticker import FormatStrFormatter
from scipy.interpolate import griddata

import azcam
from azcam.tools.testers.basetester import Tester


class Metrology(Tester):
    """
    Metrology analysis.
    This class analyzes a grid of (x,y,z) image surface points.
    """

    def __init__(self):

        super().__init__("metrology")

        self.itl_sn = -1
        self.itl_id = ""

        # inputs
        self.data_file = "metrology.txt"
        self.report_file = "metrology"

        self.standard_correct = 0
        self.standard_zheight = 13.000

        self.show_height_grade = 0
        self.z_nom = None  # must be defined before .analyze()
        self.z_spec = []  # spec [Zmin,Zmax]

        self.grade_mounting = "UNKNOWN"

        self.height_half_band_spec = None
        self.height_fraction_limit = 0.95

        self.show_quantiles = 0
        self.quantile_percents = [
            0.0,
            0.5,
            1.0,
            2.5,
            25.0,
            50.0,
            75.0,
            97.5,
            99.0,
            99.5,
            100.0,
        ]
        self.qfh0 = 3  # quantile index
        self.qfh1 = 7

        self.flatness_half_band_spec = None  # from best fit plane
        self.flatness_fraction_limit = 0.95

        # outputs
        self.grade_height = "UNKNOWN"
        self.z_mean = -1
        self.z_median = -1
        self.zsdev = -1
        self.z_mid = -1
        self.z_halfband = -1

        self.quantile_values = []
        self.flatness_quantile_values = []

        self.grade_flatness = "UNKNOWN"
        self.fmin = -1
        self.fmax = -1
        self.fsdev = -1
        self.fmid = -1
        self.f_halfband = -1

        # filename
        self.HistogramFlatnessPlot = "HistogramFlatnessPlot.png"
        self.ColorZPlot = "ColorZPlot.png"
        self.WiskerPlot = "WhiskerPlot.png"
        self.HistogramHeightPlot = "HistogramHeightPlot.png"
        self.SurfacePlot = "SurfacePlot.png"
        self.StandardPlot = "StandardPlot.png"

        # new
        self.stage_temp = None
        self.start_time = None
        self.end_time = None
        self.date = None

    def find_file(self, filename):
        """
        Find a filename starting with filename.
        """

        path = pathlib.Path(azcam.utils.curdir())

        for _, _, files in os.walk(path):
            break

        for f in files:
            if f.startswith(filename):
                break

        try:
            if not f.startswith(filename):
                raise azcam.AzcamError("file not found")
        except Exception:
            raise azcam.AzcamError("file not found")

        return f

    def analyze(self, filename=None):
        """
        Analyze existing metrology data.
        """

        azcam.log("Analyzing metrology data")

        if filename is None:
            filename = self.find_file("sn")

        # read data
        self.read_data(filename)

        # get stats
        self.z_mean = self.z.mean()
        self.z_median = numpy.median(self.z)
        self.zsdev = self.z.std()
        numpoints = len(self.z)

        azcam.log("%s\t\t%.04f" % ("Mean", self.z_mean))
        azcam.log("%s\t\t%.04f" % ("Median", self.z_median))
        azcam.log("%s\t\t%.04f" % ("Sdev", self.zsdev))
        if self.z_nom is not None:
            azcam.log("%s\t\t%.04f" % ("z_nom", self.z_nom))

        # ***********************************************************
        # analyze height
        # ***********************************************************

        if self.z_spec != []:
            fails1 = self.z < self.z_spec[0] - self.height_half_band_spec
            fails2 = self.z > self.z_spec[1] + self.height_half_band_spec
            fails = numpy.count_nonzero(fails1) + numpy.count_nonzero(fails2)
            self.heightpassfrac = (numpoints - fails) / float(numpoints)

        if self.z_spec != [] and self.show_height_grade:
            azcam.log(
                "Height: %.01f%% of points are within height specification"
                % (self.heightpassfrac * 100.0)
            )
            if self.heightpassfrac >= self.height_fraction_limit:
                self.grade_height = "PASS"
            else:
                self.grade_height = "FAIL"

            azcam.log("Height grade is %s" % self.grade_height)

        # make quantiles
        self.quantile_values = numpy.percentile(self.z, self.quantile_percents)
        if self.show_quantiles:
            azcam.log("Quantile\tHeight")
            for i, p in enumerate(self.quantile_percents):
                azcam.log("%5.01f\t\t%.04f" % (p, self.quantile_values[i]))
        self.z_halfband = (
            self.quantile_values[self.qfh1] - self.quantile_values[self.qfh0]
        ) / 2.0
        self.z_mid = (
            self.quantile_values[self.qfh1] + self.quantile_values[self.qfh0]
        ) / 2.0
        azcam.log("%s\t\t%.04f" % ("Z-mid", self.z_mid))
        azcam.log("%s\t%.04f" % ("Z-mid_HalfBand", self.z_halfband))

        # ***********************************************************
        # analyze flatness
        # ***********************************************************

        # make best fit plane
        def residuals(parameter, f, x, y):
            return [(f[i] - model(parameter, x[i], y[i])) for i in range(len(f))]

        def model(parameter, x, y):
            a, b, c = parameter
            return a * x + b * y + c

        p0 = [1.0, 1.0, 1.0]  # initial guess
        result = scipy.optimize.leastsq(residuals, p0, args=(self.z, self.x, self.y))[0]
        a = result[0]
        b = result[1]
        c = result[2]

        # make fitted plane z values
        self.zfit = a * self.x + b * self.y + c
        self.flatnessresiduals = self.z - self.zfit
        self.flatnessresiduals = numpy.array(self.flatnessresiduals)

        # get flatness Quantiles
        self.flatness_quantile_values = numpy.percentile(
            self.flatnessresiduals, self.quantile_percents
        )
        if self.show_quantiles:
            azcam.log("Quantile\tFlatness")
            for i, p in enumerate(self.quantile_percents):
                azcam.log("%5.01f\t\t%.01f" % (p, self.flatness_quantile_values[i]))
        self.f_halfband = (
            self.flatness_quantile_values[self.qfh1]
            - self.flatness_quantile_values[self.qfh0]
        ) / 2.0
        self.fmid = (
            self.flatness_quantile_values[self.qfh1]
            + self.flatness_quantile_values[self.qfh0]
        ) / 2.0
        azcam.log("%s\t\t%.04f" % ("F-mid", self.fmid))
        azcam.log("%s\t%.04f" % ("F-mid_HalfBand", self.f_halfband))

        # get flatness stats
        self.FMean = self.flatnessresiduals.mean()
        self.FMedian = numpy.median(self.flatnessresiduals)
        self.fsdev = self.flatnessresiduals.std()
        self.fmin = self.flatnessresiduals.min()
        self.fmax = self.flatnessresiduals.max()
        numpoints = len(self.flatnessresiduals)  # same as numpoints above

        # measure flatness residuals
        if self.flatness_half_band_spec is not None:
            fails = abs(self.flatnessresiduals) > self.flatness_half_band_spec
            fails = numpy.count_nonzero(fails)
            self.flatnesspassfract = (numpoints - fails) / float(numpoints)

            azcam.log(
                "Flatness: %.01f%% of points are within flatness spec (%.03f)"
                % (self.flatnesspassfract * 100.0, self.flatness_half_band_spec)
            )

            if self.flatnesspassfract >= self.flatness_fraction_limit:
                self.grade_flatness = "PASS"
            else:
                self.grade_flatness = "FAIL"

            azcam.log("Flatness grade is %s" % self.grade_flatness)

        self.valid = 1

        # report on standard
        if self.standard_correct:
            zstandard_min = self.zstandard.min()
            zstandard_max = self.zstandard.max()
            # zstandard_mean=self.zstandard.mean()
            # zstandard_std=self.zstandard.std()
            s = "Z-Standard (mm): Min=%.04f, Max=%.04f" % (zstandard_min, zstandard_max)
            azcam.log(s)

        # make plots
        if self.create_plots:
            self.plot()

        # define dataset
        self.dataset = {
            "data_file": self.data_file,
            "grade": self.grade,
            "itl_sn": self.itl_sn,
            "itl_id": self.itl_id,
            "grade_mounting": self.grade_mounting,
            "z_nom": self.z_nom,
            "z_spec": self.z_spec,
            "z_mean": self.z_mean,
            "z_median": self.z_median,
            "zsdev": self.zsdev,
            "z95": self.z_mid,
            "halfband": self.z_halfband,
            "quantile_percents": list(self.quantile_percents),
            "quantile_values": list(self.quantile_values),
            "grade_flatness": self.grade_flatness,
            "f_halfband": self.f_halfband,
            "fsdev": self.fsdev,
            "fmin": self.fmin,
            "fmax": self.fmax,
            "fmid": self.fmid,
            "flatness_quantile_values": list(self.flatness_quantile_values),
            "ColorZPlot": self.ColorZPlot,
            "WiskerPlot": self.WiskerPlot,
            "HistogramHeightPlot": self.HistogramHeightPlot,
            "HistogramFlatnessPlot": self.HistogramFlatnessPlot,
            "SurfacePlot": self.SurfacePlot,
        }

        # write output files
        self.write_datafile()
        if self.create_reports:
            self.report()

        return

    def plot(self):
        """
        Make metrology plots.
        """

        zmin = self.z_mid - 0.010
        zmax = self.z_mid + 0.010

        # surface plot
        zz = list(map(float, self.z))
        grid_x, grid_y = numpy.mgrid[
            min(self.x) : max(self.x) : 100j, min(self.y) : max(self.y) : 100j
        ]
        grid_z = griddata((self.x, self.y), zz, (grid_x, grid_y), method="cubic")

        fig = azcam.plot.plt.figure()
        fignum = fig.number
        azcam.plot.move_window(fignum)
        ax = azcam.plot.plt.axes(projection="3d")
        ax.plot_surface(
            grid_x,
            grid_y,
            grid_z,
            rstride=1,
            cstride=1,
            cmap=pylab.get_cmap("coolwarm"),
            linewidth=0,
            antialiased=False,
            alpha=0.9,
        )
        ax.zaxis.set_major_formatter(FormatStrFormatter("%.03f"))
        ax.set_xlabel("X [mm]")
        ax.set_ylabel("Y [mm]")
        ax.set_zlabel("Z [mm]")
        azcam.plot.plt.title("Surface Plot with Best Fit Plane")
        ax.view_init(elev=25.0, azim=-55)  # improve perspective

        # least squares plane plot on surface plot
        zz = list(map(float, self.zfit))
        grid_x, grid_y = numpy.mgrid[
            min(self.x) : max(self.x) : 100j, min(self.y) : max(self.y) : 100j
        ]
        grid_z = griddata((self.x, self.y), zz, (grid_x, grid_y), method="cubic")
        ax.plot_surface(
            grid_x,
            grid_y,
            grid_z,
            rstride=1,
            cstride=1,
            cmap=pylab.get_cmap("gray"),
            linewidth=0,
            antialiased=False,
            alpha=0.1,
        )
        ax.set_zlim(zmin, zmax)

        azcam.plot.save_figure(fignum, self.SurfacePlot)

        # height histogram plot
        fig = azcam.plot.plt.figure()
        fignum = fig.number
        azcam.plot.move_window(fignum)
        azcam.plot.plt.title("Height Histogram Plot")
        azcam.plot.plt.hist(
            self.z,
            bins="auto",
            facecolor="green",
            alpha=0.8,
            histtype="stepfilled",
            rwidth=0.8,
        )
        ax = azcam.plot.plt.gca()
        ax.set_xlabel("Z (mm)")
        ax.xaxis.set_major_formatter(FormatStrFormatter("%.03f"))
        ax.set_ylabel("Points")
        ax.grid(1)

        # draw lines for interesting data
        if self.z_nom is not None:
            names = ["Z_nom", "Z-mid", "Z-L", "Z-U", "Z-1", "Z-2"]
            colors = ["g", "b", "r", "r", "black", "black"]
            xlines = [
                self.z_nom,
                self.z_mid,
                self.z_nom - self.height_half_band_spec,
                self.z_nom + self.height_half_band_spec,
                self.z_mid - self.z_halfband,
                self.z_mid + self.z_halfband,
            ]
        else:
            xlines = [self.z_mid]
            names = ["Z-mid"]
            colors = ["b", "r", "r"]
        for i, xline in enumerate(xlines):
            azcam.plot.plt.axvline(x=xline, linewidth=1, color=colors[i])
            ypos = 0.9 * ax.get_ylim()[1]
            if names[i] in ["Z_nom", "Z-L", "Z-U"]:
                ypos = 0.9 * ax.get_ylim()[1]
            else:
                ypos = 0.8 * ax.get_ylim()[1]
            ax.text(
                xline,
                ypos,
                names[i],
                bbox=dict(facecolor="red", alpha=0.2),
                horizontalalignment="center",
                rotation="horizontal",
                fontsize=12,
            )

        azcam.plot.save_figure(fignum, self.HistogramHeightPlot)

        # flatness histogram plot
        fig = azcam.plot.plt.figure()
        fignum = fig.number
        azcam.plot.move_window(fignum)
        azcam.plot.plt.title("Flatness Histogram Plot")
        azcam.plot.plt.hist(
            self.flatnessresiduals,
            bins="auto",
            facecolor="green",
            alpha=0.8,
            histtype="stepfilled",
            rwidth=0.8,
        )
        ax = azcam.plot.plt.gca()
        ax.set_xlabel("Relative Z (mm)")
        ax.xaxis.set_major_formatter(FormatStrFormatter("%.03f"))
        ax.set_ylabel("Points")
        ax.grid(1)

        # draw lines for interesting data
        xlines = []
        names = ["FSpec-L", "FSpec-U"]
        colors = ["r", "r"]
        for i, xline in enumerate(xlines):
            azcam.plot.plt.axvline(x=xline, linewidth=1, color=colors[i])
            ypos = 0.9 * ax.get_ylim()[1]
            ax.text(
                xline,
                ypos,
                names[i],
                bbox=dict(facecolor="red", alpha=0.2),
                horizontalalignment="center",
                rotation="horizontal",
                fontsize=12,
            )

        azcam.plot.save_figure(fignum, self.HistogramFlatnessPlot)

        # color Z value plot
        fig = azcam.plot.plt.figure()
        fignum = fig.number
        azcam.plot.move_window(fignum)
        # ax = azcam.plot.plt.gca()
        ax = azcam.plot.plt.gca()
        ax.set_xlabel("X [mm]")
        ax.set_ylabel("Y [mm]")
        azcam.plot.plt.title("Color Z Plot")
        # azcam.plot.plt.scatter(self.x, self.y, s=40, c=self.z, marker="s", lw=0)
        N = int(len(self.z) ** 0.5)
        self.z2 = self.z.reshape(N, N)
        azcam.plot.plt.imshow(
            self.z2,
            extent=(
                numpy.amin(self.x),
                numpy.amax(self.x),
                numpy.amin(self.y),
                numpy.amax(self.y),
            ),
            interpolation="quadric",
            cmap="viridis",
        )
        azcam.plot.plt.axis("equal")

        cb = azcam.plot.plt.colorbar(format="%.03f")
        cb.set_label("Height [mm]")
        labels = []
        if 0:
            for lab in self.z:
                labels.append("%.03f" % float(lab))
            for label, x1, y1 in zip(labels, self.x, self.y):
                azcam.plot.plt.annotate(
                    label,
                    xy=(x1, y1),
                    textcoords="data",
                    ha="center",
                    va="center",
                    bbox=dict(boxstyle="round,pad=0", fc="yellow", alpha=0.3),
                    fontsize=6,
                )
        azcam.plot.save_figure(fignum, self.ColorZPlot)

        # box and whisker plot
        fig, ax = azcam.plot.plt.subplots()
        fignum = fig.number
        azcam.plot.move_window(fignum)
        ax.set_ylabel("Z [mm]")
        ax.yaxis.set_major_formatter(FormatStrFormatter("%.03f"))
        azcam.plot.plt.title("Box and Whisker Plot")
        ax.boxplot(self.z, notch=True)
        azcam.plot.plt.xticks([])
        azcam.plot.save_figure(fignum, self.WiskerPlot)

        # show standard drift
        if self.standard_correct:
            fig = azcam.plot.plt.figure()
            fignum = fig.number
            azcam.plot.move_window(fignum)
            ax = azcam.plot.plt.gca()
            azcam.plot.plt.title("Z-Standard Drift")
            ax.set_xlabel("Row")
            ax.set_ylabel("Z [microns]")
            ax.xaxis.set_major_locator(
                azcam.plot.plt.MaxNLocator(integer=True)
            )  # integer row numbers
            drift_1 = self.standard1_z - self.standard_zheight
            azcam.plot.plt.plot(drift_1)
            drift_2 = self.standard2_z - self.standard_zheight
            azcam.plot.plt.plot(drift_2)
            drift_3 = self.standard3_z - self.standard_zheight
            azcam.plot.plt.plot(drift_3)
            drift_4 = self.standard4_z - self.standard_zheight
            azcam.plot.plt.plot(drift_4)
            drift_mean = self.zstandard - self.standard_zheight
            azcam.plot.plt.plot(drift_mean)
            azcam.plot.save_figure(fignum, self.StandardPlot)

        azcam.plot.plt.show()

        return

    def report(self):
        """
        Write report file.
        """

        lines = []

        lines.append("# Metrology Analysis")
        lines.append("")

        s = f"ITL Serial Number = sn{self.itl_sn}"
        lines.append(s)
        lines.append("")

        if self.itl_id != "":
            s = f"Package ID = {self.itl_id}"
            lines.append(s)
            lines.append("")

        if self.stage_temp:
            s = f"Stage temperature = {self.stage_temp} C"
            lines.append(s)
            lines.append("")

        if self.start_time:
            s = f"Start time = {self.start_time} "
            lines.append(s)
            lines.append("")

        if self.date:
            s = f"Acquisition date = {self.date} "
            lines.append(s)
            lines.append("")

        if self.grade_mounting != "UNKNOWN":
            s = f"Mounting pin grade = {self.grade_mounting}"
            lines.append(s)
            lines.append("")

        if self.show_height_grade:
            s = f"Height grade = {self.grade_height}"
            lines.append(s)
            lines.append("")

        s = f"Flatness grade = {self.grade_flatness}"
        lines.append(s)
        lines.append("")

        if self.z_nom is not None:
            s = f"Z-Nom = {self.z_nom:.03f} mm"
            lines.append(s)
            lines.append("")
        if self.show_height_grade:
            s = f"Minimum Z-height Spec. {(self.height_fraction_limit * 100):.0f}% = {(self.z_nom - self.height_half_band_spec):.03f} mm"
            lines.append(s)
            lines.append("")
            s = f"Maximum Z-height Spec. {(self.height_fraction_limit * 100):0f} = {(self.z_nom + self.height_half_band_spec):.03f} mm"
            lines.append(s)
            lines.append("")

        s = f"Z Mean = {self.z_mean:.03f} mm"
        lines.append(s)
        lines.append("")
        s = f"Z Median = {self.z_median:.03f} mm"
        lines.append(s)
        lines.append("")
        s = f"Z-Mid = {self.z_mid:.03f} mm"
        lines.append(s)
        lines.append("")
        s = f"Z Sdev = {self.zsdev:.03f} mm"
        lines.append(s)
        lines.append("")

        if self.flatness_half_band_spec is not None:
            s = "Flatness Halfband Spec. (%.0f%%) = %.03f mm" % (
                self.flatness_fraction_limit * 100,
                self.flatness_half_band_spec,
            )
            lines.append(s)
            lines.append("")
            s = "Flatness Halfband = %.03f mm" % self.f_halfband
            lines.append(s)
            lines.append("")
        s = "Flatness Sdev = %.03f mm" % self.fsdev
        lines.append(s)
        lines.append("")
        s = "Flatness Minimum = %.03f mm" % self.fmin
        lines.append(s)
        lines.append("")
        s = "Flatness Maximum = %.03f mm" % self.fmax
        lines.append(s)
        lines.append("")

        lines.append("|Quantiles (%) |Height (mm)|Flatness (mm)|")
        s = "|:---|:---|:---|"
        lines.append(s)
        for i, p in enumerate(self.quantile_percents):
            s = f"|{p:.01f}|{self.quantile_values[i]:.04f}|{self.flatness_quantile_values[i]:.03f}|"
            lines.append(s)
        lines.append("")

        lines.append(
            f"![Z-Height Histogram]({os.path.abspath(self.HistogramHeightPlot)})  "
        )
        lines.append("")
        lines.append(f"Z-Height Histogram.")
        lines.append("")

        lines.append(
            f"![Flatness Histogram]({os.path.abspath(self.HistogramFlatnessPlot)})  "
        )
        lines.append("")
        lines.append(f"Flatness Histogram.")
        lines.append("")

        lines.append(f"![Z-Height Histogram]({os.path.abspath(self.SurfacePlot)})  ")
        lines.append("")
        lines.append(f"Surface Plot.")
        lines.append("")

        lines.append(f"![Z-Height Histogram]({os.path.abspath(self.ColorZPlot)})  ")
        lines.append("")
        lines.append(f"Color Z-Plot.")
        lines.append("")

        lines.append(f"![Z-Height Histogram]({os.path.abspath(self.WiskerPlot)})  ")
        lines.append("")
        lines.append(f"BoxWisker Plot.")
        lines.append("")

        # Make report files
        report_file = f"{self.report_file}_sn{self.itl_sn}"
        self.write_report(report_file, lines)

        return

    def read_data(self, filename=""):

        # get filename
        if filename == "":
            filename = azcam.utils.prompt("Enter data filename", "viewdata.txt")

        azcam.log("Data file is %s" % filename)

        # read file
        with open(filename, "r") as f:
            lines = f.readlines()

        x = []
        y = []
        z = []

        standard1_x = []
        standard1_y = []
        standard1_z = []

        standard2_x = []
        standard2_y = []
        standard2_z = []

        standard3_x = []
        standard3_y = []
        standard3_z = []

        standard4_x = []
        standard4_y = []
        standard4_z = []

        self.zstandard = []

        zoffset = 0.0

        # raw output datafile
        with open(
            f"{os.path.splitext(os.path.basename(filename))[0]}_out.csv", "w"
        ) as fout:

            for line in lines:
                line = line.strip()
                if line == "":
                    continue

                tokens = shlex.split(line)

                # lineout = ",".join([f"{x}" for x in tokens])
                # fout.write(f"{lineout}\n")

                if tokens[0] == "Engraved" and tokens[1] == "ID":
                    self.itl_id = tokens[3]
                    azcam.log("ID is %s" % self.itl_id)

                elif tokens[0] == "DATE":
                    self.date = tokens[2]
                    azcam.log(f"Data acquisition date is {self.date}")

                elif tokens[0] == "START" and tokens[1] == "TIME":
                    self.start_time = tokens[3]
                    azcam.log(f"Start time is {self.start_time}")

                elif tokens[0] == "END" and tokens[1] == "TIME":
                    self.end_time = tokens[3]
                    azcam.log(f"End time is {self.start_time}")

                elif tokens[0] == "STAGE" and tokens[1] == "TEMP":
                    self.stage_temp = tokens[3]
                    azcam.log(f"Stage temperature is {self.stage_temp}")

                elif tokens[0] == "PACKAGE" and tokens[1] == "NUMBER":
                    self.itl_id = tokens[3]
                    azcam.log(f"Package ID is {self.itl_id}")

                elif tokens[0] == "CCD" and tokens[1] == "NUMBER":
                    self.itl_sn = int(tokens[3])
                    azcam.log(f"ITL serial number is {self.itl_sn}\n")

                elif tokens[0] == "Row":
                    zstandard = []  # start fresh

                elif (
                    tokens[0].startswith("Im_Point")
                    and tokens[1] == "X"
                    and tokens[2] == "Position"
                    and tokens[-1] == "M"
                ):
                    xx = float(tokens[3])
                    xx = int(xx)
                    x.append(xx)
                elif (
                    tokens[0].startswith("Im_Point")
                    and tokens[1] == "Y"
                    and tokens[2] == "Position"
                    and tokens[-1] == "M"
                ):
                    yy = float(tokens[3])
                    yy = int(yy)
                    y.append(yy)
                elif (
                    tokens[0].startswith("Im_Point")
                    and tokens[1] == "Z"
                    and tokens[2] == "Position"
                    and tokens[-1] == "M"
                ):
                    if self.standard_correct:
                        zz = float(tokens[3]) - zoffset
                    else:
                        zz = float(tokens[3])
                    z.append(zz)

                elif (
                    tokens[0] == "STANDARD_1"
                    and tokens[1] == "X"
                    and tokens[2] == "Position"
                    and tokens[4] == "M"
                ):
                    x1 = float(tokens[3])
                    standard1_x.append(x1)
                elif (
                    tokens[0] == "STANDARD_1"
                    and tokens[1] == "Y"
                    and tokens[2] == "Position"
                    and tokens[4] == "M"
                ):
                    x1 = float(tokens[3])
                    standard1_y.append(x1)
                elif (
                    tokens[0] == "STANDARD_1"
                    and tokens[1] == "Z"
                    and tokens[2] == "Position"
                    and tokens[4] == "M"
                ):
                    x1 = float(tokens[3])
                    standard1_z.append(x1)
                    zstandard.append(x1)

                elif (
                    tokens[0] == "STANDARD_2"
                    and tokens[1] == "X"
                    and tokens[2] == "Position"
                    and tokens[4] == "M"
                ):
                    x1 = float(tokens[3])
                    standard2_x.append(x1)
                elif (
                    tokens[0] == "STANDARD_2"
                    and tokens[1] == "Y"
                    and tokens[2] == "Position"
                    and tokens[4] == "M"
                ):
                    x1 = float(tokens[3])
                    standard2_y.append(x1)
                elif (
                    tokens[0] == "STANDARD_2"
                    and tokens[1] == "Z"
                    and tokens[2] == "Position"
                    and tokens[4] == "M"
                ):
                    x1 = float(tokens[3])
                    standard2_z.append(x1)
                    zstandard.append(x1)

                elif (
                    tokens[0] == "STANDARD_3"
                    and tokens[1] == "X"
                    and tokens[2] == "Position"
                    and tokens[4] == "M"
                ):
                    x1 = float(tokens[3])
                    standard3_x.append(x1)
                elif (
                    tokens[0] == "STANDARD_3"
                    and tokens[1] == "Y"
                    and tokens[2] == "Position"
                    and tokens[4] == "M"
                ):
                    x1 = float(tokens[3])
                    standard3_y.append(x1)
                elif (
                    tokens[0] == "STANDARD_3"
                    and tokens[1] == "Z"
                    and tokens[2] == "Position"
                    and tokens[4] == "M"
                ):
                    x1 = float(tokens[3])
                    standard3_z.append(x1)
                    zstandard.append(x1)

                elif (
                    tokens[0] == "STANDARD_4"
                    and tokens[1] == "X"
                    and tokens[2] == "Position"
                    and tokens[4] == "M"
                ):
                    x1 = float(tokens[3])
                    standard4_x.append(x1)
                elif (
                    tokens[0] == "STANDARD_4"
                    and tokens[1] == "Y"
                    and tokens[2] == "Position"
                    and tokens[4] == "M"
                ):
                    x1 = float(tokens[3])
                    standard4_y.append(x1)
                elif (
                    tokens[0] == "STANDARD_4"
                    and tokens[1] == "Z"
                    and tokens[2] == "Position"
                    and tokens[4] == "M"
                ):
                    x1 = float(tokens[3])
                    standard4_z.append(x1)
                    zstandard.append(x1)

                    zs_mean = numpy.array(zstandard).mean()
                    self.zstandard.append(zs_mean)
                    zoffset = (
                        zs_mean - self.standard_zheight
                    )  # this updates current value

                # write line to CSV file
                self.csv_tokens_raw = [
                    "Program:",
                    "Results",
                    "Company",
                    "VmsVersion",
                    "Engraved",
                ]

                # output only
                if tokens[0] in self.csv_tokens_raw:
                    lineout = " ".join([f"{x}" for x in tokens])
                    lineout = lineout.replace(",", " ")
                    fout.write(f"{lineout},\n")

                elif (
                    line.startswith("START TIME")
                    or line.startswith("PACKAGE NUMBER")
                    or line.startswith("END TIME")
                    or line.startswith("CCD NUMBER")
                ):
                    lineout = " ".join([f"{x}" for x in tokens[:2]])
                    lineout = lineout + "," + ",".join([f"{x}" for x in tokens[3:]])
                    fout.write(f"{lineout},\n")

                elif line.startswith("DATE"):
                    lineout = " ".join([f"{x}" for x in tokens[:1]])
                    lineout = lineout + "," + ",".join([f"{x}" for x in tokens[2:]])
                    fout.write(f"{lineout},\n")

                elif tokens[0] == "Measurement":
                    line = line.replace("+ Tol", "Tol+")
                    line = line.replace("- Tol", "Tol-")
                    tokens = shlex.split(line)
                    lineout = ",".join([f"{x}" for x in tokens])
                    fout.write(f"{lineout},\n")

                # two token line header
                elif tokens[0] in [
                    "A1",
                    "A2",
                    "A3",
                    "ANG1",
                    "ANG2",
                    "ANG3",
                    "ANG4",
                    "ANG5",
                    "ANG6",
                    "ANG7",
                    "ANG8",
                    "ANG9",
                    "JIG_TOP",
                    "FFLA_Foot",
                    "Im_Plane",
                ]:
                    lineout = " ".join([f"{x}" for x in tokens[:2]])
                    lineout = lineout + "," + ",".join([f"{x}" for x in tokens[2:]])
                    fout.write(f"{lineout},\n")

                # three token line header
                elif tokens[0] in [
                    "D1",
                    "D2",
                    "D3",
                    "D4",
                    "D5",
                    "D6",
                    "D7",
                    "Invar1",
                    "Invar2",
                    "Invar3",
                    "Invar4",
                    "HOLE_DIST",
                ]:
                    lineout = " ".join([f"{x}" for x in tokens[:3]])
                    lineout = lineout + "," + ",".join([f"{x}" for x in tokens[3:]])
                    fout.write(f"{lineout},\n")

                elif line.startswith("BC1 Diameter"):
                    lineout = " ".join([f"{x}" for x in tokens[:2]])
                    lineout = lineout + "," + ",".join([f"{x}" for x in tokens[2:]])
                    fout.write(f"{lineout},\n")

                elif line.startswith("BC1"):
                    lineout = " ".join([f"{x}" for x in tokens[:3]])
                    lineout = lineout + "," + ",".join([f"{x}" for x in tokens[3:]])
                    fout.write(f"{lineout},\n")

                elif line.startswith("Ref1 Diameter") or line.startswith(
                    "Ref1 Roundness"
                ):
                    lineout = " ".join([f"{x}" for x in tokens[:2]])
                    lineout = lineout + "," + ",".join([f"{x}" for x in tokens[2:]])
                    fout.write(f"{lineout},\n")

                elif line.startswith("Ref1"):
                    lineout = " ".join([f"{x}" for x in tokens[:3]])
                    lineout = lineout + "," + ",".join([f"{x}" for x in tokens[3:]])
                    fout.write(f"{lineout},\n")

                elif line.startswith("Ref2 Diameter") or line.startswith(
                    "Ref2 Roundness"
                ):
                    lineout = " ".join([f"{x}" for x in tokens[:2]])
                    lineout = lineout + "," + ",".join([f"{x}" for x in tokens[2:]])
                    fout.write(f"{lineout},\n")

                elif line.startswith("Ref2"):
                    lineout = " ".join([f"{x}" for x in tokens[:3]])
                    lineout = lineout + "," + ",".join([f"{x}" for x in tokens[3:]])
                    fout.write(f"{lineout},\n")

                elif line.startswith("Ref3 Diameter") or line.startswith(
                    "Ref3 Roundness"
                ):
                    lineout = " ".join([f"{x}" for x in tokens[:2]])
                    lineout = lineout + "," + ",".join([f"{x}" for x in tokens[2:]])
                    fout.write(f"{lineout},\n")

                elif line.startswith("Ref3"):
                    lineout = " ".join([f"{x}" for x in tokens[:3]])
                    lineout = lineout + "," + ",".join([f"{x}" for x in tokens[3:]])
                    fout.write(f"{lineout},\n")

                elif line.startswith("Ref4 Diameter") or line.startswith(
                    "Ref4 Roundness"
                ):
                    lineout = " ".join([f"{x}" for x in tokens[:2]])
                    lineout = lineout + "," + ",".join([f"{x}" for x in tokens[2:]])
                    fout.write(f"{lineout},\n")

                elif line.startswith("Ref4"):
                    lineout = " ".join([f"{x}" for x in tokens[:3]])
                    lineout = lineout + "," + ",".join([f"{x}" for x in tokens[3:]])
                    fout.write(f"{lineout},\n")

                elif line.startswith("Im_Point"):
                    lineout = " ".join([f"{x}" for x in tokens[:3]])
                    lineout = lineout + "," + ",".join([f"{x}" for x in tokens[3:]])
                    fout.write(f"{lineout},\n")

                elif line.startswith("FFLA_MTG Diameter"):
                    lineout = " ".join([f"{x}" for x in tokens[:2]])
                    lineout = lineout + "," + ",".join([f"{x}" for x in tokens[2:]])
                    fout.write(f"{lineout},\n")

                elif line.startswith("FFLA_MTG"):
                    lineout = " ".join([f"{x}" for x in tokens[:3]])
                    lineout = lineout + "," + ",".join([f"{x}" for x in tokens[3:]])
                    fout.write(f"{lineout},\n")

        # make numpy arrays
        self.x = numpy.array(x)
        self.y = numpy.array(y)
        self.z = numpy.array(z)

        if self.standard_correct:
            self.standard1_x = numpy.array(standard1_x)
            self.standard1_y = numpy.array(standard1_y)
            self.standard1_z = numpy.array(standard1_z)

            self.standard2_x = numpy.array(standard2_x)
            self.standard2_y = numpy.array(standard2_y)
            self.standard2_z = numpy.array(standard2_z)

            self.standard3_x = numpy.array(standard3_x)
            self.standard3_y = numpy.array(standard3_y)
            self.standard3_z = numpy.array(standard3_z)

            self.standard4_x = numpy.array(standard4_x)
            self.standard4_y = numpy.array(standard4_y)
            self.standard4_z = numpy.array(standard4_z)

            self.zstandard = numpy.array(self.zstandard)

        return
