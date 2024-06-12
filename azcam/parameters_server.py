"""
Parameter handling tool for azcamserver.
"""

import typing

import azcam
from azcam.parameters import Parameters


class ParametersServer(Parameters):
    """
    Main class for server parameters tool.
    This tool sets the default subdict to *azcamserver*.
    """

    def __init__(self):
        """
        Creates parameters tool, optionally setting default parameter dictionary name.
        """

        Parameters.__init__(self, "azcamserver")

    def _get_par_hook(self, parameter, subdict):
        """
        Return the value of a parameter for server special cases.
        """

        value = None

        if parameter == "wd":
            value = azcam.utils.curdir()
        elif parameter == "logdata":
            value = azcam.logger.get_logdata()
        elif parameter == "imagefilename":
            value = azcam.db.tools["exposure"].get_filename()
        elif parameter == "imagetitle":
            value = azcam.db.tools["exposure"].get_image_title()
            value = f'"{value}"'
        elif parameter == "exposuretime":
            value = azcam.db.tools["exposure"].get_exposuretime()
        elif parameter == "exposurecompleted":
            value = azcam.db.tools["exposure"].finished()
        elif parameter == "exposuretimeremaining":
            value = azcam.db.tools["exposure"].get_exposuretime_remaining()
        elif parameter == "pixelsremaining":
            value = azcam.db.tools["exposure"].get_pixels_remaining()
        elif parameter == "camtemp":
            value = azcam.db.tools["tempcon"].get_temperatures()[0]
        elif parameter == "dewtemp":
            value = azcam.db.tools["tempcon"].get_temperatures()[1]
        elif parameter == "temperatures":
            camtemp = azcam.db.tools["tempcon"].get_temperatures()[0]
            dewtemp = azcam.db.tools["tempcon"].get_temperatures()[1]
            value = [camtemp, dewtemp]
        elif parameter == "logcommands":
            value = azcam.db.cmdserver.logcommands
        else:
            raise AttributeError

        return value

    def _set_par_hook(self, parameter, value, subdict):
        """
        Sets the value of a parameter for server special cases.
        """

        # special cases
        if parameter == "imagefilename":
            azcam.db.tools["exposure"].image.filename = value
        elif parameter == "imagetitle":
            if value is None or value == "" or value == "None":
                azcam.db.tools["exposure"].set_image_title("")
            else:
                azcam.db.tools["exposure"].set_image_title(f"{value}")
        elif parameter == "autotitle":
            azcam.db.tools["exposure"].set_auto_title(int(value))
        elif parameter == "imagetype":
            azcam.db.tools["exposure"].image_type = value
            azcam.db.tools["exposure"].set_image_title()
        elif parameter == "exposuretime":
            azcam.db.tools["exposure"].set_exposuretime(value)
        elif parameter == "logcommands":
            azcam.db.cmdserver.logcommands = int(value)
        elif parameter == "wd":
            azcam.utils.curdir(value)
        else:
            raise AttributeError

        return None

    # TODO - below is for compatibility with azcamtool only - to be removed

    def set_script_par(self, attribute, value, subdict) -> None:
        azcam.db.parameters.par_dict[subdict][attribute] = value
        return

    def get_script_par(self, subdict, attribute) -> typing.Any:
        reply = azcam.db.parameters.par_dict[subdict][attribute]
        return reply
