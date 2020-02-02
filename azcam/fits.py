"""
Contains FITS image manipulation commands.
"""

import warnings
import time
import os
from typing import Any, List

import numpy
from astropy.io import fits as pyfits

import azcam


def file_exists(filename: str) -> bool:
    """
    Returns True is the file exists, else False.
    """

    fe = azcam.utils.make_image_filename(filename)

    return os.path.exists(fe)


# *******************************************************************************
# image header commands
# *******************************************************************************
def get_section(filename: str, section: str, extension: int = 0) -> List:
    """
    Extract image section pixel values from a FITS keyword to a list.
    Format is always zero-based: [first_col,last_col,first_row,last_row].

    :param filename: image filename
    :param section: section name (like "CCDSEC")
    :param extension: image extension number
    """

    filename = azcam.utils.make_image_filename(filename)

    # get row limits
    datasec = get_keyword(filename, section, extension)
    datasec = datasec.lstrip("[")
    datasec = datasec.split(":")
    first_col = int(datasec[0]) - 1

    datasec1 = datasec[1].split(",")
    last_col = int(datasec1[0]) - 1
    first_row = int(datasec1[1]) - 1
    last_row = int(datasec[2].rstrip("]")) - 1

    return [first_col, last_col, first_row, last_row]


def get_keyword(filename: str, keyword: str, extension: int = 0) -> Any:
    """
    Return a header keyword value.

    :param filename: image filename
    :param keyword: keyword name
    :param extension: image extension number
    """

    Image = azcam.utils.make_image_filename(filename)

    hdr = pyfits.getheader(Image, extension)
    value = hdr[keyword]

    return value


def edit_keyword(filename: str, keyword: str, value: Any, extension: int = 0) -> None:
    """
    Edits a header keyword value.

    :param filename: image filename
    :param keyword: keyword name
    :param value: new value of keyword
    :param extension: image extension number
    """

    Image = azcam.utils.make_image_filename(filename)

    with pyfits.open(Image, mode="update") as hdulist:
        prihdr = hdulist[0].header
        prihdr[keyword] = value

    return


def get_header(filename: str, extension: int = 0):
    """
    Return the image header as a pyfits header object.

    :param filename: image filename
    :param extension: image extension number
    """

    filename = azcam.utils.make_image_filename(filename)

    hdr = pyfits.getheader(filename, extension)

    return hdr


def add_history(filename: str, history_string: str, extension: int = 0) -> None:
    """
    Adds a HISTORY line containing 'history_string' to the image.
    Used to record actions performed on an image. A 20 character time stamp
    is added as a prefix, and the result is split across up to three cards
    if it is too long to fit in one. Any extra text is truncated.

    :param filename: image filename
    :param history_string: string to add as a HISTORY keyword
    :param extension: image extension number
    """

    value = (
        time.strftime("%Y/%m/%d %H:%M:%S ", time.gmtime(time.time())) + history_string
    )
    if len(value) > 70:
        value = value[:70] + "\n" + value[70:]
    if len(value) > 141:
        value = value[:141] + "\n" + value[141:]
    if len(value) > 212:
        value = value[:212]

    # write the keyword
    filename = azcam.utils.make_image_filename(filename)

    hdu = pyfits.open(filename, mode="update")
    hdu[extension].header.add_history(value)
    hdu.close()

    return


def get_history(filename: str, extension: int = 0) -> str:
    """
    Returns the HISTOR header lines.

    :param filename: image filename
    :param extension: image extension number
    """

    filename = azcam.utils.make_image_filename(filename)

    hdr = pyfits.getheader(filename, extension)

    history = hdr["HISTORY"]

    return str(history)


# **************************************************************************************************
# Image extensions
# **************************************************************************************************


