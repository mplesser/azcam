import azcam

azcam.db.app_type = 1  # server

# errorstatus has client side issue

from .api_server import API

api = API()

# clean namespace (never used directly again)
del azcam.api_server
