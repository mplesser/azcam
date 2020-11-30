# Display Class

This class defines Azcam's image display interface. 
It is usually instantiated as the *display* object for both server and clients.

Depending on system configuration, the *display* object may be available 
directly from the command line, e.g. `display.display('test.fits'`).

Usage Example:

    rois = azcam.db.display.get_rois(2, 'detector')  
    azcam.display.db.display(test.fits')

::: azcam.display.Display
    :docstring:
    :members:
