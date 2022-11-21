# Tools

AzCam's *tools* are used to define and control a system.

## Exposure Tool

This tool defines the exposure interface.  The default tool name is *exposure*.

The *exposure* tool often coordinates the actions of the hardware tools such as *controller*, 
*instrument*, etc. For example, when *exposure* is initialized the tools in the 
*exposure.tools_init* list are initialized.  Similarly when *exposure* is reset, the tools in the 
*exposure.tools_reset* list are reset.

[Documentation for the Exposure class](https://mplesser.github.io/docs/azcam/tools/exposure.html)

## Controller Tool

This tool defines the camera controller interface. The default tool name is *controller*. 

[Documentation for the Controller class](https://mplesser.github.io/docs/azcam/tools/controller.html)

## TempCon Tool

This tool defines the temperature controller interface. The default tool name is *tempcon*.

[Documentation for the TempCon class](https://mplesser.github.io/docs/azcam/tools/tempcon.html)

## Instrument Tool

This tool defines the instrument interface.  The default tool name is *instrument*.

[Documentation for the Instrument class](https://mplesser.github.io/docs/azcam/tools/instrument.html)

## Telescope Tool

This tool defines the telescope interface. The default tool name is *telescope*.

[Documentation for the Telescope class](https://mplesser.github.io/docs/azcam/tools/telescope.html)

## Display Tool

This tool defines the image display interface. The default tool name is *display*. 

Usage Example:

    rois = display.get_rois(2, 'detector')  
    display.display(test.fits')

[Documentation for the Display class](https://mplesser.github.io/docs/azcam/tools/display.html)

## Base Server Tools

The base Tools class described below is inherited by all server tools. 

[Documentation for the base Tools class](https://mplesser.github.io/docs/azcam/tools/tools.html)

## Console Tools

Console tools are commands which can be called from a console application to send the equivalent command to a server process.  Commands are typically accessed in a console process as `toolname.commandname(parameters)`, e.g. `instrument.get_wavelength()`.

A console tool may be obtained by `toolname = azcam.get_tools("toolname")` where *toolname* is like *exposure*, *instrument*, or *tempcon*.  A tool may also be accessed as *azcam.db.toolname*, like `azcam.db.controller`. 

[Documentation for the ConsoleTools class](https://mplesser.github.io/docs/azcam/tools/console_tools.html)

