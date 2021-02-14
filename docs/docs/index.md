# Home

AzCam is a software framework for the acquisition and analysis of image data from scientific imaging cameras. It is intended to be customized for specific hardware and observational needs. It is is not appropriate for consumer-level cameras and is not intended to have a common API across all possible acquisition and analysis environments.

## Extension Packages
AzCam *extension packages* define additional resources which extend AzCam's functionality. In general some of these packages must be installed to create a useful configuration. Examples include:

  * [azcam-arc](https://github.com/mplesser/azcam-arc) to add support for ARC camera controllers
  * [azcam-archon](https://github.com/mplesser/azcam-archon) to add support for STA Archon camera controllers
  * [azcam-ds9](https://github.com/mplesser/azcam-ds9) to add support for the SAO ds9 image display
  * [azcam-mag](https://github.com/mplesser/azcam-mag) to add support for Magellan/ITL camera controllers
  * [azcam-imageserver](https://github.com/mplesser/azcam-imageserver) to add support for remote image servers
  * [azcam-cryocon](https://github.com/mplesser/azcam-cryocon) to add support for CryoCon temperature controllers
  * [azcam-qhy174](https://github.com/mplesser/azcam-qhy174) to add support for QHY174 CMOS cameras
  * [azcam-testers](https://github.com/mplesser/azcam-testers) to add support for image sensor testing such as QE, CTE, PRNU, etc.
  * [azcam-webserver](https://github.com/mplesser/azcam-webserver) to add support for client web applications
  * [azcam-scripts](https://github.com/mplesser/azcam-scripts) to add general purpose scripts

## Environments
  AzCam *environments* define code and data files used for specific hardware systems.  These are not python packages and may be cloned to any location. Examples include:

  * [azcam-bok](https://github.com/mplesser/azcam-bok) for the UArizona Bok telescope environment
  * [azcam-mont4k](https://github.com/mplesser/azcam-mont4k) for the UArizona Mont4k instrument environment
  * [azcam-vatt](https://github.com/mplesser/azcam-vatt) for the VATT vattspec and vatt4k cameras

## Applications
AzCam *applications* are stand-alone programs which utilize AzCam functionality.  Ofthen they are clients which connect to AzCam server applications. There are multiple clients written in a variety of languages. Examples include:

  * [azcam-tool](https://github.com/mplesser/azcam-tool), a GUI using National Instruments LabVIEW
  * [azcam-status](https://github.com/mplesser/azcam-status), a web-based status page
  * [azcam-exptool](https://github.com/mplesser/azcam-exptool), a web-based exposure control app
  * [azcam-focus](https://github.com/mplesser/azcam-focus), an app for acquiring focus images
  * [azcam-observe](https://github.com/mplesser/azcam-observe) to add support for observing scripts (GUI, web, and command line support is included)

## Configuration
Once configured, the system is controlled by class instances (*objects*) of the hardware modules, such as *controller*, *instrument*, *telescope*, *tempcon*, *system*, and others.  Perhaps the most important object is *exposure*, which controls an actual observation. 

There are three main operational modes of AzCam:
  1. Server-side, usually implemented as the *azcamserver* application, which communicates directly or indirectly to all system hardware.
  2. Console, usually called *azcamconsole*, which is typically implemented as an IPython command window that communicates with *azcamserver* and is used to acquire and analyze image data through the command line and python code.
  3. Applications, as descrived above. Client apps communicate with *azcamserver* over sockets or the web API.

## Operation
While there are multiple pythonic ways to access the object instances in code, they are always accessible from the *database* object `db`. For example, when defined, the `controller` object can be accessed as `db.controller` and the `qe` object can be accessed as `db.qe`.  In most environments these objects are mapped directly into the command line namespace, so in practice commands are executed directly as `object.method`, e.g. `exposure.expose(2.5, "dark", "dark image")`. 

On the python console client side, the `api` object allows communication from the client to an *azcamserver* application over the socket-based command server interface.  The API class typically exposed allows only a limited set of methods to the standard server-side objects. So while `api.exposure.reset` may be available the command `api.exposure.set_video_gain` may not be.  These less commonly used commands are still accessible, but only with lower level code such as `api.server.rcommand("controller.set_video_gain 2")`.

As an example, the code below can be used to set the current system wavelength and take an exposure.  It is assumed the the *azcam_itl* environment has been added to the python search path.

```python
# server-side (azcamserver)
import azcam
import server_itl
wavelength = azcam.db.instrument.set_wavelength(450)
azcam.db.exposure.expose(2., 'flat', "a 450 nm flat field image")

OR

# client-side (azcamconsole)
import azcam
import console_itl
wavelength = azcam.api.instrument.set_wavelength(450)
azcam.api.exposure.expose(2., 'flat', "a 450 nm flat field image")
```

Example configuration code can be found in `azcam.example_server_config` and `azcam.example_console_config`.

When working in a command line environment, it is often convenient to import commonly used commands into the CLI namespace. This provides direct access to objects such as *api*, *db*, *exposure*, *controller*, and various pre-defined shortcuts. To do this, after configuring the environment, execute the command:

```python
from azcam.cli import *
```

And then the code above could be executed as:
```python
instrument.set_wavelength(450)
exposure.expose(2., 'flat', "a 450 nm flat field image")
```

## Help
AzCam is often used with IPython.  Help is then avaialble by typing `?xxx`, `xxx?`, `xxx??` or `help(xxx)` where `xxx` is an AzCam class, command, or object instance.

Useful links include:
* IPython <https://ipython.org>
* Python programming language <https://www.python.org>

## AzCamServer
An AzCam installation often includes a server application to which clients connect via ethernet sockets or the web API.  The clients might be a GUI like *azcam-tool* or a python command line interface using AzCam's console code.

The AzCam command structure provides a fairly uniform interface which can be used from the local command line (CLI), a remote socket connection, or the web interface.  An example for taking a 2.5 second "flat field" exposure is:

Local CLI or script example:

```python
exposure.expose(2.5, 'flat', 'an image title')
```

A remote socket connection example:

```python
exposure.expose 2.5 flat "an image title"
```

Web (http) connection example:

`http://hostname:2403/api/exposure/expose?exposure_time=2.5&image_type=flat&image_title=an+image+title`

Web pages which are served by *azcamserver* are found at URL's such as:

`http://hostname:2403/status` <br>
`http://hostname:2403/exptool`

## Shortcuts
When using IPython, the auto parenthesis mode allows typing commands without 
requiring the normal python syntax of ``command(par1, par2, ...)``. The equivalent 
shortcut/alias syntax is ``command par1 par2``. With IPython in this mode all commands may 
use this syntax.  There are a few useful command line commands defined within AzCam which 
are listed below. Most aliases are implemeted from a command such as `from shortcuts_console import *`.

  * *sav* - save the current parameters to the parameter file
  * *p* - toggle the command line printout of client commands and responses
  * *Run* - run a command found on the python search path, usually for scripts. Note the upper case *R* to distinguish it from IPython's built-in *run* magic command.
  * *gf* - try and go to current image folder.
  * *sf* - try and set the image folder to the current directory.
  * *bf* - browse for a file or folder usign a Tcl/Tk GUI.

## Code Descriptions
The links below describe some of the many classes and commands found in AzCam. Availability depends on configuration.

- [Classes](classes.md)
- [Commands](commands.md)
- [Console API](api_console.md)

## Scripts
Scripts are python code modules which generally contain one function and are available from  the command line or by importing the *azcam-scripts* extension module. They may interact with other *azcam* code if they are configured to be called automatically during enviroment configuration. Note that they may make extensive use of  the *azcam.db* database. By convention scripts use database items named as `db.scriptname_xxx`. As an example, `db.imsnap_resize=2.5"`will shrink a snapped image by 2.5x when the `imsnap` script is called. 

## Configuration Folders
There are several folder names which are usually defined, although their use may be optional for some systems:

  * *systemfolder* - the main folder where configuration code is located
  * *datafolder* - the root folder where data and parameters are saved, write access is required

## Programming

The link below contains information about *azcam* programming and more advanced features.

- [Programming](programming.md)
