# Display Class

This class defines Azcam's image display interface to SAO's ds9 image display. 
It is usually instantiated as the *display* object for both server and clients.

Depending on system configuration, the *display* object may be available 
directly from the command line, e.g. `display.display('test.fits'`).

Usage Example:

    rois = azcam.db.display.get_rois(2, 'detector')  
    azcam.display.db.display(test.fits')

```eval_rst
.. autoclass:: azcam.displays.ds9display.Ds9Display
   :members:
   :undoc-members:
   :show-inheritance:
   :inherited-members:
```
