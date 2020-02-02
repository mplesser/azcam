import warnings
import time

import numpy
import matplotlib
import matplotlib.pyplot as plt
from matplotlib import pylab

import azcam

# allow for interactive plots after this import
pylab.ion()

style_x = [
    "bx",
    "rx",
    "gx",
    "cx",
    "mx",
    "yx",
    "kx",
    "bx",
    "rx",
    "gx",
    "cx",
    "mx",
    "yx",
    "kx",
    "bx",
    "rx",
    "gx",
]
style_o = [
    "bo",
    "ro",
    "go",
    "co",
    "mo",
    "yo",
    "ko",
    "bo",
    "ro",
    "go",
    "co",
    "mo",
    "yo",
    "ko",
    "bo",
    "ro",
    "go",
]
style_dot = [
    "b.",
    "r.",
    "g.",
    "c.",
    "m.",
    "y.",
    "k.",
    "b.",
    "r.",
    "g.",
    "c.",
    "m.",
    "y.",
    "k.",
    "b.",
    "r.",
    "g.",
]
style_lines = [
    "bx-",
    "rx-",
    "gx-",
    "cx-",
    "mx-",
    "yx-",
    "kx-",
    "bx-",
    "rx-",
    "gx-",
    "cx-",
    "mx-",
    "yx-",
    "kx-",
    "bx-",
    "rx-",
    "gx-",
]

# plot data
azcam.db.plotdata = {
    "KeyPressed": "",
    "MouseButton": -1,
    "X": -1.0,
    "Y": -1.0,
    "Xpix": -1,
    "Ypix": -1,
    "EnteredFigure": 0,
    "EnteredAxes": 0,
}


def update():
    """
    Use this method in a loop to update a plot in real-time.
    """

    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        plt.pause(0.001)

    return


def tools(FigureNumber=1):
    """
    Starts interactive plotting tool for a Figure.
    Updates data fron plot events.
    Data may be read from get_data().
    :param FigureNumber:
    """

    # define event handlers
    def onmouseclick(event):
        azcam.db.plotdata["MouseButton"] = event.button
        azcam.db.plotdata["X"] = event.xdata
        azcam.db.plotdata["Y"] = event.ydata
        azcam.db.plotdata["Xpix"] = event.x
        azcam.db.plotdata["Ypix"] = event.y

        return

    def onmouserelease(event):
        azcam.db.plotdata["MouseButton"] = event.button
        azcam.db.plotdata["X"] = event.xdata
        azcam.db.plotdata["Y"] = event.ydata
        azcam.db.plotdata["Xpix"] = event.x
        azcam.db.plotdata["Ypix"] = event.y

        return

    def onkeypress(event):
        azcam.db.plotdata["X"] = event.xdata
        azcam.db.plotdata["Y"] = event.ydata
        azcam.db.plotdata["Xpix"] = event.x
        azcam.db.plotdata["Ypix"] = event.y
        azcam.db.plotdata["KeyPressed"] = event.key

        return

    def enter_figure(event):
        azcam.db.plotdata["EnteredFigure"] = 1
        return

    def leave_figure(event):
        azcam.db.plotdata["EnteredFigure"] = 0
        return

    def enter_axes(event):
        azcam.db.plotdata["EnteredAxes"] = 1
        return

    def leave_axes(event):
        azcam.db.plotdata["EnteredAxes"] = 0
        return

    fig = plt.figure(FigureNumber)
    fig.canvas.mpl_connect("button_press_event", onmouseclick)
    fig.canvas.mpl_connect("button_release_event", onmouserelease)
    fig.canvas.mpl_connect("key_press_event", onkeypress)
    fig.canvas.mpl_connect("figure_enter_event", enter_figure)
    fig.canvas.mpl_connect("figure_leave_event", leave_figure)
    fig.canvas.mpl_connect("axes_enter_event", enter_axes)
    fig.canvas.mpl_connect("axes_leave_event", leave_axes)

    return


def get_data():
    """
    Returns PlotData from tools().
    Initial PlotData is {'KeyPressed':'','MouseButton':-1,'X':-1.0,'Y':-1.0}
    """

    return azcam.db.plotdata


def clear_data():
    """
    Clears PlotData from tools().
    """

    azcam.db.plotdata = {
        "KeyPressed": "",
        "MouseButton": -1,
        "X": -1.0,
        "Y": -1.0,
        "Xpix": -1,
        "Ypix": -1,
        "EnteredFigure": 0,
        "EnteredAxes": 0,
    }

    return


def close_figure(Figures="all"):
    """
    Close plot figure and their windows.
    Default is all.
    :param Figures:
    """

    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        plt.close(Figures)

    return


def set_figure(FigureNumber=1, Subplot="111"):
    """
    Set the active figure and plot for subsequent plot commands.
    A single plot is '111', a top plot of 2 is '211' and the bottom is '212'.
    :param Subplot:
    :param FigureNumber:
    """

    plt.figure(FigureNumber)

    subplot = int(Subplot)
    plt.axes(subplot)

    return


