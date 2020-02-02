"""
Script paramater utility.
"""

import azcam


def get_parfile_par(caller, attribute, value="default", prompt_string="", default=None):
    """
    Return a parameter from the parfile_dict database, or prompt as needed.
    The new value is saved in the database.

    :param str caller: Name of caller, used as dictionary name
    :param str attribute: Name of attribute, used as dictionary key
    :param str value: "default" or "prompt" or a value
    :param str prompt: Prompt message
    :param str default: Default value to be used
    :return str:  parameter
    """

    # check if dictionary for caller does not exist
    if not azcam.db.parfile_dict.get(caller):
        azcam.db.parfile_dict[caller] = {}

    # check if a value exists in dictionary
    if azcam.db.parfile_dict[caller].get(attribute):
        default = azcam.db.parfile_dict[caller].get(attribute)

    if value == "prompt":
        if prompt_string == "":
            prompt_string = f"Enter value for {attribute}"
        value = azcam.utils.prompt(prompt_string, default)
        _, value = azcam.utils.get_datatype(value)
    elif value == "default":
        value = default
    else:
        pass  # value passsed is used

    azcam.db.parfile_dict[caller][attribute] = value

    return value


def set_parfile_par(caller, attribute, value):
    """
    Set a parameter from the parfile_dict database.

    :param str caller: Name of caller, used as dictionary name
    :param str attribute: Name of attribute, used as dictionary key
    :param str value: "default" or "prompt" or a value
    :return:  None
    """

    # check if dictionary for caller does not exist
    if not azcam.db.parfile_dict.get(caller):
        azcam.db.parfile_dict[caller] = {}

    # get value
    azcam.db.parfile_dict[caller][attribute] = value

    return
