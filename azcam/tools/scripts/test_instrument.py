"""
test instrument hardware - server-side
"""

import sys
import time

import azcam


def test_instrument(loops=2):
    """
    Test instrument hardware.
    """

    loops = int(loops)

    print("Testing instrument...")

    for i in range(loops):
        print("Reading header")
        reply = azcam.db.tools["instrument"].read_header()
        for x in reply:
            print(f"--> {x}")

        print("Reading wavelength")
        reply = azcam.db.tools["instrument"].get_wavelength()
        print(f"--> {reply:.3f}")

        print("Cycling shutter")
        reply = azcam.db.tools["instrument"].set_shutter(1)
        print("--> Opened")
        time.sleep(1)
        reply = azcam.db.tools["instrument"].set_shutter(0)
        print("--> Closed")

    print("Finished testing")

    return


if __name__ == "__main__":
    args = sys.argv[1:]
    test_instrument(*args)
