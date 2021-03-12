# Exposure Tool

This tool defines azcam's exposure interface.  The default tool name is *exposure*.

The *exposure* tool often coordinates the actions of the hardware tools such as *controller*, 
*instrument*, etc. For example, when *exposure* is initialized the tools in the 
*exposure.tools_init* list are initialized.  Similarly when *exposure* is reset, the tools in the 
*exposure.tools_reset* list are reset.

::: azcam.exposure.Exposure

::: azcam.exposure.ExposureConsole