def get_extensions(filename: str) -> List:
    """
    Returns [NumExt,first_ext,last_ext] which are the number of IMAGE extensions
    and extension number limits FOR THE RANGE command [range(first_ext,last_ext)].
    NumExt is 0 for a standard FITS file and >0 for MEF.  The first data extension for an
    MEF file is 1.

    :param filename: image filename
    """

    filename = azcam.utils.make_image_filename(filename)
    with pyfits.open(filename) as hdulist:
        if len(hdulist) == 1:
            NumExt = 0
            first_ext = 0
            last_ext = 1
        else:
            n = 0
            for i in range(len(hdulist)):
                if "XTENSION" in hdulist[i].header:
                    if hdulist[i].header["XTENSION"] == "IMAGE":
                        n += 1
            first_ext = 1
            last_ext = n + 1
            NumExt = n

    return [NumExt, first_ext, last_ext]


# **************************************************************************************************
# Image math
# **************************************************************************************************


def arith(
    filename1: str,
    operator: str,
    filename2: str,
    filename3: str = "",
    datatype: str = "uint16",
) -> None:
    """
    Simple image manipulation of FITS files.
    Converts back to unsigned 16 bit.

    :param filename1: image filename
    :param operator: '+','-','/','*'
    :param filename2: may be an image filename or a constant.
    :param filename3: optional, must be an image filename.  If not specified, result goes into filename1.
    :param datatype: valid datatype string for resultant data type
    """

    MakeU16 = 1
    extension = 0

    if datatype == "uint16":
        MakeU16 = 1
    else:
        MakeU16 = 0

    header = []  # header for output file

    # open Image1
    filename1 = azcam.utils.make_image_filename(filename1)
    numext1, fext, lext = get_extensions(filename1)
    im1 = pyfits.open(filename1, lazy_load_hdus=False)  # this is an hdulist
    if numext1 > 1:
        MEF = 1
        header.append(im1[0].header)  # save for output file
        data1 = []  # first data index is 0
        for i in range(1, lext):
            header.append(im1[i].header)  # save for output
            if _is_image_extension(im1, i):  # only use image data
                data1.append(im1[i].data)
    else:
        MEF = 0
        header = im1[0].header  # save for output file
        data1 = im1[0].data

    # make float - new
    if MEF:
        for i in range(len(data1)):
            if _is_image_extension(im1, i):
                data1[i] = data1[i].astype("float32")
    else:
        data1 = data1.astype("float32")

    # check if filename2 is actually a number and not a filename
    if isinstance(filename2, (int, float)):
        data2 = filename2
        SCALAR = 1

    # open Image2 and get data
    else:
        SCALAR = 0
        filename2 = azcam.utils.make_image_filename(filename2)
        numext2, fext, lext = get_extensions(filename2)
        with pyfits.open(filename2, lazy_load_hdus=False) as im2:
            if numext1 != numext2:
                im2.close()
                raise azcam.AzcamError("unequal FITS image extensions")
            if MEF:
                data2 = []
                for i in range(1, lext):
                    if _is_image_extension(im2, i):
                        data2.append(im2[i].data.astype("float32"))
            else:
                data2 = im2[0].data.astype("float32")

    # operate
    NewFile = 1
    if MEF:
        data3 = []
    if operator == "+":
        if MEF:
            if SCALAR:
                for i in range(len(data1)):
                    data3.append(data1[i] + data2)
            else:
                for i in range(len(data1)):
                    data3.append(data1[i] + data2[i])
        else:
            data3 = data1 + data2
    elif operator == "-":
        if MEF:
            if SCALAR:
                for i in range(len(data1)):
                    data3.append(data1[i] - data2)
            else:
                for i in range(len(data1)):
                    data3.append(data1[i] - data2[i])
        else:
            data3 = data1 - data2
    elif operator == "/":
        if MEF:
            if SCALAR:
                for i in range(len(data1)):
                    data3.append(data1[i] / data2)
            else:
                for i in range(len(data1)):
                    data3.append(data1[i] / data2[i])
        else:
            data3 = data1 / data2
    elif operator == "*":
        if MEF:
            if SCALAR:
                for i in range(len(data1)):
                    data3.append(data1[i] * data2)
            else:
                for i in range(len(data1)):
                    data3.append(data1[i] * data2[i])
        else:
            data3 = data1 * data2

    # write result (all data is now float32)
    if filename3 == "":
        filename3 = filename1
        os.remove(filename1)
    filename3 = azcam.utils.make_image_filename(filename3)

    if NewFile:
        if MEF:
            phdu = pyfits.PrimaryHDU(None, header[0])
            hdulist = pyfits.HDUList()
            hdulist.append(phdu)
            for i in range(numext1):
                if MakeU16:
                    numpy.clip(data3[i], 0, 2 ** 16, data3[i])  # clip values below zero
                    hdu = pyfits.ImageHDU(data3[i].astype("uint16"), header[i + 1])
                else:
                    hdu = pyfits.ImageHDU(data3[i], header[i + 1])
                hdulist.append(hdu)
            if len(header) > len(data3):
                for i in range(len(data3) + 1, len(im1)):
                    hdulist.append(im1[i])

            im1.close()

            for _ in range(10):  # locking issue
                try:
                    hdulist.writeto(filename3, overwrite=1)
                except Exception:
                    azcam.AzcamWarning("FITS file locked")
                    time.sleep(0.5)
        else:
            im1.close()
            im3 = pyfits.PrimaryHDU(data3, header)
            im3.writeto(filename3, overwrite=1)

    return


