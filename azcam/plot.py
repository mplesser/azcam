import time
import warnings

import matplotlib
import numpy
from matplotlib import pylab
from matplotlib import pyplot as plt

import azcam

# global data

plotdata = {
    "KeyPressed": "",
    "MouseButton": -1,
    "X": -1.0,
    "Y": -1.0,
    "Xpix": -1,
    "Ypix": -1,
    "EnteredFigure": 0,
    "EnteredAxes": 0,
}

# allow for interactive plots after this import
# pylab.ion()

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


def update():
    """
    Use this method in a loop to update a plot in real-time.
    """

    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        plt.pause(0.001)

    return


def tools(figure_number=1):
    """
    Starts interactive plotting tool for a Figure.
    Updates data fron plot events.
    Data may be read from get_data().
    :param figure_number:
    """

    global plotdata

    # define event handlers
    def onmouseclick(event):
        plotdata["MouseButton"] = event.button
        plotdata["X"] = event.xdata
        plotdata["Y"] = event.ydata
        plotdata["Xpix"] = event.x
        plotdata["Ypix"] = event.y

        if 1:
            print(plotdata)

        return

    def onmouserelease(event):
        plotdata["MouseButton"] = event.button
        plotdata["X"] = event.xdata
        plotdata["Y"] = event.ydata
        plotdata["Xpix"] = event.x
        plotdata["Ypix"] = event.y

        if 1:
            print(plotdata)

        return

    def onkeypress(event):
        plotdata["X"] = event.xdata
        plotdata["Y"] = event.ydata
        plotdata["Xpix"] = event.x
        plotdata["Ypix"] = event.y
        plotdata["KeyPressed"] = event.key

        if 1:
            print(plotdata)

        return

    def enter_figure(event):
        plotdata["EnteredFigure"] = 1
        return

    def leave_figure(event):
        plotdata["EnteredFigure"] = 0
        return

    def enter_axes(event):
        plotdata["EnteredAxes"] = 1
        return

    def leave_axes(event):
        plotdata["EnteredAxes"] = 0
        return

    fig = plt.figure(figure_number)
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
    Returns plotdata from tools().
    Initial plotdata is {'KeyPressed':'','MouseButton':-1,'X':-1.0,'Y':-1.0}
    """

    global plotdata

    return plotdata


def clear_data():
    """
    Clears plotdata from tools().
    """

    global plotdata

    plotdata = {
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


def close_figure(figures="all"):
    """
    Close plot figure and their windows.
    Default is all.
    :param Figures:
    """

    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        plt.close(figures)

    return


def set_figure(figure_number=1, subplot="111"):
    """
    Set the active figure and plot for subsequent plot commands.
    A single plot is '111', a top plot of 2 is '211' and the bottom is '212'.
    :param Subplot:
    :param figure_number:
    """

    plt.figure(figure_number)

    subplot = int(subplot)
    plt.axes(subplot)

    return


def save_figure(figure_number=1, figure_name=""):
    """
    Save a plotted figure to disk.
    If FigureName is not specified then the name is 'Figure'+figure_number.
    :param figure_number:
    :param FigureName:
    """

    if figure_name == "":
        figure_name = f"Figure{figure_number}"

    plt.figure(figure_number)
    plt.savefig(figure_name, bbox_inches="tight")

    return


def rescale(axes_values=None, sub_plot=111, figure_number=1):
    """
    Replot a figure with new axes limits.
    AxisValues is [xmin,xmax,ymin,ymax].
    SubPlot is pylab subplot integer, as NumRows+NumCols+Number (111, 221, etc).
    figure_number is the figure number (starts at 1).
    During prompt, hit return to leave as is.
    :param figure_number:
    :param SubPlot:
    :param AxesValues:
    """

    plt.figure(figure_number)  # make FigureNumbe current
    ax1 = plt.subplot(sub_plot)  # make subplot axes current

    [xmin0, xmax0, ymin0, ymax0] = ax1.axis()  # get current values

    if not axes_values:
        xmin = azcam.utils.prompt("Enter xmin value", xmin0)
        xmax = azcam.utils.prompt("Enter xmax value", xmax0)
        ymin = azcam.utils.prompt("Enter ymin value", ymin0)
        ymax = azcam.utils.prompt("Enter ymax value", ymax0)

        xmin = float(xmin)
        xmax = float(xmax)
        ymin = float(ymin)
        ymax = float(ymax)

        axes_values = [xmin, xmax, ymin, ymax]

    ax1.axis(axes_values)
    plt.draw()

    return


def display(azimage, cmap="gray"):
    """
    Make a matplotlib display of an azcam image.
    cmap is color map, try cm.*
    :param Cmap:
    :param Image:
    """

    if not azimage.assembled:
        azimage.assemble()

    plt.imshow(azimage.buffer, cmap=cmap, origin="lower")

    return


def plot_image(azimage, scale_type="useimage", scale_factor="useimage", cmap="gray"):
    """
    Plot an Azcam image buffer nicely.
    scaletype is sdev, minmax, scaled,absolute.
    """

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


def line(figure=1):
    """
    Interactive: Plot a line on a plot figure.
    print() allowed here as interactive only.

    :param Figure:
    """

    tools(figure)
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
