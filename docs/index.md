# General

Azcam is a software environment for the acquisition and analysis of image data from scientific imaging cameras. It is intended to be extensively customized for specific hardware and observational needs. It is is not appropriate for consumer-level cameras and is not intended to have a common API across all possible acquisition and analysis environments.

```eval_rst
.. toctree::
   :hidden:

   Home <self>
```

Most of azcam's functionality is available only after installing *extension packages* which contain configuration and hardware code that define a system's hardware resources.  Examples include:

  - azcam-arc
  - azcam-archon
  - azcam-ds9
  - azcam-bok
  - azcam-mont4k
   
Once configured, the system is controlled by class instances (*objects*) of the hardware modules, such as *controller*, *instrument*, *telescope*, *tempcon*, *system*, and others.  Perhaps the most important object is *exposure*, which controls an actual observation.  Most of these objects are exposed through the *azcam.api* object.  There is also a database of parameters maintained in the *azcam.db* object 

There are two three main operational modes of azcam:
 - One is the server-side, usually implemented as the *azcamserver* application, which communicates directly or indirectly to all system hardware.
 - Another is the console, usually called *azcamconsole*, which is typically implemented as an IPython command window that communicates with *azcamserver* and is used to acquire and analyze image data through the command line and python code.
 - The final mode is through client applications, which communicate with *azcamserver* over sockets or the web API. There are multiple clients written in a variety of languages. Examples are:
   - azcam-tool
   - azcam-webobs
   - azcam-status
   - azcam-exptool

While there are multiple pythonic ways to access the object instances in code, it is common to use the `api` object, often available as `azcam.api`. On there server side the `controller` object, for example, can be accessed as `api.controller`.  On the client side, the `api` object maps to the standard objects but with only a reduced set of exposed methods.  So while `api.exposure.reset` may available to server and client code, `api.exposure.set_video_gain` may only be available on the sever.

As an example, to get the current system wavelength and take an exposure, the commands using the *azcam-itl* extension are:

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

Example configuration code can be found in `azcam.example_server_config` and `azcam.example_console_config`.

When working in a command line environment, it is often convenient to import commonly used commands into the CLI namespace. To do this, after configuring the environment, execute the command:

    from azcam.cli import *

This provides direct access to objects such as *api*, *db*, *exposure*, *controller*, and various pre-defined shortcuts. 

# Help
Azcam is often used with IPython.  Help is then avaialble by typing `?xxx`, `xxx?`, `xxx??` or `help(xxx)` where `xxx` is an azcam class, command, or object instance.

Useful links include:
* IPython <https://ipython.org>
* Python programming language <https://www.python.org>

# Server Operation
Azcam is most often used as a server application to which clients connect via ethernet sockets or from a web browser.  The clients might be a GUI like *azcam-tool* or a python command line interface using azcam's console code.

The azcam command structure provides a fairly uniform interface which can be used from the local command line (CLI), a remote socket connection, or the web interface.  An example for taking a 2.5 second "flat field" exposure is:

Local CLI or script example:

`exposure.expose(2.5, 'flat', 'an image title')`

Remote socket connection example:

`exposure.expose 2.5 flat "an image title"`

Web (http) connection example:

`http://hostname:2403/api/exposure/expose?exposure_time=2.5&image_type=flat&image_title=an+image+title`

Web pages which are served by *azcamserver* are found at URL's such as:

`http://hostname:2403/status` <br>
`http://hostname:2403/exptool`.

## Server Classes
These classes are useed to define and control a system.

```eval_rst
.. toctree::
   :maxdepth: 1

   exposure
   controller
   tempcon
   instrument
   telescope
```

# Shortcuts
When using IPython, the auto parenthesis mode allows typing commands without 
requiring the normal python syntax of command(par1, par2, ...). The equivalent 
shortcut or alias syntax is command par1 par2. With Ipython in this mode all commands can 
use this syntax, there are a few especially useful command line commands which 
are listed below. Most aliases are implemeted from a command such 
as ``from shortcuts_console import *``.

  * **sav** to save the current parameters to the parameter file
  * **p** to toggle the command line printout of client commands and responses
  * **Run** to run a command in the python search path, usually for scripts (note the upper case R to distinguish it from IPython's built-in run magic command).
  * **gf** to try and go to current image folder.
  * **sf** to try and set image folder to the current directory.
  * **bf** to browse for a file or folder.  

# Code Descriptions
There are many functions and classes which are available to manipulate hardware, 
data images, and exposures. The links listed below describe some of these commands.
Availability depends on configuration.

The classes and commands listed here are useful both in the server and in a console application.

```eval_rst
.. toctree::
   :maxdepth: 1

   image
   display
   fits
   plot
```

The *utility* commands are intended to be used only within other *azcam* code.
```eval_rst
.. toctree::
   :maxdepth: 1

   utils
```

# Console API
These commands are used in a console application which may be connected via a socket to the server.

```eval_rst
.. toctree::
   :maxdepth: 1
   
   api_console
```

# Configuration Folders
There are several folder names which are usually defined, although their use may be optional for some systems:

  * *systemfolder* - the main folder where configuration data is located
  * *datafolder* - the root folder where data and parameters are saved, write access is required
  * *projectfolder* - related to systemfolder, but for a specific project rather the the entire system (optional)
 
# Programming

The link below contains informationa about *azcam* programming.

```eval_rst
.. toctree::
   :maxdepth: 1
   
   programming
```
