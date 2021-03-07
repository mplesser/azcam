# Exposure Class

This class defines Azcam's exposure interfaces. 
One class is usually instantiated as the *exposure* tools in the server.

The *exposure* object often coordinates the actions of the hardware tools such as *controller*, 
*instrument*, etc. For example, when *exposure* is initialized the tools in the 
*exposure.tools_init* list are initialized.  Similarly when *exposure* is reset, the tools in the 
*exposure.tools_reset* list are reset.

::: azcam.exposure.Exposure
    :docstring:
    :members:
