"""
Shortcuts for CLI interface in azcam app.

Defines: sav, p, sroi, sf, gf
"""

import azcam

__all__ = ["sav", "p", "sf", "gf", "bf'"]


def sav():
    """Shortcut to parfile_write() to save current folder in database."""
    azcam.utils.curdir()  # update wd
    azcam.utils.parfile_write()

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
    if isinstance(folder, list):
        folder = folder[0]
    azcam.utils.curdir(folder)
    sav()

    return folder
