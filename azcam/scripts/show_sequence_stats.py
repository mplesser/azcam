"""
evaluate image statistics from a sequence of images.
"""

import sys

from matplotlib.ticker import MaxNLocator

import azcam


def show_sequence_stats(file_root="itl.", starting_sequence=1):
    """
    Calculates stats from a sequence of images.
    Returns data.
    """

    # inputs
    file_root = azcam.db.parameters.get_script_par(
        "show_sequence_stats", "file_root", "prompt", "Enter file root name", file_root
    )
    starting_sequence = azcam.db.parameters.get_script_par(
        "show_sequence_stats",
        "starting_sequence",
        "prompt",
        "Enter starting sequence number",
        starting_sequence,
    )
    starting_sequence = int(starting_sequence)
    SequenceNumber = starting_sequence

    roi = azcam.db.tools["display"].get_rois(-1, "image")[0]  # use only first ROI

    means = []
    sigmas = []
    i = SequenceNumber

    image_numbers = []
    while True:
        # img = file_root + "%.4u" % i
        img = f"{file_root}{i:d}"
        print(img)
        img = azcam.utils.make_image_filename(img)
        print(img)
        if not azcam.fits.file_exists(img):
            break
        stats = azcam.fits.stat(img, roi)
        if len(stats[0]) == 0:
            break

        m = float(stats[0][0])
        sdev = float(stats[1][0])
        try:
            temp = float(azcam.fits.get_keyword(img, "CAMTEMP"))
        except KeyError:
            temp = -999.99
        means.append(m)
        sigmas.append(sdev)
        print("Image %3d, Mean %6.0f, Sigma: %6.02f, Temp: %6.01f" % (i, m, sdev, temp))
        image_numbers.append(i)
        i += 1

    # plot
    if i == SequenceNumber:
        return "no files analyzed"

    fig, ax = azcam.plot.plt.subplots(constrained_layout=True)
    fignum = fig.number
    azcam.plot.move_window(fignum)
    azcam.plot.plt.title("Mean")
    azcam.plot.plt.xlabel("Image Number")
    azcam.plot.plt.ylabel("Mean [DN]")
    ax.xaxis.set_major_locator(MaxNLocator(integer=True))
    ax.grid(1)
    azcam.plot.plt.plot(image_numbers, means)
    azcam.plot.save_figure(fignum, "means.png")

    fig, ax = azcam.plot.plt.subplots(constrained_layout=True)
    fignum = fig.number
    azcam.plot.move_window(fignum)
    azcam.plot.plt.title("Standard Deviation")
    azcam.plot.plt.xlabel("Image Number")
    azcam.plot.plt.ylabel("Sigma [DN]")
    ax.xaxis.set_major_locator(MaxNLocator(integer=True))
    ax.grid(1)
    azcam.plot.plt.plot(image_numbers, sigmas)
    azcam.plot.save_figure(fignum, "sigmas.png")

    # make differences
    means_delta = []
    for j in range(0, len(means) - 1):
        means_delta.append(means[j + 1] - means[j])
    fig, ax = azcam.plot.plt.subplots(constrained_layout=True)
    fignum = fig.number
    azcam.plot.move_window(fignum)
    azcam.plot.plt.title("Mean Differences")
    azcam.plot.plt.xlabel("Image Number")
    azcam.plot.plt.ylabel("Mean [DN]")
    ax.xaxis.set_major_locator(MaxNLocator(integer=True))
    ax.grid(1)
    azcam.plot.plt.plot(image_numbers[:-1], means_delta, "bs")
    azcam.plot.save_figure(fignum, "differences.png")

    azcam.plot.update()
    data = means, sigmas, means_delta

    return data


if __name__ == "__main__":
    args = sys.argv[1:]
    data = show_sequence_stats(*args)
