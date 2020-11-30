# Image Class

This class defines Azcam's image object. Within *azcam* it is also used to define 
the *exposure.image* object which receives image data from a camera controller.

The *Image* class is imported automatically into the *azcam* namespace from the 
*azcam.image* module.

Usage Example:

    im1 = azcam.Image('test.fits')

::: azcam.image.Image
    :docstring:
    :members:

## SendImage Class

This subclass defines AzCam's code to send image data to a remote image server.

::: azcam.image_send.SendImage
    :docstring:
    :members:
