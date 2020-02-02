"""
Contains the Ds9Display class.
"""

import os
import time
import shutil
import tempfile
import numpy
import subprocess
from typing import List

from astropy.io import fits as pyfits

import azcam
from azcam.displays.display import Display


class Ds9Display(Display):
    """
    azcam's interface to SAO's ds9 image display tool.
    """

    def __init__(self, *args):

        super().__init__(*args)

        #: display ID
        self.id = "ds9"

        #: display Host, as a string hex code
        self.host = "0"
        #: display Port, as a string decimal code
        self.port = "0"

        #: image size for binary images
        self.size_x = 0
        self.size_y = 0

        #: region of interests [first_col,last_col,first_row,last_row]
        # image coords     - entire image, binned units (starts at each amps reference)
        self.image_roi = []
        self.detector_roi = []  # detector coords  - single detector, unbinned units
        self.amp_roi = []  # amplifier coords - single amp, unbinned units
        self.return_integers = True  # true to return all coords as closest integers
        self.coordinate_type = "detector"

        #: mean of current display ROI
        self.mean = 0.0
        #: standard deviation of current display ROI
        self.sdev = 0.0

        #: get names based on OS type
        self.root = "c:\\ds9\\"
        self.xpaproc = None

        # set default display server
        self.default_display = 0

    def initialize(self):
        """
        Initialize Ds9.

        :return None:
        """

        if self.initialized:
            return

        if os.name == "posix":
            self.xpaset_app = "xpaset"
            self.xpaget_app = "xpaget"
            self.xpaaccess_app = "xpaaccess"
            self.xpans = "xpans"
        else:
            self.ds9_app = f'"{self.root}ds9.exe"'
            self.xpaset_app = f'"{self.root}xpaset.exe"'
            self.xpaget_app = f'"{self.root}xpaget.exe"'
            self.xpaaccess_app = f'"{self.root}xpaaccess.exe"'
            self.xpans = f"{self.root}xpans.exe"

        if not self.enabled:
            azcam.AzcamWarning("Display is not enabled")
            return

        self.set_display(self.default_display)

        return

    # *************************************************************************************************
    #   display server info
    # *************************************************************************************************
    def find_displays(self):
        """
        Returns a list of ds9 servers.
        The returned list is like: ['a00009c:50064', 'a00009c:59734'], which is host:port.
        If not servers are found, the returned list is empty.

        :return list: Display info from XPA
        """

        # command: xpaacess -v ds9

        resp = []

        # cmd = '\"'+self.xpaaccess_app+'\" -v ds9 '
        # output = os.popen(cmd).readlines()

        cmd = os.path.abspath("c:/ds9/xpaaccess.exe")
        # cmd = '\"'+self.xpaaccess_app+'\" -v ds9 '
        # args=['-v','ds9']
        # p=subprocess.Popen([cmd,args],stdout=subprocess.PIPE,stderr=subprocess.PIPE)
        p = subprocess.Popen(
            [cmd, "-v", "ds9"], stdout=subprocess.PIPE, stderr=subprocess.PIPE
        )
        # output = os.popen(cmd).readlines()
        # 1output=p.stdout.readlines()
        output, errors = p.communicate()
        output = output.decode("utf-8")
        if output == "":
            return []
        output = output.strip()
        resp = output.split("\n")

        """
        if len(output) > 0:
            for i,item in enumerate(output):
                addr = item.split(':')
                itemHost = addr[0]
                itemPort = addr[1].split('\n')[0]
                if itemPort.endswith('\n'):
                    itemPort=itemPort[:-1]

                resp.append(itemHost + ':' + itemPort)
        """

        return resp

    def set_display(self, display_number=-1):
        """
        Set the current ds9 display by number.

        :param int display_number: Number for display to be used (0->N)
        :return None:
        """

        if display_number == -1:
            display_number = self.default_display

        reply = self.find_displays()
        if not reply:
            return

        cnt = len(reply)  # number of displays available

        addrList = reply
        if cnt > 0 and display_number < cnt:
            if len(addrList) > 0:
                addr = addrList[display_number].split(":")
                self.host = addr[0]
                self.port = addr[1]
                self.default_display = display_number
        elif cnt > 0:  # one display, set reset default to it
            addr = addrList[0].split(":")
            self.host = addr[0]
            self.port = addr[1]
            self.default_display = 0
            return
        else:
            return

        return

    # *************************************************************************************************
    #   ROI's
    # *************************************************************************************************
    def get_rois(self, roi_number=-1, coordinate_type="default"):
        """
        Returns the Region Of Interest from the display tool and sets the internal ROI descriptors
        to the values read.
        If roi_number is not specified then a list of all defined ROI's is returned.

        :param int roi_number: roi number to be returned
        :param str CoorinateType: Type of coords as defined by the display server ['image','detector', 'amplifier']
        :return list: The list of ROIs
        """

        if coordinate_type == "default":
            coordinate_type = self.coordinate_type

        # single ROI
        if roi_number != -1:
            roi = self._get_ds9_rois(coordinate_type)
            if not roi:
                return []
            if roi_number + 1 > len(roi):
                return []
            if self.return_integers:
                roi1 = []
                for r in roi[roi_number]:
                    roi1.append(int(r))
                return roi1
            else:
                return roi

        roi = self._get_ds9_rois(coordinate_type)
        if not roi:
            return []
        if not self.return_integers:
            return roi

        # make all ROIs integers
        roi1 = []
        for x in roi:
            roiN = []
            for r in x:
                roiN.append(int(r))
            roi1.append(roiN)

        return roi1

    def _get_ds9_rois(self, coordinate_type=""):
        """
        Returns all regions as a list of lists, each as [firstcol,lastcol,firstrow,lastrow].
        Ds9 regions are converted to [firstcol,lastcol,firstrow,lastrow] as close as possible.

        :param str coordinate_type: Type of coords as defined by the display server ['image','detector', 'amplifier']
        :return list: List of ROI's
        """

        if coordinate_type == "":
            coordinate_type = self.coordinate_type

        Rois = self.get_regions(
            coordinate_type
        )  # this is a list of roi's, each [shape, roi]
        if not Rois:
            return []

        rois = []
        for roi in Rois:
            if roi[0] == "box":  # box is the only shape supported at this time
                xcenter = roi[1]
                ycenter = roi[2]
                width = roi[3]
                length = roi[4]
            else:
                return []

            firstcol = xcenter - width / 2.0
            lastcol = xcenter + width / 2.0
            firstrow = ycenter - length / 2.0
            lastrow = ycenter + length / 2.0
            r = [firstcol, lastcol, firstrow, lastrow]
            rois.append(r)

        return rois

    def get_regions(self, coordinate_type="image"):
        """
        Returns a list of regions, each a list of [shape,coords...].

        :param str coordinate_type: Type of coords as defined by the display server ['image','detector', 'amplifier']
        :param list: List of ROI info in ds9 format
        """

        data = []

        # test, could be slow but seems to work nicely
        self.set_display()

        try:
            if coordinate_type == "image":
                cmd = "regions -system image -strip yes"
            elif coordinate_type == "detector":
                cmd = "regions -system detector -strip yes"
            elif coordinate_type == "amplifier":
                cmd = "regions -system amplifier -strip yes"
            else:
                return []

            datads9 = self.xpaget(cmd)[0]
            datads9 = datads9.lstrip("detector;")
            datads9 = datads9.lstrip("image;")
            datads9 = datads9.lstrip("amplifier;")
            datads9 = datads9.rstrip(";")
            datads9 = datads9.split(";")
            # a list of regions
            if len(datads9) > 0:
                for roinum, d in enumerate(datads9):  # each region
                    d = d.lstrip("box(")
                    d = d.rstrip(")")
                    shape = "box"
                    coords = d.split(",")
                    a = []
                    for x in coords:
                        a.append(float(x))
                    a.insert(0, shape)
                    data.append(a)
            else:
                return []

        except Exception:
            return []

        return data

    def read_rois(self):
        """
        Read and internally save image, detector, and amplifier all Rois.

        :return None:
        """

        self.image_roi = self.get_rois(-1, "image")
        if not self.image_roi:
            self.detector_roi = []
            self.amp_roi = []
            return
        self.detector_roi = self.get_rois(-1, "detector")
        self.amp_roi = self.get_rois(-1, "amplifier")

        return

    def get_number_rois(self):
        """
        Returns the number of defined ROI's.

        :return int: Number of ROI's specified by ds9
        """

        self.read_rois()
        numrois = len(self.image_roi)

        return numrois

    def get_roi_string(self, roi_number=0, coordinate_type=""):
        """
        Get an ROI descriptor formatted as a string with integer values.

        :param int roi_number: roi_number to return
        :param str coordinate_type:

        :return list: List of ROIs
        """

        self.read_rois()
        if coordinate_type == "":
            coordinate_type = self.coordinate_type

        if roi_number > len(self.image_roi) - 1:
            return []

        if coordinate_type == "image":
            roi = self.image_roi[roi_number]
        elif coordinate_type == "detector":
            roi = self.detector_roi[roi_number]
        elif coordinate_type == "amplifier":
            roi = self.amp_roi[roi_number]
        else:
            return ""

        roistring = " ".join(str(x) for x in roi)

        return roistring

    def get_last_point(self, coordinate_mode="physical"):
        """
        Returns coordinates of the last point selected.

        :param str coordinate_mode: Coorinate mode, wcs or pysical
        :return list: Coords of point as [x,y] or [] if none
        """
        posX = 0
        posY = 0
        # coordinate_mode = ''

        if coordinate_mode == "wcs":
            cmd = "regions -system wcs -strip yes"
        else:
            cmd = "regions -system physical -strip yes"

        datads9 = self.xpaget(cmd)
        if len(datads9) > 0:
            data = datads9[0]
            if coordinate_mode == "wcs":
                pts = data.lstrip("fk5")
            else:
                pts = data.lstrip("physical")
            pts = pts.split(";")

            for pt in pts:
                pt.strip()
                if len(pt) == 0:
                    continue
                if len(pt) > 0:
                    coord = pt.lstrip("point")
                    coord = pt.lstrip("box")
                    try:
                        coord = coord.lstrip("(")
                        coord = coord.rstrip(")")
                        nums = coord.split(",")
                        posX = nums[0]
                        posY = nums[1]
                    except Exception:
                        pass

            return [float(posX), float(posY)]

        else:
            return []

    def delete_all_rois(self):
        """
        Delete all ROIs.

        :return None:
        """

        cmd = "regions delete all"
        self.xpaset(cmd)

        return

    def draw_box(self, xy, size=[51, 51], angle=0):
        """
        Draw a box on the display.

        :param list xy: [x,y] coords of box to be drawn in image coordinates
        :param list size: [xwidth,ywidth] of box
        :param float angle: Angle of box.
        :return None:
        """

        cmd = f"regions command '{{box {xy[0]} {xy[1]} {size[0]} {size[1]} {angle}}}'"
        self.xpaset(cmd)

        return

    def get_box(self) -> List:
        """
        Get position of the first box in image coords.

        :return None:
        """

        self.read_rois()

        if len(self.image_roi) > 0:
            roi = self.image_roi[0]
            return roi
        else:
            return []

    def set_cursor_mode(self, mode="point", clear_rois=0) -> None:
        """
        Set the display cursor mode.

        :param str mode: Cursor mode ("point", "crosshair")
        :param bool clear_rois: True to clear all ROIs
        """

        if mode == "point":
            self._set_pointer(clear_rois)
        elif mode == "crosshair":
            self._set_crosshair(clear_rois)
        else:
            raise azcam.AzcamError("Invalid cursor mode")

        return

    def _set_crosshair(self, clear_rois=0):
        """
        Set the ds9 pointer to a crosshair.

        :param bool clear_rois: True to clean all ROIs
        :return None:
        """

        if clear_rois:
            self.delete_all_rois()

        # set crosschair
        try:
            cmd = "mode crosshair"
            self.xpaset(cmd)
        except Exception:
            return

        return

    def _set_pointer(self, clear_rois=0):
        """
        Set the ds9 pointer to a pointer.

        :param bool clear_rois: True to clean all ROIs
        :return None:
        """

        # delete all reagions if clear = 1
        if clear_rois:
            self.delete_all_rois()

        # set pointer
        try:
            cmd = "mode pointer"
            self.xpaset(cmd)
        except Exception:
            return

        return

    def zoom(self, scale=0):
        """
        Set display zoom factor relative to current zoom.

        :param int Scale: Scale factor for zoom, 0 "to fit"
        :return None:
        """

        if scale == 0:
            s = "to fit"
        else:
            s = str(scale)

        try:
            cmd = "zoom " + s
            self.xpaset(cmd)
        except Exception:
            return

    # *************************************************************************************************
    #   image display
    # *************************************************************************************************
    def display(self, image, extension_number=-1):
        """
        Display a file in ds9, making a copy so locking does not occur.
        If specified for an MEF file, only extension_number is displayed.

        :param image: a filename or an image object
        :param int extension_number: FITS extension number of image, -1 for all
        :return None:
        """

        # test, could be slow but seems to work nicely
        self.set_display()

        ds9 = self.host + ":" + self.port + " "

        if type(image) == str:
            filename1 = azcam.utils.make_image_filename(image)
        else:
            filename1 = image.filename

        ext = os.path.splitext(filename1)[-1]

        # copy image file so it is not locked by ds9
        filename = os.path.join(tempfile.gettempdir(), "tempdisplayfile" + ext)
        shutil.copyfile(filename1, filename)

        if ext == ".fits":
            im = pyfits.open(filename)
            ne = max(0, len(im) - 1)
            im.close()
            if ne == 0 or ne == 1:
                s = self.xpaset_app + " " + ds9 + "fits iraf < " + filename
            else:
                if extension_number == -1:
                    s = (
                        self.xpaset_app
                        + " "
                        + ds9
                        + "fits mosaicimage iraf < "
                        + filename
                    )
                else:
                    s = (
                        self.xpaset_app
                        + " "
                        + ds9
                        + "fits "
                        + " ["
                        + str(extension_number)
                        + "] "
                        + "< "
                        + filename
                    )
        elif ext == ".bin":
            NumCols, NumRows = self.size_x, self.size_y
            s = (
                self.xpaset_app
                + " "
                + ds9
                + "array [xdim="
                + str(NumCols)
                + ",ydim="
                + str(NumRows)
                + ",bitpix=-16] < "
                + filename
            )

        # execute XPA command to display file
        os.popen(s).readlines()  # grab output to avoid printed error message, always []

        return

    # *************************************************************************************************
    #   examine displayed image
    # *************************************************************************************************
    def exam(self, box_size=20, loop=1):
        """
        Interactive: Get info around blinking cursor position.
        print() is allowed here as interactive only.

        :param int box_size: Size of examine box
        :param bool Loop: True for keep looping until *q* pressed
        :return list: [KeyPressed,X,Y] or [] in case or error.  KeyPressed is a character.
        """

        if loop:
            print("Press q to quit...")

        while 1:
            try:
                xsize = int(box_size)
                ysize = xsize
                cmd = "imexam key data %d %d" % (xsize, ysize)
                datads9 = self.xpaget(cmd)
                key = datads9[0]
                datads9 = datads9[1:]
                data = []
                for d in datads9:
                    data.append(float(d))
                if key == "q":
                    loop = 0
                if loop:
                    print(
                        "key=%1s, mean=%7.0f, std=%6.01f"
                        % (key, float(numpy.mean(data)), float(numpy.std(data)))
                    )
                else:
                    return [key, numpy.mean(data), numpy.std(data)]
            except Exception:
                return []

            if not loop:
                break

    def get_stats(self, roi_number=-1):
        """
        Returns statistics [status,mean,sdev] of an  ROI
        Also sets display.mean and display.sdev global variables.

        :param int roi_number: Number of ROI to get status
        :return list: [status,mean,sdev] for ROI
        """

        data = self.get_data(roi_number)
        self.mean = numpy.mean(data)
        self.sdev = numpy.std(data)

        return [self.mean, self.sdev]

    def show_stats(self, roi_number=0):
        """
        Interactive: Print stats from an ROI in a real-time loop until *q* is pressed.
        print() is allowed here as interactive only.

        :param int roi_number: Number of ROI to get status
        :return list: [status,mean,sdev] for ROI
        """

        print("Displaying mean, sdev, ROI - press q to quit...")

        while 1:
            try:
                mean, sdev = self.get_stats(roi_number)
                print(
                    "mean: %.1f   sdev: %.2f   ROI: %s"
                    % (mean, sdev, str(self.get_roi_string(roi_number)))
                )
                key = azcam.utils.check_keyboard(0)
                if key == "q":
                    break
                time.sleep(0.1)
            except Exception:
                pass

            if azcam.utils.check_keyboard(0) == "q":
                break

        return

    def get_data(self, roi_number=0):
        """
        Returns [Status,[pixel1,pixel2,...]] in display ROI.

        :param int roi_number: Number of ROI to get data
        :return list: [status,[pixel1,pixel2,...]] for ROI
        """

        self.read_rois()
        numrois = len(self.detector_roi)
        if numrois == 0:
            raise azcam.AzcamError("No ROI defined")
        elif roi_number > numrois:
            raise azcam.AzcamError("Invalid ROI number")

        roi = self.detector_roi[roi_number]

        try:
            firstcol = roi[0]
            lastcol = roi[1]
            firstrow = roi[2]
            lastrow = roi[3]
            width = lastcol - firstcol + 1
            length = lastrow - firstrow + 1
            xcenter = firstcol + width / 2.0
            ycenter = firstrow + length / 2.0
            cmd = "data detector %d %d %d %d yes" % (
                xcenter,
                ycenter,
                width,
                length,
            )  # may not be right
            datads9 = self.xpaget(cmd)
            data = []
            for d in datads9:
                d = d.strip()
                data.append(float(d))
            return data
        except Exception:
            return []

    def save_image(self, filename="display.png"):
        """
        Save displayed image as a PNG snapshot.

        :param str filename: filename of image to be saved.
        :return None:
        """

        # many kluges here, XPA seems buggy on this.

        # problem with paths so use only filename
        # fullname=os.path.abspath(filename)
        # filename=os.path.basename(filename)
        # folder=os.path.dirname(fullname)
        fullname = filename

        f = fullname.lstrip("C:")

        # save image
        cmd = "saveimage png " + f
        self.xpaset(cmd)

        return None

    def save_fits(self, filename="display.fits"):
        """
        Save displayed image as a FITS file.

        :param str filename: filename of image to be saved.
        :return None:
        """

        folder = os.getcwd()
        filename = os.path.join(folder, filename)

        filename = os.path.normpath(filename)

        cmd = "save " + filename
        reply = self.xpaset(cmd)

        return reply

    # *************************************************************************************************
    #   XPA commands
    # *************************************************************************************************

    def xpaget(self, command):
        """
        Issue xpaget command for ds9.
        Returns data as a list of space deliminated items.

        :param str command: command string for xpaget command
        :return: Return value
        """

        ds9 = self.host + ":" + self.port + " "

        cmd = self.xpaget_app + " " + ds9 + command
        output = os.popen(cmd).readlines()

        if len(output) == 1:
            output = output[0].strip().split(" ")

        return output

    def xpaset(self, command):
        """
        Issue xpaset command for ds9.

        :param str command: command string for xpaset command
        :return: Return value

        """

        ds9 = self.host + ":" + self.port + " "
        cmd = self.xpaset_app + " -p " + ds9 + command

        cmd = cmd.replace("\\\\", "/")
        cmd = cmd.replace("/", "\\")

        reply = os.popen(cmd)
        # reply=subprocess.Popen(cmd,cwd=folder)
        # reply=subprocess.Popen(cmd)

        return reply
