"""
server script to test Mag controller - server-side
"""

import sys

import azcam


def test_mag_controller(cycles=100):

    # loop through boards for communications
    azcam.log("Testing communications...")
    for loop in range(cycles):
        azcam.db.tools["controller"].test_datalink(2, 222, 1)
    azcam.log("Communications to controller OK")

    # reset
    azcam.log("Testing controller reset...")
    for loop in range(cycles):
        azcam.db.tools["controller"].reset()
        azcam.log(f"Controller reset {loop}/{cycles}")

    # reset
    azcam.log("Testing exposures...")
    for loop in range(cycles):
        azcam.db.tools["exposure"].expose()
        azcam.log(f"Exposure {loop}/{cycles}")

    return


if __name__ == "__main__":
    args = sys.argv[1:]
    test_mag_controller(*args)
