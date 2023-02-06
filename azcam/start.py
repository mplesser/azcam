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
      -python system_python_command (default is "ipython --profile azcam")

    Usage example:
      azcam azcam_xxx.start -venv ve_activation_path -python python3
    """

    if len(sys.argv) >= 2:
        startmod = sys.argv[1]
    else:
        print("Error: No startup script specified")
        exit()

    if "-venv" in sys.argv:
        i1 = sys.argv.index("-venv")
        use_venv = True
        activator = sys.argv[i1 + 1]
    else:
        use_venv = False
        activator = None

    if "-python" in sys.argv:
        i2 = sys.argv.index("-python")
        pythoncmd = sys.argv[i2 + 1]
    else:
        pythoncmd = "ipython --profile azcam"
        # Examples:
        # pythoncmd = "start ipython --profile azcam"
        # pythoncmd = "wt ipython --profile azcam"

    if os.name == "posix":
        if use_venv:
            cmds = [
                f". {activator} ; {pythoncmd} -m {startmod}",
                f"{' '.join(sys.argv)}",
            ]
        else:
            cmds = [
                f"{pythoncmd} -m {startmod}",
                f"{' '.join(sys.argv)}",
            ]
    else:
        if use_venv:
            cmds = [
                "cmd /k",
                f'"{activator} & {pythoncmd} -m {startmod} -i"',
                f"-- {' '.join(sys.argv)}",
            ]
        else:
            cmds = [
                "cmd /k",
                f"{pythoncmd} -m {startmod} -i",
                f"-- {' '.join(sys.argv)}",
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


"""

if os.name == "posix":
    AZCAM_DATAROOT = f'{os.path.abspath("data")}'
    os.environ["AZCAM_DATAROOT"] = AZCAM_DATAROOT
    print(f"AzCam data root is {AZCAM_DATAROOT}")

    if SERVER:
        command = f"ipython --profile azcamserver -i -c \"import azcam_itl.server ; from azcam.cli import *\" -- {' '.join(args)}"
    elif CONSOLE:
        command = f"ipython --profile azcamconsole -i -c \"import azcam_itl.console ; from azcam.cli import *\" -- {' '.join(args)}"
    os.system(command)

else:
    if SERVER:
        config_file = os.path.join(os.path.dirname(__file__), "ipython_config.py")
        cmds = [
            # f"ipython --profile azcamserver -i -c",
            f"ipython --profile azcamserver --config={config_file} -i -c",
            '"import azcam_itl.server ; from azcam.cli import *"',
            f" -- {' '.join(args)}",
        ]
    if CONSOLE:
        cmds = [
            "ipython --profile azcamconsole -i -c",
            '"import azcam_itl.start"',
            f" -- {' '.join(args)}",
        ]

    command = " ".join(cmds)
    print(command)
    input()
    os.system(command)


    if "-console" in args:
        tabColor = "#000099"
        tabTitle = "azcamconsole"
    elif "-server" in args:
        tabColor = "#990000"
        tabTitle = "azcamserver"
    else:
        # assume console mode
        tabColor = "#000099"
        tabTitle = "azcamconsole"

        if use_venv: 
            cmds = [
                f"wt -w azcam --suppressApplicationTitle=True --title {tabTitle} --tabColor {tabColor}",
                "cmd /k",
                f'"{activator} & python -m {startmod}"',
                f"{' '.join(args)}",
            ]
        else:
            cmds = [
                f"wt -w azcam --suppressApplicationTitle=True --title {tabTitle} --tabColor {tabColor}",
                "cmd /k",
                f"python -m {startmod}",
                f"{' '.join(args)}",
            ]

"""
