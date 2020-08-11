# AzCam Documentation

AzCam is a software environment for the acquisition and analysis of image data from scientific CCD/CMOS cameras. It is intended to be extensively customized for specific hardware and observational needs. It is is not appropriate for consumer-level cameras and is not intended to have a common API across all possible acquiistion and analysis environments.

AzCam is implemented as a base python package (*azcam*) and typically requires additional add-on packages and scripts to create a functional environment.

This documentation was built for azcam version 20.2.

```eval_rst
.. toctree::
   :hidden:

   Home - AzCam Documentation <self>
```

## Help
AzCam is often used with IPython.  Help is then avaialble by typing `?xxx`, `xxx?`, `xxx??` or `help(xxx)` where `xxx` is an azcam class, command, or object instance.

Useful links include:
* IPython <https://ipython.org>
* Python programming language <https://www.python.org>
  
## Usage
Most of AzCam's functionality is available only after importing configuration code which defines a system's hardware resources. Once configured, the system is controlled by class instances (objects) of the hardware modules, such as *controller*, *instrument*, *telescope*, *tempcon*, and others.  Perhaps the most important object is *exposure*, which controls an actual observation.

There are several operation modes of azcam. One is the server-side, usually implemented as the *azcamserver* application, which communicates directly or indirectly to all system hardware. Another is the console, usually called *azcamconsole*, which is usually implemented as an IPython command window that is able to communicate with *azcamserver* and is used to acquire and analyze image data through the command line and python code. 
  
Using the *azcam_itl* environment as an example, the server-side code to get the current system wavelength is:

    from server_azcam_itl import exposure, instrument  # configures the server
    wavelength = instrument.get_wavelength()
    exposure.expose(30., 'dark', "a dark image title")

For a console application (which usually connects to a separate server application), this would be:

    import console_azcam_itl  # configures the console
    from azcam import api
    wavelength = api.get_wavelength()
    api.exposure.expose(30., 'dark', "a dark image title")

   Example configuration code can be loaded with either of the commands:
    
    import azcam.example_server_config
    import azcam.example_console_config

When working in a command line environment, it is often convenient to import commonly used commands into the CLI namespace. To do this, **after** configuring the environment, execute the command:

    from azcam.cli import *

This provides direct access to objects such as *exposure*, *controller*, *db*, and shortcuts in *azcamserver*, or *api*, *db*,  and shortcuts in *azcamconsole*. 

## Server Operation
AzCam is most often used as a server application to which clients connect via ethernet sockets or from a web browser.  The clients might be a GUI like *azcamtool* or a pyhton command line interface using azcam's console code.

The azcam command structure provides a fairly uniform interface which can be used from the local command line (CLI), a remote socket connection, or the web interface.  An example for taking a 2.5 second "flat field" exposure is:

Local CLI or script example:

`expose.exposure(2.5, 'flat', 'an image title')`

Remote socket connection example:

`exposure.expose 2.5 flat "an image title"`

Web (http) connection example:

`http://hostname:2403/api/exposure/expose?exposure_time=2.5&image_type=flat&image_title=an+image+title`

Web pages which are served by *azcamserver* are found at URL's such as:

`http://hostname:2403/status` <br>
`http://hostname:2403/exptool`.

## Shortcuts
When using IPython, the auto parenthesis mode allows typing commands without 
requiring the normal python syntax of command(par1, par2, ...). The equivalent 
shortcut or alias syntax is command par1 par2. With Ipython in this mode all commands can 
use this syntax, there are a few especially useful command line commands which 
are listed below. Most aliases are implemeted from a command such 
as ``from shortcuts_console import *``.

  * **sav** to save the current AzCamConsole state
  * **p** to toggle the command line printout of client commands and responses
  * **Run** to run a command in the python search path, usually for scripts (note the upper case R to distinguish it from IPython's built-in run magic command).
  * **gf** to try and go to current image folder.
  * **sf** to try and set image folder to the current directory.
  * **bf** to browse for a file or folder.  

## Commands and Objects
There are many commands and classes (which create objects and their methods) which are 
available to manipulate hardware, data, images, and exposures. The links listed 
below describe some of these commands. Availability depends on configuration.

### General
These classes and commands are useful both in the server and in a console application.

```eval_rst
.. toctree::
   :maxdepth: 1

   image
   display
   fits
   plot
```

These commands are intended to be used only with other *AzCam* code.
```eval_rst
.. toctree::
   :maxdepth: 1

   utils
```

### Server Classes
These classes are server-side only and are useed to define or control a system.

```eval_rst
.. toctree::
   :maxdepth: 1

   exposure
   controller
   tempcon
   instrument
   telescope
```

### Console API
These commands are used in a console application which may be connected via a socket to the server.

```eval_rst
.. toctree::
   :maxdepth: 2
   
   api_console
```

### Report Commands

The report commands are helpful when generating reports. 
    
```eval_rst
.. toctree::
   :maxdepth: 1

   report
```
### Tester Classes

The report commands are helpful when generating reports. 
    
```eval_rst
.. toctree::
   :maxdepth: 1

   testers
```

## Configuration

### Folders
There are several folder names which are usually defined, although their use may be optional for some systems:

  * *systemfolder* - the main folder where configuration data is located
  * *datafolder* - the root folder where data and parameters are saved, write access is required
  * *projectfolder* - related to systemfolder, but for a specific project rather the the entire system (optional)
 
### Virtual Environment
When a python virtual environment is used, it is typically contained in a folder named `../venvs/azcam`.

### Dependencies
AzCam currently uses *Python 3.7*. Important dependancies include:

  * *numpy*
  * *astropy*
  * *loguru*

There are many other dependencies depending on configuration. Examples are:

  * *ipython*
  * *scipy*
  * *matplotlib*
  * *pandas*
  * *keyring*
  * *flask*
  * *PyPDF2*
  * *rst2pdf*
  * *pdfkit*
  * *markdown*
  * *mysql-connector*
  * *pyserial*

## Programming
```eval_rst
.. toctree::
   :maxdepth: 2
   
   programming
```
