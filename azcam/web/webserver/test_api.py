import requests

if 1:
    data1 = {
        "tool": "parameters",
        "command": "get_par",
        "args": ["imagetest"],
        "kwargs": {},
    }

    data2 = {
        "tool": "parameters",
        "command": "set_par",
        "args": ["imagetest", "2222"],
        "kwargs": {},
    }

    data3 = {
        "tool": "parameters",
        "command": "set_par",
        "args": [],
        "kwargs": {"parameter": "imagetest", "value": 3333},
    }

    data4 = {
        "tool": "parameters",
        "command": "get_par",
        "args": ["imagetest"],
        "kwargs": {},
    }

    r = requests.post("http://localhost:2403/api", json=data1)
    print(r.status_code, r.json())

    r = requests.post("http://localhost:2403/api", json=data2)
    print(r.status_code, r.json())

    r = requests.post("http://localhost:2403/api", json=data3)
    print(r.status_code, r.json())

    r = requests.post("http://localhost:2403/api", json=data4)
    print(r.status_code, r.json())

    r = requests.get("http://localhost:2403/api/exposure/get_status")
    print(r.status_code, r.json())