def _is_image_extension(hdulist, extension: int) -> bool:
    """
    Check is an extension of a image (hdulist) contains image data.
    """

    if "XTENSION" in hdulist[extension].header:
        if hdulist[extension].header["XTENSION"] == "IMAGE":
            return True

    return False


def add(filename1: str, filename2: str, filename3: str, datatype: str = "uint16"):
    """
    Add two images.
    :param filename1: image filename
    :param filename2: may be an image filename or a constant.
    :param filename3: optional, must be an image filename.  If not specified, result goes into filename1.
    :param datatype: valid datatype string for resultant data type
    """

    return arith(filename1, "+", filename2, filename3, datatype)


def sub(filename1: str, filename2: str, filename3: str, datatype: str = "uint16"):
    """
    Subtract filename2 from filename1.

    :param filename1: image filename
    :param operator: '+','-','/','*'
    :param filename2: may be an image filename or a constant.
    :param filename3: optional, must be an image filename.  If not specified, result goes into filename1.
    :param datatype: valid datatype string for resultant data type
    """

    return arith(filename1, "-", filename2, filename3, datatype)


def mult(filename1: str, filename2: str, filename3: str, datatype: str = "uint16"):
    """
    Multiple two images.

    :param filename1: image filename
    :param operator: '+','-','/','*'
    :param filename2: may be an image filename or a constant.
    :param filename3: optional, must be an image filename.  If not specified, result goes into filename1.
    :param datatype: valid datatype string for resultant data type
    """

    return arith(filename1, "*", filename2, filename3, datatype)


def div(filename1: str, filename2: str, filename3: str, datatype: str = "uint16"):
    """
    Divide Image1 by Image2.

    :param filename1: image filename
    :param operator: '+','-','/','*'
    :param filename2: may be an image filename or a constant.
    :param filename3: optional, must be an image filename.  If not specified, result goes into filename1.
    :param datatype: valid datatype string for resultant data type
    """

    return arith(filename1, "/", filename2, filename3, datatype)


