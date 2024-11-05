# Installation Notes

## Environment (optional) - 2024
  - Update python to 3.11.9
  - Update Windows Terminal and PowerShell
    - winget install --id=Microsoft.PowerShell -e 
  - "pip install pickleshare" may be needed for IPython
  - install Visual Studio Code
  - install GIT
  - For ARC controller DSP code modifications, install *motoroladsptools*
  - For Archon controller systems, install *archongui* from STA website.


## AzCam root folder
```shell
mkdir /azcam
cd /azcam
```

## Get Repositories
```shell
git clone https://github.com/mplesser/azcam
git clone https://github.com/mplesser/azcam-console
git clone https://github.com/mplesser/azcam-90prime  # example
git clone https://github.com/mplesser/azcam-tool  # windows only
```

## Install repositories
```shell
pip install -e azcam
pip install -e azcam-console
pip install -e azcam-90prime  # example
```

Optionally install and start xpans from `../azcam/support/ds9`

## Execution examples
```shell
python -i -m azcam_90prime.server
ipython -i -m azcam_90prime.server
ipython --profile azcamserver -i -m azcam_90prime.server -- -archon -nogui
```

## Linux Notes
- upgrade python3 to python 3.11 and add pip
- alias `python` to python3
- create and goto ~/azcam
- `python -m pip install --user -e ./azcam`
- `python -m pip install --user -e ./azcam-console`
- `python -m pip install --user -e ./azcam-90prime`
- `sudo apt install saods9`
- `sudo apt install xpa-tools`

## Windows azcam-tool GUI
- install Labview 2014 runtime for azcam-tool
- install ds9, xpans, and nssm from `../azcam/support`

## Camera Server Windows 10 machines
- install ARC Win10 PCI card driver
- install and configure controller server for proper camera server port

## Example installation sequence for fresh Linux installation (WSL under Windows 11)

```shell
wsl --install -d Ubuntu-24.04

sudo add-apt-repository ppa:deadsnakes/ppa
sudo apt update && sudo apt upgrade -y
sudo apt install python3.11
echo "alias python=/usr/bin/python3.11" >> ~/.bashrc
source ~/.bashrc
python -m pip install --upgrade pip

sudo apt install saods9
sudo apt install xpa-tools

mkdir ~/azcam
mkdir ~/data
cd ~/azcam
git clone https://github.com/mplesser/azcam
git clone https://github.com/mplesser/azcam-console
git clone https://github.com/mplesser/azcam-90prime

ipython --profile azcamserver -i -m azcam_90prime.server -- -archon -nogui
```

## Time Sync
AzCam sets the time written into FITS image headers as close as possible to when an integration would start (just before the shutter opens). This occurs from the `exposure.begin()` method by the `exposure.record_current_times()` method. The keywords set are:

  - "DATE-OBS", "UTC shutter opened"
  - "DATE", "UTC date and time file writtten"
  - "TIME-OBS", "UTC at start of exposure"
  - "UTC-OBS", "UTC at start of exposure"
  - "UT", "UTC at start of exposure"
  - "TIMESYS", "Time system"
  - "TIMEZONE", "Local time zone"
  - "LOCTIME", "Local time at start of exposure"

(Windows OS) For the local machine time to be as accurate as possible, some machines sync time on a fairly short interval (every few minutes). A time sync setup app may be used to set the sync interval and remote time server addresses for the w32tm system time process. This file is typically a shell file named *setup_time_sync* and is found in the azcam environment support folders. It is usually executed automatically when the machine boots (see the shell:startup fodler).
