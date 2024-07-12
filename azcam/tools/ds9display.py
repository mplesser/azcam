"""
Contains the Ds9Display class.
"""

"""
Note: This is a special tool as it is used by server and clients and so does not use 
the base Tools class.
"""

import os
import shutil
import subprocess
import tempfile
import time
from typing import List

import numpy
from astropy.io import fits as pyfits

import azcam
import azcam.utils
import azcam.exceptions
from azcam.tools.display import Display


class Ds9Display(Display):
    """
    Azcam's interface to SAO's ds9 image display tool.
    """

    def __init__(self):
        #: name used to reference the tool ("controller", "display", ...)
        self.tool_id: str = "display"

        #: descriptive tool name
        self.description: str = "ds9 display"

        super().__init__(self.tool_id, self.description)

        #: 1 when tool is enabled
        self.is_enabled: int = 1

        #: 1 when tool has been initialized
        self.is_initialized: int = 0

        #: 1 when tool has been reset
        self.is_reset: int = 0

        azcam.db.tools[self.tool_id] = self

        #: verbosity for debug, >0 is more verbose
        self.verbosity = 0

        # display Host, as a string hex code
        self.host = "0"
        # display Port, as a string decimal code
        self.port = "0"

        # image size for binary images
        self.size_x = 0
        self.size_y = 0

        # ROI's[first_col,last_col,first_row,last_row]
        # image coords     - entire image, binned units (starts at each amps reference)
        self.image_roi = []
        self.detector_roi = []  # detector coords  - single detector, unbinned units
        self.amp_roi = []  # amplifier coords - single amp, unbinned units
        self.return_integers = True  # true to return all coords as closest integers
        self.coordinate_type = "detector"

        # mean of current display ROI
        self.mean = 0.0
        # standard deviation of current display ROI
        self.sdev = 0.0

        # get names based on OS type
        self.root = None
        self.xpaproc = None

        # set default display server
        self.default_display = 0

    def initialize(self):
        """
        Initialize Ds9.

        :return None:
        """

        if self.is_initialized:
            return

        if os.name == "posix":
            self.xpaset_app = "xpaset"
            self.xpaget_app = "xpaget"
            self.xpaaccess_app = "xpaaccess"
            self.xpans = "xpans"
        else:
            self.root = "c:\\ds9\\"
            self.ds9_app = os.path.join(self.root, "ds9.exe")
            self.ds9_app = os.path.abspath(self.ds9_app)
            self.xpaset_app = os.path.join(self.root, "xpaset.exe")
            self.xpaset_app = os.path.abspath(self.xpaset_app)
            self.xpaget_app = os.path.join(self.root, "xpaget.exe")
            self.xpaget_app = os.path.abspath(self.xpaget_app)
            self.xpaaccess_app = os.path.join(self.root, "xpaaccess.exe")
            self.xpaaccess_app = os.path.abspath(self.xpaaccess_app)
            self.xpans = os.path.join(self.root, "xpans.exe")
            self.xpans = os.path.abspath(self.xpans)

        if not self.is_enabled:
            azcam.exceptions.warning("Display is not enabled")
            return

        self.set_display(self.default_display)

        self.is_initialized = 1

        return

    def reset(self) -> None:
        """
        Reset the tool.
        """

        self.is_reset = 1

        return

    def start(self, flag=0):
        """
        Starts a display process.
        """

        self.initialize()

        cmd = [self.ds9_app]
        p = subprocess.Popen(
            cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=False
        )

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

        cmd = self.xpaaccess_app
        p = subprocess.Popen(
            [self.xpaaccess_app, "-v", "ds9"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            shell=False,
        )
        output, errors = p.communicate()
        output = output.decode("utf-8")
        if output == "":
            return []
        output = output.strip()
        resp = output.split("\n")

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
    #   display image
    # *************************************************************************************************
    def display(self, image, extension_number=-1):
        """
        Display a file in ds9, making a copy so locking does not occur.
        If specified for an MEF file, only extension_number is displayed.

        :param image: a filename or an image object
        :param int extension_number: FITS extension number of image, -1 for all
        :return None:
        """

        self.initialize()

        # test, could be slow but seems to work nicely
        self.set_display()

        ds9 = self.host + ":" + self.port

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
            if ne in [0, 1]:
                # s = self.xpaset_app + " " + ds9 + "fits iraf < " + filename
                s = [self.xpaset_app, ds9, f"fits iraf < {filename}"]
            else:
                if extension_number == -1:
                    # s = self.xpaset_app + " " + ds9 + "fits mosaicimage iraf < " + filename
                    s = [self.xpaset_app, ds9, f"fits mosaicimage iraf < {filename}"]
                else:
                    s = [
                        self.xpaset_app,
                        ds9,
                        "fits",
                        f"[{extension_number}] < {filename}",
                    ]
        elif ext == ".bin":
            NumCols, NumRows = self.size_x, self.size_y
            s = [
                self.xpaset_app,
                ds9,
                "array",
                f"[xdim={NumCols},ydim={NumRows},bitpix=-16] < {filename}",
            ]
        else:
            azcam.exceptions.warning("invalid image extension")
            return

        # execute XPA command to display file
        s = " ".join(s)
        p = subprocess.Popen(
            s,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            shell=True,
        )
        stdout, stderr = p.communicate()
        stdout = stdout.decode("utf-8")

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
            if coordinate_type == "amplifier":
                cmd = "regions -system amplifier -strip yes"
            elif coordinate_type == "detector":
                cmd = "regions -system detector -strip yes"
            elif coordinate_type == "image":
                cmd = "regions -system image -strip yes"
            else:
                return []

            datads9 = self.xpaget(cmd)
            datads9 = datads9.lstrip("detector;")
            datads9 = datads9.lstrip("image;")
            datads9 = datads9.lstrip("amplifier;")
            datads9 = datads9.rstrip(";")
            datads9 = datads9.split(";")
            # a list of regions
            if len(datads9) > 0:
                shape = "box"
                for roinum, d in enumerate(datads9):  # each region
                    d = d.lstrip("box(")
                    d = d.rstrip(")")
                    coords = d.split(",")
                    a = [float(x) for x in coords]
                    a.insert(0, shape)
                    data.append(a)
            else:
                return []

        except Exception as e:
            azcam.log(e)
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
        return len(self.image_roi)

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

        if coordinate_type == "amplifier":
            roi = self.amp_roi[roi_number]
        elif coordinate_type == "detector":
            roi = self.detector_roi[roi_number]
        elif coordinate_type == "image":
            roi = self.image_roi[roi_number]
        else:
            return ""

        return " ".join(str(x) for x in roi)

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
            return self.image_roi[0]
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
            raise azcam.exceptions.AzcamError("Invalid cursor mode")

        return

    def zoom(self, scale=0):
        """
        Set display zoom factor relative to current zoom.

        :param int Scale: Scale factor for zoom, 0 "to fit"
        :return None:
        """

        s = "to fit" if scale == 0 else str(scale)
        try:
            cmd = "zoom " + s
            self.xpaset(cmd)
        except Exception:
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
                data = [float(d) for d in datads9]
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
            raise azcam.exceptions.AzcamError("No ROI defined")
        elif roi_number > numrois:
            raise azcam.exceptions.AzcamError("Invalid ROI number")

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
            datads9 = datads9.split("\n")
            for d in datads9:
                if len(d) == 0:
                    continue
                data.append(float(d))
            return data
        except Exception as e:
            azcam.log(f"ds9 error: {e}")
            return []

    # *************************************************************************************************
    #   save displayed image
    # *************************************************************************************************
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
        return self.xpaset(cmd)

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

        # execute XPA command
        p = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            shell=True,
        )
        stdout, stderr = p.communicate()
        stdout = stdout.decode("utf-8")

        return stdout

    def xpaset(self, command) -> None:
        """
        Issue xpaset command for ds9.

        :param str command: command string for xpaset command

        """

        ds9 = self.host + ":" + self.port + " "
        cmd = self.xpaset_app + " -p " + ds9 + command

        cmd = cmd.replace("\\\\", "/")
        cmd = cmd.replace("/", "\\")

        # execute XPA command
        p = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            shell=True,
        )
        stdout, stderr = p.communicate()

        return
