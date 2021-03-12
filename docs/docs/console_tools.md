# Console Tools

Console tools are commands which can be called from a console application to send the equivalent command to a server process.  Commands are typically accessed in a console process 
as `toolname.commandname(parameters)`, e.g. `instrument.get_wavelength()`.

A console tool may be obtained by `toolname = azcam.get_tools("toolname")` where *toolname* is like *exposure*, *instrument*, or *tempcon*.  A tool may also be accessed as *azcam.db.toolname*, like `azcam.db.controller`. 

::: azcam.console_tools.ConsoleTools

::: azcam.console_tools.ServerConnection

