"""
Startup script for azcam.

For installations, this is the "azcam" command.
"""

import os
import sys

import azcam


def main():
    """
    Main method to allow for installed azcam command.
    Requried arguments is startup script
    Local optional arguments are: -venv virtual_environment_activation_script

    Usage:
        azcam startup_script -venv path_to_venv
            startup_script, ex: azcam_itl.start
            -venv path_to_venv: use virtual environment
    """

    args = sys.argv[1:]

    if len(args) >= 1:
        startmod = sys.argv[1]
    else:
        print("No startup package/script specified - stopping.")
        exit()

    if "-venv" in args:
        i = sys.argv.index("-venv")
        activator = sys.argv[i + 1]
        use_venv = True
    else:
        use_venv = False
        activator = None

    if os.name == "posix":
        if use_venv:
            cmds = [
                f". {activator} ; python3 -m {startmod}",
                f"{' '.join(args)}",
            ]
        else:
            cmds = [
                f"python3 -m {startmod}",
                f"{' '.join(args)}",
            ]
    else:
        if use_venv:
            cmds = [
                "cmd /k",
                f'"{activator} & ipython --profile azcam -m {startmod} -i"',
                f"-- {' '.join(args)}",
            ]
        else:
            cmds = [
                "cmd /k",
                f"ipython --profile azcam -m {startmod} -i",
                f"-- {' '.join(args)}",
            ]

    command = " ".join(cmds)
    os.system(command)


def start():
    """
    Method called from azcam.__main__.py
    """

    main()

    return


if __name__ == "__main__":
    main()
