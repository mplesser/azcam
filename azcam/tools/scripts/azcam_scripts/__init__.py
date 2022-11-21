from importlib import metadata

__version__ = metadata.version(__package__)
__version_info__ = tuple(int(i) for i in __version__.split(".") if i.isdigit())

import importlib
import os

import azcam


def load(scripts="all") -> None:
    """
    Load all scripts from folder into azcam.db.scripts.
    """

    rootpackage = "azcam_scripts"
    folder = importlib.util.find_spec(rootpackage).submodule_search_locations[0]

    # bring all .py modules with same function name into namespace
    _, _, filenames = next(os.walk(folder))
    pyfiles = []
    for files in filenames:
        if files.endswith(".py"):
            pyfiles.append(files[:-3])
    if "__init__" in pyfiles:
        pyfiles.remove("__init__")

    for pfile in pyfiles:
        try:
            mod = importlib.import_module(f"{rootpackage}.{pfile}")
            func = getattr(mod, pfile)
            azcam.db.scripts[pfile] = func
        except Exception as e:
            azcam.log(e)
            azcam.AzcamWarning(f"Could not import script {pfile}")

    return
