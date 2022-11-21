@echo off
rem Starts AzCamImageWriter under Windows.

set ROOT="..\azcam_imageserver\"
start /high /min /d %ROOT% "AzCamImageWriter" python imageserver.py -l 6543 -v
