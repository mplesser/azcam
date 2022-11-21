"""
Parameter handling tool for azcam.
"""

import configparser
import os
import typing

import azcam
from azcam.tools.tools import Tools


class Parameters(Tools):
    """
    Main class for parameters tool.
    """

    def __init__(self, default_dictname: str = None):
        """
        Creates parameters tool, optionally setting default parameter dictionary name.
        """

        Tools.__init__(self, "parameters", "parameters tool")

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

        return

    def write_parfile(self, parfilename: str = None) -> None:
        """
        Update a parameter file with current values.

        Args:
            parfilename (str, optional): Name of parameter file. Defaults to None.
                None indicates use self.par_file

        Raises:
            FileNotFoundError: if parfilename not found
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
        attribute: typing.Any,
        value: typing.Any = "default",
        prompt_string: str = "",
        default: typing.Any = None,
    ) -> typing.Any:
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

    def set_script_par(self, attribute, value, par_dict) -> None:
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

    def prompt(self, message="Enter a string", default="") -> str:
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

    def save_pars(self) -> None:
        """
        Save the current parameter set.
        """

        self.update_pars(1)
        self.write_parfile()

        return

    def get_par(self, parameter: str) -> typing.Any:
        """
        Return the value of a parameter in the parameters dictionary.


        Args:
            parameter (str): name of the parameter

        Returns:
            value (Any): value of the parameter
        """

        parameter = parameter.lower()
        value = None

        if azcam.db.mode == "console":
            try:
                reply = azcam.db.tools["server"].command(f"parameters.get_par {parameter}")
            except azcam.AzcamError:
                return
            _, value = azcam.utils.get_datatype(reply)
            return value

        # special cases
        if parameter == "imagefilename":
            value = azcam.db.tools["exposure"].get_filename()
            return value
        elif parameter == "imagetitle":
            value = azcam.db.tools["exposure"].get_image_title()
            return value
        elif parameter == "exposuretime":
            value = azcam.db.tools["exposure"].get_exposuretime()
            return value
        elif parameter == "exposurecompleted":
            value = azcam.db.tools["exposure"].finished()
            return value
        elif parameter == "exposuretimeremaining":
            value = azcam.db.tools["exposure"].get_exposuretime_remaining()
            return value
        elif parameter == "pixelsremaining":
            value = azcam.db.tools["exposure"].get_pixels_remaining()
            return value
        elif parameter == "camtemp":
            value = azcam.db.tools["tempcon"].get_temperatures()[0]
            return value
        elif parameter == "dewtemp":
            value = azcam.db.tools["tempcon"].get_temperatures()[1]
            return value
        elif parameter == "temperatures":
            camtemp = azcam.db.tools["tempcon"].get_temperatures()[0]
            dewtemp = azcam.db.tools["tempcon"].get_temperatures()[1]
            return [camtemp, dewtemp]
        elif parameter == "logcommands":
            value = azcam.db.tools["cmdserver"].logcommands
            return value
        elif parameter == "wd":
            value = azcam.utils.curdir()
            return value
        elif parameter == "logdata":
            value = azcam.db.logger.get_logdata()
            return value

        # parameter must be in parameters
        try:
            attribute = azcam.db.pardict[parameter]
        except KeyError:
            azcam.AzcamWarning(f"Parameter {parameter} not available for get_par")
            return None

        tokens = attribute.split(".")
        numtokens = len(tokens)

        # a tool and attribute is required
        if numtokens == 1:
            return None

        object1 = tokens[0]

        # object1 must be a tool
        try:
            obj = azcam.db.tools[object1]
            for i in range(1, numtokens):
                try:
                    obj = getattr(obj, tokens[i])
                except AttributeError:
                    pass
            value = obj  # last time is value
        except KeyError:
            value = None

        return value

    def set_par(self, parameter: str, value: typing.Any = None) -> None:
        """
        Set the value of a parameter in the parameters dictionary.

        Args:
            parameter (str): name of the parameter
            value (Any): value of the parameter. Defaults to None.
        Returns:
            None
        """

        parameter = parameter.lower()

        if azcam.db.mode == "console":
            try:
                azcam.db.tools["server"].command(f"parameters.set_par {parameter} {value}")
            except azcam.AzcamError:
                return
            return None

        # special cases
        if parameter == "imagefilename":
            azcam.db.tools["exposure"].image.filename = value
            return None
        elif parameter == "imagetitle":
            if value is None or value == "" or value == "None":
                azcam.db.tools["exposure"].set_image_title("")
            else:
                azcam.db.tools["exposure"].set_image_title(f"{value}")
            return None
        elif parameter == "exposuretime":
            azcam.db.tools["exposure"].set_exposuretime(value)
            return None
        elif parameter == "logcommands":
            azcam.db.tools["cmdserver"].logcommands = int(value)
            return None

        # parameter must be in parameters
        try:
            attribute = azcam.db.pardict[parameter]
        except KeyError:
            azcam.AzcamWarning(f"Parameter {parameter} not available for set_par")
            return None

        # object must be a tool
        tokens = attribute.split(".")
        numtokens = len(tokens)
        if numtokens < 2:
            azcam.log("%s not valid for parameter %s" % (attribute, parameter))
            return None

        # first try to set value type
        _, value = azcam.utils.get_datatype(value)
        object1 = tokens[0]

        # run through tools
        try:
            obj = azcam.db.tools[object1]
            for i in range(1, numtokens - 1):
                obj = getattr(obj, tokens[i])
            # last time is actual object
            try:
                setattr(obj, tokens[-1], value)
            except AttributeError:
                pass
                # azcam.AzcamWarning(f"Could not set parameter: {parameter}")
        except KeyError:
            pass

        return None

    def update_pars(self, write, par_dictname: str = None) -> None:
        """
        Update azcam parameters to/from a config dictionary.
        write True => write values into dictionary.
        write False => set values from dictionary.
        """

        if par_dictname is None:
            par_dictname = self.default_pardict_name

        par_dict = azcam.db.tools["parameters"].par_dict.get(par_dictname)
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
