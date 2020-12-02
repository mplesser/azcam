"""
Script parameter handling utility.
"""

import configparser
import os
import typing

import azcam


class GenPars(object):
    """
    Main class for genpars.
    """

    def __init__(self, parfile: str = None):

        self.parfile: str = parfile
        self.par_dict: dict = {}

        # save object
        setattr(azcam.api, "genpars", self)
        setattr(azcam.db, "genpars", self)

    def parfile_read(self, parfilename: str = None) -> None:
        """
        Read a parameter file and create sub-dictionaries for saving
        parameters between sessions.

        :param str parfilename: Name of parameter file
        :return: None
        """

        if parfilename is None:
            parfilename = self.parfile
            if parfilename is None:
                raise FileNotFoundError("Parameter file is not defined")

        self.parfile = parfilename

        if not os.path.exists(parfilename):
            raise FileNotFoundError(f"Parameter file not found: {parfilename}")

        cp = configparser.ConfigParser()
        cp.read(parfilename)

        sections = cp.sections()

        # sectionname & value case sensitive, name is not
        for sectionname in sections:

            self.par_dict[sectionname] = {}

            for name, value in cp.items(sectionname):
                name = name.lower()
                self.par_dict[sectionname][name] = value

        # update current values
        azcam.utils.update_pars(0)

        return self.par_dict

    def parfile_write(self, parfilename: str = None) -> None:
        """
        Update a parameter file with current values.

        :param str parfilename: Name of parameter file
        :return: None
        """

        # update current values
        azcam.utils.update_pars(1)

        if parfilename is None:
            parfilename = self.parfile
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

    def get_par(
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
                default = par_dict.get(attribute)
        else:
            par_dict = {}

        if value == "prompt":
            if prompt_string == "":
                prompt_string = f"Enter value for {attribute}"
            value = self.prompt(prompt_string, default)
            _, value = self.get_datatype(value)
        elif value == "default":
            value = default
        else:
            pass  # value passsed is used

        par_dict[attribute] = value

        return value

    def set_par(self, par_dict, attribute, value):
        """
        Set a parameter from the par_dict database.

        :param str par_dict: Parameter dictionary
        :param str attribute: Name of attribute, used as dictionary key
        :param str value: "default" or "prompt" or a value
        :return:  None
        """

        if type(par_dict) == str:
            par_dict = self.par_dict[par_dict]

        # get value
        par_dict[attribute] = value

        return

    def get_datatype(self, value: any) -> list:
        """
        Determine the data type for an object and set the type if possible.
        A string such as "1.23" will result in a type "float" and "2" will
        result in type "int".

        :param value: object to be typed
        :return [type, value]: list of data type (as a code) and object with
        that type
        """

        if type(value) is str:

            # string integer
            if value.isdigit():
                attributetype = "int"
                value = int(value)
                return [attributetype, value]
            else:
                try:
                    value = float(value)
                    attributetype = "float"
                    return [attributetype, value]
                except ValueError:
                    pass

            attributetype = "str"

        elif type(value) is int:
            attributetype = "int"
            value = int(value)

        elif type(value) is float:
            attributetype = "float"
            value = float(value)

        # more work here
        else:
            attributetype = "str"

        return [attributetype, value]

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

        azcam.utils.update_pars(1)
        self.parfile_write()

        return
