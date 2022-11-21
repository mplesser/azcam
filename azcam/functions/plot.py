"""
*azcam.plot* contains plotting support for azcam.

When working in IPython, use `pylab.ion()` for interactions after this import.
"""

import time
import warnings

import azcam
import matplotlib
import numpy
from matplotlib import pyplot as plt

#: plot data - *azcam.functions.plot.plotdata*
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

# can combine stypes like "bo-"

#: list of markers with crosses  - *azcam.functions.plot.style_x*
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
#: list of markers with circles - *azcam.functions.plot.style_o*
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
#: list of markers with dots - *azcam.functions.plot.style_dot*
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
#: list of line styles - *azcam.functions.plot.style_lines*
style_lines = [
    "b-",
    "r-",
    "g-",
    "c-",
    "m-",
    "y-",
    "k-",
    "b-",
    "r-",
    "g-",
    "c-",
    "m-",
    "y-",
    "k-",
    "b-",
    "r-",
    "g-",
]


def update() -> None:
    """
    Use this method in a loop to update a plot in real-time.
    """

    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        plt.pause(0.05)

    return


def delay(delay: float) -> None:
    """
    Delay for delay seconds keeping GUI event loop working.

    Args:
        delay: delay in seconds.
    """

    plt.pause(delay)

    return


def tools(figure_number=1, include_motion: bool = 0) -> None:
    """
    Starts interactive plotting tool for a Figure.
    Updates data fron plot events.
    Data may be read from get_data().

    Args:
        figure_number: figure number.
        include_motion: True to include mouse motion within axes as an event
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

        if 0:
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

    def mouse_motion(event):
        """
        Get the x and y pixel coords for plots.
        :param event:
        """

        if event.inaxes:
            azcam.log("data coords", event.xdata, event.ydata)

        return

    fig = plt.figure(figure_number)
    fig.canvas.mpl_connect("button_press_event", onmouseclick)
    fig.canvas.mpl_connect("button_release_event", onmouserelease)
    fig.canvas.mpl_connect("key_press_event", onkeypress)
    fig.canvas.mpl_connect("figure_enter_event", enter_figure)
    fig.canvas.mpl_connect("figure_leave_event", leave_figure)
    fig.canvas.mpl_connect("axes_enter_event", enter_axes)
    fig.canvas.mpl_connect("axes_leave_event", leave_axes)

    if include_motion:
        fig.canvas.mpl_connect("motion_notify_event", mouse_motion)

    return


def get_data() -> dict:
    """
    Returns plot data from tools().
    Initial data is {'KeyPressed':'','MouseButton':-1,'X':-1.0,'Y':-1.0}
    """

    global plotdata

    return plotdata


def clear_data() -> None:
    """
    Clears plot data from tools().
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


def close_figure(figures: str = "all") -> None:
    """
    Close plot figure and their windows.

    Args:
        figures: list a string of figure numbers to close.
    """

    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        plt.close(figures)

    return


def set_figure(figure_number: int = 1, subplot: int = 111) -> None:
    """
    Set the active figure and plot for subsequent plot commands.
    A single plot is '111', a top plot of 2 is '211' and the bottom is '212'.

    Args:
        figure_number: figure number.
        subplot: subplot ID.
    """

    plt.figure(figure_number)
    subplot = int(subplot)
    plt.axes(subplot)

    return


def save_figure(figure_number: int = 1, figure_name: str = "") -> None:
    """
    Save a plotted figure to disk.
    If FigureName is not specified then the name is 'Figure'+figure_number.

    Args:
        figure_number: figure number.
        figure_name: figure name.
    """

    if figure_name == "":
        figure_name = f"Figure{figure_number}"

    plt.figure(figure_number)
    plt.savefig(figure_name, bbox_inches="tight")

    return


def rescale(axes_values: list = None, sub_plot: int = 111, figure_number: int = 1) -> None:
    """
    Replot a figure with new axes limits.
    During prompt, hit return to leave as is.

    Args:
        axes_values: list of new axis values as `[xmin,xmax,ymin,ymax]`.
        sub_plot: subplot ID, as NumRows+NumCols+Number (111, 221, etc).
        figure_number: figure number.
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


def display(azimage: object, cmap: str = "gray") -> None:
    """
    Make a matplotlib display of an azcam image.
    cmap is a matplotlib color map.

    Args:
        azmage: azcam image.
        cmap: color map name.
    """

    if not azimage.assembled:
        azimage.assemble()

    plt.imshow(azimage.buffer, cmap=cmap, origin="lower")

    return


def plot_image(
    azimage: object,
    scale_type: str = "sdev",
    scale_factor: float = 20.0,
    cmap: str = "gray",
) -> None:
    """
    Plot an Azcam image buffer nicely.

    Args:
        scale_type: one of (sdev, minmax, scaled, absolute).
        scale_factor: scaling factor for 8-bit conversion.
        cmap: color map name.
    """

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


def move_window(figure_number=1, x=None, y=None) -> None:
    """
    Moves a figure to position x,y in screen pixels.

    Args:
        figure_number: figure number.
        x: Use None for auto.
        y: Use None for auto.
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


def line(figure_number=1) -> None:
    """
    Interactive: Plot a line on a plot figure.
    print() allowed here as interactive only.

    Args:
        figure_number: figure number.
    """

    tools(figure_number)
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
