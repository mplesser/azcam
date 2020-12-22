import azcam


def test_parameters():
    for par in azcam.db.parameters:
        value = azcam.api.config.get_par(par)
        print(f"{par}: {value}")
