# Home

AzCam is a software framework for the acquisition and analysis of image data from scientific imaging systems as well as the control of instrumentation. It is intended to be customized for specific hardware, observational, and data reduction requirements.

AzCam is not appropriate for consumer-level cameras and is not intended to have a common API across all systems. It's primary design principle is to allow interfacing to a wide variety of custom instrumentation which is required to acquire and analyze scientific image data.

## Installation

`pip install azcam` 

`pip install azcam-console`  # optional component for CLI and sensor characterization

Or download the latest versions from github at <https://github.com/mplesser/azcam.git> and <https://github.com/mplesser/azcam-console.git>

## Links

  - Main links
    - [AzCam documentation (this site)](https://azcam.readthedocs.io)
    - [AzCamConsole documentation](https://azcam-console.readthedocs.io)
    - [GitHub repos](https://github.com/mplesser)

  - Code details and links
    - [API](api.md)
    - [Classes](classes.md)
    - [Commands](commands.md)
    - [azcamserver](azcamserver.md)
    - [Code Docs](autocode.md)
    - [Advanced concepts](advanced.md)
    - [Focus Command -- server](autocode/focus_server.md)

## Tools

AzCam is based on the concept of *tools* which are the interfaces to both hardware and software code.  Examples of tools are *instrument* which controls instrument hardware, *telescope* which interfaces to a telescope, *linearity* which acquires and analyzes images to determine sensor linearity, and *exposure* which controls a scientific observation by interfacing with a variety of other tools. As an example, the *exposure* tool may move a telescope and multiple filter wheels, control a camera shutter, operate the camera by taking an exposure, display the resultant image, and begin data reduction of that image. There are many supported tools within azcam.

## Operation

There are three main operational modes of AzCam:

  1. A server, usually called [azcamserver](azcamserver.md), which communicates directly or indirectly with system hardware.

  2. A console, usually called *azcamconsole*, which is typically implemented as an IPython command line interface that communicates with *azcamserver* over a socket connection.  It is used to acquire and analyze image data through the command line and python code. This mode requires the `azcam-console` package which is optional.

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

*azcamserver* may also be called in a manner similar to:

```python
python -m azcam_itl.server -i -- -system LVM
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

Example configuration code may be found in the various environment packages with names like `server.py`.

When working in a command line environment, it is often convenient to import commonly used commands into the CLI namespace. This provides direct access to objects and tools such as *db*, *exposure*, *controller*, and various pre-defined shortcuts. To do this, after configuring the environment, execute the commandfrom `from azcam.cli import *`.

And then the code above could be executed as:
```python
from azcam.cli import *
instrument.set_wavelength(450)
exposure.expose(2., 'flat', "a 450 nm flat field image")
```

## AzcamServer

*azcamserver* is the main server application for *azcam*. It usually runs in an IPython window and is mainly used to control data acquistion. 

See [azcamserver](azcamserver.md).

## Code Documentation
Much of the python code is autodocumented from the internal doc strings. See [Code Docs](autocode.md).

## Environments

Some packages act as *environments* to define code and data files used for specific systems. Examples include:

  * [azcam-90prime](https://github.com/mplesser/azcam-90prime) for the UArizona Bok telescope 90prime instrument
  * [azcam-mont4k](https://github.com/mplesser/azcam-mont4k) for the UArizona Mont4k instrument
  * [azcam-vattspec](https://github.com/mplesser/azcam-vattspec) for the VATT VattSpec camera

## Applications
AzCam *applications* are stand-alone programs which utilize AzCam functionality. The most important application is *azcamserver* which defines the tools for a system. Most but not all applications are clients which connect to an *azcamserver* application. These clients may be written in any language. Examples include:

  * [azcam-tool](https://github.com/mplesser/azcam-tool): an exposure control GUI written in National Instruments LabVIEW
  * [azcam-expstatus](https://github.com/mplesser/azcam-expstatus): a small GUI which displays exposure progress 
  * [azcam-imageserver](https://github.com/mplesser/azcam-imageserver) an app to receive and write image data from a remote *azcamserver*

## Command Structure
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
Example URL's which provide exposure status and control are are:

```html
http://hostname:2403/status
```
```html
http://hostname:2403/exptool
```

The value *2403* here is the web server port configured by a specific environment. Not all services may be enabled for a particular system.

## Shortcuts
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
  * *bf* - browse for a file or folder using a GUI.

## Scripts
Scripts are functions contained in python code modules of the same name. They may be loaded automatically during enviroment configuration and can be found in the `db.scripts` dictionary. Scripts defined on the server side are not available as remote commands. An example script to measure system pressures might be:

```python
get_pressures(2.0, "get_pressures.log", 1)
```

## Configuration Folders
There are two important folders which are defined by most environments:

  * *systemfolder* - the main folder where configuration code is located. It is often the root of the environment's python package.
  * *datafolder* - the root folder where data and parameters are saved. Write access is required. It is often similar to `/data/sytemfolder`.

## Help
AzCam is commonly used with IPython.  Help is then available by typing `?xxx`, `xxx?`, `xxx??` or `help(xxx)` where `xxx` is an AzCam class, command, or object instance.

## External Links

Useful external links include:
  
 * IPython <https://ipython.org>
 * Python programming language <https://www.python.org>
