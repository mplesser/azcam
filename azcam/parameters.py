"""
Parameter handling tool for azcam.
"""

import configparser
import os
import typing

import azcam
from azcam.tools import Tools


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

        # azcam.db.parameters = self

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

    def save_pars(self) -> None:
        """
        Save the current parameter set.
        """

        self.update_pars(1)
        self.write_parfile()

        return

    def update_pars(self, write, par_dictname: str = None) -> None:
        """
        Update azcam parameters to/from a config dictionary.
        write True => write values into dictionary.
        write False => set values from dictionary.
        """

        if par_dictname is None:
            par_dictname = self.default_pardict_name

        par_dict = azcam.db.parameters.par_dict.get(par_dictname)
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

        # special cases
        if parameter == "wd":
            value = azcam.utils.curdir()
            return value
        elif parameter == "logdata":
            value = azcam.logger.get_logdata()
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
        except Exception:  # new
            pass

        return None

    def get_script_par(
        self,
        par_dict_id: typing.Dict,
        attribute: typing.Any,
        value: typing.Any = "default",
        prompt_string: str = "",
        default: typing.Any = None,
    ) -> typing.Any:
        """
        Return a parameter from the par_dict database, or prompt as needed.
        The new value is saved in the database.

        :param str par_dict_id: Parameter dictionary name of in parameters.par_dict
        :param str attribute: Name of attribute, used as dictionary key
        :param str value: "default" or "prompt" or a value
        :param str prompt: Prompt message
        :param str default: Default value to be used
        :return str:  parameter
        """

        par_dict = self.par_dict.get(par_dict_id)
        if par_dict is None:
            self.par_dict[par_dict_id] = {}
            par_dict = self.par_dict[par_dict_id]

        if par_dict.get(attribute):
            default = par_dict.get(attribute)  # overides default value

        if value == "prompt":
            if prompt_string == "":
                prompt_string = f"Enter value for {attribute}"
            value = azcam.utils.prompt(prompt_string, default)
            _, value = azcam.utils.get_datatype(value)
        elif value == "default":
            value = default
        else:
            pass  # value passsed is used

        # save
        self.set_script_par(par_dict_id, attribute, value)

        return value

    def set_script_par(self, par_dict_id, attribute, value) -> None:
        """
        Set a parameter from the par_dict database.

        :param str par_dict_id: Parameter dictionary
        :param str attribute: Name of attribute, used as dictionary key
        :param str value: "default" or "prompt" or a value
        :return:  None
        """

        par_dict = self.par_dict.get(par_dict_id)
        if par_dict is None:
            self.par_dict[par_dict_id] = {}
            par_dict = self.par_dict[par_dict_id]

        # get value
        par_dict[attribute] = value

        return
