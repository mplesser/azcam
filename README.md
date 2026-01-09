# AzCam

AzCam is a software framework for the acquisition and analysis of image data from scientific imaging systems as well as the control of instrumentation. It is intended to be customized for specific hardware, observational, and data reduction requirements.

Operation is based on the concept of *tools* which are the interfaces to both hardware and software code.  Examples of tools are *instrument* which controls instrument hardware, *telescope* which interfaces to a telescope, *linearity* which acquires and analyzes images to determine sensor linearity, and *exposure* which controls a scientific observation by interfacing with a variety of other tools. As an example, the *exposure* tool may move a telescope and multiple filter wheels, control a camera shutter, operate the camera by taking an exposure, display the resultant image, and begin data reduction of that image.

The *azcam* python package currently supports Astronomical Research Cameras, Inc. Gen3, Gen2, and Gen1 CCD controllers, Magellan Guider controllers, STA Archon controllers, and CMOS cameras using ASCOM. It also supports a variety of temperature controollers, telecopes, and image displays.

AzCam is not appropriate for consumer-level cameras and is not intended to have a common API across all systems. It's primary design principle is to allow interfacing to a wide variety of custom instrumentation which is required to acquire and analyze scientific image data.

## Documentation

See https://azcam.readthedocs.io.

See https://github.com/mplesser/azcam-tool.git for the standard GUI used by most telescope observers.

See https://github.com/mplesser/azcam-console.git for a python package which supports a local or remote command line interface and sensor characterization tools.

## Installation Example

`pip install azcam`

or 

```shell
git clone https://github.com/mplesser/azcam
git clone https://github.com/mplesser/azcam-console
pip install -e azcam
pip install -e azcam-console
```
