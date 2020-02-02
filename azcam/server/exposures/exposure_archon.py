"""
Contains the ExposureArchon class.
"""

import numpy
import os
import time

from astropy.io import fits as pyfits

import azcam
from azcam.server.exposures.exposure import Exposure


class ExposureArchon(Exposure):
    """
    The exposure class for Archon controllers.
    The methods here override the default Exposure class and are for the STA Archon controller
    used in 'direct mode', communicating directly with the controller hardware.
    """

    def __init__(self, *args):

        super().__init__(*args)

        self.id = "archon"
        self.receive_data = ReceiveDataArchon(self)
        self.fileconverter = ArchonFileConverter()

        # add extra extensions for additional non-image data
        self.add_extensions = 0

        try:
            self.objects_init.remove("controller")
        except Exception:
            pass

    def abort(self):
        """
        Abort an exposure in progress.
        Sends RESETTIMING to controller and sets the ExposureFlag which is read
        in during the exposure.
        """

        azcam.db.objects["controller"].archon_command("RESETTIMING")

        if self.exposure_flag != azcam.db.exposureflags["NONE"]:
            self.exposure_flag = azcam.db.exposureflags["ABORT"]

        return

    def start_readout(self):
        """
        Immediate exposure readout.
        """

        if self.exposure_flag != azcam.db.exposureflags["NONE"]:
            self.exposure_flag = azcam.db.exposureflags["READ"]

        azcam.db.objects["controller"].archon_command("FASTLOADPARAM StopExposure 1")
        time.sleep(0.1)
        azcam.db.objects["controller"].archon_command("FASTLOADPARAM StopExposure 0")

        return

    def flush(self, cycles=1):
        """
        Flush/clear detector.
        cycles is the number of times to flush the detector.
        """

        # not supported yet
        return

    def integrate(self):
        """
        Integration.
        """

        # make the exposure itself here
        self.dark_time_start = time.time()
        # azcam.log("Integration started")

        azcam.db.objects["controller"].start_exposure(1)

        # dark time includes readout
        self.dark_time = time.time() - self.dark_time_start

        # turn off comp lamps
        if self.comp_exposure:
            if not azcam.db.objects["instrument"].shutter_strobe:
                azcam.db.objects["instrument"].comps_off()
            azcam.db.objects["instrument"].set_active_comps("shutter")

        # set times
        self.exposure_time_remaining = 0
        if self.image_type == "zero":
            self.exposure_time = self.exposure_time_saved

        self.exposure_flag == azcam.db.exposureflags["READ"]

        # azcam.log("Integration finished", level=2)

        return

    def end(self):
        """
        Completes an exposure by writing file and displaying image.
        """

        self.exposure_flag = azcam.db.exposureflags["WRITING"]

        if self.image.remote_imageserver_flag:
            LocalFile = (
                self.temp_image_file + "." + self.filename.get_extension(self.filetype)
            )
            try:
                os.remove(LocalFile)
            except FileNotFoundError:
                pass
        else:
            LocalFile = self.filename.get_name()

        # get the image data and put into buffer controller.imagedata
        self.receive_data.receive_archon_image_data()

        self.pixels_remaining = 0

        controller = azcam.db.objects["controller"]

        # create buffer for entire image, including all overscans
        self.image.data = numpy.empty(
            shape=(
                self.image.focalplane.numamps_image,
                self.image.focalplane.numcols_amp * self.image.focalplane.numrows_amp,
            ),
            dtype="uint16",
        )

        self.fileconverter.copy_to_buffer(controller.imagedata, self.image.data)

        # why is this necessary?
        self.image.data.reshape(
            self.image.focalplane.numamps_image,
            self.image.focalplane.numcols_amp * self.image.focalplane.numrows_amp,
        )

        # write MEF file
        self.image.overwrite = self.filename.overwrite
        self.image.test_image = self.filename.test_image

        controller = azcam.db.objects["controller"]
        controller.header.set_keyword(
            "INTMS", self.fileconverter.intms, "Open shutter exposure time (ms)"
        )
        controller.header.set_keyword(
            "NOINTMS", self.fileconverter.nointms, "Closed shutter exposure time (ms)"
        )

        # update controller header with keywords which might have changed
        et = float(int(self.exposure_time_actual * 1000.0) / 1000.0)
        self.dark_time = et  # does not yet include pause/resume
        dt = float(int(self.dark_time * 1000.0) / 1000.0)
        azcam.db.headers["exposure"].set_keyword(
            "EXPTIME", et, "Exposure time (seconds)", float
        )
        azcam.db.headers["exposure"].set_keyword(
            "DARKTIME", dt, "Dark time (seconds)", float
        )

        self.image.write_file(LocalFile, self.filetype)

        # add info data in extra extensions
        if self.add_extensions:

            controller.get_status()  # get current controller data

            # hdu17 is Test Conditions extension
            hdu17 = pyfits.BinTableHDU()

            # hdu18 is CCD Operating Conditions extension
            hdu18 = pyfits.BinTableHDU()

            # hdu19 is Site-Specific extension

            # create data arrays
            keywords = []
            values = []
            datatypes = []
            units = []
            comments = []
            for key in controller.dict_status:
                keywords.append(key)
                values.append(controller.dict_status[key])
                datatypes.append("unknown")
                units.append("a unit")
                comments.append("a comment")

            # make table columns
            c1 = pyfits.Column(name="Keyword", format="20A", array=keywords)
            c2 = pyfits.Column(name="Value", format="20A", array=values)
            c3 = pyfits.Column(name="DataType", format="20A", array=datatypes)
            c4 = pyfits.Column(name="Units", format="20A", array=units)
            c5 = pyfits.Column(name="Comment", format="80A", array=comments)
            coldefs = pyfits.ColDefs([c1, c2, c3, c4, c5])
            hdu19 = pyfits.BinTableHDU.from_columns(coldefs)

            # append HDU's to image file
            with pyfits.open(LocalFile, mode="update") as hdulist:
                hdulist.append(hdu17)
                hdulist.append(hdu18)
                hdulist.append(hdu19)

        azcam.log(f"Writing finished: {LocalFile}", level=2)

        # set flag that image now written to disk
        self.image.written = 1

        # image data and file are now ready
        self.image.toggle = 1

        # display image
        if self.display_image:
            azcam.log("Displaying image")
            azcam.db.objects["display"].display(LocalFile)

        if self.image.remote_imageserver_flag:
            azcam.log("Sending image to image server")
            self.image.send_image(LocalFile)

        # increment file sequence number if image was written
        if self.save_file:
            self.filename.increment()

        self.exposure_flag = azcam.db.exposureflags["NONE"]

        return

    def set_exposuretime(self, ExposureTime):
        """
        Set current exposure time in seconds.
        """

        self.exposure_time = float(ExposureTime)
        self.exposure_time_actual = self.exposure_time  # may be changed later

        controller = azcam.db.objects["controller"]

        if self.image_type == "zero":
            controller.set_exposuretime(0)
            controller.set_no_int_ms(0)
            return

        # set timer and for header keyword
        controller.set_exposuretime(int(self.exposure_time * 1000))

        # get shutter state
        try:
            shutterstate = self.shutter_dict[self.image_type]
        except KeyError:
            shutterstate = "open"  # other types are comps, so open shutter

        if shutterstate == "open":
            controller.set_int_ms(int(self.exposure_time * 1000))
            controller.set_no_int_ms(0)
        else:
            controller.set_no_int_ms(int(self.exposure_time * 1000))
            controller.set_int_ms(0)

        return

    def get_exposuretime(self):
        """
        Get current exposure time in seconds.
        """

        # not read directly from Archon controller
        return self.exposure_time

    def get_pixels_remaining(self):
        """
        Return number of remaining pixels to be read.
        """

        return azcam.db.objects["controller"].get_pixels_remaining()


