import socket
import time

import numpy

import azcam
import azcam.exceptions


class ReceiveData(object):
    """
    Exposure subclass to receive image data.
    """

    def __init__(self, exposure):

        self.exposure = exposure  # upper level exposure object

        self.DeinterlaceParams = ""
        self.port = 0
        self.is_valid = 1

        self.PixelsReadout = 0
        self.pixels_remaining = 0
        self.camserver = 0
        self.socket = 0

        # Deinterlace mode
        self.deinterlace_mode = 1
        # Number of pixels per amplifier
        self.numpix_amp = 0
        # Number of amplifiers
        self.numamps_image = 0

        # using this helps writing efficiency, bytes
        self.RecBufferSize = 5 * 1024 * 1024

    def receive_image_data(self, data_size):
        """
        Receive binary image data from controller server.
        data_size is bytes.
        """

        if azcam.db.tools["controller"].camserver.demo_mode:
            self.mock_data()
            return

        # create a new socket for binary data and connect to the controller server
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        self.socket.connect(
            (
                azcam.db.tools["controller"].camserver.host,
                azcam.db.tools["controller"].camserver.port,
            )
        )

        azcam.log(f"Receiving image data: {data_size} bytes", level=3)

        # Init Deinterlace
        self.numamps_image = self.exposure.image.focalplane.numamps_image
        self.numpix_amp = self.exposure.image.focalplane.numpix_amp

        reqCnt = min(
            data_size - 17, self.RecBufferSize - 17
        )  # 17 bytes for the data frame size (%16d + space)
        dataCnt = 0  # receved data counter
        repCnt = 0  # repeate data request counter: 100
        getData = b""
        totalpixels = int(data_size / 2)
        self.PixelsReadout = 0
        self.pixels_remaining = totalpixels

        # create temporary image buffer
        BufferTemp = numpy.empty(shape=(self.exposure.image.data.size), dtype="<u2")

        # set image data pointer
        ptrData = 0

        # loop over data just read, long repeat as images could be slow to start
        while (dataCnt < data_size) and (repCnt < 50):

            # check if aborted by user (from abort() - controller.abort()
            if (
                azcam.db.tools["exposure"].exposure_flag
                == azcam.db.tools["exposure"].exposureflags["ABORT"]
            ):

                # if in a sequence then let this readout finish
                if self.exposure.is_exposure_sequence:
                    pass  # return will not be an error
                else:
                    # break out of read loop
                    azcam.db.tools[
                        "controller"
                    ].readout_abort()  # stop ControllerServer
                    break

            getData = self.request_data(
                reqCnt + 17
            )  # request data + 17 bytes for data length
            len1 = len(getData)
            azcam.log(f"Readout: {self.pixels_remaining:10d} pixels remaining", level=3)

            if len1 != 0:
                dataCnt += len1
                repCnt = 0

                # store data
                pixelsreadout = int(
                    len1 / 2
                )  # number pixels in this read now available

                # convert received data to unsigned shorts
                ImageBufferTemp = numpy.ndarray(
                    shape=(1, pixelsreadout), dtype="<u2", buffer=getData
                )

                # copy the data into TempBuffer
                BufferTemp[ptrData : ptrData + pixelsreadout] = ImageBufferTemp[
                    0:pixelsreadout
                ]
                ptrData = ptrData + pixelsreadout

                reqCnt = min(data_size - dataCnt - 17, self.RecBufferSize - 17)
                self.PixelsReadout = self.PixelsReadout + pixelsreadout
                self.pixels_remaining = self.pixels_remaining - pixelsreadout
                # time.sleep(0.2)
            else:
                time.sleep(0.2)
                repCnt = repCnt + 1

        # check if all data has been received
        if dataCnt == data_size:
            self.is_valid = 1
            self.pixels_remaining = 0
            azcam.log("Image data received")
        else:
            if (
                not azcam.db.tools["exposure"].exposure_flag
                == azcam.db.tools["exposure"].exposureflags["ABORT"]
            ):
                s = "ERROR in ReceiveImageData: Received %d of %d bytes" % (
                    dataCnt,
                    data_size,
                )
                self.socket.close()
                raise azcam.exceptions.AzcamError(s)
            else:
                self.socket.close()
                raise azcam.exceptions.AzcamError(
                    "Aborted in receive_image_data", error_code=3
                )
        self.socket.close()

        # deinterlace into exposure.image.data
        BufferTemp = BufferTemp.reshape(self.numpix_amp, self.numamps_image)

        if len(self.exposure.data_order) == 0:
            for AmpPos in range(0, self.numamps_image):
                self.exposure.image.data[AmpPos, 0 : self.numpix_amp] = BufferTemp[
                    0 : self.numpix_amp, AmpPos
                ]
        else:
            indx = 0
            for item in self.exposure.data_order:
                self.exposure.image.data[indx, 0 : self.numpix_amp] = BufferTemp[
                    0 : self.numpix_amp, item
                ]
                indx += 1

        return

    def request_data(self, datacnt):

        request = "GetImageData " + str(datacnt) + "\n"
        self.socket.send(str.encode(request))

        loop = 1
        rptCnt = 10
        data = b""
        gotCnt = 0
        dataFrame = b""
        oneFrame = b""
        cntFrame = 0

        datacnt += 17
        while (loop == 1) and (rptCnt > 0):
            oneFrame = self.socket.recv(datacnt)
            if len(oneFrame) > 0:
                dataFrame += oneFrame
                cntFrame += 1

                if gotCnt == 0:
                    if len(dataFrame) >= 17:
                        dataCnt = int(dataFrame[0:16])
                        if dataCnt > 0:
                            data += dataFrame[17:]
                            if dataCnt == len(dataFrame[17:]):
                                gotCnt = 0
                                loop = 0
                            else:
                                dataFrame = dataFrame[17:]
                                datacnt = datacnt - 17 - len(dataFrame[17:])
                                gotCnt = 1
                        else:
                            loop = 0
                            data = ""
                    else:
                        datacnt = datacnt - len(dataFrame)
                        rptCnt -= 1
                else:
                    if dataCnt == len(dataFrame):
                        data = dataFrame
                        loop = 0

            else:  # time out: received no data
                rptCnt -= 1

        if rptCnt == 0:
            data = ""

        return data

    def mock_data(self):
        """
        Generate mock data for demo mode.
        """

        ix = self.exposure.image.focalplane.numcols_image
        iy = self.exposure.image.focalplane.numrows_image

        for AmpPos in range(azcam.db.tools["exposure"].image.focalplane.numamps_image):
            self.exposure.image.data[AmpPos] = numpy.linspace(
                0, 65355, int(iy * ix / self.image.focalplane.numamps_image)
            )

        return
