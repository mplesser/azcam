"""
Measure centroid and moments of objects such as Fe55 events and stars.
"""

import os
import sys

import matplotlib.mlab as mlab
import numpy
import scipy.ndimage
import scipy.optimize
from astropy.modeling import fitting, models
from scipy.stats import norm
from astropy.io import fits as pyfits

import azcam
import azcam.utils
import azcam.fits
import azcam.image
import azcam.console
from azcam.console.plot import plt, update


def centroids(filename: str = ".", threshold: float = 500.0) -> None:
    """
    Find centroids of events in image.
    Also plot them and create ds9/text file outputs.

    Args:
        filename: image filename
        threshold: pixel value for limit.
    """

    # inputs
    threshold = float(threshold)
    if filename == ".":
        filename = azcam.db.parameters.get_local_par(
            "centroids",
            "filename",
            "prompt",
            "Enter image filename or . to browse",
            filename,
        )
    if filename == ".":
        reply = azcam.console.utils.file_browser("", [("image files", ("*.fits"))])
        if reply is None:
            return
        filename = reply[0]
        azcam.db.parameters.set_local_par("centroids", "filename", filename)

    filename = azcam.utils.make_image_filename(filename)

    # debias the image
    azcam.fits.colbias(filename)

    # open FITS file
    fe55im = pyfits.open(filename)

    # make data buffer from FITS file
    im1 = azcam.image.Image(filename)
    im1.assemble(1)
    data = im1.buffer
    maxrows = len(data)
    maxcols = len(data[0])

    # get original mean and sdev
    mean = data.mean()
    # sdev = data.std()
    sdev = 10.0

    # set detection threshholds
    # threshold = 10 * sdev
    maxvalue = 5000
    boxsize = 5  # "radius" of detection box
    FWHM_min = 0.5  # min acceptable FWMH
    FWHM_max = 3.0  # max acceptable FWHM

    # define functions needed for gaussian fitting
    def gaussian(B, x):
        # Returns the gaussian function for B=mean,stdev,max,offset
        return B[3] + B[2] / (B[1] * numpy.sqrt(2 * numpy.pi)) * numpy.exp(
            -((x - B[0]) ** 2 / (2 * B[1] ** 2))
        )

    def errfunc(p, x, y):
        return y - gaussian(p, x)

    # find objects and get centroids - floats
    labels, numevents = scipy.ndimage.label(
        data > threshold, [[0, 1, 0], [1, 1, 1], [0, 1, 0]]
    )
    coords = scipy.ndimage.center_of_mass(data, labels, list(range(1, numevents + 1)))
    x = numpy.array(coords)[:, 1]  # cols
    y = numpy.array(coords)[:, 0]  # rows
    print(f"Number of events found: {len(x)}")

    # save points as ds9 regions
    with open("centroids.reg", "w+") as f1:
        with open("centroids.txt", "w+") as f2:
            lines1 = []
            lines2 = []
            lines1.append("detector\n")
            for i in range(numevents):
                line1 = "point(%.2f,%.2f) # point=cross" % (
                    x[i] + 1.0,
                    y[i] + 1.0,
                )  # add for for (1,1) coords
                line2 = "%-10.2f\t%-10.2f" % (
                    x[i] + 1.0,
                    y[i] + 1.0,
                )  # add for for (1,1) coords
                lines1.append(line1 + "\n")
                lines2.append(line2 + "\n")
            f1.writelines(lines1)
            f2.writelines(lines2)

    # get integer pixel indices and data value for center pixels
    xint = x.astype(int)
    yint = y.astype(int)
    values = data[yint, xint]  # data is rows by cols

    # g = models.Gaussian1D(amplitude=1.2, mean=0.9, stddev=0.5)

    # plot the events
    if 0:
        plt.figure()
        plt.plot(xint, yint, "r.")
        update()

    # plot a histogram of values
    if 0:
        plt.figure()
        rng = int((max(values) + 1) / 100.0)
        plt.hist(values, bins=rng)
        plt.ylim(0)
        plt.xlim(0)

    # plot image
    if 0:
        plt.figure()
        plt.imshow(data, cmap="gray", origin="lower", vmin=0, vmax=threshold)

    FWHM_array = []
    print("Finding FWHM...")
    for i in range(numevents):
        row = yint[i]

        # ignore edges
        if row < boxsize + 1:
            continue
        col = xint[i]
        if col < boxsize + 1:
            continue
        if row > maxrows - boxsize:
            continue
        if col > maxcols - boxsize:
            continue

        if 0:
            databox = data[row - boxsize : row + boxsize, col - boxsize : col + boxsize]
            plt.figure(4)
            z1 = databox.min()
            z2 = databox.max()
            imgplot = plt.imshow(databox, vmin=z1, vmax=z2)
            imgplot.set_cmap("Blues")  # Blues gray hot
            imgplot.set_interpolation("nearest")  # bicubic

        # for irow in range(-boxsize,boxsize+1):
        for irow in range(0, 1):  # 0
            dataslice = data[
                row + irow, col - boxsize : col + boxsize
            ]  # 1D strip along a row
            indices = list(
                range(0, boxsize * 2)
            )  # make an array of y values, same length as x
            if 0:
                plt.plot(indices, dataslice)
                plt.show()
                update()

            # mean1,sigma1 = norm.fit(dataslice)
            # yfit = mlab.normpdf(dataslice,mean1,sigma1)*dataslice.max()   # normalized probability

            p0 = [1.0, 1.0, 1.0, 1.0]
            coeffs, success = scipy.optimize.leastsq(
                errfunc, p0, args=(indices, dataslice)
            )
            fitmean = coeffs[2]
            fitfwhm = coeffs[1]

            # exclude bad values
            if fitfwhm < FWHM_min or fitfwhm > FWHM_max:
                continue
            else:
                FWHM_array.append(fitfwhm)

            # print("%d of %d: FWHM = %.3f, Max = %.1f" % (i, len(yint), fitfwhm, fitmean))

            if 0:
                plt.plot(indices, gaussian(coeffs, indices), "ro")
                update()

            if 0:
                coeffs = numpy.polyfit(indices, dataslice, 3)
                yfit = numpy.polyval(coeffs, indices)
                plt.plot(indices, yfit, "r--", linewidth=2)
                plt.errorbar(indices, slice, yerr=numpy.sqrt(slice), fmt="ro")
                update()

    FWHM_mean = sum(FWHM_array) / len(FWHM_array)
    print("Mean FWHM = %.2f, Mean Sigma = %.1f" % (FWHM_mean, FWHM_mean / 2.355))

    if 0:
        plt.figure(6)
        rng = len(FWHM_array) + 1
        plt.hist(values, bins=rng)
        plt.ylim(
            0,
        )
        plt.xlim(
            0,
        )

    # show plots
    plt.show()

    # finish
    fe55im.close()

    return


if __name__ == "__main__":
    args = sys.argv[1:]
    centroids(*args)
