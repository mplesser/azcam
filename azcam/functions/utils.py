"""
*azcam.utils* contains general purpose support commands used throughout azcam.
"""

import os
import shlex
import sys
import tkinter
import tkinter.filedialog
from typing import Callable, List

if os.name == "nt":
    import winsound

# keyboard checking is optional
try:
    import msvcrt
except Exception:
    pass

import azcam


def beep(frequency=2000, duration=500) -> None:
    """
    Play a sound.
    Install beep on Linux systems.
    """

    if os.name == "posix":
        os.system("beep -f %s -l %s" % (frequency, duration))
    else:
        winsound.Beep(frequency, duration)

    return


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
        bool no_drive_letter: Removes leading drive letter.
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

    search_folder = azcam.utils.fix_path(search_folder)

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
                    sub = azcam.utils.fix_path(sub)
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


def parse(string: str, set_type=0) -> List[str]:
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


def get_datatype(value) -> list:
    """
    Determine the data type for an object and set the type if possible. A string such as "1.23"
    will result in a type "float" and "2" will result in type "int".

    Args:
        value: object to be typed
    Returns:
        list [type, value] of data type as a code and object with that type
    """

    if type(value) is str:

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

    elif type(value) is int:
        attributetype = "int"
        value = int(value)

    elif type(value) is float:
        attributetype = "float"
        value = float(value)

    # more work here
    else:
        attributetype = "str"

    return [attributetype, value]


def prompt(prompt_message: str = "Enter a string", default: str = "") -> str:
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
        raise azcam.AzcamError("check_keyboard not supported on this OS")

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
            azcam.AzcamWarning("Quit detected")
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


def get_image_roi() -> list:
    """
    Get the data and noise regions of interest in image image coordinates.
    Check for ROI's in the following order:
      - azcam.db.imageroi if defined
      - display.roi if defined

    Returns:
        list of ROIs
    """

    # database roi
    if azcam.db.get("imageroi"):
        if azcam.db.imageroi != []:
            return azcam.db.imageroi

    # display.roi
    roi = []

    try:
        reply = azcam.db.tools["display"].get_rois(0, "image")
    except AttributeError:
        raise azcam.AzcamError("cannot get ROI - display not found")
    roi.append(reply)
    reply = azcam.db.tools["display"].get_rois(1, "image")
    if reply:
        roi.append(reply)
    else:
        roi.append(roi[0])

    return roi


def set_image_roi(roi: list = []) -> None:
    """
    Set the global image region of interest "db.imageroi".
    If roi is not specified, use display ROI.

    Args:
        roi: ROI list or []
    """

    # set directly with given value
    if roi != []:
        azcam.db.imageroi = roi
        return

    # use display ROIs
    roi = []
    try:
        reply = azcam.db.tools["display"].get_rois(-1, "image")
    except AttributeError:
        raise azcam.AzcamError("cannot set ROI - no display found")

    if not reply:
        raise azcam.AzcamError("could not get display ROI")

    azcam.db.imageroi = reply

    return


def file_browser(Path: str = "", SelectString: str = "*.*", Label: str = "") -> list:
    """
    Filebrowser GUI to select files.  This is the tcl/tk version.

    Args:
        Path: Starting path for selection.
        SelectString: Selection string like [('all files',('*.*'))] for filtering file names or *folder* to select folders.
        Label: Dialog box label.
    Returns:
        list of selected files/folders or None
    """

    tkinter.Tk().withdraw()  # we don't want a full GUI, so keep the root window from appearing

    options = {}

    if Path != "":
        options["initialdir"] = Path if os.path.isdir(Path) else os.path.dirname(Path)
    else:
        options["initialdir"] = ""

    if SelectString == "folder":
        options["mustexist"] = True
        options["title"] = "Select folder" if Label == "" else Label
        folder = tkinter.filedialog.askdirectory(**options)
        if folder is None:
            return
        if folder == "":
            folder = None
        return folder

    else:
        options["title"] = "Select file(s)" if Label == "" else Label
        options["multiple"] = True

        # get filetypes string
        if SelectString == "*.*":
            options["filetypes"] = [("all files", "*.*")]
        else:
            options["filetypes"] = SelectString

        filename = tkinter.filedialog.askopenfilename(**options)
        if filename == "":
            filename = None

        return filename


