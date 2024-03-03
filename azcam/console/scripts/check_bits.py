"""
check_bits.py
Adapted from code by Ian McGreer.
"""

import sys

import numpy as np
from astropy.io import fits as fits_io

import azcam
import azcam.utils


def check_bits(filename: str) -> None:
    """
    Prints the fraction of pixels in an image with each bit set.
    Value should be 0.5 except for high order bits.

    Args:
        filename: image filename
    """

    filename = azcam.utils.make_image_filename(filename)
    fits = fits_io.open(filename)
    print("%5s  " % "", end="")
    for bit in range(16):
        print(f"bit{bit:02} ", end="")
    print("")
    for ext, hdu in enumerate(fits[1:], start=1):
        print(f"HDU{ext:02}  ", end="")
        data = hdu.data.astype(np.int16)
        npix = float(data.size)
        for bit in range(16):
            nbit = np.sum((data & (1 << bit)) > 0)
            fbit = nbit / npix
            print(f"{fbit:5.3f} ", end="")
        print("")


if __name__ == "__main__":
    args = sys.argv[1:]
    check_bits(*args)
