# UNDER CONSTRUCTION - new monorepo

# AzCam

*azcam* is an python package used to control an observation from a scientific imaging camera. It is intended to be used as an interface to multiple non-standard hardware interfaces such as camera controllers, telescopes, instruments, and temperature controllers.

The *azcam* package is currently used for Astronomical Research Cameras, Inc. Gen3, Gen2, and Gen1 CCD controllers, Magellan Guider controllers, STA Archon controllers, and CMOS cameras using ASCOM. Hadrware-specific code is found in azcam *extension* packages. 

See *azcam-tool* for a common extension package which implements a GUI used by many observers.

## Documentation

See https://mplesser.github.io/azcam/

See https://github.com/mplesser/azcam-tool.git for the standard GUI used by most telescope observers.

## Installation

`pip install azcam`

Or download the latest version from from github: https://github.com/mplesser/azcam.git.

You may need to install `python3-tk` on Linux systems [`sudo apt-get install python3-tk`].

## Startup and configuration

An *azcamserver* process is really only useful with a customized configuration script and environment which defines the hardware to be controlled.  Configuration scripts from existing environments may be used as examples. They would be imported into a python or IPython session or uses a startup script such to create a new server or console application. 

# Tools

Supported tools are listed below.

## Astronomical Research Cameras Controllers

# azcam_arc

*azcam_arc* is an *azcam* extension for Astronomical Research Cameras, Inc. gen1, gen2, and gen3 controllers. See https://www.astro-cam.com/.

## Example Code

The code below is for example only.

### Controller Setup
```python
import azcam.server
from azcam_arc.controller_arc import ControllerArc
controller = ControllerArc()
controller.timing_board = "arc22"
controller.clock_boards = ["arc32"]
controller.video_boards = ["arc45", "arc45"]
controller.utility_board = None
controller.set_boards()
controller.pci_file = os.path.join(azcam.db.systemfolder, "dspcode", "dsppci3", "pci3.lod")
controller.video_gain = 2
controller.video_speed = 1
```

### Exposure Setup
```python
import azcam.server
from azcam_arc.exposure_arc import ExposureArc
exposure = ExposureArc()
exposure.filetype = azcam.db.filetypes["MEF"]
exposure.image.filetype = azcam.db.filetypes["MEF"]
exposure.set_remote_imageserver("localhost", 6543)
exposure.image.remote_imageserver_filename = "/data/image.fits"
exposure.image.server_type = "azcam"
exposure.set_remote_imageserver()
```

## Camera Servers
*Camera servers* are separate executable programs which manage direct interaction with 
controller hardware on some systems. Communication with a camera server takes place over a socket via 
communication protocols defined between *azcam* and a specific camera server program. These 
camera servers are necessary when specialized drivers for the camera hardware are required.  They are 
usually written in C/C++. 

## DSP Code
The DSP code which runs in the ARC controllers is assembled and linked with
Motorola software tools. These tools are typically installed in the folder `/azcam/motoroladsptools/` on a
Windows machine as required by the batch files which assemble and link the code.

While the AzCam application code for the ARC timing board is typically downloaded during
camera initialization, the boot code must be compatible for this to work properly. Therefore
AzCam-compatible DSP boot code may need to be burned into the timing board EEPROMs before use, depending on configuration. 

The gen3 PCI fiber optic interface boards and the gen3 utility boards use the original ARC code and do not need to be changed. The gen1 and gen2 situations are more complex.

For ARC system, the *xxx.lod* files are downlowded to the boards.

## STA Archon Controller

*azcam-archon* is an *azcam* extension for STA Archon controllers. See http://www.sta-inc.net/archon/.

## Example Code

The code below is for example only.

### Controller
```python
import azcam.server
from azcam_archon.controller_archon import ControllerArchon
controller = ControllerArchon()
controller.camserver.port = 4242
controller.camserver.host = "10.0.2.10"
controller.header.set_keyword("DEWAR", "ITL1", "Dewar name")
controller.timing_file = os.path.join(
    azcam.db.systemfolder, "archon_code", "ITL1_STA3800C_Master.acf"
)
```

### Exposure
```python
import azcam.server
from azcam_archon.exposure_archon import ExposureArchon
exposure = ExposureArchon()
filetype = "MEF"
exposure.fileconverter.set_detector_config(detector_sta3800)
exposure.filetype = azcam.db.filetypes[filetype]
exposure.image.filetype = azcam.db.filetypes[filetype]
exposure.display_image = 1
exposure.image.remote_imageserver_flag = 0
exposure.add_extensions = 1
```

## ASCOM

# azcam-ascom

*azcam-ascom* is an *azcam* extension for ASCOM cameras. See https://ascom-standards.org/.

