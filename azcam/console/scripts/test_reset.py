"""
reset controller repeatedly
"""

import sys

import azcam


def test_reset(Cycles=10):
    Cycles = azcam.db.parameters.get_local_par(
        "test_reset", "Cycles", "prompt", "Enter number of reset cycles", Cycles
    )
    Cycles = int(Cycles)

    # **************************************************************
    # Loop
    # **************************************************************
    print("Resetting controller...")
    for i in range(Cycles):
        print("Cycle %d of %d" % (i + 1, Cycles))
        azcam.db.tools["exposure"].reset()

    return


if __name__ == "__main__":
    args = sys.argv[1:]
    test_reset(*args)
