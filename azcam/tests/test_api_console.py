from azcam.api_console import API

api = API()

# test connection to azcamserver as required for most tests
def test_connect(host="localhost", port=2402):
    assert api.serverconn.connect() == True


def test_rcommand(command="get_par version"):
    v = float(api.rcommand(command))
    assert v >= 20


def test_abort_exposure():
    assert api.exposure.abort_exposure() is None


def test_initialize():
    assert api.exposure.initialize() is None