This code has been used for the QHY and ZWO cameras.

## Example Code

The code below is for example only.

### Controller

```python
import azcam.server
from azcam_ascom.controller_ascom import ControllerASCOM
controller = ControllerASCOM()
```

### Exposure

```python
import azcam.server
from azcam_ascom.exposure_ascom import ExposureASCOM
exposure = ExposureASCOM()
filetype = "FITS"
exposure.filetype = exposure.filetypes[filetype]
exposure.image.filetype = exposure.filetypes[filetype]
exposure.display_image = 1
exposure.image.remote_imageserver_flag = 0
exposure.set_filename("/data/zwo/asi1294/image.fits")
exposure.display_image = 1
```

## CryoCon Testerature Controller
# azcam-cryocon

*azcam-cryocon* is an *azcam* extension for Cryogenic Control Systems Inc. (cryo-con) temperature controllers. See http://www.cryocon.com/.

## Example Code

The code below is for example only.

### Temperature Controller

```python
import azcam.server
from azcam_cryocon.tempcon_cryocon24 import TempConCryoCon24
tempcon = TempConCryoCon24()
tempcon.description = "cryoconqb"
tempcon.host = "10.0.0.44"
tempcon.control_temperature = -100.0
tempcon.init_commands = [
"input A:units C",
"input B:units C",
"input C:units C",
"input A:isenix 2",
"input B:isenix 2",
"input C:isenix 2",
"loop 1:type pid",
"loop 1:range mid",
"loop 1:maxpwr 100",
]
```


## SAO Ds9 Image Display Tool

## Purpose

*azcam-ds9* is an *azcam extension* which supports SAO's ds9 display tool running under Windows. See https://sites.google.com/cfa.harvard.edu/saoimageds9.

See https://github.com/mplesser/azcam-ds9-winsupport for support code which may be helpful when displaying images on Windows computers

## Display Class
This class defines Azcam's image display interface to SAO's ds9 image display. 
It is usually instantiated as the *display* object for both server and clients.

Depending on system configuration, the *display* object may be available 
directly from the command line, e.g. `display.display("test.fits")`.

Usage Example:

```python
from azcam_ds9.ds9display import Ds9Display
display = Ds9Display()
display.display("test.fits")
rois = display.get_rois(0, "detector")
print(rois)
```

## Code Documentation

https://mplesser.github.io/azcam-ds9

## Notes

It may be helpful to remove all associations of .fits files in the registry and then only
execute the above batch files.  Do not directly associate .fits files with ds9.exe.

## Exposure Status

# azcam-expstatus

*azcam-expstatus* is an *azcam* extension for displaying exposure status in a Qt (PySide6) window.

## FastAPI

*azcam-fastapi* is an *azcam* extension which adds support for a fastapi-based web server.

## Uage Example

```python
from azcam_fastapi.fastapi_server import WebServer
webserver = WebServer()
webserver.index = f"index_mysystem.html"
webserver.start()
```

## Focus
# azcam-focus

*azcam-focus* is an *azcam* extension to control focus observations used to determine optimal instrument or telescope focus position.

This code is usually executed in the console window although a server-side version is available on some systems.

`focus` is an instance of the *Focus* class.

## Code Documentation

See https://mplesser.github.io/docs/azcam_focus/.

## Code Examples

`focus.command(parameters...)`

```python
focus.set_pars(1, 30, 10)  
focus.run()
```

## Parameters

Parameters may be changed from the command line as:
`focus.number_exposures=7`
or
`focus.set_pars(1.0, 5, 25, 15)`.

<dl>
  <dt><strong>focus.number_exposures = 7</strong></dt>
  <dd>Number of exposures in focus sequence</dd>

  <dt><strong>focus.focus_step = 30</strong></dt>
  <dd>Number of focus steps between each exposure in a frame</dd>

  <dt><strong>focus.detector_shift = 10</strong></dt>
  <dd>Number of rows to shift detector for each focus step</dd>

  <dt><strong>focus.focus_position</strong></dt>
  <dd>Current focus position</dd>

  <dt><strong>focus.exposure_time = 1.0</strong></dt>
  <dd>Exposure time (seconds)</dd>

  <dt><strong>focus.focus_component = "instrument"</strong></dt>
  <dd>Focus component for motion - "instrument" or "telescope"</dd>

  <dt><strong>focus.focus_type = "absolute"</strong></dt>
  <dd>Focus type, "absolute" or "step"</dd>

  <dt><strong>focus.set_pars_called = 1</strong></dt>
  <dd>Flag to not prompt for focus position</dd>

  <dt><strong>focus.move_delay = 3</strong></dt>
  <dd>Delay in seconds between focus moves</dd>
</dl>

## Remote Imageserver
# azcam-imageserver

