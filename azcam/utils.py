"""
General support commands for throughout azcam code.
"""

import importlib
import imp
import os
import shlex
import sys
import tkinter
import tkinter.filedialog

# keyboard checking is optional
try:
    import msvcrt
except Exception:
    pass

import azcam


def curdir(folder=""):
    """
    Gets and sets the working folder.
    If folder=='', return the current working folder.

    :param str folder: Name of folder
    :return: None
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


def fix_path(Path="", no_drive_letter=1):
    """
    Makes a nice absolute path, hopefully leaving only forward slashes.

    :param str Path: Name of path to cleanup
    :param bool no_drive_letter: Removes leading drive letter
    :return: Cleaned path name
    """

    norm = os.path.abspath(os.path.normpath(Path))

    pth = norm.replace("\\", "/")  # go to forward slashes only

    if no_drive_letter and len(pth) > 2 and pth[1] == ":":
        pth = pth[2:]

    return pth


def add_searchfolder(search_folder="", include_subfolders=True):
    """
    Appends search_folder (and by default all its subfolders) to the current python search path.
    Default is current folder and its subfolders.
    Subfolders beginning with "_" are not included.

    :param search_folder: Name of folder to add to sys.path
    :param include_subfolders: True to include all subfolders in sys.path
    :return: None
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


def make_image_filename(imagefile):
    """
    Returns the absolute file imagefile, with forward slashes.
    Appends ".fits" if no extension is included.

    :param str imagefile: Image filename to be expanded
    :return str: Expanded image filename
    """

    if imagefile.endswith(".fits"):
        pass
    elif imagefile.endswith(".fit"):
        pass
    elif not imagefile.endswith(".bin"):
        imagefile += ".fits"

    return fix_path(imagefile)


def parse(String, SetType=0):
    """
    Parse a string into tokens using the standard azcam rules.
    If setType is true, try and set data data type for each token.

    :param str String: String to be parsed into tokens
    :param bool SetType: True to try and set *type* of each token
    :return lsit: list of parsed tokens
    """

    # allow for quotes
    lex = shlex.shlex(String)
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

    if SetType:
        for i, tok in enumerate(tokens):
            t, value = get_datatype(tok)
            tokens[i] = value

    return tokens


def get_datatype(value) -> list:
    """
    Determine the data type for an object and set the type if possible. A string such as "1.23"
    will result in a type "float" and "2" will result in type "int".

    :param value: object to be typed
    :return [type, value]: list of data type as a code and object with that type
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


def prompt(PromptMessage="Enter a string", Default=""):
    """
    Prints a message and waits for user input.

    :param str PromptMessage: String to be printed
    :param str Default:  String to be returned if no value is entered
    :return str: String entered or Default
    """

    Default = str(Default)
    try:
        if Default != "":
            in1 = input(PromptMessage + " [" + Default + "]: ")
        else:
            in1 = input(PromptMessage + ": ")
    except KeyboardInterrupt:
        return ""

    if in1 == "":
        return Default
    else:
        return in1


def check_keyboard(Wait=False):
    """
    Checks user's keyboard for a key press.

    :param bool Wait: True to wait until a key is pressed
    :return str: Key which was pressed or empty string none.
    """

    # TODO: map sequences like 'F1'

    if os.name != "nt":
        raise azcam.AzcamError("Comamnd check_keyboard not supported on this OS")

    loop = 1
    key = ""

    while loop:
        if msvcrt.kbhit():
            key = msvcrt.getch()
            # msvcrt.getch()  # new extra null removed 08Oct18
            try:
                key = key.decode()

                # since the key is byte type, maybe escape sequence so check for more
                # if msvcrt.kbhit():
                #    key1 = msvcrt.getch()
                #    # key = key + key1.decode()
            except UnicodeDecodeError:
                pass
            break
        if not Wait:
            loop = 0

    return key


def show_menu(configs):
    """
    Interative: Show a menu and wait for selection.
    "blank" may be used to display an empty line.
    print() is allowed here as interactive only.

    :param dict configs: Dictionary of strings which are menu items
    :return str: Number of item selected or empty.
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


def set_error_status(ErrorFlag="OK", Message=""):
    """
    Sets the global *errorstatus* list database parameter.

    :param list ErrorFlag: value to set global errorstatus flag. "OK" by default.
    :param str Message: value to set global error status message. Empty by default.
    """

    azcam.db.errorstatus[0] = ErrorFlag
    azcam.db.errorstatus[1] = Message

    return


def get_error_status():
    """
    Returns and clears the global *errorstatus* list database parameter.

    return list: ['OK',''] or ['ERROR','an error string'].
    """

    status = azcam.db.errorstatus
    azcam.db.errorstatus = ["OK", ""]

    return status


