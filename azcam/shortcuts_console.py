"""
Shortcuts for azcam console CLI.
Defines: sav, bf, sroi, sf, gf
"""


import azcam
from azcam.console import api


def sav():
    """Shortcut for parfile_write() saving current folder in database."""

    azcam.db.genpars.set_par("azcamconsole", "wd", azcam.utils.curdir())
    azcam.utils.update_pars(1, azcam.db.genpars.par_dict["azcamconsole"])
    azcam.db.genpars.parfile_write()

    return


def bf():
    """Shortcut for file_browser()."""

    folder = azcam.utils.file_browser("", "folder", "Select folder")
    if folder == []:
        return
    if isinstance(folder, list):
        folder = folder[0]
    azcam.utils.curdir(folder)

    return folder


def sroi():
    """Alias for set_image_roi()."""
    azcam.utils.set_image_roi()

    return


def sf():
    """Shortcut to set imagefolder to current folder"""

    folder = azcam.utils.curdir()
    api.set_par("imagefolder", folder)

    return


def gf():
    """
    Shortcut to Go to image folder.
    Also issues sav() command to save folder location.
    """

    folder = api.get_par("imagefolder")
    if folder is None:
        return
    azcam.utils.curdir(folder)
    azcam.db.wd = folder
    sav()

    return


# add to CLI dict
azcam.db.cli_cmds.update({"sav": sav, "bf": bf, "sroi": sroi, "sf": sf, "gf": gf})
