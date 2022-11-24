"""
Startup script for azcam.

For installations, this is the "azcam" command.
"""

import os
import sys

import azcam


def main():
    """
    Method for the azcam command.
    Required argument is a startup script name.
    Local optional arguments are:
      -venv path_to_ve_activation_script
      -python system_python_command (default is ipython)
         may include python options in quotes (e.g. "ipython --profile azcamserver")

    Usage example:
      azcam azcam_xxx.start -venv ve_activation_path -python python3
    """

    args = sys.argv[1:]

    if len(args) >= 1:
        startmod = sys.argv[1]
    else:
        print("No startup package/script specified - stopping")
        exit()

    i1=i2=0
    if "-venv" in args:
        i1 = sys.argv.index("-venv")
        activator = sys.argv[i1 + 1]
        use_venv = True
    else:
        use_venv = False
        activator = None

    if "-python" in args:
        i2 = sys.argv.index("-python")
        pythoncmd = sys.argv[i2 + 1]
    else:
        pythoncmd = "ipython --profile azcam"

    args = args[(2+i1+i2):]

    if os.name == "posix":
        if use_venv:
            cmds = [
                f". {activator} ; {pythoncmd} -m {startmod}",
                f"{' '.join(args)}",
            ]
        else:
            cmds = [
                f"{pythoncmd} -m {startmod}",
                f"{' '.join(args)}",
            ]
    else:
        if use_venv:
            cmds = [
                "cmd /k",
                f'"{activator} & {pythoncmd} -m {startmod} -i"',
                f"-- {' '.join(args)}",
            ]
        else:
            cmds = [
                "cmd /k",
                f"{pythoncmd} -m {startmod} -i",
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
