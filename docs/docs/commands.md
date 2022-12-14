---
title: "Commands"
date: 2022-11-27
draft: false
weight: 24
---

# Commands

These commands are useful both in server and console applications. Note these are direct commands (function calls) and not class/tool methods.

## Fits Image Commands
The *azcam.fits* commands provide FITS image support functions.

Usage Example:

    azcam.fits.colbias("test.fits", 3)

[Documentation for the FITS functions](/code/azcam/functions/fits.html)

## Plot Commands
The *azcam.plot* commands are helpful for general plotting using matplotlib. 

Usage Example:

    azcam.plot.save_figure(1, "myfigure.png")

[Documentation for the plot functions](/code/azcam/functions/plot.html)


## Utility commands
The *azcam.utils* commands are general purpose python functions used throughout azcam.

Usage Example:

    azcam.utils.curdir("/data")

[Documentation for the utility functions](/code/azcam/functions/utils.html)
