import datetime
import sys

import azcam

from .show_sequence_keywords import show_sequence_keywords

# val1=abs((val1-datetime.datetime(1970,1,1)).total_seconds())


def plot_keywords():
    """
    Plot header time keywords values.
    """

    data_strings = show_sequence_keywords("itl.ZERO.", 2, "UTC-OBS")
    start = datetime.datetime.strptime(data_strings[0], "%H:%M:%S.%f")
    data = []
    last = start

    for i, val in enumerate(data_strings):
        val1 = datetime.datetime.strptime(val, "%H:%M:%S.%f")
        val1 = (val1 - start).total_seconds()
        if val1 == last:
            print("ERROR same time found", i, data_strings[i])
        last = val1
        data.append(val1)

    azcam.plot.plt.plot(data)

    return


if __name__ == "__main__":
    args = sys.argv[1:]
    plot_keywords(*args)