def find_file(filename, include_curdir=False) -> str:
    """
    Find the absolute filename for a file in the current search path.
    Set include_curdir True to add curdir() to search path.

    Args:
        filename: Name of file.
        include_curdir: True to include current folder in sys.path.
    Returns:
        Cleaned path name
    Raises:
        FileNotFoundError if file not found.

    """

    added_cd = 0
    if include_curdir:
        cd = azcam.utils.curdir()
        if cd not in sys.path:
            sys.path.append(cd)
            added_cd = 1

    # absolute pathname
    if os.path.isabs(filename):
        if added_cd:
            sys.path.remove(cd)
        if os.path.exists(filename):
            return filename
        else:
            raise FileNotFoundError(f'file "{filename}" not found')

    file_found = 0
    for path in sys.path:
        if path == "":
            pass
        elif os.path.exists(os.path.join(path, filename)):
            if os.path.isdir(os.path.join(path, filename)):  # no folders
                continue
            file_found = 1
            break
    if added_cd:
        sys.path.remove(cd)

    if file_found:
        return os.path.normpath(os.path.join(path, filename))
    else:
        raise FileNotFoundError(f'file "{filename}" not found')

    return


def find_file_in_sequence(file_root: str, file_number: int = 1) -> tuple:
    """
    Returns the Nth file in an image sequence where N is file_number (-1 for first file).

    Args:
        file_root: image file root name.
        file_number: image file number in sequence.

    Returns:
        tuple (filename,sequencenumber).
    """

    currentfolder = azcam.utils.curdir()

    for _, _, files in os.walk(currentfolder):
        break

    for f in files:
        if f.startswith(file_root):
            break

    try:
        if not f.startswith(file_root):
            raise azcam.AzcamError("image sequence not found")
    except Exception:
        raise azcam.AzcamError("image sequence not found")

    firstfile = azcam.utils.fix_path(os.path.join(currentfolder, f))
    firstsequencenumber = firstfile[-9:-5]
    firstnum = firstsequencenumber
    firstsequencenumber = int(firstsequencenumber)
    sequencenumber = firstsequencenumber + file_number - 1
    newnum = "%04d" % sequencenumber
    filename = firstfile.replace(firstnum, newnum)

    return (filename, sequencenumber)


def make_file_folder(subfolder: str, increment: bool = True, use_number: bool = False) -> tuple:
    """
    Creates a new subfolder in the current FileFolder.

    Args:
        subfolder: subfolder name to create
        increment: - if True, subfolder name may be incremented to create a unique name (e.g. ptc1, ptc2, ptc3...)
        use_number: - if True, starts with '1' after Subfolder name (e.g. report1 not report)
    Returns:
        tuple (currentfolder,newfolder)
    """

    currentfolder = azcam.utils.curdir()

    sf = subfolder + "1" if use_number else subfolder

    try:
        newfolder = os.path.join(currentfolder, sf)  # new subfolder
        os.mkdir(newfolder)
        newfolder = azcam.utils.fix_path(newfolder)
    except Exception:
        if not increment:
            raise azcam.AzcamError("could not make new subfolder")
        else:
            for i in range(1, 1000):
                newfolder = os.path.join(
                    currentfolder, subfolder + str(i)
                )  # try a new subfolder name
                try:
                    os.mkdir(newfolder)
                    newfolder = azcam.utils.fix_path(newfolder)
                    break
                except Exception:  # error OK
                    continue
            if i == 999:
                raise azcam.AzcamError("could not make subfolder")

    newfolder = azcam.utils.fix_path(newfolder)

    return (currentfolder, newfolder)


def save_imagepars(imagepars={}) -> None:
    """
    Save current image parameters.
    imagepars is a dictionary.

    Args:
        imagepars: dict of azcam.db.imageparnames names to save
    """

    for par in azcam.db.imageparnames:
        imagepars[par] = azcam.db.parameters.get_par(par)

    return


def restore_imagepars(imagepars: dict, folder: str = "") -> None:
    """
    Restore image parameters from dictionary.

    Args:
        imagepars: dictionary set with save_imagepars().
        folder: folder to set as current
    """

    for par in azcam.db.imageparnames:
        impar = imagepars[par]
        if impar == "":
            impar = '""'
        imagepars[par] = impar
        if par == "imagetitle":
            impar = f'"{impar}"'
        azcam.db.parameters.set_par(par, impar)

    # return to folder
    if folder != "":
        curdir(folder)

    return


