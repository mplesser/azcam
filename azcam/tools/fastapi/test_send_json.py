import requests

data1 = {
    "tool": "parameters",
    "command": "get_par",
    "args": ["imagetest"],
    "kwargs": {},
}

data2 = {"tool": "parameters", "command": "set_par", "args": ["imagetest", "2222"], "kwargs": {}}

data3 = {
    "tool": "parameters",
    "command": "set_par",
    "args": [],
    "kwargs": {"parameter": "imagetest", "value": 3333},
}

r = requests.post("http://localhost:2403/japi", json=data1)
print(r.status_code, r.json())