class ArchonFileConverter(object):
    """
    Class to convert Archon image file.
    """

    def __init__(self):

        # save MEF file
        self.save_file = 0
        # output buffer
        self.o_data = 0

        # data types for fits images
        self.data_types = {
            8: "uint8",
            16: "uint16",
            32: "uint32",
            64: "uint64",
            -32: "float32",
            -64: "float64",
        }

        self.detector_filename = ""

        self.overwrite_infile = 0
        self.overwrite_outfile = 0

        self.fSize = 0
        self.out_file = ""
        self.curr_file = ""

        self.hdulist = ""

        # values read from the configuration file
        self.detname = ""
        self.detnum = []
        self.detpos_x = []
        self.detpos_y = []
        self.extpos_x = []
        self.extpos_y = []
        self.detformat = []
        self.focalplane = []
        self.roi = []
        self.amppix1 = []
        self.amppix2 = []
        self.ampcfg = []
        self.extname = []
        self.extnum = []
        self.jpgext = []
        self.amppos1 = []
        self.amppos2 = []
        self.ampcfg = []

        self.ns_total = 0
        self.ns_predark = 0
        self.ns_underscan = 0
        self.ns_overscan = 0
        self.np_total = 0
        self.np_predark = 0
        self.np_underscan = 0
        self.np_overscan = 0
        self.np_frametransfer = 0

        self.valid = 1
        self.num_extensions = 16
        self.asmsize = (0, 0)
        self.size_x = 0
        self.size_y = 0
        self.asmmode = 1
        self.from_file = 0

        self.offsets = 16 * [0.0]
        self.scales = 16 * [1.0]

        self.prescan1 = 0
        self.prescan2 = 0

        self.exptime = 0.0
        self.intms = 0
        self.nointms = 0

    def copy_to_buffer(self, in_buffer, out_buffer):
        """
        Copies the data from the controller to a data buffer.
        Last change: 21Dec2016 Zareba
        """

        self.InData = in_buffer
        self.o_data = out_buffer

        self.buffer_processing()

        return

    def buffer_processing(self):
        """
        Process input buffer to output MEF file.
        Last change: 21Dec2016 Zareba
        """

        controller = azcam.db.objects["controller"]
        frameBase = "BUF%d" % (controller.read_buffer)

        self.NAMPS = self.numparamps * self.numseramps
        self.NAXIS1 = int(controller.dict_frame[frameBase + "WIDTH"])
        self.NAXIS2 = int(controller.dict_frame[frameBase + "HEIGHT"])
        self.PIXELS = int(controller.dict_frame[frameBase + "PIXELS"])
        self.LINES = int(controller.dict_frame[frameBase + "LINES"])

        self.data_type = "<u2"
        self.exptime = float(controller.int_ms / 1000)
        self.intms = controller.int_ms
        self.nointms = controller.noint_ms

        # if self.NAMPS > 1 disassemble image
        # if self.NAMPS == 1:
        #    return

        # make a copy on the input data
        self.data = numpy.ndarray(
            shape=(self.NAXIS1 * self.NAXIS2), buffer=self.InData, dtype=self.data_type
        ).copy()

        # reshape the input data array copy
        self.NData = self.data.reshape(self.NAMPS * self.LINES, self.PIXELS).copy()

        # current line of self.PIXELS pixels
        cntLine = 0

        self.StartTime = time.time()

        for posY in range(0, self.numparamps):
            currPart = posY * self.numseramps
            for currLine in range(0, self.LINES):
                for posX in range(0, self.numseramps):
                    posAmp = posX + currPart
                    indxAmp = (
                        (self.extpos_y[posAmp] - 1) * self.numseramps
                        + self.extpos_x[posAmp]
                        - 1
                    )
                    if self.ampcfg[posAmp] == 0:
                        # no flip
                        self.o_data[indxAmp][
                            currLine * self.PIXELS : (currLine + 1) * self.PIXELS
                        ] = self.NData[cntLine]
                    elif self.ampcfg[posAmp] == 1:
                        # flip X
                        self.o_data[indxAmp][
                            currLine * self.PIXELS : (currLine + 1) * self.PIXELS
                        ] = self.NData[cntLine][::-1]
                    elif self.ampcfg[posAmp] == 2:
                        # flip Y
                        self.o_data[indxAmp][
                            (self.LINES - currLine - 1)
                            * self.PIXELS : (self.LINES - currLine)
                            * self.PIXELS
                        ] = self.NData[cntLine]
                    else:
                        # flip XY
                        self.o_data[indxAmp][
                            (self.LINES - currLine - 1)
                            * self.PIXELS : (self.LINES - currLine)
                            * self.PIXELS
                        ] = self.NData[cntLine][::-1]
                    cntLine += 1

        self.StopTime = time.time()

        return

    def set_detector_config(self, sensor_data):
        """
        Set detector configuration parameters.
        """

        """
        Notes:
            # ExtPosN - in ds9 - (1,1) is bottem left
            # ExtNum for IMAGEID
        """

        self.detname = sensor_data["name"]
        self.detnum = sensor_data["detnum"]
        self.detformat = sensor_data["format"]
        self.focalplane = sensor_data["focalplane"]
        self.roi = sensor_data["roi"]
        self.extname = sensor_data["extname"]
        self.extnum = sensor_data["extnum"]
        self.jpgext = sensor_data["jpg_order"]
        self.ampcfg = sensor_data["ampcfg"]

        self.extpos_x = [x[0] for x in sensor_data["extension_position"]]
        self.extpos_y = [x[1] for x in sensor_data["extension_position"]]
        self.amppos1 = [x[0] for x in sensor_data["amp_position"]]
        self.amppos2 = [x[1] for x in sensor_data["amp_position"]]
        self.detpos_x = [x[0] for x in sensor_data["detpos"]]
        self.detpos_y = [x[1] for x in sensor_data["detpos"]]
        self.amppix1 = [x[0] for x in sensor_data["amp_pixel_position"]]
        self.amppix2 = [x[1] for x in sensor_data["amp_pixel_position"]]

        self.ns_total = self.detformat[0]
        self.ns_predark = self.detformat[1]
        self.ns_underscan = self.detformat[2]
        self.ns_overscan = self.detformat[3]
        self.np_total = self.detformat[4]
        self.np_predark = self.detformat[5]
        self.np_underscan = self.detformat[6]
        self.np_overscan = self.detformat[7]
        self.np_frametransfer = self.detformat[8]

        self.numseramps = self.focalplane[2]
        self.numparamps = self.focalplane[3]

        return


