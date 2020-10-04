"""
API interface for azcamserver.
"""

import sys

import azcam
from azcam.api_azcam import api

azcam.db.cli_cmds["api"] = api
