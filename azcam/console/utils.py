"""
# utils.py

*azcam.utils* contains general purpose support commands used throughout azcam.
"""

import os
import sys
import tkinter
import tkinter.filedialog

if os.name == "nt":
    import winsound

import azcam
import azcam.exceptions


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
            raise azcam.exceptions.AzCamError("image sequence not found")
    except Exception:
        raise azcam.exceptions.AzCamError("image sequence not found")

    firstfile = azcam.utils.fix_path(os.path.join(currentfolder, f))
    firstsequencenumber = firstfile[-9:-5]
    firstnum = firstsequencenumber
    firstsequencenumber = int(firstsequencenumber)
    sequencenumber = firstsequencenumber + file_number - 1
    newnum = "%04d" % sequencenumber
    filename = firstfile.replace(firstnum, newnum)

    return (filename, sequencenumber)


def make_file_folder(
    subfolder: str, increment: bool = True, use_number: bool = False
) -> tuple:
    """
    Creates a new subfolder in the current FileFolder.

    Args:
        subfolder: subfolder name to create
        increment: - if True, subfolder name may be incremented to create a unique name
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
            raise azcam.exceptions.AzCamError("could not make new subfolder")
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
                raise azcam.exceptions.AzCamError("could not make subfolder")

    newfolder = azcam.utils.fix_path(newfolder)

    return (currentfolder, newfolder)


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
        raise azcam.exceptions.AzCamError("cannot get ROI - display not found")
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
        raise azcam.exceptions.AzCamError("cannot set ROI - no display found")

    if not reply:
        raise azcam.exceptions.AzCamError("could not get display ROI")

    azcam.db.imageroi = reply

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


def file_browser(Path: str = "", SelectString: str = "*.*", Label: str = "") -> list:
    """
    Filebrowser GUI to select files.  This is the tcl/tk version.

    Args:
        Path: Starting path for selection.
        SelectString: Selection string like [('all files',('*.*'))] or *folder* to select folders.
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
