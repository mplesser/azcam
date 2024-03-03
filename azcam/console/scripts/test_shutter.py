"""
test shutter - controller or instrument
"""

import sys
import time

import azcam


def test_shutter(number_cyles=5, open_delay=1, close_delay=2, shutter_type="controller"):

    number_cyles = int(number_cyles)
    open_delay = int(open_delay)
    close_delay = int(close_delay)

    for i in range(number_cyles):
        if shutter_type == "controller":
            azcam.db.tools["controller"].set_shutter(1)
        elif shutter_type == "instrument":
            azcam.db.tools["instrument"].set_shutter(1)
        print("open")
        time.sleep(open_delay)

        if shutter_type == "controller":
            azcam.db.tools["controller"].set_shutter(0)
        elif shutter_type == "instrument":
            azcam.db.tools["instrument"].set_shutter(0)
        print("closed")

        if i < number_cyles - 1:
            time.sleep(close_delay)  # don't wait last time

    return


if __name__ == "__main__":
    args = sys.argv[1:]
    test_shutter(*args)
