"""
Shortcuts for CLI, console.
"""


import azcam


def bf():
    """Shortcut for file_browser()."""

    folder = azcam.utils.file_browser("", "folder", "Select folder")
    if folder == []:
        return
    if isinstance(folder, list):
        folder = folder[0]
    azcam.utils.curdir(folder)

    return folder


def sf():
    """Shortcut to Set image folder"""

    try:
        folder = azcam.utils.curdir()
        azcam.db.params.set_par("imagefolder", folder)
    except Exception:
        pass

    return


def gf():
    """
    Shortcut to Go to image folder.
    Also issues sav() command to save folder location.
    """

    folder = azcam.db.params.get_par("imagefolder")
    azcam.utils.curdir(folder)
    azcam.db.wd = folder
    sav()

    return


def sav():
    """Shortcut for parfile_write() saving current folder in database."""

    azcam.db.params.set_script_par("azcamconsole", "wd", azcam.utils.curdir())
    azcam.db.params.update_pars(1, "azcamconsole")
    azcam.db.params.write_parfile()

    return


def sroi():
    """Alias for set_image_roi()."""
    azcam.utils.set_image_roi()

    return


# add to CLI dictionary
azcam.db.cli_tools.update({"sav": sav, "sroi": sroi, "sf": sf, "gf": gf, "bf": bf})
