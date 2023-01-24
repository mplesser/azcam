"""
Image threshold
"""

import os
import sys

import numpy
import scipy.ndimage
import scipy.optimize

import azcam
from azcam.image import Image


def threshold_image(filename="test.fits"):

    filename = azcam.db.parameters.get_script_par(
        "threshold_image", "filename", "prompt", "Enter image filename", filename
    )
    if filename == ".":
        reply = azcam.utils.file_browser("", [("image files", ("*.fits"))])
        filename = reply[0]
    if not os.path.isabs(filename):
        filename = azcam.utils.make_image_filename(filename)

    # **************************************************************
    # Threshold data
    # **************************************************************
    im = Image(filename)
    im.assemble(1)
    data = im.buffer
    # halfwidth = 3  # half width in pixels of an event

    # cross structure element
    el = scipy.ndimage.generate_binary_structure(2, 1)
    el = el.astype(numpy.int)

    threshold = data.mean() + 3 * data.std()
    # labels, num = scipy.ndimage.label(data > threshold, numpy.ones((3,3)))
    labels, num = scipy.ndimage.label(data > threshold, el)
    centers = scipy.ndimage.center_of_mass(data, labels, list(range(1, num + 1)))

    x = numpy.array(centers)[:, 0]
    y = numpy.array(centers)[:, 1]

    # r = numpy.sqrt((x-512)**2+(y-512)**2)
    # azcam.plot.plt.hist(r, bins=50)

    xint = x.astype(int)
    yint = y.astype(int)
    values = data[xint, yint]

    bins = int(threshold * 1.2 - threshold * 0.95)
    azcam.plot.plt.hist(values, bins=bins)
    azcam.plot.plt.xlim(threshold * 0.95, threshold * 1.2)
    azcam.plot.plt.show()

    """
    # pick good events on DS9 for PSF fitting
    regions = numpy.loadtxt("ds9.reg")
    xc,yc = regions[:,0],regions[:,1]

    y = data[xc[0],yc[0]-halfwidth:yc[0]+halfwidth] # take star values in a 1 by 2*halfwidth pixel strip
    x = numpy.linspace(0,len(y)-1,len(y))              # make an array of x values, same length as y

    fitfunc = lambda p, x: p[0]*scipy.exp(-(x-p[1])**2/(2.0*p[2]**2))
    errfunc = lambda p, x, y: fitfunc(p,x)-y
    parameters,foo = scipy.optimize.leastsq(errfunc,(100,10,3),args=(x,y))

    azcam.plot.plt.clf()
    azcam.plot.plt.xlabel('X')
    azcam.plot.plt.ylabel('Pixel value above background')
    azcam.plot.plt.plot(x,fitfunc(parameters,x))
    azcam.plot.plt.errorbar(x,y,yerr=numpy.sqrt(y),fmt='ro')
    """

    """
    window = 5
    pos_value = threshold
    neg_value = 0

    mask_pos = data > threshold
    mask_rev = (mask_pos == False)
    #mask = scipy.ndimage.uniform_filter(mask_pos.astype(numpy.float), size=window)
    #mask_pos = mask_pos > 0
    data[mask_pos] = pos_value
    data[mask_rev] = neg_value
    """

    # write and display new image
    im.write_file("filtered.fits", 6)
    azcam.db.tools["display"].display("filtered")

    azcam.plot.plt.show()

    return


if __name__ == "__main__":
    args = sys.argv[1:]
    threshold_image(*args)
