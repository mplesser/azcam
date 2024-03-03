"""
show keywords from a sequence of images.
"""

import sys

import azcam
import azcam.utils
import azcam.fits


def show_sequence_keywords(FileRoot="itl.", StartingSequence=1, keyword="OBJECT"):
    """
    Calculates stats from a sequence of images.
    Returns data.
    """

    data = []

    # inputs
    FileRoot = azcam.db.parameters.get_local_par(
        "show_sequence_keywords", "FileRoot", "prompt", "Enter file root name", FileRoot
    )
    StartingSequence = azcam.db.parameters.get_local_par(
        "show_sequence_keywords",
        "StartingSequence",
        "prompt",
        "Enter starting sequence number",
        StartingSequence,
    )
    keyword = azcam.db.parameters.get_local_par(
        "show_sequence_keywords", "keyword", "prompt", "Enter keyword name", keyword
    )
    StartingSequence = int(StartingSequence)
    SequenceNumber = StartingSequence
    i = SequenceNumber

    while True:
        img = FileRoot + "%.4u" % i
        img = azcam.utils.make_image_filename(img)
        if not azcam.fits.file_exists(img):
            break
        reply = azcam.fits.get_keyword(img, keyword)
        value = reply

        data.append(value)

        # print('Image %3d: %s = %s' % (i,keyword,str(value)))
        i += 1

    return data


if __name__ == "__main__":
    args = sys.argv[1:]
    data = show_sequence_keywords(*args)
