"""
cli.py - use to import CLI commands into current namespace

Usage:  from azcam.cli import *
"""
import azcam

for name in azcam.db.cli_tools:
    globals()[name] = azcam.db.cli_tools[name]
__all__ = [x for x in azcam.db.cli_tools.keys()]

__all__.append("azcam")
db = azcam.db
__all__.append("db")
