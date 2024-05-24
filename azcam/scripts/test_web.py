import sys
import requests


def test_web(loops=1):

    for loop in range(loops):

        r = requests.get(f"http://localhost:2403/api/instrument/get_wavelength")
        print(r.json()["data"])


if __name__ == "__main__":
    args = sys.argv[1:]
    test_web(*args)
