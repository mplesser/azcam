@echo off

rem batch file to open an MEF fits image with Ds9

c:\ds9\ds9.exe -mosaicimage iraf %1% -zoom to fit
