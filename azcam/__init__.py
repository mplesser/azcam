"""
azcam observation control application.
"""

from types import ModuleType as __module_type__
import socket

# bring these into azcam namespace so importing not required
from .exceptions import AzcamError, AzcamWarning
from . import utils

# helpful shortcuts for namespace
from .database import db
from .utils import log
from . import fits, report, plot, params

# save this machine's hostname and ip address
db.hostname = socket.gethostname()
db.hostip = socket.gethostbyname(db.hostname)

#: parameter dictionary
db.parameters = {
    "autotitle": "exposure.auto_title",
    "imagetype": "exposure.image_type",
    "exposureflag": "exposure.exposure_flag",
    "exposuresequencedelay": "exposure.exposure_sequence_delay",
    "exposuresequencetotal": "exposure.exposure_sequence_total",
    "exposuresequencenumber": "exposure.exposure_sequence_number",
    "exposuresequenceflush": "exposure.exposure_sequence_flush",
    "exposureupdatingheader": "exposure.updating_header",
    "writewcs": "exposure.image.write_wcs",
    "isexposuresequence": "exposure.is_exposure_sequence",
    "displayimage": "exposure.display_image",
    "savefile": "exposure.save_file",
    "flusharray": "exposure.flush_array",
    "tdidelay": "exposure.tdi_delay",
    "tdimode": "exposure.tdi_mode",
    "pardelay": "exposure.par_delay",
    "remoteimageserverflag": "exposure.image.remote_imageserver_flag",
    "remote_imageserver_host": "exposure.image.remote_imageserver_host",
    "remote_imageserver_port": "exposure.image.remote_imageserver_port",
    "remote_imageserver_filename": "exposure.image.remote_imageserver_filename",
    "exposureguidemode": "exposure.guide_mode",
    "exposureguidestatus": "exposure.guide_status",
    "imagetest": "exposure.filename.test_image",
    "imagesequencenumber": "exposure.filename.sequence_number",
    "imageautoincrementsequencenumber": "exposure.filename.auto_increment_sequence_number",
    "imageincludesequencenumber": "exposure.filename.include_sequence_number",
    "imageautoname": "exposure.filename.autoname",
    "imageoverwrite": "exposure.filename.overwrite",
    "imageroot": "exposure.filename.root",
    "imagefolder": "exposure.filename.folder",
    "imagefiletype": "exposure.filetype",
    "imageheaderfile": "exposure.imageheaderfile",
    "imagesizex": "exposure.image.focalplane.numcols_image",
    "imagesizey": "exposure.image.focalplane.numrows_image",
    "numpiximage": "exposure.image.focalplane.numpix_image",
    "colbin": "exposure.image.focalplane.col_bin",
    "rowbin": "exposure.image.focalplane.row_bin",
    "firstcol": "exposure.image.focalplane.first_col",
    "firstrow": "exposure.image.focalplane.first_row",
    "lastcol": "exposure.image.focalplane.last_col",
    "lastrow": "exposure.image.focalplane.last_row",
    "instrumentname": "instrument.name",
    "instrumentenabled": "instrument.enabled",
    "telescopename": "telescope.name",
    "telescopeenabled": "telescope.enabled",
    "telescopefocus": "telescope.focus_position",
    "instrumentfocus": "instrument.focus_position",
    "controltemperature": "tempcon.control_temperature",
    "camtemp": "tempcon.temperatures[0]",
    "dewtemp": "tempcon.temperatures[1]",
    "utilityboardinstalled": "controller.utility_board_installed",
    "videogain": "controller.video_gain",
    "videospeed": "controller.video_speed",
    "usereadlock": "controller.use_read_lock",
    "pcifile": "controller.pci_file",
    "timingfile": "controller.timing_file",
    "utilityfile": "controller.utility_file",
    "timingboard": "controller.timing_board",
    "videoboards": "controller.video_boards",
    "clockboards": "controller.clock_boards",
    "dewarname": "dewar.name",
    "systemname": "db.systemname",
    "systemid": "db.systemid",
    "version": "db.version",
    "abortflag": "db.abortflag",
    "errorstatus": "db.errorstatus",
    "verbosity": "db.verbosity",
    "hostname": "db.hostname",
}

# cleanup namespace
del database, socket, exceptions
