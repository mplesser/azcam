"""
AzCam is a software framework for the acquisition and analysis of image data
from scientific imaging systems as well as the control of instrumentation.
It is intended to be customized for specific hardware, observational,
and data reduction requirements.
"""

from importlib import metadata

__version__ = metadata.version(__package__)
__version_info__ = tuple(int(i) for i in __version__.split(".") if i.isdigit())

import typing
from typing import List, Dict

# import here so future importing is not required
from azcam.functions import fits
from azcam.functions import utils
from azcam.functions import plot
from azcam.exceptions import AzcamError, AzcamWarning

# initially azcam.log() is print(), will usually be overwritten
log: typing.Callable = print

import azcam.database

db = azcam.database.AzcamDatabase()
"""database"""

mode = "unknown"
"""azcam mode, usually server or console"""

# image pardict
pardict: dict = {
    # exposure
    "autotitle": "exposure.auto_title",
    "imagetype": "exposure.image_type",
    "exposureflag": "exposure.exposure_flag",
    "exposuresequencedelay": "exposure.exposure_sequence_delay",
    "exposuresequencetotal": "exposure.exposure_sequence_total",
    "exposuresequencenumber": "exposure.exposure_sequence_number",
    "exposuresequenceflush": "exposure.exposure_sequence_flush",
    "exposureupdatingheader": "exposure.updating_header",
    "isexposuresequence": "exposure.is_exposure_sequence",
    "displayimage": "exposure.display_image",
    "sendimage": "exposure.send_image",
    "savefile": "exposure.save_file",
    "flusharray": "exposure.flush_array",
    "tdidelay": "exposure.tdi_delay",
    "tdimode": "exposure.tdi_mode",
    "pardelay": "exposure.par_delay",
    "exposureguidemode": "exposure.guide_mode",
    "exposureguidestatus": "exposure.guide_status",
    "lastfilename": "exposure.last_filename",
    "imagefiletype": "exposure.filetype",
    "imageheaderfile": "exposure.imageheaderfile",
    "imagetest": "exposure.test_image",
    "imagesequencenumber": "exposure.sequence_number",
    "imageautoincrementsequencenumber": "exposure.auto_increment_sequence_number",
    "imageincludesequencenumber": "exposure.include_sequence_number",
    "imageautoname": "exposure.autoname",
    "imageoverwrite": "exposure.overwrite",
    "imageroot": "exposure.root",
    "imagefolder": "exposure.folder",
    "remote_imageserver_host": "sendimage.remote_imageserver_host",
    "remote_imageserver_port": "sendimage.remote_imageserver_port",
    # image
    "imagesizex": "exposure.image.focalplane.numcols_image",
    "imagesizey": "exposure.image.focalplane.numrows_image",
    "numpiximage": "exposure.image.focalplane.numpix_image",
    "colbin": "exposure.image.focalplane.col_bin",
    "rowbin": "exposure.image.focalplane.row_bin",
    "firstcol": "exposure.image.focalplane.first_col",
    "firstrow": "exposure.image.focalplane.first_row",
    "lastcol": "exposure.image.focalplane.last_col",
    "lastrow": "exposure.image.focalplane.last_row",
    # instrument
    "instrumentenabled": "instrument.enabled",
    "instrumentfocus": "instrument.focus_position",
    # telescope
    "telescopeenabled": "telescope.enabled",
    "telescopefocus": "telescope.focus_position",
    # tempcon
    "controltemperature": "tempcon.control_temperature",
    "camtemp": "tempcon.temperatures[0]",
    "dewtemp": "tempcon.temperatures[1]",
    # controller
    "utilityboardinstalled": "controller.utility_board_installed",
    "pciboardinstalled": "controller.pci_board_installed",
    "timingboardinstalled": "controller.timing_board_installed",
    "videogain": "controller.video_gain",
    "videospeed": "controller.video_speed",
    "usereadlock": "controller.use_read_lock",
    "pcifile": "controller.pci_file",
    "timingfile": "controller.timing_file",
    "utilityfile": "controller.utility_file",
    "timingboard": "controller.timing_board",
    "videoboards": "controller.video_boards",
    "clockboards": "controller.clock_boards",
    # database
    "systemname": "db.systemname",
    "abortflag": "db.abortflag",
    "verbosity": "db.verbosity",
    "hostname": "db.hostname",
}
"""dict of general parameters"""

imageparnames: List[str] = [
    "imageroot",
    "imageincludesequencenumber",
    "imageautoname",
    "imageautoincrementsequencenumber",
    "imagetest",
    "imagetype",
    "imagetitle",
    "imageoverwrite",
    "imagefolder",
]
"""image parameters"""

exposureflags: Dict[str, int] = {
    "NONE": 0,
    "EXPOSING": 1,
    "ABORT": 2,
    "PAUSE": 3,
    "RESUME": 4,
    "READ": 5,
    "PAUSED": 6,
    "READOUT": 7,
    "SETUP": 8,
    "WRITING": 9,
    "GUIDEERROR": 10,
    "ERROR": 11,
}
"""exposure flags"""

# clean namespace
del metadata
del typing
