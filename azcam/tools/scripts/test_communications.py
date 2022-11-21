"""
test system communications.
"""

import sys

import azcam


def test_communications(cycles: int = 100):

    cycles = int(cycles)

    # loop through boards
    print("\nTesting controller board level communications")
    print("PCI board TestDataLink:")
    for loop in range(cycles):
        azcam.db.tools["server"].command("controller.test_datalink 1 111 1 ")
        print("Cycle: %6d/%d" % (loop, cycles - 1), end="\r")
    print()

    print("Timing board TestDataLink:")
    for loop in range(cycles):
        azcam.db.tools["server"].command("controller.test_datalink 2 222 1")
        print("Cycle: %6d/%d" % (loop, cycles - 1), end="\r")
    print()

    print("Utility board TestDataLink:")
    try:
        for loop in range(cycles):
            azcam.db.tools["server"].command("controller.test_datalink 3 333 1")
            print("Cycle: %6d/%d" % (loop, cycles - 1), end="\r")
        print()
    except Exception as e:
        print(e)

    return


if __name__ == "__main__":
    args = sys.argv[1:]
    test_communications(*args)
