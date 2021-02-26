import socket

import azcam

# obj_id's which can be accessed remotely
azcam.db.remote_objects = []

# local configuration parameters
from azcam.parameters import Parameters

params = Parameters("azcamserver")
setattr(azcam.db, "params", params)
azcam.db.cli_objects["params"] = params
azcam.db.remote_objects.append("params")

# logging
from azcam.logging import Logger

azcam.db.logger = Logger()
azcam.log = azcam.db.logger.log  # to allow azcam.log()

# save this machine's hostname and ip address
azcam.db.hostname = socket.gethostname()
azcam.db.hostip = socket.gethostbyname(azcam.db.hostname)

# obj_id's which are reset or initialized with exposure
azcam.db.objects_reset = {}
azcam.db.objects_init = {}

# clean namespace (never used directly again)
del azcam.database
del azcam.exceptions
del azcam.logging
