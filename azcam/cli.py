"""
Used to bring commands into the current namespace.

Usage:  `from azcam.cli import *`

`azcam` as well as items in `db.tools`, `db.shortcuts`, and `db.scripts` are 
added to __all__ here for import into the CLI namespace.
"""

import azcam

# main database object
db = azcam.db

# directly put tools in namespace
try:
    for name in azcam.db.tools:
        globals()[name] = azcam.db.tools[name]
    for name in azcam.db.shortcuts:
        globals()[name] = azcam.db.shortcuts[name]
    for name in azcam.db.scripts:
        globals()[name] = azcam.db.scripts[name]

    __all__ = (
        [x for x in azcam.db.tools]
        + [x for x in azcam.db.shortcuts]
        + [x for x in azcam.db.scripts]
    )
    __all__.append("azcam")
    __all__.append("db")
except Exception:
    pass
