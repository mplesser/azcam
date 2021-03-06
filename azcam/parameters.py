"""
Parameter handling for azcam.
"""

import configparser
import os
import typing

import azcam


class Parameters(object):
    """
    Main class for azcam parameter handling.
    """

    def __init__(self, default_dictname: str = None):

        self.par_file = None
        self.par_dict = {}

        self.default_pardict_name = default_dictname

    def read_parfile(self, parfilename: str = None) -> None:
        """
        Read a parameter file and create sub-dictionaries for saving parameters between sessions.

        Args:
            parfilename: Name of parameter file
        """

        if parfilename is None:
            parfilename = self.par_file
            if parfilename is None:
                azcam.AzcamWarning("Parameter file is not defined")
                return

        self.par_file = parfilename

        if not os.path.exists(parfilename):
            azcam.AzcamWarning(f"Parameter file not found: {parfilename}")
            return

        cp = configparser.ConfigParser()
        cp.read(parfilename)

        sections = cp.sections()

        # sectionname & value case sensitive, name is not
        for sectionname in sections:

            self.par_dict[sectionname] = {}

            for name, value in cp.items(sectionname):
                name = name.lower()
                self.par_dict[sectionname][name] = value

        return self.par_dict

    def write_parfile(self, parfilename: str = None) -> None:
        """
        Update a parameter file with current values.

        :param str parfilename: Name of parameter file
        :return: None
        """

        if parfilename is None:
            parfilename = self.par_file
            if parfilename is None:
                raise FileNotFoundError("Parameter file is not defined")

        config = configparser.ConfigParser()

        for sectionname in self.par_dict:
            for par in self.par_dict[sectionname]:
                if self.par_dict[sectionname][par] is None:
                    self.par_dict[sectionname][par] = "None"
            config[sectionname] = self.par_dict[sectionname]

        # write parfile
        with open(parfilename, "w") as configfile:
            config.write(configfile)

        return

    def get_script_par(
        self,
        par_dict: typing.Union[str, dict],
        attribute: any,
        value: any = "default",
        prompt_string: str = "",
        default: any = None,
    ):
        """
        Return a parameter from the par_dict database, or prompt as needed.
        The new value is saved in the database.

        :param str par_dict: Parameter dictionary or name of dictionary in self.par_dict
        :param str attribute: Name of attribute, used as dictionary key
        :param str value: "default" or "prompt" or a value
        :param str prompt: Prompt message
        :param str default: Default value to be used
        :return str:  parameter
        """

        if type(par_dict) == str:
            if self.par_dict is not None:
                par_dict = self.par_dict.get(par_dict)

        # check if a value exists in dictionary
        if par_dict is not None:
            if par_dict.get(attribute):
                default = par_dict.get(attribute)  # overides method default
        else:
            par_dict = {}

        if value == "prompt":
            if prompt_string == "":
                prompt_string = f"Enter value for {attribute}"
            value = azcam.utils.prompt(prompt_string, default)
            _, value = azcam.utils.get_datatype(value)
        elif value == "default":
            value = default
        else:
            pass  # value passsed is used

        par_dict[attribute] = value

        return value

    def set_script_par(self, par_dict, attribute, value):
        """
        Set a parameter from the par_dict database.

        :param str par_dict: Parameter dictionary
        :param str attribute: Name of attribute, used as dictionary key
        :param str value: "default" or "prompt" or a value
        :return:  None
        """

        if type(par_dict) == str:
            par_dict = self.par_dict.get(par_dict)
            if par_dict is None:
                par_dict = {}

        # get value
        par_dict[attribute] = value

        return

    def prompt(self, message="Enter a string", default=""):
        """
        Prints a message and waits for user input.

        :param str message: String to be printed
        :param str default:  String to be returned if no value is entered
        :return str: String entered or default
        """

        default = str(default)
        try:
            if default != "":
                in1 = input(message + " [" + default + "]: ")
            else:
                in1 = input(message + ": ")
        except KeyboardInterrupt:
            return ""

        if in1 == "":
            return default
        else:
            return in1

    def save_pars(self):
        """
        Save the current parameter set.
        """

        self.update_pars(1)
        self.write_parfile()

        return

    def get_par(self, parameter):
        """
        Return the value of a parameter in the parameters dictionary.
        Parameters valid only on server.
        Returns None on error.
        """

        parameter = parameter.lower()
        value = None

        if azcam.db.mode == "console":
            server = azcam.get_tools("server")
            try:
                reply = server.command(f"params.get_par {parameter}")
            except azcam.AzcamError:
                return
            _, value = azcam.utils.get_datatype(reply)
            return value

        exposure = azcam.get_tools("exposure")

        # special cases
        if parameter == "imagefilename":
            value = exposure.get_filename()
            return value
        elif parameter == "imagetitle":
            value = exposure.get_image_title()
            return value
        elif parameter == "exposuretime":
            value = exposure.get_exposuretime()
            return value
        elif parameter == "exposurecompleted":
            value = exposure.finished()
            return value
        elif parameter == "exposuretimeremaining":
            value = exposure.get_exposuretime_remaining()
            return value
        elif parameter == "pixelsremaining":
            value = exposure.get_pixels_remaining()
            return value
        elif parameter == "camtemp":
            value = azcam.db.tempcon.get_temperatures()[0]
            return value
        elif parameter == "dewtemp":
            value = azcam.db.tempcon.get_temperatures()[1]
            return value
        elif parameter == "temperatures":
            camtemp = azcam.db.tempcon.get_temperatures()[0]
            dewtemp = azcam.db.tempcon.get_temperatures()[1]
            return [camtemp, dewtemp]
        elif parameter == "logcommands":
            value = azcam.db.cmdserver.logcommands
            return value
        elif parameter == "wd":
            value = azcam.utils.curdir()
            return value

        # parameter must be in parameters
        try:
            attribute = azcam.db.parameters[parameter]
        except KeyError:
            azcam.AzcamWarning(f"Parameter {parameter} not available for get_par")
            return None

        tokens = attribute.split(".")
        numtokens = len(tokens)
        if numtokens == 1:
            return None

        object1 = tokens[0]

        if object1 == "db":
            value = getattr(azcam.db, tokens[1], None)
            return value

        # object must be in db
        else:
            obj = azcam.db.get(object1)
            for i in range(1, numtokens):
                try:
                    obj = getattr(obj, tokens[i])
                except AttributeError:
                    pass
            value = obj  # last time is value

        return value

    def set_par(self, parameter, value=None):
        """
        Set the value of a parameter in the parameters dictionary.
        Parameters valid only on server.
        Returns None on error.
        """

        parameter = parameter.lower()

        if azcam.db.mode == "console":
            server = azcam.get_tools("server")
            try:
                server.command(f"params.set_par {parameter} {value}")
            except azcam.AzcamError:
                return
            return value

        exposure = azcam.get_tools("exposure")

        # special cases
        if parameter == "imagefilename":
            exposure.image.filename = value
            return None
        elif parameter == "imagetitle":
            if value is None or value == "":
                exposure.set_image_title("")
            else:
                exposure.set_image_title(f"{value}")
            return None
        elif parameter == "exposuretime":
            exposure.set_exposuretime(value)
            return None
        elif parameter == "logcommands":
            azcam.db.cmdserver.logcommands = int(value)
            return None

        # parameter must be in parameters
        try:
            attribute = azcam.db.parameters[parameter]
        except KeyError:
            azcam.AzcamWarning(f"Parameter {parameter} not available for set_par")
            return None

        # object must be on db
        tokens = attribute.split(".")
        numtokens = len(tokens)
        if numtokens < 2:
            azcam.log("%s not valid for parameter %s" % (attribute, parameter))
            return None

        # first try to set value type
        _, value = azcam.utils.get_datatype(value)
        object1 = tokens[0]

        if object1 == "db":
            setattr(azcam.db, tokens[1], value)

        # run through sub-tools
        else:
            obj = azcam.db.get(object1)
            for i in range(1, numtokens - 1):
                obj = getattr(obj, tokens[i])
            # last time is actual object
            try:
                setattr(obj, tokens[-1], value)
            except AttributeError:
                pass
                # azcam.AzcamWarning(f"Could not set parameter: {parameter}")

        return None

    def update_pars(self, write, par_dictname: str = None):
        """
        Update azcam parameters to/from a config dictionary.
        write True => write values into dictionary.
        write False => set values from dictionary.
        """

        if par_dictname is None:
            par_dictname = self.default_pardict_name

        par_dict = azcam.db.params.par_dict.get(par_dictname)
        if par_dict is None:
            return
        keys = par_dict.keys()
        if keys is None:
            return

        if write:
            # run before writing parfile
            # read values into dict
            for parname in par_dict:
                if parname == "wd":
                    value = azcam.utils.curdir()
                else:
                    value = self.get_par(parname)
                if value is None:
                    value = "None"
                par_dict[parname] = value

        else:
            # after reading parfile
            # set values from dict
            for parname in par_dict:
                value = par_dict[parname]
                if parname == "wd":
                    azcam.db.wd = value
                    azcam.utils.curdir(value)

                else:
                    value = par_dict[parname]
                    self.set_par(parname, value)

        return