class ReceiveDataArchon(object):
    """
    Exposure subclass to receive image data.
    """

    def __init__(self, exposure):

        self.exposure = exposure  # upper level exposure object

        self.DeinterlaceParams = ""
        self.port = 0
        self.valid = 1

        self.PixelsReadout = 0
        self.pixels_remaining = 0
        self.pixels_remaining = 0
        self.camserver = 0
        self.socket = 0

        # Deinterlace mode
        self.deinterlace_mode = 1
        # Number of pixels per amplifier
        self.numpix_amp = 0
        # Number of amplifiers
        self.numamps_image = 0

    def receive_archon_image_data(self):
        """
        Receives image data and raw data (if rawdata_enable=1) from the Archon controller in the Direct Mode.
        Last change: 06Feb2018 Zareba
        """

        exposure = azcam.db.objects["exposure"]
        controller = azcam.db.objects["controller"]

        # initial values
        self.PixelsReadout = 0
        self.pixels_remaining = 0

        # values taken from the Archon GUI
        BURST_LEN = 1024
        lineSize = BURST_LEN
        # chunkSize = 1024 * BURST_LEN
        rawBlockSize = 2048

        if controller.read_buffer > 0 and controller.read_buffer < 4:

            frameBase = "BUF%d" % (controller.read_buffer)
            frame = frameBase + "FRAME"

            if int(controller.dict_frame[frame]) > 0:

                # frame buffer base address
                addr = int(controller.dict_frame[frameBase + "BASE"])
                # get frame width and height
                frameW = int(controller.dict_frame[frameBase + "WIDTH"])
                frameH = int(controller.dict_frame[frameBase + "HEIGHT"])
                # get sample mode
                sampleMode = int(controller.dict_frame[frameBase + "SAMPLE"]) + 1

                # calculate fetch command values
                frameSize = sampleMode * 2 * frameW * frameH
                lines = int((frameSize + lineSize - 1) / lineSize)
                rawBlocks = int(controller.dict_frame[frameBase + "RAWBLOCKS"])
                rawLines = int(controller.dict_frame[frameBase + "RAWLINES"])
                rawSize = rawBlocks * rawLines * rawBlockSize
                rawOffset = int(controller.dict_frame[frameBase + "RAWOFFSET"])

                cmd = "FETCH%08X%08X" % (addr, lines)

                """
                size = (
                    (int(controller.dict_frame[frameBase + "SAMPLE"]) + 1)
                    * 2
                    * int(controller.dict_frame[frameBase + "HEIGHT"])
                    * int(controller.dict_frame[frameBase + "WIDTH"])
                )
                """

                controller.archon_bin_command(cmd)

                # frameSize = frameSize + 4
                totalRecv = 0

                self.TData = numpy.empty(shape=int(frameSize / 2), dtype="<u2")

                self.pixels_remaining = frameSize / 2
                self.PixelsReadout = 0

                # total bytes received from the Archon controller | each data frame starts with preamble '<NN:' | last data frame includes padding bytes
                totalBytes = lines * (lineSize + 4)

                totalRecv = 0
                currLine = lineSize + 4

                dataBuff = b""
                totalPix = 0
                imgPix = frameSize / 2

                while totalRecv < totalBytes:
                    getData = controller.camserver.socket.recv(currLine)

                    totalRecv += len(getData)

                    dataBuff += getData
                    currLen = len(dataBuff)

                    if currLen >= 1028:
                        # got one fulle data frame
                        if dataBuff[3] == 58:
                            if totalPix + 512 < imgPix:
                                pixCnt = 512
                            else:
                                pixCnt = imgPix - totalPix

                            currBytes = 2 * pixCnt

                            lData = int(currBytes + 4)
                            ImageBufferTemp = numpy.ndarray(
                                shape=(int(pixCnt)),
                                dtype="<u2",
                                buffer=dataBuff[4:lData],
                            )

                            lData = int(totalPix + pixCnt)
                            self.TData[totalPix:lData] = ImageBufferTemp[
                                0 : int(pixCnt)
                            ]
                            totalPix += pixCnt

                            dataBuff = dataBuff[1028:]
                        else:
                            azcam.log(
                                "-----> dataBuff length:", len(dataBuff), level=3
                            )
                            totalRecv = totalBytes

                azcam.log("----> totalRecv =", totalRecv, level=3)
                if totalRecv == totalBytes:
                    exposure.image.valid = 1
                    self.pixels_remaining = 0
                    controller.imagedata = self.TData
                    azcam.db.objects["exposure"].image.data = self.TData

                    if controller.rawdata_enable == 1:
                        # receive rad data
                        lines = int((rawSize + lineSize - 1) / lineSize)

                        cmd = "FETCH%08X%08X" % (addr + rawOffset, lines)

                        controller.archon_bin_command(cmd)

                        # frameSize = frameSize + 4
                        totalRecv = 0

                        self.RData = numpy.empty(shape=int(rawSize / 2), dtype="<u2")

                        self.pixels_remaining = rawSize / 2
                        self.PixelsReadout = 0

                        # total bytes received from the Archon controller | each data frame starts with preamble '<NN:' | last data frame includes padding bytes
                        totalBytes = lines * (lineSize + 4)

                        totalRecv = 0
                        currLine = lineSize + 4

                        dataBuff = b""
                        totalPix = 0
                        imgPix = frameSize / 2

                        # total bytes received from the Archon controller | each data frame starts with preamble '<NN:' | last data frame includes padding bytes
                        totalBytes = lines * (lineSize + 4)

                        totalRecv = 0

                        self.RData = numpy.empty(shape=int(rawSize / 2), dtype="<u2")

                        while totalRecv < totalBytes:
                            getData = controller.camserver.socket.recv(currLine)

                            totalRecv += len(getData)

                            dataBuff += getData
                            currLen = len(dataBuff)

                            if currLen >= 1028:
                                # got one fulle data frame
                                if dataBuff[3] == 58:
                                    if totalPix + 512 < imgPix:
                                        pixCnt = 512
                                    else:
                                        pixCnt = imgPix - totalPix

                                    currBytes = 2 * pixCnt

                                    lData = int(currBytes + 4)
                                    ImageBufferTemp = numpy.ndarray(
                                        shape=(int(pixCnt)),
                                        dtype="<u2",
                                        buffer=dataBuff[4:lData],
                                    )

                                    lData = int(totalPix + pixCnt)
                                    self.RData[totalPix:lData] = ImageBufferTemp[
                                        0 : int(pixCnt)
                                    ]
                                    totalPix += pixCnt

                                    dataBuff = dataBuff[1028:]
                                else:
                                    azcam.log(
                                        "-----> dataBuff length:",
                                        len(dataBuff),
                                        level=3,
                                    )
                                    azcam.log("ERROR ", dataBuff[:4].decode(), level=3)
                                    totalRecv = totalBytes

                        if totalRecv == totalBytes:
                            controller.rawdata = self.RData

                    return

                else:
                    if exposure.exposure_flag != exposure.EF_ABORT:
                        s = "ERROR did not receive entire image buffer"
                        raise azcam.AzcamError(s)
                    else:
                        raise azcam.AzcamError("Exposure ABORTED")

            else:
                raise azcam.AzcamError("No frame available for fetching")

        else:
            raise azcam.AzcamError("Wrong frame number")
