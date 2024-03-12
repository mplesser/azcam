# Introduction

AzCam is a software framework for the acquisition and analysis of image data from scientific imaging systems as well as the control of instrumentation. It is intended to be customized for specific hardware, observational, and data reduction requirements.

AzCam is not appropriate for consumer-level cameras and is not intended to have a common API across all systems. It's primary design principle is to allow interfacing to a wide variety of custom instrumentation which is required to acquire and analyze scientific image data.

## Installation

`pip install azcam`

Or download the latest version from from github: https://github.com/mplesser/azcam.git.

You may need to install `python3-tk` on Linux systems [`sudo apt-get install python3-tk`].

# Links

  - Main links
    - [AzCam documentation (this site)](https://azcam.readthedocs.io)
    - [GitHub repos](https://github.com/mplesser)

  - Code details and links
    - [Classes](classes.md)
    - [Commands](commands.md)
    - [Advanced concepts](advanced.md)
    - [Server docs](server.md)

# Tools

AzCam is based on the concept of *tools* which are the interfaces to both hardware and software code.  Examples of tools are *instrument* which controls instrument hardware, *telescope* which interfaces to a telescope, *linearity* which acquires and analyzes images to determine sensor linearity, and *exposure* which controls a scientific observation by interfacing with a variety of other tools. As an example, the *exposure* tool may move a telescope and multiple filter wheels, control a camera shutter, operate the camera by taking an exposure, display the resultant image, and begin data reduction of that image. There are many supported tools within azcam.

# Operation

There are three main operational modes of AzCam:

  1. A server, usually called *azcamserver*, which communicates directly or indirectly with system hardware.

  2. A console, usually called *azcamconsole*, which is typically implemented as an IPython command line interface that communicates with *azcamserver* over a socket connection.  It is used to acquire and analyze image data through the command line and python code.

  3. Applications, which are usually client programs that communicate with *azcamserver* over sockets or the web API.

While there are multiple pythonic ways to access the various tools in code, they are always accessible from the *database* object `db`, which can always be accessed as `azcam.db`. For example, when defined, the `controller` tool can be accessed as `db.tools["controller"]` and the `qe` tool can be accessed as `db.tools["qe"]`.  In most environments these tool are mapped directly into the command namespace, so in practice commands are executed directly as `object.method`, e.g. `exposure.expose(2.5, "dark", "dark image")`.

Tools defined on the server side may or may not be available as remote commands from a client. 

In *azcamconsole*, the available tools usually communication from the console to an *azcamserver* application over a socket interface.  These client-side tools may only expose a limited set of methods as compared to the server-side tools. So while the command `exposure.reset` may be available from a client the command `exposure.set_video_gain` may not be.  These less commonly used commands are still accessible, but only with lower level code such as `server.command("controller.set_video_gain 2")` where `server` is a client's server communication tool.

As an specific example, the code below can be used to set the current system wavelength and take an exposure.  For this example, it is assumed here that the *azcam-itl* environment package has been installed (see [Environments](#azcam-environments) below.).

```python
# server-side (azcamserver)
import azcam
import azcam_itl.server
instrument = azcam.db.tools["instrument"]
exposure = azcam.db.tools["exposure"]
instrument.set_wavelength(450)
wavelength = instrument.get_wavelength()
print(f"Current wavelength is {wavelength}")
exposure.expose(2., 'flat', "a 450 nm flat field image")
```
or

```python
# client-side (azcamconsole)
import azcam
import azam_itl.console
instrument = azcam.db.tools["instrument"]
exposure = azcam.db.tools["exposure"]
instrument.set_wavelength(450)
wavelength = instrument.get_wavelength()
print(f"Current wavelength is {wavelength}")
exposure.expose(2., 'flat', "a 450 nm flat field image")
```

Both *azcamserver* and *azcamconsole* may also be called in a manner similar to:

```python
python -m azcam_itl.server -i -- -system LVM
python -m azcam_itl.console - -- -system LVM
or
ipython -m azcam_itl.server -i -- -system LVM
```

Other examples:
```python
python --profile azcamserver
from azcam_itl import server
from azcam.cli import *
instrument.set_wavelength(450)
exposure.expose(2.5,"flat","a test image")
```

```python
azcam azcam_itl.console -system DESI
```

Example configuration code may be found in the various environment packages with names like `server.py` and `console.py`.

When working in a command line environment, it is often convenient to import commonly used commands into the CLI namespace. This provides direct access to objects and tools such as *db*, *exposure*, *controller*, and various pre-defined shortcuts. To do this, after configuring the environment, execute the commandfrom `from azcam.cli import *`.

And then the code above could be executed as:
```python
from azcam.cli import *
instrument.set_wavelength(450)
exposure.expose(2., 'flat', "a 450 nm flat field image")
```
# Code Documentation
Much fo the python code is autodocumented from the internal doc strings.  See [Code Docs](autocode/autocode.md) and the links within these documents.

# AzCam Environments

Some packages act as *environments* to define code and data files used for specific hardware systems. Examples include:

  * [azcam-90prime](https://github.com/mplesser/azcam-bok) for the UArizona Bok telescope 90prime instrument
  * [azcam-mont4k](https://github.com/mplesser/azcam-mont4k) for the UArizona Mont4k instrument
  * [azcam-vattspec](https://github.com/mplesser/azcam-vattspec) for the VATT VattSpec camera

# AzCam Applications
AzCam *applications* are stand-alone programs which utilize AzCam functionality. The most important application is *azcamserver* which defines the tools for a hardware system. Most but not all applications are clients which connect to an *azcamserver* application. These clients cab be written in any languages.  Some are experimental or still in development. Examples include:

  * [azcam-tool](https://github.com/mplesser/azcam-tool): an exposure control GUI written in National Instruments LabVIEW
  * [azcam-expstatus](https://github.com/mplesser/azcam-expstatus): a small GUI which displays exposure progress 
  * [azcam-imageserver](https://github.com/mplesser/azcam-imageserver) an app to receive and write image data from a remote *azcamserver*

# Command Structure
The AzCam command structure provides a fairly uniform interface which can be used from the local command line (CLI), a remote socket connection, or the web interface.  An example for taking a 2.5 second *flat field* exposure is:

Local CLI or script example:

```python
exposure.expose(2.5, 'flat', 'an image title')
```

A remote socket connection example:

```python
exposure.expose 2.5 flat "an image title"
```

Web (http) connection example:

```html
http://hostname:2403/api/exposure/expose?exposure_time=2.5&image_type=flat&image_title=an+image+title
```
Web support requires an extension package such as *azcam-fastapi* to be installed with *azcamserver*.  Example URL's are:

```html
http://hostname:2403/status
```
```html
http://hostname:2403/exptool
```

The value *2403* here is the web server port configured by a specific environment.

# Shortcuts
When using IPython, auto parenthesis mode allows typing commands without 
requiring the normal python syntax of ``command(par1, par2, ...)``. The equivalent 
shortcut/alias syntax is ``command par1 par2``. With IPython in this mode all commands may 
use this syntax.

There are some simple but useful command line commands which can be optionally installed within
console or server applications as typing shortcuts. Shortcuts are intended for command line use only
and can be found in the `db.shortcuts` dictionary (see `azcam.shortcuts`). Examples include:

  * *sav* - save the current parameters to the parameter file
  * *pp* - toggle the command line printout of client commands and responses command.
  * *gf* - try and go to current image folder.
  * *sf* - try and set the image folder to the current directory.
  * *bf* - browse for a file or folder using a Tcl/Tk GUI.

# Scripts
Scripts are functions contained in python code modules of the same name. They may be loaded automatically during enviroment configuration and can be found in the `db.scripts` dictionary. Scripts defined on the server side are not available as remote commands. An example script to measure system pressures might be:

```python
get_pressures(2.0, "get_pressures.log", 1)
```

# Configuration Folders
There are two important folders which are defined by most environments:

  * *systemfolder* - the main folder where configuration code is located. It is often the root of the environment's python package.
  * *datafolder* - the root folder where data and parameters are saved. Write access is required. It is often similar to `/data/sytemfolder`.

# Help
AzCam is commonly used with IPython.  Help is then available by typing `?xxx`, `xxx?`, `xxx??` or `help(xxx)` where `xxx` is an AzCam class, command, or object instance.

# External Links

Useful external links include:
  
 * IPython <https://ipython.org>
 * Python programming language <https://www.python.org>

# Configuration and startup

An *azcamserver* process is really only useful with a customized configuration script and environment which defines the hardware to be controlled.  Configuration scripts from existing environments may be used as examples. They would be imported into a python or IPython session or uses a startup script such to create a new server or console application.

An example code snippet to start *azcamserver* when using the *azcam-itl environment* is:

```python
# server-side (azcamserver)
import azcam
import azcam_itl.server
instrument = azcam.db.tools["instrument"]
exposure = azcam.db.tools["exposure"]
instrument.set_wavelength(450)
wavelength = instrument.get_wavelength()
print(f"Current wavelength is {wavelength}")
exposure.expose(2., 'flat', "a 450 nm flat field image")
```

# AzCam Server

*azcamserver* is the main server application for the *azcam* acquisition and analysis package. It usually runs in an IPython window and is mainly used to control data acquistion. 

## Documentation

See https://azcam.readthedocs.io/.

## Configuration and startup 

An example code snippet to start an *azcamserver* process is:

```
python -i -m azcam.server.server_mock
or
ipython -m azcam.server.server_mock --profile azcamserver -i
```

and then in the IPython window:

```python
instrument.set_wavelength(450)
wavelength = instrument.get_wavelength()
print(f"Current wavelength is {wavelength}")
exposure.expose(2., 'flat', "a 450 nm flat field image")
```

# AzCam Console

*azcamconsole* is a console application for the *azcam* acquisition and analysis package. It usually runs in an IPython window and is used to both acquire and analyze data in a python scripting environment.

## Configuration and startup 

An example code snippet to start an *azcamconsole* process is:

```
ipython -m azcam_itl.console --profile azcamconsole -i -- -system DESI
```

and then in the IPython window:

```python
instrument.set_wavelength(450)
wavelength = instrument.get_wavelength()
print(f"Current wavelength is {wavelength}")
exposure.expose(2., 'flat', "a 450 nm flat field image")
```

# Observe

The *observe* tool supports running observing scripts. It can be used
with a Qt-based GUI or with a command line interface.

The `observe.observe()` command executed from a console window uses the CLI interface. The `observe` command executed from a terminal or icon starts the Qt GUI.

The Qt GUI uses the *PySide6* package.

## Usage

`observe` to start the GUI from a terminal.  A new window will open.

Use `observe.observe()` from an azcam console window to run the CLI version.

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

## Misc

Import observe for observing command use:
```
from azcam.server.tools.observe.observe import Observe
```

```
# this is a single line comment python style
```

This block shows some direct commands
```
observe = Observe()
observe.test(et=1.0,object="flat", filter="400")
observe.comment("a different new comment 123")
observe.delay(1)
observe.obs(et=2.0,object="zero", filter="400", dec="12:00:00.23", ra="-23:34:2.1")
```

This block shows an example of commands using python flow control
```
alt_start = 0.0
step_size = 0.01
num_steps = 100
for count in range(num_steps):
    altitude = alt_start + count*step_size
    observe.steptel(altitude=altitude)
    print(f"On loop {count} altitude is {altitude}")
```

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

## Observe Script Commands

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