def get_tools(tool_names: list) -> list:
    """
    Return a list of tool objects from a list of their names.

    Args:
        tool_names: list of the tool names to get

    Returns:
        list of tool objects
    """

    tools = []

    for tool in tool_names:
        tool1 = azcam.db.tools[tool]
        if tool1 is not None:
            tools.append(tool1)
        else:
            tools.append(azcam.db.tools(tool))

    return tools


def parse_command_string(command: str, case_insensitive: int = 0):
    """
    Parse a command string into tool and arguments.
    If command does not start with a dotted object.method token, then
    assume it is the method of the default_tool.

    Returns (objid, args, kwargs)
    objid is a bound method of a class
    args is a list of strings
    kwargs is a dict of strings
    """

    # parse command string
    tokens = azcam.utils.parse(command, 0)
    cmd = tokens[0]

    if case_insensitive:
        cmd = cmd.lower()

    arglist = tokens[1:]
    args = []
    kwargs = {}
    if len(arglist) == 0:
        pass
    else:
        for token in arglist:
            if "=" in token:
                keyname, value = token.split("=")
                kwargs[keyname] = value
            else:
                args.append(token)

    if "." not in cmd:

        # get method from db.default_tool
        if azcam.db.default_tool is None:
            s = f"command not recognized: {cmd} "
            raise azcam.AzcamError(s)
        else:
            objid = getattr(azcam.db.tools[azcam.db.default_tool], cmd)

    else:

        # get method from tool in db.tools
        objects = cmd.split(".")
        if objects[0] not in azcam.db.tools:
            raise azcam.AzcamError(f"remote call not allowed: {objects[0]}", 4)

        if len(objects) == 1:
            objid = azcam.db.tools[objects[0]]
        elif len(objects) == 2:
            objid = getattr(azcam.db.tools[objects[0]], objects[1])
        elif len(objects) == 3:
            objid = getattr(getattr(azcam.db.tools[objects[0]], objects[1]), objects[2])
        elif len(objects) == 4:
            objid = getattr(
                getattr(getattr(azcam.db.tools[objects[0]], objects[1]), objects[2]),
                objects[3],
            )
        else:
            objid = None  # too complicated for now

        # kwargs = {}
        # l1 = len(tokens)
        # if l1 > 1:
        #     args = tokens[1:]
        #     if "=" in args[0]:
        #         # assume all keywords for now
        #         kwargs = {}
        #         for argtoken in args:
        #             keyword, value = argtoken.split("=")
        #             kwargs[keyword] = value
        #         args = []
        # else:
        #     args = []

    return objid, args, kwargs


def execute_command(tool: Callable, args: list, kwargs: dict = {}) -> str:
    """
    Executes a tool command which has been parsed into tool method and arguments and
    returns its reply string.

    Args:
        tool: tool object (not name)
        args: list of arguments
        kwargs: dictionary of keyword:value pairs for arguments

    Returns:
        reply: reply from command executed. Always starts with OK or ERROR.
    """

    if len(args) == 0 and len(kwargs) == 0:
        reply = tool()

    elif len(kwargs) == 0:
        reply = tool(*args)

    elif len(args) == 0:
        reply = tool(**kwargs)

    else:
        reply = tool(*args, **kwargs)

    reply = _command_reply(reply)

    return reply


def _command_reply(reply: str):
    """
    Create a reply string for a socket command.

    Args:
        reply (str): command reply

    Returns:
        [type]: formatted reply string
    """

    if reply is None or reply == "":
        s = ""

    elif type(reply) == str:
        s = reply

    elif type(reply) == list:
        s = ""
        for x in reply:
            if type(x) == str and " " in x:  # check if space in the string
                s = s + " " + "'" + str(x) + "'"
            else:
                s = s + " " + str(x)
        s = s.strip()

    elif type(reply) == dict:
        s = json.dumps(reply)

    else:
        s = repr(reply)

        if s != '""':
            s = s.strip()

    # add OK status if needed
    if not (s.startswith("OK") or s.startswith("ERROR") or s.startswith("WARNING")):
        s = "OK " + s

    s = s.strip()

    return s
