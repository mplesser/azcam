"""
correct for system readnoise
"""

import math
import sys

import azcam


def readnoise_correction(system_noise: list[float] = [2.0]) -> list[float]:
    """
    Corrects measured read noise for camera system noise to return just the sensor noise.
    Requires gain.noise to already be set.

    Args:
        system_noise: system noise list in DN

    Returns:
        float: sensor_noise corrected for system_noise in DN
    """

    measured_noise = azcam.db.tools["gain"].noise

    sensor_noise = []
    for chan, mn in enumerate(measured_noise):
        gain = azcam.db.tools["gain"].system_gain[chan]
        sn = math.sqrt(mn ** 2 - system_noise[chan] ** 2)
        sensor_noise.append(sn)

        print(
            f"Chan: {chan:02}\tGain: {gain:3.2f}\tNoise_(DN): {sn:4.2f}\tNoise_(e): {(sn*gain):4.1f}"
        )

    return sensor_noise


if __name__ == "__main__":
    args = sys.argv[1:]
    sensor_noise = readnoise_correction(*args)
