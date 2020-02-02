# Instrument Class

This class defines Azcam's instrument interface. A class is usually instantiated as the *instrument* object 
in the server.

A specific Instrument class usually communicates with an *instrument server* via a network socket connection. 
An instrument server communicates directly with the instrument hardware. The socket connection is with 
Azcam's standard *cmdserver* interface.  

Because *cmdserver* uses string-based message passing, data such as lists should be encoded in 
space-delimited strings. As an example, a list of temperatures such as [-45.678, -22.2, +34.5678] 
should be sent as "-45.678 -22.2, +34.5678".  Floats must also be encoded as strings.

Each instrument server has its own custom command set which depends entirely on the hardware supported. 
It is the job of the Azcam Instrument class (running within *AzCamServer*) to provide the common Azcam 
API for instruments.

Instrument servers often also support a web interface, usually for status and GUI control. There is typically
a single method in the instrument server which translates web command strings into the *command parser* commands
which are accepted by the instrument server's *cmdserver*.

```eval_rst
.. autoclass:: azcam.server.instruments.instrument.Instrument
    :members:
    :undoc-members:
    :show-inheritance:
    :inherited-members:
```