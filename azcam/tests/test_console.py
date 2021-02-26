import azcam

# test connection to azcamserver as required for most tests
def test_connect(host="localhost", port=2402):
    server = azcam.get_tools("server")
    assert server.connect() == True


def test_rcommand(command="get_par version"):
    server = azcam.get_tools("server")
    v = float(server.rcommand(command))
    assert v >= 20


def test_abort_exposure():
    assert azcam.db.exposure.abort() is None


def test_initialize():
    assert azcam.db.exposure.initialize() is None


def test_parameters():
    for par in azcam.db.parameters:
        value = azcam.db.params.get_par(par)
        print(f"{par}: {value}")
