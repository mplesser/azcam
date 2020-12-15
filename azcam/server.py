import azcam

azcam._app_type = 1  # server

# errorstatus has client side issue

from .api_server import API

api = API()

# database configuration
setattr(api, "db", azcam.db)
azcam.db.cli_cmds["db"] = azcam.db

# clean namespace (never used directly again)
del azcam.api_server
