"""
test filter changing
"""

import sys

import azcam


def test_filters(cycles: int = 2, filter_id: int = 0):

    cycles = int(cycles)

    filters = azcam.db.tools["server"].command(f"instrument.get_filters {filter_id}")
    print(f"Available filters are: {filters}")

    for filter_name in filters:
        for i in range(cycles):
            print(f"Test cycle {(i+1)}/{cycles} at {filter_name}")
            azcam.db.tools["instrument"].set_filter(filter_name, filter_id)
            print(f"Filter read: {azcam.db.tools['instrument'].get_filter(filter_id)}")

    return


if __name__ == "__main__":
    args = sys.argv[1:]
    test_filters(*args)
