"""
Shortcuts for CLI, server.
"""


import azcam


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
    azcam.db.params.set_script_par("azcamserver", "wd", azcam.utils.curdir())
    azcam.db.params.update_pars(1, "azcamserver")
    azcam.db.params.write_parfile()

    return None


def p():
    """Shortcut to toggle cmdserver printing."""

    old = azcam.db.cmdserver.logcommands
    new = not old
    azcam.db.cmdserver.logcommands = new
    print("cmdserver logcommands is now %s" % ("ON" if new else "OFF"))

    return


# add to CLI dictionary
azcam.db.cli_objects.update({"sav": sav, "p": p, "sf": sf, "gf": gf})
