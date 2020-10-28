# Image Class

This class defines Azcam's image object. Within *azcam* it is also used to define 
the *exposure.image* object which receives image data from a camera controller.

The *Image* class is imported automatically into the *azcam* namespace from the 
*azcam.image* module.

Usage Example:

    im1 = azcam.Image('test.fits')

```eval_rst
.. autoclass:: azcam.image.Image
   :members:
   :undoc-members:
   :show-inheritance:
   :inherited-members:
```

# SendImage Class

This class defines AzCam's code to send image data to a remote image server.

```eval_rst
.. autoclass:: azcam.image.SendImage
   :members:
   :undoc-members:
   :show-inheritance:
   :inherited-members:
```