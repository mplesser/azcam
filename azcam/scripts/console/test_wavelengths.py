"""
test wavelength changing
"""

import sys

import azcam


def test_wavelengths(cycles: int = 1):

    cycles = int(cycles)
    wavelength_id = 0

    wavelength = azcam.db.tools["server"].command("instrument.get_wavelengths")

    for wave in wavelength:
        for i in range(cycles):
            print(f"Test cycle {(i+1)}/{cycles} at {wave}")
            azcam.db.tools["instrument"].set_wavelength(wave, wavelength_id)
            print(f"Wavelength read: {azcam.db.tools['instrument'].get_wavelength(wavelength_id)}")

    return


if __name__ == "__main__":
    args = sys.argv[1:]
    test_wavelengths(*args)