def combine(
    file_list: list = [],
    out_filename: str = "combined.fits",
    combination_type: str = "median",
    overscan_correct: int = 1,
) -> None:
    """
    Make a combination of a list of FITS filenames.

    :param file_list: list of filenames to combine
    :param out_filename: output filename
    :param combination_type: combination type, "median", "sum", or "mean"
    :param overscan_correct: > 0 to correct overscan with specified fir order before combination
    """

    numfiles = len(file_list)
    if numfiles < 2:
        raise azcam.AzcamError("two or more images are required")

    header = []  # header for output file
    dataset = []  # combined data

    for fnum, f in enumerate(file_list):
        filename = azcam.utils.make_image_filename(f)

        # overscan correct
        if overscan_correct > 0:
            colbias(filename, overscan_correct)

        dataarray = []  # each dataset by channel

        # open each image and get data
        with pyfits.open(filename) as im:
            numexts, firstext, lastext = get_extensions(filename)

            # setup based on first image
            if fnum == 0:
                if numexts > 0:
                    MEF = 1
                    header.append(im[0].header)
                    for i in range(firstext, lastext):
                        header.append(im[i].header)
                        dataarray.append(im[i].data)
                else:
                    MEF = 0
                    header = im[0].header  # save for output file
                    dataarray = im[0].data

            else:
                if numexts > 0:
                    for i in range(numexts):
                        dataarray.append(im[i + 1].data)
                else:
                    # dataarray=dataarray+im.data
                    dataarray = im[0].data

            dataset.append(dataarray)

    if MEF:
        data3d = []
        for chan in range(numexts):
            data3d.append(numpy.array([x[chan] for x in dataset]))
        data_combined = []
        for chan in range(numexts):
            if combination_type == "median":
                data_combined.append(numpy.median(data3d[chan], axis=0))
            elif combination_type == "sum":
                data_combined.append(numpy.sum(data3d[chan], axis=0))
            elif combination_type == "mean":
                data_combined.append(numpy.mean(data3d[chan], axis=0))
    else:
        data3d = numpy.array([x for x in dataset])
        if combination_type == "median":
            data_combined = numpy.median(data3d, axis=0)
        elif combination_type == "sum":
            data_combined = numpy.sum(data3d, axis=0)
        elif combination_type == "mean":
            data_combined = numpy.mean(data3d, axis=0)

    if MEF:
        newdata = []
        for i in range(numexts):
            newdata.append(data_combined[i])
    else:
        newdata = data_combined

    # write result
    if MEF:
        phdu = pyfits.PrimaryHDU(None, header[0])
        hdulist = pyfits.HDUList()
        hdulist.append(phdu)
        for i in range(firstext, lastext):
            hdu = pyfits.PrimaryHDU(newdata[i - 1], header[i])
            hdulist.append(hdu)

        with warnings.catch_warnings():  # surpress warning
            warnings.simplefilter("ignore")
            hdulist.writeto(out_filename, overwrite=1)
        hdulist.close()
    else:
        im1 = pyfits.PrimaryHDU(newdata, header)
        im1.writeto(out_filename, overwrite=1)

    # update header
    add_history(
        out_filename,
        "COMBINED Data was %s combined from %d images" % (combination_type, numfiles),
        0,
    )

    return


# *********************************************************************************************
# pixel computations - uses ROI
# *********************************************************************************************
def mean(filename: str = "test", roi: List = []) -> List:
    """
    Compute mean of an image ROI in every extension.

    :param filename: image filename
    :param roi: ROI
    """

    roi = _get_data_roi(roi)

    means = []
    filename = azcam.utils.make_image_filename(filename)

    with pyfits.open(filename) as im:
        NumExt, first_ext, last_ext = get_extensions(filename)
        for chan in range(first_ext, last_ext):
            data = im[chan].data
            numpy.seterr(under="ignore")
            mean1 = data[roi[0] : roi[1], roi[2] : roi[3]].mean()
            means.append(mean1)

    return means


def sdev(filename: str = "test", roi: List = []) -> List:
    """
    Compute standard deviation of an image ROI in every extension.

    :param filename: image filename
    :param roi: ROI
    """

    roi = _get_data_roi(roi)

    filename = azcam.utils.make_image_filename(filename)

    with pyfits.open(filename) as im:
        sdevs = []
        NumExt, first_ext, last_ext = get_extensions(filename)
        for chan in range(first_ext, last_ext):
            data = im[chan].data
            sdev1 = data[roi[0] : roi[1], roi[2] : roi[3]].std()
            sdevs.append(sdev1)

    return sdevs


