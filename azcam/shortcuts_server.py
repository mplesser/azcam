"""
Shortcuts for CLI interface in azcam app.

Defines: sav, p, sroi, sf, gf
"""

import azcam

__all__ = ["sav", "p", "sf", "gf", "bf"]


def sav():
    """Shortcut for parfile_write() saving current folder in database."""
    azcam.db.genpars.set_par("azcamserver", "wd", azcam.utils.curdir())
    azcam.utils.update_pars(1, azcam.db.genpars.par_dict["azcamserver"])
    azcam.db.genpars.parfile_write()

    return None


def p():
    """Shortcut to toggle cmdserver printing."""

    old = azcam.db.cmdserver.logcommands
    new = not old
    azcam.db.cmdserver.logcommands = new
    print("cmdserver logcommands is now %s" % ("ON" if new else "OFF"))

    return


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


def bf():
    """Shortcut for file_browser()."""

    folder = azcam.utils.file_browser("", "folder", "Select folder")
    if folder == []:
        return
    if isinstance(folder, list):
        folder = folder[0]
    azcam.utils.curdir(folder)

    return folder


# add to CLI dict
azcam.db.cli_cmds.update({"sav": sav, "p": p, "sf": sf, "gf": gf, "bf": bf})
