
import importlib
import importlib.util
import os

import azcam


def load(scripts="all") -> None:
    """
    Load scripts into azcam.db.scripts.
    Upper level (azcam.scripts) are always installed.
    """

    if scripts=="all":
        packages = ["azcam.scripts"]
    elif scripts=="console":
        packages = ["azcam.scripts", "azcam.scripts.console"]
    elif scripts=="server":
        packages = ["azcam.scripts", "azcam.scripts.server"]
    else:
        azcam.AzcamWarning("Invalid scripts option")
        return

    for package in packages:
        pyfiles = []
        folder = importlib.util.find_spec(package).submodule_search_locations[0]

        # bring all .py modules with same function name into namespace
        _, _, filenames = next(os.walk(folder))
        for file1 in filenames:
            if file1.endswith(".py"):
                pyfiles.append(file1[:-3])
        if "__init__" in pyfiles:
            pyfiles.remove("__init__")

        for pfile in pyfiles:
            try:
                mod = importlib.import_module(f"{package}.{pfile}")
                func = getattr(mod, pfile)
                azcam.db.scripts[pfile] = func
            except Exception as e:
                azcam.log(e)
                azcam.AzcamWarning(f"Could not import script {pfile}")

    return
