# Azcam Documentation

Azcam is a software package which controls a hardware system that acquires image data from a 
scientific CCD/CMOS camera. It is implemented as a python package (*azcam*). The hardware enviroment is intended to be throughly customized and so the software is not appropriate for consumer-level cameras.

This documentation was built for azcam version 20.0.

```eval_rst
.. toctree::
   :hidden:

   Home - Azcam Documentation <self>
```   

## Help
Azcam is often used with IPython.  Help is then avaialble by typing ``?xxx``, ``xxx?``, ``xxx??`` or ``help(xxx)`` where ``xxx`` is an azcam class, command, or object instance.

Useful links include:

 * IPython <https://ipython.org>
 * Python programming language <https://www.python.org>
  
## Usage
Most of Azcam's functionality is available only after importing a configuration file from another package which defines a system's hardware resources. Once configured, the system is controlled by class instances (objects) of the hardware modules, such as *controller*, *instrument*, *telescope*, *tempcon*, and others.  Perhaps the most important object is *exposure*, which controls an actual observation. 
   
Example code to get the current system wavelength is:

    import azcam
    import azcam_itl
    from azcam_itl.server.config_server import exposure, instrument
    (... this imports and configures a specific system...)
    wavelength = instrument.get_wavelength()
    exposure.expose(30., 'dark', "a dark image title")

    Ina console CLI appliction, this would be:

    import azcam
    import azcam_itl.console.config_console
    (... this imports and configures a specific system...)
    wavelength = azcam.console.api.get_wavelength()
    azcam.console.api.exposure.expose(30., 'dark', "a dark image title")

## Server Operation
Azcam is most often used as a server application to which clients connect via ethernet sockets or from a web browser.  The clients may be GUI's like *obstool* or a pyhton command line interface using azcam's console code.

The azcam command structure provides a fairly uniform interface which can be used from the local command line (CLI), a remote socket connection, or the web interface.  An example for taking a 2.5 second "flat field" exposure is:

Local CLI or script example: ``expose.exposure(2.5, 'flat', 'an image title')``

Remote socket connection example: ``expose 2.5 flat "an image title"``

Web (http) connection example: ``http://hostname:2403/expose?exposure_time=2.5&image_type=flat&image_title=an+image+title``.

## Aliases
When using IPython, the auto parenthesis mode allows typing commands without requiring the normal python syntax 
of command(par1, par2, ...). The equivalent alias syntax is command par1 par2. With Ipython in this mode all 
commands can use this syntax, there are a few especially useful command line commands which are listed below. Most aliases
are implemeted from a command such as ``from cli_shortcuts import *``.

  * **sav** to save the current AzCamConsole state
  * **p** to toggle the command line printout of client commands and responses
  * **Run** to run a command in the python search path, usually for scripts (note the upper case R to distinguish it from IPython's built-in run magic command).
  * **gf** to try and go to current image folder.
  * **sf** to try and set image folder to the current directory.
  
## Commands and Objects
There are many commands and classes (which create objects and their methods) which are available to manipulate 
hardware, data, images, and exposures. The links listed below describe some of these commands. Availability depends on configuration.

### General
These are useful both in the server and in a console application.

```eval_rst
.. toctree::
   :maxdepth: 1

   image
   display
   fits
   utils
```

### Server Classes
These are useful only for defining a system in the server.

```eval_rst
.. toctree::
   exposure
   controller
   tempcon
   instrument
   telescope
```
### Console API
These are used in a console application which may be connected via a socket to the server. 

```eval_rst
.. toctree::
   :maxdepth: 2
   
   api_console
```

## Configuration
### Folders
There are several folder names which are usually defined, although their use may be optional for some systems:

  * *systemfolder* - the main folder where configuration data if located 
  * *projectfolder* - related to systemfolder, but for a specific project rather the the entire system
  * *datafolder* - the root folder where data and parameters are saved, write access is required
    
### Virtual Environment
When a virtual environment is used, it is typically contained in a folder named `../venvs/azcam`.

### Dependencies
Azcam currently uses *Python 3.7*. Important dependancies include:

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
  * *docutils*
  * *mysql-connector*
  * *pyserial*

## Programming

```eval_rst
.. toctree::
   :maxdepth: 2
   
   programming
```