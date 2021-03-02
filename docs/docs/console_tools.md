# Console Tools

The *console tools* are commands which can be called from a console application to send the equivalent command to a server process.  Commands are typically accessed in a console process 
as `toolname.commandname(parameters)`, e.g. `instrument.get_wavelength()`. The console tool itself can be obtained by `toolname = azcam.get_tools("toolname")` where *toolname* is like *exposure*, *instrument*, *tempcon*, etc..

::: azcam.console_tools.ConsoleTools
    :docstring:
    :members:

::: azcam.exposure.ExposureConsole
    :docstring:
    :members:

::: azcam.controller.ControllerConsole
    :docstring:
    :members:

::: azcam.instrument.InstrumentConsole
    :docstring:
    :members:

::: azcam.telescope.TelescopeConsole
    :docstring:
    :members:

::: azcam.tempcon.TempconConsole
    :docstring:
    :members:

::: azcam.system.SystemConsole
    :docstring:
    :members:

::: azcam.console_tools.ServerConnection
    :docstring:
    :members:

