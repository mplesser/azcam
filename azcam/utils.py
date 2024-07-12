"""
*azcam_console.utils* contains general purpose support commands used throughout azcam_console.
"""

import os
import shlex
import sys
from typing import List


# keyboard checking is optional
try:
    import msvcrt
except Exception:
    pass

import azcam
import azcam.exceptions


def curdir(folder: str = "") -> str:
    """
    Gets and sets the working folder.
    If folder is not specified then just return the current working folder.

    Args:
        folder: name of folder set.
    Returns:
        the current folder (after changing).
    """

    if folder is None:
        return

    if folder != "":
        folder = folder.lstrip('"').rstrip('"')
        try:
            os.chdir(folder)
        except FileNotFoundError:
            pass

    reply = os.getcwd()

    reply = reply.replace("\\", "/")

    azcam.db.wd = reply  # save result

    return reply


def fix_path(path: str = "", no_drive_letter: bool = True) -> str:
    """
    Makes a nice absolute path, leaving only forward slashes.

    Args:
        path: name of path to cleanup.
        no_drive_letter: Removes leading drive letter.
    Returns:
        cleaned path name.
    """

    norm = os.path.abspath(os.path.normpath(path))

    pth = norm.replace("\\", "/")  # go to forward slashes only

    if no_drive_letter and len(pth) > 2 and pth[1] == ":":
        pth = pth[2:]

    return pth


def add_searchfolder(search_folder: str = "", include_subfolders: bool = True) -> None:
    """
    Appends search_folder (and by default all its subfolders) to the current python search path.
    Default is current folder and its subfolders.
    Subfolders beginning with "_" are not included.

    Args:
        search_folder: Name of folder to add to sys.path
        include_subfolders: True to include all subfolders in sys.path
    """

    if search_folder == "":
        search_folder = curdir()

    search_folder = fix_path(search_folder)

    # append all subfolders of search_folder to current search path
    if search_folder not in sys.path:
        sys.path.append(search_folder)

    if include_subfolders:
        for root, dirs, _ in os.walk(search_folder):
            if dirs:
                for s in dirs:
                    if s.startswith("_"):
                        continue
                    sub = os.path.join(root, s)
                    sub = fix_path(sub)
                    if sub not in sys.path:
                        sys.path.append(sub)

    return


def make_image_filename(imagefile: str) -> str:
    """
    Returns the absolute file imagefile, with forward slashes.
    Appends ".fits" if no extension is included.

    Args:
        imagefile: image filename to be expanded
    Returns:
        expanded image filename.
    """

    if imagefile.endswith(".fits"):
        pass
    elif imagefile.endswith(".fit"):
        pass
    elif not imagefile.endswith(".bin"):
        imagefile += ".fits"

    return fix_path(imagefile)


def parse(string: str, set_type: bool = False) -> List[str]:
    """
    Parse a string into tokens using the standard azcam rules.
    If setType is true, try and set data data type for each token.

    Args:
        string: String to be parsed into tokens
        set_type: True to try and set the type of each token ("1" to 1)
    Returns:
        list of parsed tokens
    """

    # allow for quotes
    lex = shlex.shlex(string)
    lex.quotes = "\"'"
    lex.whitespace_split = True
    lex.commenters = "#"
    toks = list(lex)

    # remove bounding quotes unless quoting a number (leave as string)
    tokens = []
    for tok in toks:
        if tok.startswith('"') and tok.endswith('"'):
            tok1 = tok[1:-1]
            t, value = get_datatype(tok1)
            if t not in ["int", "float"]:
                tok = tok1

        elif tok.startswith("'") and tok.endswith("'"):
            tok1 = tok[1:-1]
            t, value = get_datatype(tok1)
            if t not in ["int", "float"]:
                tok = tok1

        tokens.append(tok)

    if set_type:
        for i, tok in enumerate(tokens):
            t, value = get_datatype(tok)
            tokens[i] = value

    return tokens


def get_datatype(value: any) -> list:
    """
    Determine the data type for an object and set the type if possible. A string such as "1.23"
    will result in a type "float" and "2" will result in type "int".

    Args:
        value: object to be typed
    Returns:
        list [type, value] of data type as a code and object with that type
    """

    if isinstance(value, str):
        # string integer
        if value.isdigit():
            attributetype = "int"
            value = int(value)
            return [attributetype, value]
        else:
            try:
                value = float(value)
                attributetype = "float"
                return [attributetype, value]
            except ValueError:
                pass

        attributetype = "str"

    elif isinstance(value, int):
        attributetype = "int"
        value = int(value)

    elif isinstance(value, float):
        attributetype = "float"
        value = float(value)

    # more work here
    else:
        attributetype = "str"

    return [attributetype, value]


