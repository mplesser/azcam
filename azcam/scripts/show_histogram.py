"""
PLot a histogram of image to check ADC.
"""

import sys

import numpy

import azcam
from azcam.image import Image


def show_histogram(filename: str) -> None:
    """
    Plot a histogram of pixel values.
    Uses assembled images so all HDU's are included together.

    Args:
        filename: iamge filename
    """

    im1 = Image(filename)
    im1.assemble(1)
    data = im1.buffer

    # make histogram
    HistY, HistX = numpy.histogram(data, bins="auto")
    centers = (HistX[:-1] + HistX[1:]) / 2

    # plot
    fig, ax = azcam.plot.plt.subplots(constrained_layout=False)
    azcam.plot.plt.semilogy([int(x) for x in centers], HistY)
    xlabel = "Pixel Value"
    ylabel = "Number of Events"
    title = "Image Histogram"
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    ax.set_title(title)
    azcam.plot.plt.ylim(1)
    ax.grid(True)
    azcam.plot.plt.show()

    return


if __name__ == "__main__":
    args = sys.argv[1:]
    show_histogram(*args)
