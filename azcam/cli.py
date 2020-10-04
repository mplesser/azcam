"""
cli.py - use to import CLI commands into current namespace

Usage:  from azcam.cli import *
"""
import azcam

for name in azcam.db.cli_cmds:
    globals()[name] = azcam.db.cli_cmds[name]
__all__ = [x for x in azcam.db.cli_cmds.keys()]

__all__.append("azcam")
