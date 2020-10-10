"""
General support commands for throughout azcam code.
"""

import os
import sys
import shlex
import tkinter
import tkinter.filedialog
import tarfile
import hashlib
import fnmatch
import shutil
from typing import List
import importlib
import pkgutil

# keyboard checking is optional
try:
    import msvcrt
except Exception:
    pass

import azcam


def find_plugins():
    """
    Find all azcam plugins.
    """

    discovered_plugins = {}
    for finder, name, ispkg in pkgutil.iter_modules():
        if name.startswith("azcam_"):
            mod = importlib.import_module(name)
            discovered_plugins[name] = mod

    return discovered_plugins


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

    :param search_folder: Name of folder to add to sys.path
    :param include_subfolders: True to include all subfolders in sys.path
    :return: None
    """

    if search_folder == "":
        search_folder = curdir()

    # search_folder = os.path.normpath(search_folder)
    # search_folder = os.path.abspath(search_folder)
    search_folder = azcam.utils.fix_path(search_folder)

    # append all subfolders of search_folder to current search path
    if search_folder not in sys.path:
        sys.path.append(search_folder)

    if include_subfolders:
        for root, dirs, _ in os.walk(search_folder):
            if dirs:
                for s in dirs:
                    sub = os.path.join(root, s)
                    sub = azcam.utils.fix_path(sub)
                    # sub = os.path.normpath(sub)
                    # sub = os.path.abspath(sub)
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


def get_datatype(value) -> List:
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


def update_pars(write, par_dict=None):
    """
    Update azcam parameters to/from a genpars dictionary.
    write True => write values into dictionary.
    write False => set values from dictionary.
    """

    if par_dict is None:
        if azcam.db.app_type == 1:
            dictname = "azcamserver"
        elif azcam.db.app_type == 2:
            dictname = "azcamconsole"
        else:
            dictname = "azcamserver"
        par_dict = azcam.db.genpars.par_dict[dictname]
    elif type(par_dict) == str:
        par_dict = azcam.db.genpars.par_dict[par_dict]

    keys = par_dict.keys()
    if keys is None:
        return

    if write:
        # run before writing parfile
        # read values into dict
        for parname in par_dict:
            if parname == "wd":
                value = azcam.utils.curdir()
            else:
                value = get_par(parname)
            if value is None:
                value = "None"
            par_dict[parname] = value

    else:
        # after reading parfile
        # set values from dict
        for parname in par_dict:
            value = par_dict[parname]
            if parname == "wd":
                azcam.db.wd = value
            else:
                value = par_dict[parname]
                set_par(parname, value)

    return


def get_par(parameter):
    """
    Return the value of a parameter from the local azcamparameters dictionary.
    Returns None on error.
    """

    parameter = parameter.lower()
    value = None

    # special cases
    if parameter == "imagefilename":
        value = azcam.api.exposure.filename.get_name()
        return value
    elif parameter == "imagetitle":
        value = azcam.api.exposure.get_image_title()
        return value
    elif parameter == "exposuretime":
        value = azcam.api.exposure.get_exposuretime()
        return value
    elif parameter == "exposurecompleted":
        value = azcam.api.exposure.finished()
        return value
    elif parameter == "exposuretimeremaining":
        value = azcam.api.exposure.get_exposuretime_remaining()
        return value
    elif parameter == "pixelsremaining":
        value = azcam.api.exposure.get_pixels_remaining()
        return value
    elif parameter == "camtemp":
        value = azcam.api.tempcon.get_temperatures()[0]
        return value
    elif parameter == "dewtemp":
        value = azcam.api.tempcon.get_temperatures()[1]
        return value
    elif parameter == "temperatures":
        camtemp = azcam.api.tempcon.get_temperatures()[0]
        dewtemp = azcam.api.tempcon.get_temperatures()[1]
        return [camtemp, dewtemp]
    elif parameter == "logcommands":
        value = azcam.db.cmdserver.logcommands
        return value
    elif parameter == "wd":
        value = azcam.utils.curdir()
        return value

    # parameter must be in parameters
    try:
        attribute = azcam.db.parameters[parameter]
    except KeyError:
        azcam.AzcamWarning(
            f"Parameter {parameter} not available for get_par"
        )  # don't print a message
        return None

    tokens = attribute.split(".")
    numtokens = len(tokens)
    if numtokens == 1:
        return None

    object1 = tokens[0]

    if object1 == "db":
        value = getattr(azcam.db, tokens[1], None)
        return value

    # object must be in api
    else:
        obj = azcam.api._get(object1)
        for i in range(1, numtokens):
            obj = getattr(obj, tokens[i])
        value = obj  # last time is value

    return value


def set_par(parameter, value=None):
    """
    Set the value of a parameter in the local azcamparameters dictionary.
    Returns None on error.
    """

    if parameter == "":
        return None

    parameter = parameter.lower()

    # special cases
    if parameter == "imagefilename":
        azcam.api.exposure.filename.set_name(value)
        return None
    elif parameter == "imagetitle":
        if value is None or value == "":
            azcam.api.exposure.set_image_title("")
        else:
            azcam.api.exposure.set_image_title(f"{value}")
        return None
    elif parameter == "exposuretime":
        azcam.api.exposure.set_exposuretime(value)
        return None
    elif parameter == "logcommands":
        azcam.db.cmdserver.logcommands = int(value)
        return None

    # parameter must be in parameters
    try:
        attribute = azcam.db.parameters[parameter]
    except KeyError:
        azcam.AzcamWarning(f"Parameter {parameter} not available for set_par")
        return None

    # object must be on API
    tokens = attribute.split(".")
    numtokens = len(tokens)
    if numtokens < 2:
        azcam.log("%s not valid for parameter %s" % (attribute, parameter))
        return None

    # first try to set value type
    _, value = azcam.utils.get_datatype(value)
    object1 = tokens[0]

    if object1 == "db":
        setattr(azcam.api, tokens[1], value)

    # run through sub-objects
    else:
        obj = azcam.api._get(object1)
        for i in range(1, numtokens - 1):
            obj = getattr(obj, tokens[i])
        # last time is actual object
        setattr(obj, tokens[-1], value)

    return None


def get_attr(object_name, attribute):
    """
    Get the value of an object's attribute.
    Advanced Use only!
    """

    if "." in object_name:
        cmdobject, cmdcommand = object_name.split(".")
        object_id = getattr(getattr(azcam.api, cmdobject), cmdcommand)
    else:
        object_id = getattr(azcam.api, object_name)

    if object_id is None:
        raise azcam.AzcamError(f"Unsupported object: {object_name}")

    return getattr(object_id, attribute)


def get_image_roi():
    """
    Get the data and noise regions of interest in image image coordinates.
    Check for ROI's in the following order:

    - azcam.db.imageroi if defined
    - display.roi if defined
    """

    # database roi
    if azcam.db.imageroi != []:
        return azcam.db.imageroi

    # display.roi
    roi = []

    try:
        reply = azcam.api.display.get_rois(0, "image")
    except AttributeError:
        raise azcam.AzcamError("cannot get ROI - display not found")
    roi.append(reply)
    reply = azcam.api.display.get_rois(1, "image")
    if reply:
        roi.append(reply)
    else:
        roi.append(roi[0])

    return roi


def set_image_roi(roi=[]):
    """
    Set the image region of interest.
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
        reply = azcam.api.display.get_rois(-1, "image")
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


