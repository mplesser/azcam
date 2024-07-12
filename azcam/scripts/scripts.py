import importlib
import importlib.util
import os

import azcam
import azcam.exceptions


def loadscripts(packages: list) -> None:
    """
    Load scripts into azcam.db.scripts.
    """

    for package in packages:
        pyfiles = []
        spec = importlib.util.find_spec(package)
        if spec is not None:
            folder = spec.submodule_search_locations[0]
        else:
            return

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
                # azcam.db.scripts[pfile] = func
                azcam.db.cli[pfile] = func
            except Exception as e:
                azcam.log(e)
                azcam.exceptions.warning(f"Could not import script {pfile}")

    return
