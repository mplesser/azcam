"""
Contains the ControllerArchon class.
"""

import socket
import time

import azcam
from azcam.server.controllers.controller import Controller
from azcam.sockets import SocketInterface

# Exposure states
EXP_UNKNOWN = 0
EXP_IDLE = 1
EXP_EXPOSE = 2
EXP_READY = 3
EXP_FETCH = 4
EXP_DONE = 5


class ControllerArchon(Controller):
    def __init__(self, *args):

        super().__init__(*args)

        self.id = "archon"
        self.controller_class = "archon"
        self.controller_type = "archon"

        # Azcam connected to the controller
        self.connected_controller = 0

        # Parameters
        self.parameters = {}

        self.timing_file = ""

        self.heater_board_installed = 0

        # Status keywords
        self.status_valid = 0
        self.status_count = 0
        self.status_log = 0
        self.status_power = 0
        self.status_backplane_temp = 0.0

        self.cont_exp = 0
        self.exp = 1
        self.sweep_cnt = 1
        self.exp_time_ms = 0
        self.int_ms = 0
        self.noint_ms = 0
        self.pixels = 0
        self.lines = 0

        # Response to the FRAME command
        self.frame = 0
        # FRAME data dictionary
        self.dict_frame = {}

        # Response to the STATUS command
        self.status = 0
        # STATUS data dictionary
        self.dict_status = {}

        # Config data lines read from a file or downloaded from the Archon controller - raw format 'parameter=value'
        self.config_data = []

        # Sorted Parameters section of the configuration data
        self.config_params = []

        # Config data lines counter
        self.config_lines_cnt = 0

        # Config data lines:  parameter:value pairs
        self.dict_config = {}

        # Config data lines positions: parameter_name:position pairs
        self.dict_wconfig = {}

        # Parameters positions: parameter_name:parameter_position pairs
        self.dict_params = {}

        # Taplines dictionary
        self.dict_taplines = {}

        # Config data OK flag
        self.config_ok = 0

        self.read_buffer = 0

        self.currframe1 = 0
        self.currframe2 = 0
        self.currframe3 = 0

        # Config data read from a file of from the GUI - raw format 'parameter=value'
        self.config_data = ""
        # Config data dictionary

        self.power_values = [
            "UNKNOWN",
            "NOT_CONFIGURED",
            "OFF",
            "INTERMEDIATE",
            "ON",
            "STADBY",
        ]
        self.power_status = "UNKNOWN"
        self.archon_status = 0

        self.exp_start = 0
        self.exp_timer = 0
        self.newframe = 0

        # image type
        self.img_type = 0

        self.EXP_UNKNOWN = 0
        self.EXP_IDLE = 1
        self.EXP_EXPOSE = 2
        self.EXP_READY = 3
        self.EXP_FETCH = 4
        self.EXP_DONE = 5

        # Image data received from the Archom controller in Direct Mode
        self.imagedata = 0

        self.is_reset = 0

        # video gain flag
        self.video_gain = 1

        # True to lower voltages when integrating
        self.lower_voltages = 0

        # True when controller is enabled
        self.enabled = 1

        # For timing
        self.frame_time = 0

        # not used - fix me
        self.timing_board = "arc22"
        self.clock_boards = ["arc32"]
        self.video_boards = ["arc48", "arc48"]

        self.pixels = 0
        self.lines = 0

        # set to define interface initialization state (False->closed, True->opened)
        self.initialized = False
        self.is_reset = 0

        # video gain flag
        self.video_gain = 1

        # True to lower voltages when integrating
        self.lower_voltages = 0

        # CDS parameters (taplines) - default values used just for test
        self.cds = [
            "AD12L, -3.0, 3000",
            "AD11L, 3.0, 3000",
            "AD8L, -3.0, 3000",
            "AD7L, 3.0, 3000",
            "AD6L, 3.0, 4000",
            "AD5L, -3.0, 3000",
            "AD10L, 3.0, 3000",
            "AD9L, -3.0, 3000",
            "AD4L, -3.0, 3000",
            "AD3L, 3.0, 3000",
            "AD2L, -3.0, 3000",
            "AD1L, 3.0, 3000",
            "AD16L, 3.0, 3000",
            "AD15L, -3.0, 3000",
            "AD14L, 3.0, 3000",
            "AD13L, -3.0, 3000",
        ]

        # CDS parameters read from the Archon controller
        self.rcds = []

        # CDS parameters string updated from the console
        self.ucds = ""

        # Total number of taplines
        self.tap_lines = 0

        # GSZ 05Feb2018: receiving raw data
        self.rawdata_enable = 1
        # Raw channel - in the config dictionary raw channel numbers start from 0
        self.rawdata_channel = 1
        # Raw data received from the Archom controller
        self.rawdata = 0

        # controller server
        self.camserver = SocketInterface()
        self.camserver.host = ""
        self.camserver.port = 4242
        self.camserver.cmd_id = 0x00
        self.camserver.lastcmd_id = 0x00

    def connect(self):
        """
        Connects Azcam to the controller.
        """

        if self.camserver.open():
            self.connected_controller = 1
            self.camserver.set_timeout(5)
        else:
            self.connected_controller = 0

        return

    def disconnect(self):
        """
        Disconnets Azcam from the controller.
        """

        self.camserver.close()
        self.connected_controller = 0

        return

    def reboot(self):
        """
        Send REBOOT command.
        """
        cmd = "REBOOT"
        self.archon_command(cmd)

        return

    def warmboot(self):
        """
        Send WARMBOOT command.
        """

        cmd = "WARMBOOT"
        self.archon_command(cmd)

        return

    def get_power_status(self):
        """
        Get power status: ON, OFF, NOT_CONFIGURED, UNKNOWN, INTERMEDIATE, STANDBY.
        """

        self.get_status()
        self.power_status = self.power_values[int(self.status_power)]

        return self.power_status

    def get_status_valid(self):
        """
        Get status_valid value.
        Last change: 21Dec2016 Zareba
        """

        self.get_status()

        return self.status_valid

    def get_status(self):
        """
        Get status value.
        """

        cmd = "STATUS"
        reply = self.archon_command(cmd)

        # if reply == "OK":
        retVal = reply
        self.status = retVal.split(" ")
        self.dict_status = {}

        # Create a dictionary
        for item in self.status:
            if len(item) > 0:
                line = item.split("=")
                self.dict_status[line[0]] = line[1]

        # Update staus keywords
        StatusDict = {}
        for line in self.status:
            if len(line) > 0:
                item = line.split("=")
                StatusDict[item[0]] = item[1]

        self.status_valid = int(StatusDict["VALID"])
        self.status_count = StatusDict["COUNT"]
        self.status_log = StatusDict["LOG"]
        self.status_power = StatusDict["POWER"]
        self.status_backplane_temp = StatusDict["BACKPLANE_TEMP"]

        return self.dict_status

    def get_frame(self):
        """
        Get and updates frame status value.
        """

        cmd = "FRAME"

        try:
            reply = self.archon_command(cmd)
        except socket.timeout:
            azcam.log("Socket timeout for FRAME command")
            return

        retVal = reply
        self.frame = retVal.split(" ")

        # Update frame status values

        self.dict_frame = {}

        # Create a dictionary
        for item in self.frame:
            if len(item) > 0:
                line = item.split("=")
                self.dict_frame[line[0]] = line[1]

        return self.dict_frame

    def get_size(self):
        """
        Get pixels and lines.
        """

        if self.config_ok:

            valPixels = 0
            valLines = 0

            indxParam = self.dict_wconfig[self.dict_params["Pixels"]]
            cmd = "RCONFIG%04X" % (indxParam & 0xFFFF)
            reply = self.archon_command(cmd)

            if len(reply) > 0:
                paramStr = reply.split("=")
                if len(paramStr) == 3:
                    valPixels = int(paramStr[2])
                else:
                    raise azcam.AzcamError("Parameter error")
            else:
                raise azcam.AzcamError("Parameter not found")

            indxParam = self.dict_wconfig[self.dict_params["Lines"]]
            cmd = "RCONFIG%04X" % (indxParam & 0xFFFF)
            reply = self.archon_command(cmd)

            if len(reply) > 0:
                paramStr = reply.split("=")
                if len(paramStr) == 3:
                    valLines = int(paramStr[2])
                else:
                    raise azcam.AzcamError("Parameter error")
            else:
                raise azcam.AzcamError("Parameter not found")

            return [valPixels, valLines]

        else:
            raise azcam.AzcamError("Config data not loaded")

    def set_size(self, Pixels, Lines):
        """
        Sets pixels and lines.
        """

        if len(self.dict_config) > 0:

            if self.lines != Lines:
                self.lines = Lines

                # update config dictionary
                self.dict_config[self.dict_params["Lines"]] = "Lines=%s" % (Lines)
                self.dict_config["LINECOUNT"] = Lines

                # update Archons Lines value
                indxParam = self.dict_wconfig[self.dict_params["Lines"]]
                cmd = "WCONFIG%04X%s=%s" % (
                    indxParam & 0xFFFF,
                    self.dict_params["Lines"],
                    "Lines=" + str(Lines),
                )
                self.archon_command(cmd)

                indxParam = self.dict_wconfig["LINECOUNT"]
                cmd = "WCONFIG%04X%s=%s" % (indxParam & 0xFFFF, "LINECOUNT", str(Lines))
                self.archon_command(cmd)

            if self.pixels != Pixels:
                self.pixels = Pixels

                # update config dictionary
                self.dict_config[self.dict_params["Pixels"]] = "Pixels=%s" % (Pixels)
                self.dict_config["PIXELCOUNT"] = Pixels

                # update Archons Pixels value
                indxParam = self.dict_wconfig[self.dict_params["Pixels"]]
                cmd = "WCONFIG%04X%s=%s" % (
                    indxParam & 0xFFFF,
                    self.dict_params["Pixels"],
                    "Pixels=" + str(Pixels),
                )
                self.archon_command(cmd)

                indxParam = self.dict_wconfig["PIXELCOUNT"]
                cmd = "WCONFIG%04X%s=%s" % (
                    indxParam & 0xFFFF,
                    "PIXELCOUNT",
                    str(Pixels),
                )
                self.archon_command(cmd)

            return

        else:
            raise azcam.AzcamError("Config data not loaded")

    def load_params(self):
        """
        Send LOADPARAMS command.
        """

        cmd = "LOADPARAMS"
        self.archon_command(cmd)

        return

    def upload_config(self):
        """
        Uploads configuration data to the controller.
        """

        # start the counter
        cnt = 0x0000
        prn = 0

        azcam.log("Uploading configuration data to controller", level=2)

        # clean the Write Config dictionary
        self.dict_wconfig = {}

        if len(self.config_data) == 0:
            raise azcam.AzcamError("No configuration data")

        self.poll(0)

        # CLEARCONFIG
        cmd = "CLEARCONFIG"
        self.archon_command(cmd)

        # WCONFIG values
        for line in self.config_data:
            item = line.split("=")
            if len(item) >= 2:
                cmd = "WCONFIG%04X%s=%s" % (
                    cnt & 0xFFF,
                    item[0],
                    self.dict_config[item[0]].replace('"', ""),
                )
                self.dict_wconfig[item[0]] = cnt
                self.archon_command(cmd)
                cnt += 1
                prn += 1

                if prn > 100:
                    prn = 0

        self.poll(1)

        return

    def read_config_file(self, filename):
        """
        Read Archon configuration file and parse data into dictionaries.
        """

        self.config_data = []
        self.dict_wconfig = {}

        # Get configuration data from the timing file
        f = open(self.timing_file, "r")
        fBuff = f.read()
        sBuff = fBuff.split("\n")
        fLen = len(sBuff)

        # Extract CONFIG data
        indx = 0
        copy = 0
        pos = 0

        for line in sBuff:
            if line == "[CONFIG]":
                copy = 1

            indx += 1
            if copy == 1:
                if indx < fLen and len(sBuff[indx]) > 0:
                    # azcam.log(sBuff[indx], level=3)
                    self.config_data.append(sBuff[indx].replace("\\", "/"))
                    self.dict_wconfig[self.config_data[pos].split("=")[0]] = pos
                    pos += 1

        # close config file
        f.close()
        self.config_lines_cnt = pos

        azcam.log(f"Read {self.config_lines_cnt} configuration lines", level=3)

        return

    def update_config_data(self, mode=0):
        """
        Sets configuration data:
        if mode = 0 get config data from the Archon controller, populate dictionaries.
        if mode = 1 read configuration file and then send config data to the Archon controller, populate dictionaries.
        """

        self.config_data = []
        self.dict_wconfig = {}
        self.dict_config = {}
        self.dict_params = {}
        self.dict_taplines = {}

        self.config_params = []

        self.config_lines_cnt = 0

        # get configuration data from file
        if mode == 1:
            self.read_config_file(self.timing_file)

        # get configuration data from the Archon controller
        else:
            azcam.log("Downloading configuration data from controller.", level=2)
            cnt = 0x0000
            endCfg = 0
            prn = 0

            while endCfg != 1:
                cmd = "RCONFIG%04X" % (cnt & 0xFFFF)
                reply = self.archon_command(cmd)
                cnt += 1
                prn += 1

                if prn > 100:
                    prn = 0

                if len(reply) > 0:
                    self.config_data.append(reply)
                    self.dict_wconfig[reply.split("=")[0]] = cnt - 1
                else:
                    endCfg = 1

            self.config_lines_cnt = len(self.config_data)

        # Create a config directory with parameters:value pairs
        for item in self.config_data:
            if len(item) > 0:
                if item[0] != "[":
                    indx = item.find("=")
                    if indx > 0:
                        self.dict_config[item[:indx]] = item[indx + 1 :]

        # update parameters dictionaries
        paramCnt = int(self.dict_config["PARAMETERS"])
        for param in range(0, paramCnt):
            paramStr = "PARAMETER" + str(param)
            paramName = self.dict_config[paramStr].split("=")[0].replace('"', "")
            self.config_params.append(
                self.config_data[int(self.dict_wconfig[paramStr])]
            )
            self.dict_params[paramName] = paramStr

        """
        # Swap 'Exposures' with the last parameter
        newPos = self.dict_wconfig[self.dict_params["Exposures"]] - int(
            self.dict_wconfig["PARAMETER0"]
        )

        # lastParamVal = 'PARAMETER' + str(newPos) + '=' + self.dict_config['PARAMETER' + str(paramCnt - 1)]
        if self.dict_config["PARAMETER" + str(paramCnt - 1)] == "":
            lastParamVal = (
                "PARAMETER"
                + str(newPos)
                + "="
                + self.dict_config["PARAMETER" + str(paramCnt - 2)]
            )
        else:
            lastParamVal = (
                "PARAMETER"
                + str(newPos)
                + "="
                + self.dict_config["PARAMETER" + str(paramCnt - 1)]
            )
        expParamVal = (
            "PARAMETER"
            + str(paramCnt - 1)
            + "="
            + self.dict_config[self.dict_params["Exposures"]]
        )

        self.config_params[paramCnt - 1] = expParamVal
        self.config_params[newPos] = lastParamVal
        """

        # update configuration data
        firstParam = self.dict_wconfig["PARAMETER0"]
        for paramPos in range(0, paramCnt):
            self.config_data[firstParam + paramPos] = self.config_params[paramPos]
            item = self.config_params[paramPos]
            indx = item.find("=")
            if indx > 0:
                self.dict_config[item[:indx]] = item[indx + 1 :]

        # Update number of taplines - some lines might be empty
        cnt = 0
        tapLinesCnt = int(self.dict_config["TAPLINES"])
        for param in range(0, tapLinesCnt):
            tapLine = "TAPLINE" + str(param)
            tapLineVal = self.dict_config[tapLine].split("=")[0].replace('"', "")
            if len(tapLineVal) > 0:
                cnt += 1
                self.dict_taplines[tapLine] = tapLineVal
        self.tap_lines = cnt

        # extract exposure settings
        cont_exp = (
            self.dict_config[self.dict_params["ContinuousExposures"]]
            .replace('"', "")
            .split("=")
        )
        self.cont_exp = cont_exp[1]

        Exp = (
            self.dict_config[self.dict_params["Exposures"]].replace('"', "").split("=")
        )
        self.exp = Exp[1]

        sweep_cnt = (
            self.dict_config[self.dict_params["SweepCount"]].replace('"', "").split("=")
        )
        self.sweep_cnt = sweep_cnt[1]

        IntMS = self.dict_config[self.dict_params["IntMS"]].replace('"', "").split("=")
        self.int_ms = IntMS[1]

        NoIntMS = (
            self.dict_config[self.dict_params["NoIntMS"]].replace('"', "").split("=")
        )
        self.noint_ms = NoIntMS[1]

        azcam.log("-----> ContinuousExposures = ", self.cont_exp, level=3)
        azcam.log("-----> Exposures = ", self.exp, level=3)
        azcam.log("-----> SweepCount = ", self.sweep_cnt, level=3)
        azcam.log("-----> IntMS = ", self.int_ms, level=3)
        azcam.log("-----> NoIntMS = ", self.noint_ms, level=3)

        # Config data is valid
        self.config_ok = 1

        if mode == 1:
            self.upload_config()

            # apply all config data
            self.apply_all()
            time.sleep(1)

            # set pars for exposures
            self.set_continuous_exposures(0)
            # self.set_exposures(1)

            # power on
            reply = self.get_power_status()
            if reply == "OFF" or reply == "NOT_CONFIGURED":
                self.power_on(1)
            else:
                raise azcam.AzcamError("Power status not OFF or NOT_CONFIGURED")

        azcam.log("Configuration data updated", level=2)

        return

    def power_on(self, wait=1):
        """
        Turns power on        """

        cmd = "POWERON"

        self.archon_command(cmd)

        if wait == 1:
            # check power status - wait up to 10 second

            cnt = 0
            powerOK = 0
            while cnt < 10:
                self.get_power_status()
                if self.power_status == "ON":
                    # exit
                    cnt = 10
                    powerOK = 1
                else:
                    # wait
                    cnt = cnt + 1
                    time.sleep(1)

            if powerOK == 0:
                azcam.AzcamWarning("Controller poower is OFF")
            else:
                return
        else:
            return

    def power_off(self):
        """
        Turns power off.
        """

        cmd = "POWEROFF"

        self.archon_command(cmd)

        return

    def apply_all(self):
        """
        Send APPLYALL command to the Archon controller.
        """

        cmd = "APPLYALL"

        reply = self.archon_command(cmd)

        return reply

    def update_cds(self):
        """
        Updates TAPLINES values based on self.strcds.
        """

        temp = self.ucds[1 : len(self.ucds) - 1]

        nCDS = azcam.utils.parse(temp)

        self.cds = []
        for item in nCDS:
            if len(item) > 5:
                self.cds.append(item)

        self.set_cds()
        return

    def set_cds(self):
        """
        Sets TAPLINES values.
        """

        lenCDS = len(self.cds)

        for tapLinesCnt in range(0, lenCDS):

            tapLine = "TAPLINE" + str(tapLinesCnt)
            indx = self.dict_wconfig[tapLine]
            cmd = "WCONFIG%04X%s=%s" % (indx & 0xFFFF, tapLine, self.cds[tapLinesCnt])
            self.archon_command(cmd)

        self.apply_cds()

        return

    def get_cds(self):
        """
        Get TAPLINES values and stores them in the self.rcds array.
        """

        self.rcds = []

        for tapLines in range(0, self.tap_lines):
            indxParam = self.dict_wconfig["TAPLINE" + str(tapLines)]
            cmd = "RCONFIG%04X" % (indxParam & 0xFFFF)

            reply = self.archon_command(cmd)
            respLine = reply.split("=")
            self.rcds.append(respLine[1])

        return self.rcds

    def apply_cds(self):
        """
        Send APPLYCDS command to the controller.
        CSS/Deint values are updated.
        """

        cmd = "APPLYCDS"

        reply = self.archon_command(cmd)

        return reply

    def initialize(self, load_timing_file=0):
        """
        Initializes the Archon controller: loads configuration data.
        """

        # if self.initialized:
        #    return

        # connect to controller
        self.connect()

        # load configuration file
        self.update_config_data(load_timing_file)

        # set some pars
        self.set_continuous_exposures(0)
        self.set_exposures(1)

        # check power status
        self.get_power_status()

        if self.power_status == "OFF" or self.power_status == "NOT_CONFIGURED":
            azcam.log("Power status: ", self.power_status, level=2)
            self.power_on(1)
        elif self.power_status == "ON":
            pass
        else:
            raise azcam.AzcamError("Bad power status")

        # get dewar name - not used
        """
        reply = self.get_parameter("ITLDEWAR")
        if reply is not None:
            self.dewar_number = int(reply)
        else:
            self.dewar_number = 0
        azcam.log("Controller reports dewar number %d" % self.dewar_number, level=1)
        """

        self.initialized = 1

        return

    def get_continuous_exposures(self):
        """
        Get Continuous Exposure value.
        """

        if not self.config_ok:
            raise azcam.AzcamError("Configuration data not loaded")

        indxParam = self.dict_wconfig[self.dict_params["ContinuousExposures"]]
        cmd = "RCONFIG%04X" % (indxParam & 0xFFFF)
        reply = self.archon_command(cmd)

        if len(reply) > 0:
            paramStr = reply.split("=")
            if len(paramStr) == 3:
                return int(paramStr[2])
            else:
                raise azcam.AzcamError("Parameter error")
        else:
            raise azcam.AzcamError("Parameter not found")

        return

    def set_continuous_exposures(self, cont_exp):
        """
        Sets Continuous Exposure value.
        """

        if self.cont_exp != cont_exp:

            if not self.config_ok:
                raise azcam.AzcamError("Configuration data not loaded")

            self.cont_exp = cont_exp

            # update config dictionary
            self.dict_config[
                self.dict_params["ContinuousExposures"]
            ] = "ContinuousExposures=%s" % (self.int_ms)

            # update Archons CountinuousExposures value
            indxParam = self.dict_wconfig[self.dict_params["ContinuousExposures"]]
            cmd = "WCONFIG%04X%s=%s" % (
                indxParam & 0xFFFF,
                self.dict_params["ContinuousExposures"],
                "ContinuousExposures=" + str(cont_exp),
            )
            self.archon_command(cmd)

        return

    def get_frame_number(self):
        """
        Get Frame number.
        """

        f1 = self.dict_frame["BUF1FRAME"]
        f2 = self.dict_frame["BUF2FRAME"]
        f3 = self.dict_frame["BUF3FRAME"]

        if f2 > f1:
            if f2 > f3:
                max = f2
            else:
                max = f3
        elif f1 > f3:
            max = f1
        else:
            max = f3

        return max

    def get_parameters(self):
        """
        Get parameters.
        """

        self.parameters = {}
        if len(self.dict_config) > 0:
            cnt = int(self.dict_config["PARAMETERS"])

            for indx in range(0, cnt):
                param = "PARAMETER" + str(indx)
                parname = self.dict_config[param].split("=")[0]
                parvalue = self.dict_config[param].split("=")[1]
                self.parameters[parname] = parvalue

            return self.parameters
        else:
            raise azcam.AzcamError("Configuration data error")

    def get_parameter(self, Param):
        """
        Get a parameter by name.
        Returns None if not found.
        """

        self.get_parameters()

        val = self.parameters.get(Param)

        return val

    def set_parameter(self, Param, value):
        """
        Sets parameter.
        """

        found = 0
        if len(self.dict_config) > 0:
            cnt = int(self.dict_config["PARAMETERS"])

            for indx in range(0, cnt):
                param = "PARAMETER" + str(indx)
                paramName = self.dict_config[param].split("=")[0]  # new
                if paramName == Param:
                    self.dict_config[param] = Param + "=" + str(value)
                    found = 1
                    break

            if found == 1:
                return
            else:
                raise azcam.AzcamError("Parameter not found")
        else:
            raise azcam.AzcamError("Configuration error")

    def get_exposures(self):
        """
        Get number of exposures.
        """

        if self.config_ok:
            indxParam = self.dict_wconfig[self.dict_params["Exposures"]]
            cmd = "RCONFIG%04X" % (indxParam & 0xFFFF)
            reply = self.archon_command(cmd)

            if len(reply) > 0:
                paramStr = reply.split("=")
                if len(paramStr) == 3:
                    return int(paramStr[2])
                else:
                    raise azcam.AzcamError("Parameter error")
            else:
                raise azcam.AzcamError("Parameter not found")
        else:
            raise azcam.AzcamError("Configuration data not loaded")

        return self.exp

    def set_exposures(self, Exp):
        """
        Sets number of exposures.
        """

        if self.exp != Exp:

            if not self.config_ok:
                raise azcam.AzcamError("Configuration data not loaded")

            self.exp = Exp

            # update config dictionary
            self.dict_config[self.dict_params["Exposures"]] = "Exposures=%s" % (
                self.exp
            )

            # update Archons Exposures value
            indxParam = self.dict_wconfig[self.dict_params["Exposures"]]
            cmd = "WCONFIG%04X%s=%s" % (
                indxParam & 0xFFFF,
                self.dict_params["Exposures"],
                "Exposures=" + str(Exp),
            )
            self.archon_command(cmd)

        return

    def get_archon_status(self):
        """
        Get Archon controller status: 0 = UNKNOWN, 1 = IDLE, 2 = EXPOSE, 3 = READY, 4 = FETCH, 5 = DONE.
        """

        self.get_frame()

        return self.archon_status

    def poll(self, mode):
        """
        Send POLLON or POLLOFF command.
        """

        if mode:
            cmd = "POLLON"
        else:
            cmd = "POLLOFF"

        reply = self.archon_command(cmd)

        return reply

    def bias_poll(self, mode):
        """
        Send BIASPOLLON or BIASPOLLOFF command.
        """

        if mode:
            cmd = "BIASPOLLON"
        else:
            cmd = "BIASPOLLOFF"

        reply = self.archon_command(cmd)

        return reply

    def get_exposuretime(self):
        """
        Get exposure time from the controller.
        """

        if not self.config_ok:
            raise azcam.AzcamError("Configuration data not loaded")

        indxParam = self.dict_wconfig[self.dict_params["IntMS"]]
        cmd = "RCONFIG%04X" % (indxParam & 0xFFFF)
        reply = self.archon_command(cmd)

        if len(reply) > 0:
            paramStr = reply.split("=")
            if len(paramStr) == 3:
                et = int(paramStr[2]) / 1000.0
                return et
            else:
                raise azcam.AzcamError("IntMS parameter error")
        else:
            raise azcam.AzcamError("IntMS parameter not found")

        return

    def set_exposuretime(self, ExpTimeMS):
        """
        Set exposure time variable (millisecs).
        This is used for exposure count down.
        """

        if not self.config_ok:
            raise azcam.AzcamError("Configuration data not loaded")

        self.exp_time_ms = ExpTimeMS
        self.int_ms = ExpTimeMS

        # update config dictionary
        self.dict_config[self.dict_params["IntMS"]] = "IntMS=%s" % (self.int_ms)

        # update Archons IntMS value
        indxParam = self.dict_wconfig[self.dict_params["IntMS"]]
        cmd = "WCONFIG%04X%s=%s" % (
            indxParam & 0xFFFF,
            self.dict_params["IntMS"],
            "IntMS=" + str(ExpTimeMS),
        )
        self.archon_command(cmd)

        return

    def get_int_ms(self):
        """
        Get IntMS value. The value should be the same as the Archons IntMS.
        """

        if not self.config_ok:
            raise azcam.AzcamError("Configuration data not loaded")

        indxParam = self.dict_wconfig[self.dict_params["IntMS"]]
        cmd = "RCONFIG%04X" % (indxParam & 0xFFFF)
        reply = self.archon_command(cmd)

        if len(reply) > 0:
            paramStr = reply.split("=")
            if len(paramStr) == 3:
                return int(paramStr[2])
            else:
                raise azcam.AzcamError("Parameter error")
        else:
            raise azcam.AzcamError("Parameter not found")

        return

    def set_int_ms(self, IntMS):
        """
        Set IntMS value.
        """

        if not self.config_ok:
            raise azcam.AzcamError("Configuration data not loaded")

        self.exp_time_ms = IntMS
        self.int_ms = IntMS

        # special for long exposure times - IN PROGRESS
        ms = IntMS
        mul = 1
        IntMul = mul
        tmax = (1 << 20) - 2  # Archon parameter word length tmax=1048574
        if ms > tmax:
            mul = (ms - 1) / tmax + 1  # makes mul > 0
            ms = ms / mul
            IntMS = int(ms)
            IntMul = int(mul)

        # update config dictionary
        self.dict_config[self.dict_params["IntMS"]] = "IntMS=%s" % (IntMS)
        self.dict_config[self.dict_params["IntMul"]] = "IntMul=%s" % (IntMul)

        # update Archons IntMS value
        indxParam = self.dict_wconfig[self.dict_params["IntMS"]]
        cmd = "WCONFIG%04X%s=%s" % (
            indxParam & 0xFFFF,
            self.dict_params["IntMS"],
            "IntMS=" + str(IntMS),
        )
        self.archon_command(cmd)

        # update Archons IntMul value
        indxParam = self.dict_wconfig[self.dict_params["IntMul"]]
        cmd = "WCONFIG%04X%s=%s" % (
            indxParam & 0xFFFF,
            self.dict_params["IntMul"],
            "IntMul=" + str(IntMul),
        )
        self.archon_command(cmd)

        return

    def set_pocket_pumping(self, flag):
        """
        Set Parallel pocket pumping flag.
        """

        if not self.config_ok:
            raise azcam.AzcamError("Configuration data not loaded")

        # update config dictionary
        self.dict_config[self.dict_params["ParallelPumping"]] = "ParallelPumping=%s" % (
            str(flag)
        )

        # update Archons IntMS value
        indxParam = self.dict_wconfig[self.dict_params["ParallelPumping"]]
        cmd = "WCONFIG%04X%s=%s" % (
            indxParam & 0xFFFF,
            self.dict_params["ParallelPumping"],
            "ParallelPumping=" + str(flag),
        )
        self.archon_command(cmd)

        return

    def get_no_int_ms(self):
        """
        Get NoIntMS value. The value should be the same as the Archons NoIntMS.
        """

        if not self.config_ok:
            raise azcam.AzcamError("Configuration data not loaded")

        indxParam = self.dict_wconfig[self.dict_params["NoIntMS"]]
        cmd = "RCONFIG%04X" % (indxParam & 0xFFFF)
        reply = self.archon_command(cmd)

        if len(reply) > 0:
            paramStr = reply.split("=")
            if len(paramStr) == 3:
                return int(paramStr[2])
            else:
                raise azcam.AzcamError("Parameter error")
        else:
            raise azcam.AzcamError("Paramter not found")

        return

    def set_no_int_ms(self, NoIntMS):
        """
        Set NoIntMS value.
        """

        if not self.config_ok:
            raise azcam.AzcamError("Configuration data not loaded")

        self.noint_ms = NoIntMS

        # special for long exposure times - IN PROGRESS
        ms = NoIntMS
        mul = 1
        NoIntMul = mul
        tmax = (1 << 20) - 2  # Archon parameter word length tmax=1048574
        if ms > tmax:
            mul = (ms - 1) / tmax + 1  # makes mul > 0
            ms = ms / mul
            NoIntMS = int(ms)
            NoIntMul = int(mul)

        # update config dictionary
        self.dict_config[self.dict_params["NoIntMS"]] = "NoIntMS=%s" % (NoIntMS)
        self.dict_config[self.dict_params["NoIntMul"]] = "NoIntMul=%s" % (NoIntMul)

        # update Archons NoIntMS value
        indxParam = self.dict_wconfig[self.dict_params["NoIntMS"]]
        cmd = "WCONFIG%04X%s=%s" % (
            indxParam & 0xFFFF,
            self.dict_params["NoIntMS"],
            "NoIntMS=" + str(NoIntMS),
        )
        self.archon_command(cmd)

        indxParam = self.dict_wconfig[self.dict_params["NoIntMul"]]
        cmd = "WCONFIG%04X%s=%s" % (
            indxParam & 0xFFFF,
            self.dict_params["NoIntMul"],
            "NoIntMul=" + str(NoIntMul),
        )
        self.archon_command(cmd)

        return

    def get_raw_enable(self):
        """
        Get RAWENABLE value.
        """

        if not self.config_ok:
            raise azcam.AzcamError("Configuration data not loaded")

        indxParam = self.dict_wconfig["RAWENABLE"]
        cmd = "RCONFIG%04X" % (indxParam & 0xFFFF)
        reply = self.archon_command(cmd)

        if len(reply) > 0:
            paramStr = reply.split("=")
            if len(paramStr) == 2:
                self.rawdata_enable = int(paramStr[1])
                return int(paramStr[1])
            else:
                raise azcam.AzcamError("Parameter error")
        else:
            raise azcam.AzcamError("Parameter not found")

    def set_raw_enable(self, RawEnable):
        """
        Set RAWENABLE value.
        """

        if not self.config_ok:
            raise azcam.AzcamError("Configuration data not loaded")

        self.rawdata_enable = RawEnable

        # update config dictionary
        self.dict_config["RAWENABLE"] = "%s" % (self.rawdata_enable)

        # update Archons RAWENABLE value
        indxParam = self.dict_wconfig["RAWENABLE"]
        cmd = "WCONFIG%04X%s=%s" % (
            indxParam & 0xFFFF,
            "RAWENABLE",
            str(self.rawdata_enable),
        )
        self.archon_command(cmd)
        self.apply_cds()

        return

    def get_raw_channel(self):
        """
        Get RAWSEL value (raw channel selection).
        """

        if not self.config_ok:
            raise azcam.AzcamError("Configuration data not loaded")

        indxParam = self.dict_wconfig["RAWSEL"]
        cmd = "RCONFIG%04X" % (indxParam & 0xFFFF)
        reply = self.archon_command(cmd)

        if len(reply) > 0:
            paramStr = reply.split("=")
            if len(paramStr) == 2:
                return int(paramStr[1]) + 1
            else:
                raise azcam.AzcamError("Parameter error")
        else:
            raise azcam.AzcamError("Parameter not found")

        return

    def set_raw_channel(self, RawChannel):
        """
        Sets RAWSEL value  (raw channel selection).
        RAWSEL starts from 0.
        """

        if not self.config_ok:
            raise azcam.AzcamError("Configuration data not loaded")

        self.rawdata_channel = RawChannel

        # update config dictionary
        self.dict_config["RAWSEL"] = "%s" % (self.rawdata_channel - 1)

        # update Archons RAWENABLE value
        indxParam = self.dict_wconfig["RAWSEL"]
        cmd = "WCONFIG%04X%s=%s" % (
            indxParam & 0xFFFF,
            "RAWSEL",
            str(self.rawdata_channel - 1),
        )
        self.archon_command(cmd)
        self.apply_cds()

        return

    def get_pixels_remaining(self):
        """
        Return number of remaining pixels to be read (counts down).
        """

        if self.dict_frame == {} or self.read_buffer == 0:
            return 0

        fp = azcam.db.objects["exposure"].get_focalplane()
        numseramps = fp[2]
        numamps = fp[0] * fp[1] * fp[2] * fp[3]
        naxis1 = int(self.dict_frame[f"BUF{self.read_buffer}WIDTH"])
        naxis2 = int(self.dict_frame[f"BUF{self.read_buffer}HEIGHT"])
        numpixelsline = naxis1 / numseramps
        total_pixels = naxis1 * naxis2

        pixels = int(self.dict_frame[f"BUF{self.read_buffer}PIXELS"])
        lines = int(self.dict_frame[f"BUF{self.read_buffer}LINES"])
        pixels_read = (lines * numpixelsline + pixels) * numamps

        pixels_remaining = max(0, int(total_pixels - pixels_read))

        return pixels_remaining

    def update_exposuretime_remaining(self):
        """
        Returns exposure time remaining in seconds.
        Last change: 13Jan2017 Zareba
        """

        dt = int(self.dict_frame["TIMER"], 16) - self.exp_timer
        et = self.int_ms / 1000.0 + self.noint_ms / 1000.0 - dt / 100000000.0

        if et < 0:
            et = 0

        return et

    def command(self, CommStr):
        """
        Send arbitrary command to the controller. CommStr = Command + Params.
        Last change: 21Dec2016 Zareba
        """

        reply = self.archon_command(CommStr)

        return reply

    def reset(self, mode=-1):
        """
        Resets controller.
        mode = 0 -> soft reset (timing file not loaded)
        mode = 1 -> full reset (load timing file)
        mode = -1 -> use default mode for system
        """

        if mode == -1:
            mode = self.reset_flag

        self.is_reset = 0

        # initialize controller
        self.initialize(mode)

        self.is_reset = 1

        return

    def reset_controller(self):
        """
        Resets controller.
        Send REBOOT command + loads config file + sets Power ON.
        """

        # Connect to controller
        self.connect()

        self.warmboot()

        # Wait at least 3 sec before trying to send any command to the controller
        time.sleep(5)

        # Wait up to 30 sec for the controller to finish the boot sequence
        cnt = 0

        while cnt < 30:
            time.sleep(1)
            self.get_status()
            if self.status_valid == 1:
                cnt = 30
            else:
                cnt += 1

        if self.status_valid != 1:
            raise azcam.AzcamError("Controller reboot error")

        # connect to controller
        self.connect()

        # load configuration file
        self.update_config_data(1)

        # apply all config data
        self.apply_all()
        time.sleep(1)

        # set some pars
        self.set_continuous_exposures(0)
        self.set_exposures(1)

        # check power status
        reply = self.get_power_status()

        if reply == "OFF" or reply == "NOT_CONFIGURED":
            self.power_on(1)
        else:
            raise azcam.AzcamError("Bad controller power status")

        return

    def start_exposure(self, wait=1):
        """
        Start exposure - image type should be specified using set_image_type method
        """

        # direct mode
        # 1. Get FRAME
        # 2. LOADPARAMS -> this should start the exposure
        # 3. Loop: FRAME
        # 4. FETCH frame

        # Set exposure state to UNKNOWN
        self.archon_status = self.EXP_UNKNOWN

        # important especially for first exposure
        self.archon_command("RESETTIMING")

        # Check frame status
        self.get_frame()

        # Save current frame numbers
        self.currframe1 = self.dict_frame["BUF1FRAME"]
        self.currframe2 = self.dict_frame["BUF2FRAME"]
        self.currframe3 = self.dict_frame["BUF3FRAME"]

        # Start exposure -> send LOADPARAMS command for single exposure mode
        cmd = "LOADPARAMS"
        self.archon_command(cmd)
        self.frame_time = time.time()

        # Exposure start time -> used to determine time out
        self.exp_start = time.time()

        # Exposure start time (internal Archon controller timer - resolution 10 ns)
        self.get_frame()
        self.exp_timer = int(self.dict_frame["TIMER"], 16)

        int_time = (int(self.int_ms) + int(self.noint_ms)) / 1000

        # if no wait, just set status and exit
        if wait == 0:
            self.archon_status = EXP_EXPOSE
            return

        # frame number changes when integration is over
        stop = 0
        self.newframe = 0

        # Set exposure flag to INTEGRATING
        azcam.db.objects["exposure"].exposure_flag = azcam.db.exposureflags[
            "EXPOSING"
        ]

        # wait for frame to change in buffers
        azcam.log("Integrating", level=1)
        while stop == 0:

            # Get frame and update frame dictionary
            self.get_frame()

            # Check in a new frame is available
            if self.currframe1 != self.dict_frame["BUF1FRAME"]:
                self.newframe = 1
                stop = 1

            if self.currframe2 != self.dict_frame["BUF2FRAME"]:
                self.newframe = 2
                stop = 1

            if self.currframe3 != self.dict_frame["BUF3FRAME"]:
                self.newframe = 3
                stop = 1

            if int_time > 0:
                pass
                # azcam.log(f"Integrating: {(time.time() - self.exp_start):.1f} secs", level=2)

            # check for abort
            if (
                azcam.db.objects["exposure"].exposure_flag
                == azcam.db.exposureflags["ABORT"]
            ):
                stop = 1

            # Check if time out occured
            if not stop:
                if 0:  # 0 is no timeout
                    if time.time() > (self.frame_time + int_time + 90):  # long for 10k
                        self.newframe = -1
                        self.read_buffer = -1
                        azcam.AzcamWarning("Timed out waiting for integration")
                        stop = 1
                time.sleep(0.5)

        # check for abort
        if (
            azcam.db.objects["exposure"].exposure_flag
            == azcam.db.exposureflags["ABORT"]
        ):
            self.archon_status = EXP_DONE
            azcam.AzcamWarning("Exposure aborted")
            return

        # Set exposure flag to READOUT
        azcam.db.objects["exposure"].exposure_flag = azcam.db.exposureflags["READOUT"]

        self.read_buffer = self.newframe

        # Wait for readout to complete
        azcam.log("Reading", level=1)
        if self.newframe == 0:
            self.archon_status = EXP_UNKNOWN
            raise azcam.AzcamError("New frame is not ready")

        self.read_time = time.time()
        frameStatus = "BUF%dCOMPLETE" % (self.read_buffer)
        dataReady = 0
        cnt = 0

        while dataReady == 0 and cnt < 500:

            # Get frame and update frame dictionary
            time.sleep(0.50)
            self.get_frame()

            # Check if frame is ready
            ready = self.dict_frame[frameStatus]
            if int(ready) == 1:
                dataReady = 1
            else:
                cnt += 1

            if 1:
                azcam.log(
                    f"Reading: {(time.time() - self.read_time):.1f} secs", level=2
                )

            # check for abort
            if (
                azcam.db.objects["exposure"].exposure_flag
                == azcam.db.exposureflags["ABORT"]
            ):
                dataReady = -1
                break

        # record actual exposure time - archon time stamp valid for INT only
        et = 0
        if self.int_ms > 0:
            t1 = int(self.dict_frame[f"BUF{self.read_buffer}RETIMESTAMP"], 16)
            t2 = int(self.dict_frame[f"BUF{self.read_buffer}FETIMESTAMP"], 16)
            et = (t2 - t1) / 1.0e8
        elif self.noint_ms > 0:
            et = self.noint_ms / 1000.0
        azcam.db.objects["exposure"].exposure_time_actual = et

        if dataReady == 1:
            self.archon_status = EXP_DONE
            return
        elif dataReady == -1:
            self.archon_status = EXP_DONE
            azcam.AzcamWarning("Exposure aborted")
        else:
            raise azcam.AzcamError("New frame data is not ready")

        return

    def download_config(self):
        """
        Downloads config data from the Archon controller.
        """

        cnt = 0x0000

        self.ConfigArchon = []

        endCfg = 0

        while endCfg != 1:
            cmd = "RCONFIG%04X" % (cnt & 0xFFFF)
            reply = self.archon_command(cmd)
            cnt = cnt + 1
            if len(reply) > 0:
                self.ConfigArchon.append(reply[1])
            else:
                endCfg = 1

        self.ConfigArchonCnt = len(self.ConfigArchon)

        return

    def archon_command(self, Command):
        """
        Send a command to the Archon controller.
        """

        if not self.camserver.open():
            raise azcam.AzcamError("Could not open connection to controller")

        self.camserver.lastcmd_id = self.camserver.cmd_id
        self.camserver.cmd_id = (self.camserver.cmd_id + 1) & 0xFF
        preCmd = ">%02X" % (self.camserver.cmd_id)
        preResp = "<%02X" % (self.camserver.cmd_id)
        cmd = preCmd + Command

        self.camserver.send(cmd, "\r\n")

        if Command != "WARMBOOT" and Command != "REBOOT":
            reply = self.camserver.recv(-1)
            status = reply.split(" ")[0]

            # check if the reply is synchronized
            if status[0:3] == preResp:
                return reply[3:]
            else:
                if reply[0] == "?":
                    raise azcam.AzcamError("Archon response not valid")
                else:
                    raise azcam.AzcamError("Archon response out of sync")

        else:
            return None  # no Archon reponse is OK

    def archon_bin_command(self, command):
        """
        Send binary command to the Archon controller.
        """

        self.camserver.lastcmd_id = self.camserver.cmd_id
        self.camserver.cmd_id = (self.camserver.cmd_id + 1) & 0xFF

        preCmd = ">%02X" % (self.camserver.cmd_id)
        cmd = preCmd + command

        self.camserver.send(cmd, "\r\n")

        return

    def flush(self, cycles=1):
        """
        Flush or clear out the detector.
        Returns after clearing is finished which could take many seconds.
        """

        # not supported

        return
