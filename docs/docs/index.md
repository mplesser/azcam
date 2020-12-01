# Home

AzCam is a software environment for the acquisition and analysis of image data from scientific imaging cameras. It is intended to be extensively customized for specific hardware and observational needs. It is is not appropriate for consumer-level cameras and is not intended to have a common API across all possible acquisition and analysis environments.

Most of AzCam's functionality is available only after installing *extension packages* which contain configuration and hardware code that define a system's hardware resources.  Examples include:

  * [azcam-arc](https://github.com/mplesser/azcam-arc) for ARC camera controllers
  * [azcam-archon](https://github.com/mplesser/azcam-archon) for STA Archon camera controllers
  * [azcam-ds9](https://github.com/mplesser/azcam-ds9) for SAO ds9 image display
  * [azcam-bok](https://github.com/mplesser/azcam-bok) for the UArizona Bok telescope environment
  * [azcam-mont4k](https://github.com/mplesser/azcam-mont4k) for the UArizona Mont4k instrument environment
   
Once configured, the system is controlled by class instances (*objects*) of the hardware modules, such as *controller*, *instrument*, *telescope*, *tempcon*, *system*, and others.  Perhaps the most important object is *exposure*, which controls an actual observation.  Most of these objects are exposed through the *azcam.api* object.  There is also a database of parameters maintained in the *azcam.db* object 

There are two three main operational modes of AzCam:
 - One is the server-side, usually implemented as the *azcamserver* application, which communicates directly or indirectly to all system hardware.
 - Another is the console, usually called *azcamconsole*, which is typically implemented as an IPython command window that communicates with *azcamserver* and is used to acquire and analyze image data through the command line and python code.
 - The final mode is through client applications, which communicate with *azcamserver* over sockets or the web API. There are multiple clients written in a variety of languages. Examples are:

  * [azcam-tool](https://github.com/mplesser/azcam-tool), a GUI using National Instruments LabVIEW
  * [azcam-webobs](https://github.com/mplesser/azcam-webobs), a web-based observing script app
  * [azcam-status](https://github.com/mplesser/azcam-status), a web-based status page
  * [azcam-exptool](https://github.com/mplesser/azcam-exptool), a web-based exposure control app
  * [azcam-focus](https://github.com/mplesser/azcam-focus), an app for acquiring focus images
  * [azcam-observe](https://github.com/mplesser/azcam-observe), a Qt-based observing script app

While there are multiple pythonic ways to access the object instances in code, it is common to use the `api` object, often available as `azcam.api`. On there server side the `controller` object, for example, can be accessed as `api.controller`.  On the client side, the `api` object maps to the standard objects but with only a reduced set of exposed methods.  So while `api.exposure.reset` may available to server and client code, `api.exposure.set_video_gain` may only be available on the sever.

As an example, to get the current system wavelength and take an exposure, the commands using the *azcam-itl* extension are:

```python
# server-side (azcamserver)
import azcam
import azcam_itl.server

OR

# client-side (azcamconsole)
import azcam
import azcam_itl.console

And then:

wavelength = azcam.api.instrument.get_wavelength()
azcam.api.expose(30., 'dark', "a dark image title")
```

Example configuration code can be found in `azcam.example_server_config` and `azcam.example_console_config`.

When working in a command line environment, it is often convenient to import commonly used commands into the CLI namespace. To do this, after configuring the environment, execute the command:

```python
from azcam.cli import *
```

This provides direct access to objects such as *api*, *db*, *exposure*, *controller*, and various pre-defined shortcuts. 

## Help
AzCam is often used with IPython.  Help is then avaialble by typing `?xxx`, `xxx?`, `xxx??` or `help(xxx)` where `xxx` is an AzCam class, command, or object instance.

Useful links include:
* IPython <https://ipython.org>
* Python programming language <https://www.python.org>

## Server Operation
AzCam is often used as a server application to which clients connect via ethernet sockets or the web API.  The clients might be a GUI like *azcam-tool* or a python command line interface using AzCam's console code.

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

## Configuration Folders
There are several folder names which are usually defined, although their use may be optional for some systems:

  * *systemfolder* - the main folder where configuration code is located
  * *datafolder* - the root folder where data and parameters are saved, write access is required
 
## Programming

The link below contains information about *azcam* programming and more advanced features.

- [Programming](programming.md)