def save_figure(FigureNumber=1, FigureName=""):
    """
    Save a plotted figure to disk.
    If FigureName is not specified then the name is 'Figure'+FigureNumber.
    :param FigureNumber:
    :param FigureName:
    """

    if FigureName == "":
        FigureName = f"Figure{FigureNumber}"

    plt.figure(FigureNumber)
    plt.savefig(FigureName, bbox_inches="tight")

    return


def rescale(AxesValues=None, SubPlot=111, FigureNumber=1):
    """
    Replot a figure with new axes limits.
    AxisValues is [xmin,xmax,ymin,ymax].
    SubPlot is pylab subplot integer, as NumRows+NumCols+Number (111, 221, etc).
    FigureNumber is the figure number (starts at 1).
    During prompt, hit return to leave as is.
    :param FigureNumber:
    :param SubPlot:
    :param AxesValues:
    """

    plt.figure(FigureNumber)  # make FigureNumbe current
    ax1 = plt.subplot(SubPlot)  # make subplot axes current

    [xmin0, xmax0, ymin0, ymax0] = ax1.axis()  # get current values

    if not AxesValues:
        xmin = azcam.utils.prompt("Enter xmin value", xmin0)
        xmax = azcam.utils.prompt("Enter xmax value", xmax0)
        ymin = azcam.utils.prompt("Enter ymin value", ymin0)
        ymax = azcam.utils.prompt("Enter ymax value", ymax0)

        xmin = float(xmin)
        xmax = float(xmax)
        ymin = float(ymin)
        ymax = float(ymax)

        AxesValues = [xmin, xmax, ymin, ymax]

    ax1.axis(AxesValues)
    plt.draw()

    return


def display(Image, Cmap="gray"):
    """
    Make a matplotlib display of an image (array data like .buffer).
    Cmap is color map, try cm.*
    :param Cmap:
    :param Image:
    """

    if not Image.assembled:
        Image.assemble()

    plt.imshow(Image.buffer, cmap=Cmap, origin="lower")

    return


def plot_image(azimage, scale_type="useimage", scale_factor="useimage", cmap="gray"):
    """
    Plot an Azcam image buffer nicely.
    scaletype is sdev, minmax, scaled,absolute.
    """

    # image attributes
    # self.scale_type = 'sdev'
    # self.scale_factor=2.0

    if scale_type == "useimage":
        scale_type = azimage.scale_type
    if scale_factor == "useimage":
        scale_factor = azimage.scale_factor

    if not azimage.valid:
        raise azcam.AzcamError("Image object is not valid")

    if not azimage.assembled:
        azimage.assemble(1)

    if scale_type == "sdev":
        s = azimage.buffer.std()
        m = azimage.buffer.mean()
        z1 = m - scale_factor * s
        z2 = m + scale_factor * s
    elif scale_type == "minmax":
        z1 = azimage.buffer.min()
        z2 = azimage.buffer.max()
    elif scale_type == "scaled":
        m = azimage.buffer.mean()
        z1 = m / scale_factor
        z2 = m * scale_factor
    elif scale_type == "absolute":
        m = azimage.buffer.mean()
        z1 = m - scale_factor
        z2 = m + scale_factor
    else:
        raise azcam.AzcamError("unrecognized scale_type")

    plt.imshow(azimage.buffer, cmap=cmap, vmin=z1, vmax=z2, origin="lower")

    return


# plot windows


def move_window(figure_number=1, x=None, y=None):
    """
    Moves a figure to position x,y in screen pixels.
    :param y: Use None for auto
    :param x: Use None for auto
    :param figure_number: >= 1
    """

    if x is None:
        x = figure_number * 20
    if y is None:
        y = figure_number * 20

    backend = matplotlib.get_backend()

    f = plt.figure(figure_number)

    # this may error
    try:
        if backend == "TkAgg":
            f.canvas.manager.window.wm_geometry("+%d+%d" % (x, y))
        elif backend == "WXAgg":
            f.canvas.manager.window.SetPosition((x, y))
        else:
            # This works for QT and GTK
            # You can also use window.setGeometry
            f.canvas.manager.window.move(x, y)
    except Exception:
        return

    plt.show()

    return


def line(Figure=1):
    """
    Interactive: Plot a line on a plot figure.
    print() allowed here as interactive only.

    :param Figure:
    """

    tools(Figure)
    print("Click on 2 points to plot a line...")
    clear_data()
    x = []
    y = []
    for _ in range(2):
        while 1:
            update()
            data = get_data()
            if data["MouseButton"] != -1:
                x.append(data["X"])
                y.append(data["Y"])
                clear_data()
                break
            time.sleep(0.3)
    coefs = numpy.lib.polyfit(x, y, 1)
    fit_y = numpy.lib.polyval(coefs, x)
    plt.plot(x, fit_y, "b--")

    return


def on_moveevent(event):
    """
    Get the x and y pixel coords for plots.
    :param event:
    """

    if event.inaxes:
        azcam.log("data coords", event.xdata, event.ydata)

    return
