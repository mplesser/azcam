import sys

def test_console():
    print("I don't do anything yet")
    return

if __name__ == "__main__":
    args = sys.argv[1:]
    test_console(*args)