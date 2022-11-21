"""
Plot temperatures from logfile when tempcon.log_temps=1.
"""

import sys

import azcam


def plot_log_temps(samplestep=1, tickstep=1):
    """
    Plot camtemp and dewtemp from log file.
    """

    samplestep = int(samplestep)
    tickstep = int(tickstep)

    # setup plot
    fig, ax = azcam.plot.plt.subplots(constrained_layout=True)
    ax.grid(1)
    azcam.plot.plt.title("Temperatures")
    azcam.plot.plt.ylabel("Temperature [C]")
    azcam.plot.plt.xlabel("Time")

    with open("/data/DESI/logs/server.log", "r") as logfile:
        lines = logfile.readlines()

    # read every samplestep templog lines
    linenums = []
    sample = samplestep
    for linenum, line in enumerate(lines):
        if "templog:" in line:
            sample -= 1
            if sample == 0:
                linenums.append(linenum)
                sample = samplestep

    times = []
    camtemps = []
    dewtemps = []
    print("Time\t\tCamtemp\tDewtemp")
    for linenum in linenums:
        s = f"{lines[linenum].strip()}"
        tokens = azcam.utils.parse(s)
        camtemp = float(tokens[-4])
        camtemps.append(camtemp)
        dewtemp = float(tokens[-3])
        dewtemps.append(dewtemp)
        timestamp = tokens[1][:-4]  # remove msec
        times.append(timestamp)

        print(f"{timestamp}\t{camtemp:.1f}\t{dewtemp:.1f}")

        azcam.plot.plt.plot(times, camtemps, azcam.plot.style_lines[0])
        azcam.plot.plt.plot(times, dewtemps, azcam.plot.style_lines[1])

    azcam.plot.plt.xticks(times[::tickstep], rotation=90)  # adjust step size as needed

    return


if __name__ == "__main__":
    args = sys.argv[1:]
    plot_log_temps(*args)
