"""
test camera exposures in a loop.
"""

import sys

import azcam


def test_exposures(cycles: int = 10):

    cycles = int(cycles)
    for i in range(cycles):
        print(f"Exposure cycle {(i+1)}/{cycles}")
        azcam.db.tools["exposure"].expose(1, "dark", "test dark")

    return


if __name__ == "__main__":
    args = sys.argv[1:]
    test_exposures(*args)
