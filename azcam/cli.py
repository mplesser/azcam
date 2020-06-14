"""
cli.py - use to import CLI commands into current namespace

Usage:  from azcam.cli import *
"""

from azcam import db

for name in db.cli_cmds:
    globals()[name] = db.cli_cmds[name]
__all__ = [x for x in db.cli_cmds.keys()]