def stat(filename: str = "test", roi: List = []) -> List:
    """
    Compute mean and sdev image statistics of ROI in every extension.
    Returns [[means], [sdevs], ROI]
    :param filename: image filename
    :param roi: ROI
    """

    filename = azcam.utils.make_image_filename(filename)
    mean1 = mean(filename, roi)
    sdev1 = sdev(filename, roi)

    return [mean1, sdev1, roi]


def minimum(filename: str = "test", roi: str = []) -> List:
    """
    Compute minimum of an image ROI for every extension.

    :param filename: image filename
    :param roi: ROI
    """

    mins = []

    roi = _get_data_roi(roi)

    filename = azcam.utils.make_image_filename(filename)

    with pyfits.open(filename) as im:
        NumExt, first_ext, last_ext = get_extensions(filename)
        for chan in range(first_ext, last_ext):
            data = im[chan].data
            numpy.seterr(under="ignore")
            dmin = data[roi[0] : roi[1], roi[2] : roi[3]].min()
            mins.append(dmin)

    return mins


def maximum(filename: str = "test", roi: str = []) -> List:
    """
    Compute maximum of an image ROI for every extension.

    :param filename: image filename
    :param roi: ROI
    """

    maxs = []

    roi = _get_data_roi(roi)

    filename = azcam.utils.make_image_filename(filename)

    with pyfits.open(filename) as im:
        NumExt, first_ext, last_ext = get_extensions(filename)
        for chan in range(first_ext, last_ext):
            data = im[chan].data
            numpy.seterr(under="ignore")
            dmax = data[roi[0] : roi[1], roi[2] : roi[3]].max()
            maxs.append(dmax)

    return maxs


def get_data(filename: str = "test", roi: str = []) -> List:
    """
    Return data (pixel values) from an ROI in an image for every entension.
    NOT FINISHED!

    :param filename: image filename
    :param roi: ROI
    """

    filename = azcam.utils.make_image_filename(filename)
    roi = _get_data_roi(roi)

    with pyfits.open(filename) as im:
        NumExt, first_ext, last_ext = get_extensions(filename)
        if NumExt == 0:
            datalist = im[0].data[roi[0] : roi[1], roi[2] : roi[3]]
        else:
            datalist = []
            for chan in range(first_ext, last_ext):
                datalist.append(im[chan].data[roi[0] : roi[1], roi[2] : roi[3]])

    return datalist


def get_all_data(filename: str = "test") -> List:
    """
    Return all pixel data from image.

    :param filename: image filename
    """

    filename = azcam.utils.make_image_filename(filename)

    with pyfits.open(filename) as im:
        NumExt, first_ext, last_ext = get_extensions(filename)
        if NumExt == 0:
            datalist = im[0].data
        else:
            datalist = []
            for chan in range(first_ext, last_ext):
                datalist.append(im[chan].data)

    return datalist


