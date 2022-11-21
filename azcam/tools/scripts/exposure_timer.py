"""
exposure timing - server-side
"""

import sys
from timeit import default_timer as timer

import azcam


def exposure_timer():

    azcam.db.tools["exposure"].begin()
    azcam.db.tools["exposure"].integrate()

    start = timer()
    azcam.db.tools["exposure"].readout()
    azcam.db.tools["controller"].flush()
    end = timer()
    print(end - start)

    return


if __name__ == "__main__":
    args = sys.argv[1:]
    exposure_timer(*args)
