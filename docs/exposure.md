# Exposure Class

This class defines Azcam's exposure interfaces. 
One class is usually instantiated as the *exposure* object in the server.

The *exposure* object often coordinates the actions of the hardware objects such as *controller*, 
*instrument*, etc. For example, when *exposure* is initialized the objects in the 
*exposure.objects_init* list are initialized.  Similarly when *exposure* is reset, the objects in the 
*exposure.objects_reset* list are reset.

```eval_rst
.. autoclass:: azcam.server.exposures.exposure.Exposure
    :members:
    :undoc-members:
    :show-inheritance:
    :inherited-members:
```