import azcam
from azcam.api_console import API

# api = API()

# test connection to azcamserver as required for most tests
def test_connect(host="localhost", port=2402):
    assert azcam.api.server.connect() == True


def test_rcommand(command="get_par version"):
    v = float(azcam.api.server.rcommand(command))
    assert v >= 20


def test_abort_exposure():
    assert azcam.api.exposure.abort() is None


def test_initialize():
    assert azcam.api.exposure.initialize() is None


def test_parameters():
    for par in azcam.db.parameters:
        value = azcam.api.config.get_par(par)
        print(f"{par}: {value}")