def prompt(prompt_message: str = "Enter a string", default: any = "") -> any:
    """
    Prints a message and waits for user input.

    Args:
        prompt_message: string to be printed
        default:  string to be returned if no value is entered
    Returns:
        string entered or default value
    """

    default = str(default)
    try:
        if default != "":
            in1 = input(prompt_message + " [" + default + "]: ")
        else:
            in1 = input(prompt_message + ": ")
    except KeyboardInterrupt:
        return ""

    if in1 == "":
        return default
    else:
        return in1


def check_keyboard(wait: bool = False) -> str:
    """
    Checks keyboard for a key press.
    For Windows OS only.

    Args:
        wait: True to wait until a key is pressed
    Returns:
        key which was pressed or empty string.
    """

    # TODO: map sequences like 'F1'

    if os.name != "nt":
        raise azcam.exceptions.AzcamError("check_keyboard not supported on this OS")

    loop = 1
    key = ""

    while loop:
        if msvcrt.kbhit():
            key = msvcrt.getch()
            try:
                key = key.decode()

                # since the key is byte type, maybe escape sequence so check for more
                # if msvcrt.kbhit():
                #    key1 = msvcrt.getch()
                #    # key = key + key1.decode()
            except UnicodeDecodeError:
                pass
            break
        if not wait:
            loop = 0

    return key


def show_menu(configs: dict) -> str:
    """
    Interative: Show a menu and wait for selection.
    "blank" may be used to display an empty line.
    print() is allowed here as this is for interactive use only.

    Args:
        configs: Dictionary of strings which are menu items
    Returns:
        string associated with item selected or empty string.
    """

    if len(configs) == 1:
        choice = configs[list(configs.keys())[0]]
        return choice

    CONFIRMED = 0
    choice = ""
    while not CONFIRMED:
        print("Select configuration number from list below:\n")
        i = 0
        for c in configs:
            if c == "blank":
                print("")
            else:
                i += 1
                print("%1d.....%s" % (i, c))
        print("")
        print("Enter configuration number: ", end="")
        choiceindex = input()
        if choiceindex == "q":
            azcam.exceptions.warning("Quit detected")
            return
        try:
            choiceindex = int(choiceindex)
        except ValueError:
            print("Bad keyboard input...try again\n")
            continue

        choiceindex = int(choiceindex)
        choiceindex = choiceindex - 1  # zero based

        # remove blanks
        for x in configs:
            if x == "blank":
                configs.remove("blank")

        if choiceindex < 0 or choiceindex > len(configs) - 1:
            print("invalid selection - %d\n" % (choiceindex + 1))
            continue

        # get choice
        configlist = list(configs.keys())  # is order OK?
        choice = configs[configlist[choiceindex]]

        CONFIRMED = 1

    print("")

    return choice


def get_datafolder(datafolder: str | None = None):
    """
    Return the datafolder for this system.
    If not specified, root is /data on Windows or ~/data on Linux.
    """

    if datafolder is None:
        droot = os.environ.get("AZCAM_DATAROOT")
        if droot is None:
            if os.name == "posix":
                droot = os.environ.get("HOME")
            else:
                droot = "/"
            datafolder = os.path.join(
                os.path.realpath(droot), "data", azcam.db.systemname
            )
        else:
            datafolder = os.path.join(os.path.realpath(droot), azcam.db.systemname)
    else:
        datafolder = os.path.realpath(datafolder)

    datafolder = os.path.normpath(datafolder)

    return datafolder


def save_imagepars(imagepars: dict) -> None:
    """
    Save current image parameters.
    imagepars is a dictionary.

    Args:
        imagepars: dict of azcam.db.imageparnames names to save
    """

    for par in azcam.db.imageparnames:
        imagepars[par] = azcam.db.parameters.get_par(par)

    return


def restore_imagepars(imagepars: dict) -> None:
    """
    Restore image parameters from dictionary.

    Args:
        imagepars: dictionary set with save_imagepars().
    """

    for par in azcam.db.imageparnames:
        value = imagepars[par]
        if value == "":
            value = '""'
        imagepars[par] = value
        if par == "imagetitle":
            value = f'"{value}"'
        print(par, value)
        azcam.db.parameters.set_par(par, value)

    return