# **************************************************************************************************
# archive commands
# **************************************************************************************************
def archive(foldername="", filetype="tar"):
    """
    Make a tarfile from a folder or file.
    Type can be "tar", "tar.gz", or "zip".
    Return tarfile filename.
    """

    if foldername == "":
        reply = file_browser("", "folder", "Select folder to archive")
        if reply == []:
            raise azcam.AzcamError("no folder or file selected")
        else:
            foldername = reply[0]

    if filetype == "tar.gz":

        filename = foldername + ".tar.gz"
        tar = tarfile.open(filename, "w:gz")
        tar.add(foldername)
        tar.close()

    elif filetype == "tar":

        filename = foldername + ".tar"
        tar = tarfile.open(filename, "w:")
        tar.add(foldername)
        tar.close()

    elif filetype == "zip":

        filename = foldername
        shutil.make_archive(filename, "zip", foldername)
        filename = filename + ".zip"

    else:
        raise azcam.AzcamError("unsupported archive file type")

    return filename


def checksum(filename):
    """
    Make a checksum file in the working folder.
    Return filename and checksum value.
    """

    filechecksum = os.path.basename(filename) + ".sha256"

    # make checksum
    hasher = hashlib.sha256()
    with open(filename, "rb") as afile:
        buf = afile.read()
        hasher.update(buf)
    hashstring = hasher.hexdigest()

    with open(filechecksum, "w") as f:
        f.write(hashstring + "\n")

    return filechecksum, hashstring


def run_script(script_name):
    """
    Runs a script, either with absolute path or assumes it is in the search path.
    This method is exposed as the *Run* command when using IPython.

    :param str script_name: filename of script to run
    :return None:
    """

    # find arguments
    args = ""
    cmd = script_name.split(" ")
    if len(cmd) != 1:
        script_name = cmd[0]
        args = " ".join(cmd[1:])

    # find the file
    # try script_name as-is
    try:
        reply = find_file(script_name, 1)
        script_name = reply
    except FileNotFoundError:
        # try ScriptName.py
        try:
            reply = find_file(script_name + ".py", 1)
            script_name = reply
        except azcam.AzcamError:
            try:
                # try ScriptName.pyw
                reply = find_file(script_name + ".pyw", 1)
                script_name = reply
            except azcam.AzcamError as e:
                raise azcam.AzcamError(f"could not run script {script_name}: {e}")

    # fix the slashes
    sname = os.path.abspath(script_name)
    print(sname)

    # run it with no verbosity
    s = "run %s %s" % (sname, args)
    azcam.db.ip.magic(s)

    return


def cleanup_files(folder=None):
    """
    Cleanup folders after data analysis.
    """

    if folder is None:
        folder = azcam.utils.curdir()

    matches = []
    for root, dirnames, filenames in os.walk(folder):
        for dirname in fnmatch.filter(dirnames, "analysis*"):
            matches.append(os.path.join(root, dirname))

    for t in matches:
        azcam.log(f"Deleting folder {t}")
        shutil.rmtree(t)

    # remove test and temp FITS files
    matches = []
    for root, dirnames, filenames in os.walk(folder):
        for filename in fnmatch.filter(filenames, "test.fits"):
            matches.append(os.path.join(root, filename))
        for filename in fnmatch.filter(filenames, "TempDisplayFile.fits"):
            matches.append(os.path.join(root, filename))

    for t in matches:
        azcam.log(f"Deleting file {t}")
        os.remove(t)

    return


def count_files(path=""):
    """
    Return the number of files in path (default is current folder).
    Folders are not included.
    """

    # move to path if required
    if path != "":
        cd = azcam.utils.curdir()
        azcam.utils.curdir(path)

    nfiles = len([name for name in os.listdir(".") if os.path.isfile(name)])

    # move back
    if path != "":
        azcam.utils.curdir(cd)

    return nfiles


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
