"""
test ARC controller - server-side
"""

import sys

import azcam


def test_arc_controller(cycles: int = 10):
    """
    Test ARC controller.
    """

    cycles = int(cycles)

    # loop through boards for communications
    azcam.log("Testing controller board level communications...")

    if azcam.db.tools["controller"].pci_board_installed:
        azcam.log("Testing PCI board...")
        for loop in range(cycles):
            azcam.db.tools["controller"].test_datalink(1, 111, 1)
        azcam.log("PCI board OK")

    if azcam.db.tools["controller"].timing_board_installed:
        azcam.log("Testing Timing board...")
        for loop in range(cycles):
            azcam.db.tools["controller"].test_datalink(2, 222, 1)
        azcam.log("Timing board OK")

    if azcam.db.tools["controller"].utility_board_installed:
        azcam.log("Testing Utility board...")
        for loop in range(cycles):
            azcam.db.tools["controller"].test_datalink(3, 333, 1)
        azcam.log("Utility board OK")

    # reset
    azcam.log("Testing controller reset...")
    for loop in range(cycles):
        azcam.db.tools["controller"].reset()
    azcam.log("Controller reset OK")

    # temperature
    if azcam.db.tools["controller"].utility_board_installed:
        azcam.log("Testing controller temperature reading...")
        for loop in range(cycles):
            azcam.db.tools["tempcon"].get_temperatures()
        azcam.log("Controller temerature reading OK")

    return


if __name__ == "__main__":
    args = sys.argv[1:]
    test_arc_controller(int(*args))
