# Observing Scripts

The *observe* tool supports running observing scripts which can sequentially control all aspects of observations with no user interaction. It can be used with a GUI or with a command line interface.

The GUI uses the *PySide6* Qt package.

## Usage

Type `azcamobserve` to start the GUI from any terminal.  A new window will open.

Use `observe.observe()` from an azcamconsole window to run the CLI version.

![GUI example after loading script file.](img/observe_gui.jpg)
*GUI example after loading script file.*

After starting the GUI, Press "Select Script" to find a script to load on disk. 
Then press "Load Script" to populate the table.  The excute, press Run.
You may Pause a script after the current command by pressing the Pause/Resume button. 
Then press the same button to resume the script.  The "Abort Script" button will 
abort the script as soon as possible.

If you have troubles, close the console window and start again.

## GUI Real-time Updates

   You may change a cell in the table to update values while a script is running.  Click in the cell, make the change and press "Enter" (or click elsewhere).
   
## Non-GUI Use

It is still possible to run *observe* without the GUI, although this mode is deprecated.

## Misc

Import observe for observing command use:
```
from azcam_console.observe.observe_cli.observe_cli import ObserveCli
```

```
# this is a single line comment python style
```

This block shows some direct commands
```
observe = ObserveCli()
observe.test(et=1.0,object="flat", filter="400")
observe.comment("a different new comment 123")
observe.delay(1)
observe.obs(et=2.0,object="zero", filter="400", dec="12:00:00.23", ra="-23:34:2.1")
```

This block shows an example of commands using python flow control
```
alt_start = 0.0
step_size = 0.01
num_steps = 100
for count in range(num_steps):
    altitude = alt_start + count*step_size
    observe.steptel(altitude=altitude)
    print(f"On loop {count} altitude is {altitude}")
```

## Examples

```python
observe.observe('/azcam/systems/90prime/ObservingScripts/bass.txt',1)
observe.move_telescope_during_readout=1
```

## Parameters

   Parameters may be changed from the command line as:
   
```python
observe.move_telescope_during_readout=1
observe.verbose=1
```

## Observe Script Commands

Always use double quotes (") when needed
Comment lines start with # or !
Status integers are start of a script line are ignored or incremented

```
Observe scripts commands:
obs        ExposureTime ImageType Title NumberExposures Filter RA DEC Epoch
stepfocus  RelativeNumberSteps
steptel    RA_ArcSecs Dec_ArcSecs
movetel    RA Dec Epoch
movefilter FilterName
delay      NumberSecs
test       ExposureTime imagetype Title NumberExposures Filter RA DEC Epoch
print      "hi there"
prompt     "press any key to continue..."
quit       quit script

Example of a script:
obs 10.5 object "M31 field F" 1 u 00:36:00 40:30:00 2000.0 
obs 2.3 dark "a test dark" 2 u
stepfocus 50
delay 3.5
stepfocus -50
steptel 12.34 12.34
movetel 112940.40 +310030.0 2000.0
```
