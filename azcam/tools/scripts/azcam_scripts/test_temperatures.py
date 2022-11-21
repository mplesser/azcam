"""
test temperature controller.
"""

import sys

import azcam


def test_temperatures(number_cycles: int = 10):
    """
    Test reading temperatures from temperature controller.
    """

    number_cycles = int(number_cycles)
    control_temp = azcam.db.tools["tempcon"].get_control_temperature()
    print(f"Control temperature is {control_temp:.03f}")

    for loop in range(number_cycles):

        temps = azcam.db.tools["tempcon"].get_temperatures()

        tempstring = repr(temps)

        print(f"Temperatures read: {tempstring}")

    return


if __name__ == "__main__":
    args = sys.argv[1:]
    test_temperatures(*args)