def colbias(filename: str = "test", fit_order: int = 3, margin_cols: int = 0) -> None:
    """
    Remove column bias from a FITS file.

    :param filename: image filename
    :param fit_order: polynomial fit order, use 0 to remove median not fitted value
    :param margin_cols: number of overscan columns to skip before correction
    """

    filename = azcam.utils.make_image_filename(filename)

    # open image and get data
    with pyfits.open(filename, mode="update") as im:

        # if already COLBIAS then exit here
        try:
            history = im[0].header["History"]
            for h in history:
                h = repr(h)
                if "COLBIAS" in h:
                    return
                else:
                    pass
        except KeyError:
            pass

        numexts, firstext, lastext = get_extensions(filename)

        # find column median value
        if numexts == 0:
            Median = []
        else:
            Median = [[]]  # skip phdu

        # get overscan info
        reply = get_keyword(filename, "OVRSCAN2", firstext)
        if isinstance(reply, str):
            overscanrows = 0
        else:
            overscanrows = int(reply)
        col1, col2, row1, row2 = get_section(filename, "BIASSEC", firstext)
        col1 += 1

        col1 += margin_cols

        col2 -= 1
        row2 += overscanrows

        for i in range(firstext, lastext):

            # make data float32 for calculations
            im[i].data = im[i].data.astype("float32")

            Median.append([])  # first hdu will be 1
            for row in range(row1, row2 + 1):
                Median[i].append(
                    numpy.median(im[i].data[row : row + 1, col1 : col2 + 1])
                )

            slope, xdata, yfit, resids, residspercent = _line_fit(
                list(range(row1, row2 + 1)), Median[i], fit_order
            )
            yfit = yfit.astype("float32")

            # correct data by subtracting row by row best fit
            for row in range(row1, row2 + 1):
                if fit_order > 0:
                    im[i].data[row : row + 1] -= yfit[row]  # wraps here
                else:
                    im[i].data[row : row + 1] -= Median[i][row]

            # convert back to uint16, clipping to zero
            # im[i].data=im[i].data.clip(min=0)
            # im[i].data=im[i].data.astype('uint16')

        # new due to lock
        history_string = "COLBIAS data was column overscan corrected"
        value = (
            time.strftime("%Y/%m/%d %H:%M:%S ", time.gmtime(time.time()))
            + history_string
        )
        if len(value) > 70:
            value = value[:70] + "\n" + value[70:]
        if len(value) > 141:
            value = value[:141] + "\n" + value[141:]
        if len(value) > 212:
            value = value[:212]
        im[0].header.add_history(value)

    return


# *********************************************************************************************
# FITS support methods
# *********************************************************************************************
def _get_data_roi(azcam_roi=[]):
    """
    Converts Azcam ROI to numpy ROI.
    azcam_roi is an Azcam ROI list, i.e. one-based, Columns first: [first_col, last_col, first_row, last_row].
    Returns the equivalent python ROI,  zero-based, Rows first: [first_row, last_row, first_col, last_col].
    """

    if azcam_roi == []:
        roi = azcam.db.imageroi
    else:
        roi = azcam_roi

    if isinstance(roi[0], list):
        roi = roi[0]  # use first roi

    first_row = int(roi[2]) - 1
    last_row = int(roi[3]) - 1 + 1  # slice
    first_col = int(roi[0]) - 1
    last_col = int(roi[1]) - 1 + 1  # slice

    return [first_row, last_row, first_col, last_col]


def _line_fit(xdata, ydata, order=1, fit_min=0, fit_max=-1):
    """
    Fit a line to Data, usings points fit_min through fit_max.
    xdata and ydata must be same-sized arrays.
    Returns [Status,[slope,Y-intercept],xdata,YFit,residuals,residuals_percent].
    """

    num_points = len(xdata)
    if len(ydata) != num_points:
        return "ERROR X and Y arrays are not the same size"

    if fit_max == -1:
        fit_max = num_points - 1

    if fit_min > fit_max:
        return "ERROR fit_max must be <= fit_min"

    # make least squares fit through [fit_min:fit_max] points
    xxdata = xdata[fit_min:fit_max]
    yydata = ydata[fit_min:fit_max]

    # generate line y values
    polycoeffs = numpy.polyfit(
        xxdata, yydata, order
    )  # [slope,intercept] using just fit_min:fit_max
    yfit = numpy.polyval(polycoeffs, xdata)  # fit for all data, not just xxdata

    # calculate residuals
    residuals = []
    residuals_percent = []
    for i in range(num_points):
        r1 = ydata[i] - yfit[i]  # difference
        residuals.append(r1)  # residuals
        r2 = 100.0 * r1 / yfit[i]  # residual %
        residuals_percent.append(r2)  # residuals %

    return [polycoeffs, xdata, yfit, residuals, residuals_percent]
