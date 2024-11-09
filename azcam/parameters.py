"""
Parameter handling tool for azcam.

There is one main paramater dictionary with multiple subdicts. A default subdict can be specified.  
"""

import configparser
import os
import typing

import azcam
import azcam.utils
import azcam.exceptions


class Parameters(object):
    """
    Main class for parameters tool.
    """

    def __init__(self, default_dictname: str = None):
        """
        Creates parameters tool, optionally setting default parameter dictionary name.
        """

        self.par_file = None
        self.par_dict = {}

        self.default_pardict_name = default_dictname

        azcam.db.cli["parameters"] = self

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
                azcam.exceptions.warning("Parameter file is not defined")
                return

        self.par_file = parfilename

        if not os.path.exists(parfilename):
            azcam.exceptions.warning(f"Parameter file not found: {parfilename}")
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

    def write_parfile(self, parfilename: str | None = None) -> None:
        """
        Writes par_dict to the par file.
        Does not update any values.

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
        Writes the par_dict to the par_file using current values.
        """

        self.update_par_dict()
        self.write_parfile()

        return

    def update_pars(self) -> None:
        """
        Set current attributes from default par_dict values.
        """

        par_dictname = self.default_pardict_name

        par_dict = azcam.db.parameters.par_dict.get(par_dictname)
        if par_dict is None:
            return
        keys = par_dict.keys()
        if keys is None:
            return

        for parname in par_dict:
            value = par_dict[parname]
            if parname == "wd":
                azcam.db.wd = value
                azcam.utils.curdir(value)
            else:
                value = par_dict[parname]
                self.set_par(parname, value)

        return

    def update_par_dict(self) -> None:
        """
        Set par_dict values in default par_dict from current attributes.
        """

        par_dictname = self.default_pardict_name

        par_dict = azcam.db.parameters.par_dict.get(par_dictname)
        if par_dict is None:
            return
        keys = par_dict.keys()
        if keys is None:
            return

        for parname in par_dict:
            if parname == "wd":
                value = azcam.utils.curdir()
            else:
                value = self.get_par(parname)
            if value is None:
                value = "None"
            par_dict[parname] = value

        return

    def get_par(self, parameter: str, subdict=None) -> typing.Any:
        """
        Return the current attribute value of a parameter in the parameters dictionary.
        If subdict is not specified then the default subdict is used.

        Args:
            parameter: name of the parameter
            subdict: name of the subdict containing the parameter

        Returns:
            value: value of the parameter
        """

        parameter = parameter.lower()
        value = None

        if subdict is None:
            subdict = self.default_pardict_name

        # special cases hook
        try:
            value = self._get_par_hook(parameter, subdict)
            return value
        except NameError:  # OK if hook is not defined
            pass
        except AttributeError:  # OK if parameter not in hook
            pass

        # check if parameter is in par_table
        try:
            attribute = azcam.db.par_table[parameter]
            tokens = attribute.split(".")
            numtokens = len(tokens)

            # a tool and attribute is required
            if numtokens == 1:
                return None

            object1 = tokens[0]

            # object1 must be a tool or the database
            if object1 == "db":
                obj = azcam.db
            else:
                obj = azcam.db.tools[object1]
            for i in range(1, numtokens):
                try:
                    obj = getattr(obj, tokens[i])
                except AttributeError:
                    pass
            value = obj  # last time is value

        except KeyError:
            # check if value is known directly
            try:
                value = azcam.db.parameters.par_dict[subdict][parameter]
            except KeyError:
                azcam.exceptions.warning(
                    f"Parameter {parameter} not available for get_par"
                )
                return None

        return value

    def set_par(self, parameter: str, value: typing.Any = "None", subdict=None) -> None:
        """
        Set the value of a parameter in a parameters dictionary.
        Also attempts to set actual attribute value.

        Args:
            parameter: name of the parameter
            value: value of the parameter. Defaults to None.
            subdict: subdict in which to set paramater
        """

        parameter = azcam.utils.dequote(parameter)
        parameter = parameter.lower()

        if subdict is None:
            subdict = self.default_pardict_name

        # special cases hook
        try:
            self._set_par_hook(parameter, value, subdict)
            return None
        except NameError:  # OK if hook is not defined
            pass
        except AttributeError:  # OK if parameter not in hook
            pass

        # check if parameter is in par_table
        try:
            attribute = azcam.db.par_table[parameter]

            # object must be a tool
            tokens = attribute.split(".")
            numtokens = len(tokens)
            if numtokens < 2:
                azcam.log("%s not valid for parameter %s" % (attribute, parameter))
                return None

        except KeyError:
            _, value = azcam.utils.get_datatype(value)

            try:
                azcam.db.parameters.par_dict[subdict][parameter] = value
            except KeyError:
                if azcam.db.parameters.par_dict.get(subdict) is None:
                    azcam.db.parameters.par_dict[subdict] = {}
                azcam.db.parameters.par_dict[subdict][parameter] = value
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
        except KeyError:
            pass
        except Exception:  # new
            pass

        return None

    def _get_par_hook(self, parameter, subdict):
        """
        Return the value of a parameter for special cases.
        """

        value = None

        return value

    def _set_par_hook(self, parameter, value, subdict):
        """
        Sets the value of a parameter for special cases.
        """

        return None
