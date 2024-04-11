# AzcamConsole

## Configuration and startup 

An example code snippet to start an *azcamconsole* process is:

```
ipython -m azcam_itl.console --profile azcamconsole -i -- -system DESI
```

and then in the IPython window:

```python
instrument.set_wavelength(450)
wavelength = instrument.get_wavelength()
print(f"Current wavelength is {wavelength}")
exposure.expose(2., 'flat', "a 450 nm flat field image")
```
