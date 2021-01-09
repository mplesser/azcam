# AzCam

*AzCam* is an python package used to control an observation from a scientific imaging camera. It is intended to be used as an interface to multiple non-standard hardware interfaces such as camera controllers, telescopes, instruments, and temperature controllers. It is implemented as the python package *azcam*.

*AzCam* is currently used for Astronomical Research Cameras, Inc. Gen3, Gen2, and Gen1 CCD controllers, Magellan Guider controllers, and the STA Archon controllers. Hadrware-specific code is found in seperate azcam extension packages. 

See *azcam-tool* for a common extension package which implements a GUI used by many observers.

## Documentation

See https://mplesser.github.io/azcam/

See https://github.com/mplesser/azcam-tool.git for the standard GUI used by most telescope observers.

## Installation

`pip install azcam`

Or download the latest version from from github: https://github.com/mplesser/azcam.git.

You may need to install `python3-tk` on Linux systems [`sudo apt-get install python3-tk`].

## Startup and configuration

The *AzCam* server is really only useful with a customized configuration script and  environment which defines the hardware to be controled.  Example scripts named *azcam.config_server_example* and *azcam.config_console_example* are provided for reference. They would be imported into a python or IPython session or use a startup script such as *start_azcam.py* to create a new server or console application. 
