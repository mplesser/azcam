# Header Class

Azcam uses object specific keyword indexed dictionary to maintain textual informational about some tools. These are typically 
called headers as they are used to provide information in image headers. The keywords and their corresponding values, data type, 
and comment field are stored in each of the controller, instrument, and telescope header 
dictionary. These dictionaries are manipulated by commands both from clients and internally in Azcam. Most of the 
values are written to the image file header (such as a FITS header) when an exposure begins.

The header information is accessed through methods such as 
`controller.header.get_keywords()` to get a list of all keywords and 
`instrument.get_keyword('FILTER1')` to get the currentvalue for the keyword. 

The `read_header()` method of each tools will actively read hardware to obtain 
information (such as `controller.read_header()` or `instrument.read_header()`).

In general there is a method of the same name in both the header class and the actual tool's class, such as `controller.header.get_keyword()` and `controller.get_keyword()`.  The `.header` version reads the current data as stored in the header dictionary while the tool's version usually reads actual hardware values and then stores that data in the header dictionary. 

The telescope and instrument dictionaries are considered temporary and re-read every time an exposure starts. This 
is so that rapidly changing data values do not become stale. Most dictionary information is written to the image file header if the selected image format supports headers. When an object such as an instrument or telescope is disabled, the corresponding object database information is deleted and no longer updated.

Below is the documentation for the Header class.

::: azcam.header.Header
