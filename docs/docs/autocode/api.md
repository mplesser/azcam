# API Class

The following methods represent the azcam API. Examples of commands are below.

```
Python:
api.command(args)
Example: api.set_exposuretime(32.2)
```

```
CommandServer:
"api.command arg1 arg2"
Examples:
"api.set_exposuretime 32.2"
"set_exposuretime 32.2"
```

```
WebServer:
.../api/command?keyword1=value1 keyword2=value2
Examples:
.../api/set_exposuretime?exposuretime=32.2
.../api/set_control_temperature?temperature=-110.0&temperature_id=2
.../set_control_temperature?temperature=-110.0&temperature_id=2
```

For both the CommandServer and WebServer the "api." may be omitted.

::: azcam.api.API
