import azcam


def test_parameters():
    for par in azcam.db.parameters:
        value = azcam.db.params.get_par(par)
        print(f"{par}: {value}")
