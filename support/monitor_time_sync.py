import subprocess
import time

cmd = "w32tm /query /status"

while 1:
    p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    output, errors = p.communicate()
    output = output.decode("utf-8")
    if output == "":
        break
    output = output.strip()
    resp = output.split("\n")
    print(resp[6])
    time.sleep(10)
