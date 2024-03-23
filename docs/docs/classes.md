# Common Classes

AzCam's common classes are often combined with the classes which define *tools* to provide common functionality cross multiple tools.  For example, the *controller*, *instrument*, and *telescope* tools may all use the `header` class to define header information.

The common classes used thorughout azcam is listed here.

## Tool Class

AzCam's *tools* are used to define and control a system.

The base Tools class described below is inherited by all other tools. 

[Documentation for the Tool class](autocode/azcam_tools.md)

## Image Class

The `Image Class` defines Azcam's image object. Within *azcam* it is also used to define 
the *exposure.image* object which receives image data from a camera controller. It is imported automatically into the *azcam* namespace from the *azcam.image* module.

Usage Example:

`im1 = azcam.Image('test.fits')`

[Documentation for the Image class](autocode/azcam_image.md)

## Database Class

This class defines the `azcam.db` object.

[Documentation for the Database](autocode/azcam_database.md)

## Header Class

Azcam uses object-specific keyword indexed dictionaries to maintain textual informational about some tools. These are typically 
called headers as they are used to provide information in image headers. The keywords and their corresponding values, data type, 
and comment field are stored in each of the controller, instrument, and telescope header 
dictionary. These dictionaries are manipulated by commands both from clients and internally in azcam. Most of the 
values are written to the image file header (such as a FITS header) when an exposure begins.

The header information is accessed through methods such as 
`controller.header.get_keywords()` to get a list of all keywords and 
`instrument.get_keyword('FILTER1')` to get the currentvalue for the keyword. 

The `read_header()` method of each tools will actively read hardware to obtain 
information (such as `controller.read_header()` or `instrument.read_header()`).

In general there is a method of the same name in both the header class and the actual tool's class, such as `controller.header.get_keyword()` and `controller.get_keyword()`. The `.header` version reads the current data as stored in the header dictionary while the tool's version usually reads actual hardware values and then stores that data in the header dictionary. 

The telescope and instrument dictionaries are considered temporary and re-read every time an exposure starts. This 
is so that rapidly changing data values do not become stale. Most dictionary information is written to the image file header if the selected image format supports headers. When an object such as an instrument or telescope is disabled, the corresponding object database information is deleted and no longer updated.

[Documentation for the Header class](autocode/azcam_header.md)

## Image Related Classes

An *azcam* image is described by the Image, Focalplane, and WCS classes. The Focalplane class defines all aspects of the focal plane and sensor configuration used to create an image. The WCS class defines the World Coorindate System paramaters for the image.

[Documentation for Image related classes](autocode/azcam_image.md)
