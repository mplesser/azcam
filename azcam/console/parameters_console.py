"""
# parameters_console.py

Parameter handling tool for azcam-console.
"""

import typing

import azcam
import azcam.utils
from azcam.parameters import Parameters


class ParametersConsole(Parameters):
    """
    Main class for parameters tool.
    """

    def __init__(self, default_dictname: str = "azcamconsole"):
        """
        Creates parameters tool, optionally setting default parameter dictionary name.

        Args:
            default_dictname: parameter dict to be used when unspecified
        """

        Parameters.__init__(self, "azcamconsole")

    def get_par(self, parameter: str) -> typing.Any:
        """
        Return the value of a parameter in the parameters dictionary.

        Args:
            parameter: name of the parameter

        Returns:
            value: value of the parameter
        """

        parameter = parameter.lower()
        value = None

        try:
            reply = azcam.db.tools["server"].command(f"parameters.get_par {parameter}")
        except azcam.AzcamError:
            return
        _, value = azcam.utils.get_datatype(reply)
        return value

    def set_par(self, parameter: str, value: typing.Any = None) -> None:
        """
        Set the value of a parameter in the parameters dictionary.

        Args:
            parameter: name of the parameter
            value: value of the parameter.
        Returns:
            None
        """

        parameter = parameter.lower()

        try:
            azcam.db.tools["server"].command(f"parameters.set_par {parameter} {value}")
        except azcam.AzcamError:
            return
        return None

    def _get_par_hook(self, parameter, subdict):
        """
        Return the value of a parameter for console special cases.
        """

        value = None

        return value

    def _set_par_hook(self, parameter, value, subdict):
        """
        Sets the value of a parameter for console special cases.
        """

        return None

    def get_local_par(
        self,
        par_dict_id: dict,
        attribute: typing.Any,
        value: typing.Any = "default",
        prompt_string: str = "",
        default: typing.Any = None,
    ) -> typing.Any:
        """
        Return a parameter from a par_dict database, or prompt as needed.
        The new value is saved in the database.

        Args:
            par_dict_id: Parameter dictionary name in par_dict
            attribute: Name of attribute, used as dictionary key
            value: "default" or "prompt" or a value
            prompt: Prompt message
            default: Default value to be used
        Returns:
            parameter
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
        self.set_local_par(par_dict_id, attribute, value)

        return value

    def set_local_par(
        self, par_dict_id: str, attribute: str, value: typing.Any
    ) -> None:
        """
        Set a parameter in a par_dict database.

        Args:
            par_dict_id: Parameter dictionary name in par_dict
            attribute: Name of attribute, used as dictionary key
            value: "default" or "prompt" or a value
        Returns:
            None
        """

        par_dict = self.par_dict.get(par_dict_id)
        if par_dict is None:
            self.par_dict[par_dict_id] = {}
            par_dict = self.par_dict[par_dict_id]

        # get value
        par_dict[attribute] = value

        return
