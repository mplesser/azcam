import datetime
import sys
import time

import azcam
import azcam.utils
import azcam.console.plot
import azcam.console


def get_temperatures(delay=10.0, logfile="get_temperatures.log", plottemps=1):
    """
    Continuously read system temperatures until 'q' is pressed.
    Prints date/time, relative seconds, and temperatures in Celsius.
    Optionally plots temperatures vs times in seconds.
    Returns [temps], [times]
    """

    plot_range = [-200, 30]

    # inputs
    # delay = azcam.db.parameters.get_local_par(
    #     "get_temps", "delay", "prompt", "Enter delay time in seconds", delay
    # )
    delay = azcam.db.parameters.get_par("delay", "get_temps")
    if delay is None:
        delay = 1.0
    delay = azcam.utils.prompt("Enter delay time in seconds", delay)
    azcam.db.parameters.set_par("delay", delay, "get_temps")

    return

    logfile = azcam.db.parameters.get_local_par(
        "get_temps",
        "logfile",
        "prompt",
        "Enter log file name or N to skip logging",
        logfile,
    )
    if logfile == ".":
        reply = azcam.console.utils.file_browser(logfile, [("all files", ("*.*"))])
        logfile = reply[0]

    plottemps = azcam.db.parameters.get_local_par(
        "get_temps", "plottemps", "prompt", "Enter 1 to plot data", plottemps
    )

    delay = float(delay)
    plottemps = int(plottemps)

    # display header and open log file
    s = "#Date and Time         Secs   Temperatures"
    print(s)
    if logfile.lower() != "n":
        lfile = open(logfile, "w")
        lfile.write(s + "\n")

    timestart = datetime.datetime.now()

    if plottemps:
        fig = azcam.console.plot.plt.figure()
        fignum = fig.number
        azcam.console.plot.move_window(fignum)
        sub = azcam.console.plot.plt.subplot(111)
        sub.grid(1)
        azcam.console.plot.plt.title("System Temperatures")
        azcam.console.plot.plt.ylabel("Temperature [C]")
        azcam.console.plot.plt.xlabel("Time [secs]")
        sub.set_ylim(plot_range[0], plot_range[1])
        azcam.console.plot.update()

    times = []
    temps = []

    while 1:
        key = azcam.utils.check_keyboard()
        if key == "q":
            break

        curtemps = azcam.db.tools["tempcon"].get_temperatures()
        ntemps = len(curtemps)

        temps.append(curtemps)
        timenow = datetime.datetime.now()
        secs = timenow - timestart
        timenow = str(timenow)[:-5]
        secslist = str(secs).split(":")
        secs1 = float(secslist[0]) * 3600 + float(secslist[1]) * 60 + float(secslist[2])
        times.append(secs1)
        s = "%s  %.1f    %-6.1f   %-6.1f" % (
            timenow,
            secs1,
            curtemps[0],
            curtemps[1],
        )
        print(s)

        if logfile.lower() != "n":
            lfile.write(s + "\n")
            lfile.flush()

        # plot data
        if plottemps:
            for tnum in range(ntemps):
                azcam.console.plot.plt.plot(
                    times,
                    [t[tnum] for t in temps],
                    azcam.console.plot.style_lines[tnum],
                )
            azcam.console.plot.update()

        # delay
        azcam.console.plot.delay(delay)

    if plottemps:
        azcam.console.plot.save_figure(fignum, "get_temperatures.png")

    # close
    if logfile.lower() != "n":
        lfile.close()

    return temps, times


if __name__ == "__main__":
    args = sys.argv[1:]
    temps, times = get_temperatures(*args)