def get_image_roi():
    """
    Get the data and noise regions of interest in image image coordinates.
    Check for ROI's in the following order:

    - azcam.db.imageroi if defined
    - display.roi if defined
    """

    # database roi
    if azcam.db.get("imageroi"):
        if azcam.db.imageroi != []:
            return azcam.db.imageroi

    # display.roi
    roi = []

    try:
        reply = azcam.db.display.get_rois(0, "image")
    except AttributeError:
        raise azcam.AzcamError("cannot get ROI - display not found")
    roi.append(reply)
    reply = azcam.db.display.get_rois(1, "image")
    if reply:
        roi.append(reply)
    else:
        roi.append(roi[0])

    return roi


def set_image_roi(roi=[]):
    """
    Set the global image region of interest "db.imageroi".
    If roi is not specified, use display ROI.

    :param list roi: ROI list or []
    :return None:
    """

    # set directly with given value
    if roi != []:
        azcam.db.imageroi = roi
        return

    # use display ROIs
    roi = []
    try:
        reply = azcam.db.display.get_rois(-1, "image")
    except AttributeError:
        raise azcam.AzcamError("cannot set ROI - no display found")

    if not reply:
        raise azcam.AzcamError("could not get display ROI")

    azcam.db.imageroi = reply

    return


def file_browser(Path="", SelectString="*.*", Label=""):
    """
    Filebrowser GUI to select files.  This is the tcl/tk version.

    :param str Path: Starting path for selection
    :param str SelectString: Selection string like [('all files',('*.*'))] for filtering file names or *folder* to select folders
    :param str Label: Dialog box label
    :return list: List of selected files/folders or None
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


def find_file(filename, include_curdir=False):
    """
    Find the absolute filename for a file in the current search path.
    Set include_curdir True to add curdir() to search path.
    Raises FileNotFoundError if file not found.

    :param str filename: Name of file
    :param bool include_curdir: True to include current folder in sys.path
    :return: Cleaned path name

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


def find_file_in_sequence(FileRoot, FileNumber=1):
    """
    Returns the Nth file in an image sequence where N is FileNumber (-1 for first file).
    FileRoot is the the image file root name.
    Returns (filename,sequencenumber).
    """

    currentfolder = azcam.utils.curdir()

    for _, _, files in os.walk(currentfolder):
        break

    for f in files:
        if f.startswith(FileRoot):
            break

    try:
        if not f.startswith(FileRoot):
            raise azcam.AzcamError("image sequence not found")
    except Exception:
        raise azcam.AzcamError("image sequence not found")

    firstfile = azcam.utils.fix_path(os.path.join(currentfolder, f))
    firstsequencenumber = firstfile[-9:-5]
    firstnum = firstsequencenumber
    firstsequencenumber = int(firstsequencenumber)
    sequencenumber = firstsequencenumber + FileNumber - 1
    newnum = "%04d" % sequencenumber
    filename = firstfile.replace(firstnum, newnum)

    return filename, sequencenumber


def make_file_folder(subfolder, increment=True, use_number=False):
    """
    Creates a new subfolder in the current FileFolder.
    subfolder - subfolder name to create
    increment - if True, subfolder name may be incremented to create a unique name (e.g. ptc1, ptc2, ptc3...)
    use_number - if True, starts with '1' after Subfolder name (e.g. report1 not report)
    Returns [currentfolder,newfolder, with newfolder='ERROR' if a failure occurs.
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

    return [currentfolder, newfolder]


def save_imagepars(imagepars={}):
    """
    Save current image parameters.
    imagepars is a dictionary.
    """

    for par in azcam.db.imageparnames:
        imagepars[par] = azcam.db.params.get_par(par)

    return


def restore_imagepars(imagepars, folder=""):
    """
    Restore image parameters from dictionary.
    imagepars is a dictionary set with save_imagepars().
    """

    for par in azcam.db.imageparnames:
        impar = imagepars[par]
        if impar == "":
            impar = '""'
        imagepars[par] = impar
        if par == "imagetitle":
            impar = f'"{impar}"'
        azcam.db.params.set_par(par, impar)

    # return to folder
    if folder != "":
        curdir(folder)

    return


def load_scripts(folder: str) -> None:
    """
    Load all scripts from folder into azcam.db.cli_objects
    """

    folder = fix_path(folder)
    if folder not in sys.path:
        sys.path.append(folder)

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
            mod = importlib.import_module(f"{pfile}")
            func = getattr(mod, pfile)
            azcam.db.cli_objects[pfile] = func
        except Exception as e:
            print(e)
            azcam.AzcamWarning(f"Could not import script {pfile}")

    return


def get_tools(tool_names):
    """
    Return a tool or list of tools.
    For server or console.

    Args:
        tool_names ([type]): [description]

    Returns:
        [type]: [description]
    """

    root = azcam.db

    tools = []
    if type(tool_names) == str:
        tool_names = [tool_names]
    elif type(tool_names) == list:
        pass
    else:
        raise azcam.AzcamError("invalid type for tool_names")

    for tool in tool_names:
        tool1 = root.get(tool)
        if tool1 is not None:
            tools.append(tool1)
        else:
            tools.append(azcam.db.get(tool))

    if len(tools) == 1:
        return tools[0]
    else:
        return tools
