"""
*azcam.shortcuts* contains keyboard (CLI) shortcuts.
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


def sf_server():
    """Shortcut to Set image folder"""

    try:
        folder = azcam.utils.curdir()
        azcam.db.tools["exposure"].folder = folder
    except Exception:
        pass

    return


def gf_server():
    """
    Shortcut to Go to image folder.
    Also issues sav() command to save folder location.
    """

    folder = azcam.db.tools["exposure"].folder
    azcam.utils.curdir(folder)
    azcam.db.wd = folder
    sav_server()

    return


def sav_server():
    """Shortcut for parfile_write() saving current folder in database."""
    azcam.db.parameters.set_script_par("azcamserver", "wd", azcam.utils.curdir())
    azcam.db.parameters.update_pars(1, "azcamserver")
    azcam.db.parameters.write_parfile()

    return None


def pp():
    """Shortcut to toggle cmdserver printing."""

    old = azcam.db.cmdserver.logcommands
    new = not old
    azcam.db.cmdserver.logcommands = new
    print("cmdserver logcommands is now %s" % ("ON" if new else "OFF"))

    return


def wc():
    """Shortcut to toggle webserver command logging to console."""

    old = azcam.db.tools["webserver"].logcommands
    new = not old
    azcam.db.tools["webserver"].logcommands = new
    print("webserver logcommands is now %s" % ("ON" if new else "OFF"))

    return


def sf_console():
    """Shortcut to set image folder"""

    try:
        folder = azcam.utils.curdir()
        azcam.db.parameters.set_par("imagefolder", folder)
    except Exception:
        pass

    return


def gf_console():
    """
    Shortcut to goto image folder.
    Also issues sav() command to save folder location.
    """

    folder = azcam.db.parameters.get_par("imagefolder")
    azcam.utils.curdir(folder)
    azcam.db.wd = folder
    sav_console()

    return


def sav_console():
    """Shortcut for parfile_write() saving current folder in database."""

    azcam.db.parameters.set_script_par("azcamconsole", "wd", azcam.utils.curdir())
    azcam.db.parameters.update_pars(1, "azcamconsole")
    azcam.db.parameters.write_parfile()

    return


def sroi():
    """Alias for set_image_roi()."""
    azcam.utils.set_image_roi()


# add to shortcuts
if azcam.mode == "server":
    azcam.db.shortcuts.update(
        {"sav": sav_server, "pp": pp, "sf": sf_server, "gf": gf_server, "wc": wc}
    )
elif azcam.mode == "console":
    azcam.db.shortcuts.update(
        {"sav": sav_console, "sroi": sroi, "sf": sf_console, "gf": gf_console, "bf": bf}
    )
