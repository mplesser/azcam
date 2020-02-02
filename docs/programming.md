# Programming

This document describes Azcam installation, configuration, and programming. It is intended 
for advanced users only.

## Versioning
Because Azcam consists of many different modules and plugins, there is no single version 
number or date which uniquely identifies all the code. The best indicator of the version is to 
issue the command ``azcam.utils.get_par("version")``.

## Conventions
Modules (files), objects (such as *controller*), command names (methods) and attributes (parameters) are all lowercase.
Commands must have parentheses following their names even if no 
attributes are required. Filenames should be given with forward slash ('/') separators, even on Windows 
machines. If back slashes are needed, they must be doubled as in c:\\data. Strings must 
be enclosed in quotation marks, as in get_par('version'). Quotation marks must match ('version" is 
not acceptable). A quotation mark may be included in a string by preceding it with a backslash 
("I am Mike\'s dog.")

## Commands
Commands can be imported into modules in the standard pythonic manner, such as ``from 
azcam.fits import colbias``.

## Alias Commands
Alias commands are a special syntax available with *IPython* (using the auto-parenthesis mode) which do 
not use the standard Python syntax of ``command(par1, par2, ...)``. The equivalent magic syntax 
is ``command par1 pars ...``. Alias commands are optionally defined for a system for user convenience.

## Objects
Python is an object oriented programming language and objects are used extensively in Azcam. Object-based commands 
provide control of all aspects of Azcam. These commands (methods) interact with hardware such as controllers, 
instruments, temperature controllers, and telescopes as well as with more virtual objects such as the 
exposures, images, databases, time, communication interfaces, etc. 
The required command syntax is ``azcam.db.object.command(args)`` where ``object`` is the object name (such as 
*controller*, *instrument*, or *telescope*) and ``command()`` is the command to be sent. If ``command()``
uses arguments, they are specified as comma separated values of the appropriate type, 
such as ``azcam.db.object.command('ITL',1.234,45)``. For example, to send the command initialize to the 
instrument, use ``azcam.db.instrument.initialize()``. To send the ``get_focus`` command to the telescope, 
use ``azcam.db.telescope.get_focus()``.

## Header Commands
Azcam uses object specific keyword indexed dictionary to maintain textual informational about some objects. These are typically 
called headers as they are used to provide information in image headers. The keywords and their corresponding values, data type, 
and comment field are stored in each of the controller, instrument, and telescope header 
dictionary. These dictionaries are manipulated 
by commands both from clients and internally in Azcam. Most of the values are written to the image file header (such as a FITS header) 
when an exposure begins. The dictionaries are accessed through methods such as 
``controller.header.get_all_keywords()`` and 
``instrument.header.get_keyword('FILTER1')``. The ``read_header()`` method of each object will actively read hardware to obtain 
information (such as ``controller.read_header()`` or ``instrument.read_header()``). The telescope and instrument dictionaries are considered temporary and re-read every time an exposure starts. This 
is so that rapidly changing data values do not become stale. 
Most dictionary information is written to the image file header if the selected image format supports headers. When an object such as an instrument or telescope is disabled, the corresponding object database information is deleted and no longer updated.

## Attributes
Parameters may be read with the ``azcam.api.get_par()`` command and written with the ``azcam.api.set_par()`` 
command. For example, ``azcam.api.get_par('imagetype')`` returns the current image type.

## Logging
The ``azcam.log()`` function should be used for output instead of python's ``print()`` function. This function is mapped to the *azcam* namespace from ``azcam.utils.log()``.
This is important due to the multithreading nature of Azcam.  The output of the ``log()`` function can be defined by code, and is typically both the 
console and a rotating log file. It is possible to also direct ``log()`` output to a web application, a syslog handler, or other applications.

The ``log()`` function supports levels which determine if the log message should actually be output. If the level value is greater than or equal to the value of ``azcam.db["verbosity"]`` then the message string is output. The default level is one, as 
``azcam.log("test message", level = 1)``.  The level meanings are:

  * level = 0: silent
  * level = 1: normal
  * level = 2: added information
  * level = 3: debug
 
## Azcam Apps
The following support applications may also be useful when operating Azcam.

  * *Azcamtool* is a graphical user interface (GUI) useful for operating Azcam in a point and click mode. It is not required, but is highly recommended.
  * *EngineeringTool* performs very low level (and dangerous!) controller functions.
  * *AzcamImageServer* is a stand-alone python image server which can receive images on a remote machine. This is especially useful for receiving images on computer running Linux.
  * *Ds9Tools* is a set of tools useful when using SAO's ds9 display program.

## Python
The current version of Azcam requires Python version 3.6.x. See http://www.python.org for all things pythonic.

## Dependencies
Some Azcam commands require python packages which are not installed by default. These must be downloaded 
and installed according to their individual instructions. Not all commands require all these packages. 
The current non-default packages are currently:

  * FITS image file manipulation - astropy.io.fits <http://docs.astropy.org/en/stable/io/fits/index.html>
  * Numeric python for data manipulation - numpy <http://www.numpy.org>
  * Plotting - `matplotlib <https://matplotlib.org>

For code which use a Qt graphical interface, 
PyQt <https://www.riverbankcomputing.com/software/pyqt/intro> is required.
You may need to add *c:\python37* and/or *c:\python37\Scripts* to the Windows PATH environment variable,

## CameraServer
*CameraServers* are separate executable programs which manage direct interaction with 
controller hardware on some systems. Communication with a CameraServer takes place over sockets via 
communication protocols defined between *azcam* and a specific CameraServer program. These 
CameraServers are necessary when specialized drivers for the camera hardware are required.  They are 
usually written in C/C++. 

## National Instruments LabVIEW
The runtime LabVIEW installer must be downloaded to your computer and executed to install the 
LabVIEW Run-Time Engine which is required by Azcam LabVIEW code (such as Obstool). Administrator 
privileges may be required for installation. LabVIEW installers should be obtained directly from National Instruments, <http://www.ni.com>. Azcam currently uses LabVIEW 2014.

#Ports
Azcam reserves ten socket ports for each Azcam process. The ports are used for the 
various server functions and may not 
actually be all used on a computer. The CommandServer port is typically the base port each Azcam process and the remaining 
ports are incremented by one. The default command server port is 2402 for the first Azcam process, 2412 for the second process, 
2422 for the third, and so on. More complex systems often use many ports which the most basic systems have one a command sever port and a controller sever port.

  * CommandServerPort - 2402
  * WebServerPort - 2403
  * InstrumentServerPort - 2404
  * ControllerServerPort - 2405
  * PowerServerPort - 2406
  * Reserved - 2407
  * Reserved - 2408
  * Reserved - 2409
  * Reserved - 2410
  * Reserved - 2411

## Azcam DSP Code
The DSP code which runs in the ARC and Magellan controllers is assembled and linked with Motorola software tools. These tools should be installed in *../MotorolaDSPtools/* on a Windows machine, as required by the batch files which assemble and link the DSP source code.

While the Azcam application code for the ARC timing board is typically downloaded during camera initialization, the boot code must be compatible for this to work properly. Therefore Azcam DSP code must be burned into the timing board EEPROMs before use. The Azcam timing DSP code is quite different from the ARC code and is required for Azcam operation. The PCI fiber optic interface board and the utility board use the original ARC code and does not need to be changed. Note this applies to gen3 systems only, the gen1 and gen2 situation is more complex.

For the Magellan systems, there is only one DSP file which must be downloaded during initialization. Note that *xxx.s* files are loaded for the Magellan systems while *xxx.lod* files are loaded for ARC systems.
