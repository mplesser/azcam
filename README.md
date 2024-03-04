# AzCam

AzCam is a software framework for the acquisition and analysis of image data from scientific imaging systems as well as the control of instrumentation. It is intended to be customized for specific hardware, observational, and data reduction requirements.

AzCam is based on the concept of *tools* which are the interfaces to both hardware and software code.  Examples of tools are *instrument* which controls instrument hardware, *telescope* which interfaces to a telescope, *linearity* which acquires and analyzes images to determine sensor linearity, and *exposure* which controls a scientific observation by interfacing with a variety of other tools. As an example, the *exposure* tool may move a telescope and multiple filter wheels, control a camera shutter, operate the camera by taking an exposure, display the resultant image, and begin data reduction of that image.

AzCam is not appropriate for consumer-level cameras and is not intended to have a common API across all systems. It's primary design principle is to allow interfacing to a wide variety of custom instrumentation which is required to acquire and analyze scientific image data.

The *azcam* package currently supports Astronomical Research Cameras, Inc. Gen3, Gen2, and Gen1 CCD controllers, Magellan Guider controllers, STA Archon controllers, and CMOS cameras using ASCOM. It also supports some temperature contorollers, telecopes, and image displays.

See *azcam-tool* for a common extension package which implements a GUI used by many observers.

## Documentation

See https://azcam.readthedocs.io.

See also https://github.com/mplesser/azcam-tool.git for the standard GUI used by most telescope observers.

## Installation

`pip install azcam`

Or download the latest version from from github: https://github.com/mplesser/azcam.git.

You may need to install `python3-tk` on Linux systems [`sudo apt-get install python3-tk`].

## Configuration and startup 

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

# Observe tool script example

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

# AzCam Console

*azcamconsole* is a console application for the *azcam* acquisition and analysis package. It usually runs in an IPython window and is used to both acquire and analyze data in a python scripting environment.

## Installation

You may need to install `python3-tk` on Linux systems [`sudo apt-get install python3-tk`].

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
