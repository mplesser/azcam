"""
Shortcuts for CLI, server.
"""


import azcam


def sf():
    """Shortcut to Set image folder"""

    try:
        folder = azcam.utils.curdir()
        azcam.utils.set_par("imagefolder", folder)
    except Exception:
        pass

    return


def gf():
    """
    Shortcut to Go to image folder.
    Also issues sav() command to save folder location.
    """

    folder = azcam.utils.get_par("imagefolder")
    azcam.utils.curdir(folder)
    azcam.db.wd = folder
    sav()

    return


def sav():
    """Shortcut for parfile_write() saving current folder in database."""
    azcam.api.config.set_par("azcamserver", "wd", azcam.utils.curdir())
    azcam.utils.update_pars(1, azcam.api.config.par_dict["azcamserver"])
    azcam.api.config.parfile_write()

    return None


def p():
    """Shortcut to toggle cmdserver printing."""

    old = azcam.db.cmdserver.logcommands
    new = not old
    azcam.db.cmdserver.logcommands = new
    print("cmdserver logcommands is now %s" % ("ON" if new else "OFF"))

    return


# add to CLI dictionary
azcam.db.cli_cmds.update({"sav": sav, "p": p, "sf": sf, "gf": gf})