*azcam-imageserver* is an *azcam* extension which supports sending an image to a remote host running an image server which receives the image.

## Usage

```python
from azcam_imageserver.sendimage import SendImage
sendimage = SendImage()
remote_imageserver_host = "10.0.0.1"
remote_imageserver_port = 6543
sendimage.set_remote_imageserver(remote_imageserver_host, remote_imageserver_port, "azcam")
```

## Magellan Controller
# azcam-mag

*azcam-mag* is an *azcam* extension for OCIW Magellan CCD controllers (ITL version). See http://instrumentation.obs.carnegiescience.edu/ccd/gcam.html.

## Example Code

The code below is for example only.

### Controller

```python
import azcam.server
from azcam_mag.controller_mag import ControllerMag
controller = ControllerMag()
controller.camserver.set_server("some_machine", 2402)
controller.timing_file = os.path.join(azcam.db.datafolder, "dspcode/gcam_ccd57.s")
```
### Exposure

```python
import azcam.server
from azcam_mag.exposure_mag import ExposureMag
exposure = ExposureMag()
filetype = "BIN"
exposure.filetype = exposure.filetypes[filetype]
exposure.image.filetype = exposure.filetypes[filetype]
exposure.display_image = 1
exposure.image.remote_imageserver_flag = 0
exposure.set_filename("/azcam/soguider/image.bin")
exposure.test_image = 0
exposure.root = "image"
exposure.display_image = 0
exposure.image.make_lockfile = 1
```

## Camera Servers

*Camera servers* are separate executable programs which manage direct interaction with controller hardware on some systems. Communication with a camera server takes place over a socket via communication protocols defined between *azcam* and a specific camera server program. These camera servers are necessary when specialized drivers for the camera hardware are required.  They are usually written in C/C++. 

## DSP Code

The DSP code which runs in Magellan controllers is assembled and linked with
Motorola software tools. These tools should be installed in the folder `/azcam/motoroladsptools/` on Windows machines, as required by the batch files which assemble and link the code.

For Magellan systems, there is only one DSP file which is downloaded during initialization. 

Note that *xxx.s* files are loaded for the Magellan systems.

## Observing Scripts
# azcam-observe

*azcam-observe* is an *azcam* extension for running observing scripts. It can be used
with a Qt-based GUI or with a command line interface.

The *observe* command is usually executed from an console window. 

The Qt GUI uses the *PySide2* package.

## Code Documentation

See https://mplesser.github.io/docs/azcam_observe/.

## Usage

`observe.start()` to start the GUI.  A new window will open.

![GUI example after loading script file.](observe_gui.jpg)
*GUI example after loading script file.*

After starting the GUI, Press "Select Script" to find a script to load on disk. 
Then press "Load Script" to populate the table.  The excute, press Run.
You may Pause a script after the current command by pressing the Pause/Resume button. 
Then press the same button to resume the script.  The "Abort Script" button will 
abort the script as soon as possible.

If you have troubles, close the console window and start again.

## GUI Real-time Updates

   You may change a cell in the table to update values while a script is running.  Click in the cell, make the change and press "Enter" (or click elsewhere).
   
## Non-GUI Use

It is still possible to run *observe* without the GUI, although this mode is depricated.
   
## Examples

```python
observe.observe('/azcam/systems/90prime/ObservingScripts/bass.txt',1)
observe.move_telescope_during_readout=1
```

## Parameters

   Parameters may be changed from the command line as:
   
```python
observe.move_telescope_during_readout=1
observe.verbose=1
```

## Script Commands

Always use double quotes (") when needed
Comment lines start with # or !
Status integers are start of a script line are ignored or incremented

```
Observe scripts commands:
obs        ExposureTime ImageType Title NumberExposures Filter RA DEC Epoch
stepfocus  RelativeNumberSteps
steptel    RA_ArcSecs Dec_ArcSecs
movetel    RA Dec Epoch
movefilter FilterName
delay      NumberSecs
test       ExposureTime imagetype Title NumberExposures Filter RA DEC Epoch
print      "hi there"
prompt     "press any key to continue..."
quit       quit script

Example of a script:
obs 10.5 object "M31 field F" 1 u 00:36:00 40:30:00 2000.0 
obs 2.3 dark "a test dark" 2 u
stepfocus 50
delay 3.5
stepfocus -50
steptel 12.34 12.34
movetel 112940.40 +310030.0 2000.0
```

## AzCam Web Tools

*azcam-webtools* is an *azcam* extension which implements various browser-based tools.

## Usage

Open a web browser to http://localhost:2403/XXX where XXX is a toolname, with the appropriate replacements for localhost and the web server port number.

## Tools
 - status - display current exposure status
 - exptool - a simple exposure control tool
