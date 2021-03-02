# Programming

This document describes Azcam installation, configuration, and programming. It is intended 
for advanced users only.  See [this image](img/azcamarchitecture.jpg) for a graphical
layout of AzCam.

## Dependencies
AzCam currently uses *Python 3.8*. Important dependancies include:

  * *numpy*
  * *astropy*
  * *matplotlib*
  * *loguru*
  * *flask*

There are many other dependencies depending on configuration. Examples are:

  * *ipython*
  * *scipy*
  * *pandas*
  * *PyPDF2*
  * *rst2pdf*
  * *pdfkit*
  * *markdown*
  * *mysql-connector*
  * *pyserial*
  * *keyring*

## Versioning
Because Azcam consists of many different modules and plugins, there is no single version 
number or date which uniquely identifies all the code.

## Conventions
Modules (files), objects (such as *controller*), command names (methods) and attributes (parameters) are all lowercase.
Filenames should be given with forward slash ('/') separators, even on Windows 
machines. If back slashes are needed, they must be doubled as in `c:\\data`. Strings must 
be enclosed in quotation marks, as in `params.get_par('imageroot')`. Quotation marks must match 
('imageroot" is not acceptable). A quotation mark may be included in a string by preceding it with a backslash ("I am Mike\'s dog.")

## Objects
Python is an object oriented programming language and objects are used extensively in Azcam. Object-based commands 
provide control of all aspects of Azcam. These commands (methods) interact with hardware such as controllers, 
instruments, temperature controllers, and telescopes as well as with more virtual objects such as the 
exposures, images, databases, time, communication interfaces, etc. 
The required command syntax is `object.command(args)` where `object` is the object name (such as 
*controller*, *instrument*, *telescope*, etc.) and `command()` is the command to be sent. If `command()`
uses arguments, they are specified as comma separated values of the appropriate type, 
such as `object.command('ITL', 1.234,45)`. For example, the command to initialize to the 
instrument is `instrument.initialize()` and the command to get instrument focus is `telescope.get_focus()`.

## Attributes
Parameters may be read with the `params.get_par()` command and written with the `params.set_par()` 
command. For example, `params.get_par('imagetype')` returns the current image type.

## Logging
The `azcam.log()` function should be used for output instead of python's `print()` function. 
This is important due to the multithreading nature of Azcam.  The output of the `log()` function 
can be defined by code, and is typically both the console and a rotating log file.
It is possible to also direct logging output to a web application, a syslog handler, or other applications.

The `log()` function supports levels which determine if the log message should actually be output.
If the level value is greater than or equal to the value of `azcam.db.verbosity` then the
message string is output. The default level is one for both `verbosity` and the `log()` command. Higher verbosity
settings are intended for more detailed debug information.  The `log()` comamnd also has an argument `log_to_console` which can be set to zero for a single call to send a message to non-console loggers only. For example, `azcam.log("test message", log_to_console=0)`
 
## Python
The current version of Azcam requires Python version 3.8. See http://www.python.org for all things pythonic.

## Ports
Azcam reserves ten socket ports for each Azcam process. The ports are used for the various
server functions and may not actually be all used on a computer. The CommandServer port is
typically the base port each Azcam process and the remaining ports are incremented by one.
The default command server port is 2402 for the first Azcam process, 2412 for the second process,
2422 for the third, and so on. More complex systems often use many ports which the most basic
systems have one a command sever port and a controller sever port.

  * cmdserver port - 2402
  * web server port - 2403
  * instrument server port - 2404
  * controller server port - 2405
  * Reserved - 2406
  * Reserved - 2407
  * Reserved - 2408
  * Reserved - 2409
  * Reserved - 2410
  * Reserved - 2411

Ports 2400 and 2401 are typically reserved for the *azcam-monitor* processes.

## Misc Notes
These notes may be of some help setting up systems.

  * To allow system time update with azcamtime.py (for Windows PC):
    - gpedit may be required
    - Computer Configuration\Windows Settings\Security Settings\Local Policies\User Rights Assignment\Change the system time
    - gpupdate /force
  * Useful Tricks
    - Alt-F4 windows reboot for advanced options such as driver security
