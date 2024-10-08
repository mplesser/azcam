# Installation Notes

## Environment (optional)
 - Update python to 3.11
 - Update Windows Terminal and PowerShell
 - "pip install pickleshare" may be needed for Ipython

## create azcam root folder
```shell
mkdir /azcam
cd /azcam
```

## Get repositories
```shell
git clone https://github.com/mplesser/azcam
git clone https://github.com/mplesser/azcam-console
git clone https://github.com/mplesser/azcam-90prime
# windows only: 
git clone https://github.com/mplesser/azcam-tool
```

## Install repositories
```shell
pip install -e azcam
pip install -e azcam-console
pip install -e azcam-90prime
```

Optionally install and start xpans from `../azcam/support/ds9`

## Execute examples
```shell
python -i -m azcam_90prime.server
ipython -i -m azcam_90prime.server
ipython --profile azcamserver -i -m azcam_90prime.server -- -archon -nogui
```

## Misc Support Notes

- install python 3.11.9
- install Visual Studio Code
- install GIT
- For ARC controller DSP code, git clone https://github.com/mplesser/motoroladsptools
- winget install --id=Microsoft.PowerShell -e

## Linux Notes
- upgrade python3 to python 3.11 and add pip
- alias `python` to python3
- create and goto ~/azcam
- `python -m pip install --user -e ./azcam`
- `python -m pip install --user -e ./azcam-console`
- `python -m pip install --user -e ./azcam-90prime`
- `sudo apt install saods9`
- `sudo apt install xpa-tools`

## Windows GUI
- install Labview 2014 runtime for azcam-tool
- install xpans and nssm from `azcam/support`
- install SAO ds9 and xpa

## Camera Server Windows 10 machines
- install ARC Win10 PCI card driver
- install and configure controller server for proper port

# Example installation sequence for fresh Linux installation (WSL under Windows 11)

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
