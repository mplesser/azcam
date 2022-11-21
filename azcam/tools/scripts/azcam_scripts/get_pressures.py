import datetime
import sys
import time
from statistics import mean

import azcam


def get_pressures(delay=1.0, logfile="get_pressures.log", plot_type=1):
    """
    Continuously read system pressures until 'q' is pressed.
    Prints date/time, relative seconds, and pressures in Torr.
    Optionally plots (0-2 => none, linear, log) pressures vs times in seconds.
    Returns [pressures], [times]
    """

    plot_type = int(plot_type)

    # setup plot
    if plot_type:
        sub = azcam.plot.plt.subplot(111)
        sub.grid(1)
        azcam.plot.plt.title("Measured Pressure")
        azcam.plot.plt.ylabel("Pressure [Torr]")
        azcam.plot.plt.xlabel("Time [secs]")
        # sub.set_ylim(1.e-7, 1.e-2)

    times = []
    pressures = []

    delay = float(delay)

    timestart = datetime.datetime.now()

    data_txt_hdr = "Seconds\tPressure\tTime"
    with open("Pressure.txt", "a+") as datafile:
        datafile.write("# " + data_txt_hdr + "\n")

        loop = 1
        print("Secs\t\tPressure")
        while loop:

            timenow = datetime.datetime.now()
            s = str(timenow)
            secs = timenow - timestart
            secs1 = secs.total_seconds()
            # timenow = str(timenow)[:-5]
            # secslist = str(secs).split(":")
            # secs1 = float(secslist[0]) * 3600 + float(secslist[1]) * 60 + float(secslist[2])
            times.append(secs1)

            plist = []
            for _ in range(5):
                plist.append(azcam.db.tools["instrument"].get_pressures()[0])
                time.sleep(0.1)
            p = mean(plist)
            pressures.append(p)

            print(f"{secs1:.0f}\t\t{p:.2e}\t\t{s}")

            s = f"{secs1:.0f}\t\t{p:1.2e}\t{timenow}"
            datafile.write(s + "\n")

            if plot_type == 1:
                azcam.plot.plt.plot(times, pressures, "b.")
            elif plot_type == 2:
                azcam.plot.plt.semilogy(times, pressures, "b.-")
            azcam.plot.update()

            if azcam.utils.check_keyboard() == "q":
                break

            azcam.plot.delay(delay)

    return pressures, times


if __name__ == "__main__":
    args = sys.argv[1:]
    pressures, times = get_pressures(*args)
