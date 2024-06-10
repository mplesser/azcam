"""
Used to bring commands into the current namespace.

Usage:  `from azcam.cli import *`

`azcam` as well as items in `db.cli` are 
added to __all__ here for import into the CLI namespace.
"""

import azcam

# main database object
db = azcam.db

# directly put tools in namespace to be imported with *
try:
    for name in azcam.db.cli:
        globals()[name] = azcam.db.cli[name]

    __all__ = [x for x in azcam.db.cli]
except Exception:
    pass

# __all__.append("azcam")
__all__.append("db")
