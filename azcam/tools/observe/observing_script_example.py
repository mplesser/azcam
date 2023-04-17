# import observe for observing command use
from azcam.tools.observe.observe import Observe, ObserveConsole

# this is a single line comment python style
# use blocks with start/end triple quotes for multi-line comments

observe = Observe()  # service version
# observe = ObserveConsole()  # client version

# this block shows some direct commands
"""
observe.test(et=1.0,object="flat", filter="400")
observe.comment("a different new comment 123")
observe.delay(1)
observe.obs(et=2.0,object="zero", filter="400", dec="12:00:00.23", ra="-23:34:2.1")
"""

# this block shows an example of commands using python flow control
"""
alt_start = 0.0
step_size = 0.01
num_steps = 100
for count in range(num_steps):
    altitude = alt_start + count*step_size
    observe.steptel(altitude=altitude)
    print(f"On loop {count} altitude is {altitude}")
"""
