# Focus Class

::: azcam.tools.focus.Focus

## Focus Parameters

Parameters may be changed from the command line as:
`focus.number_exposures=7`
or
`focus.set_pars(1.0, 5, 25, 15)`.

<dl>
  <dt><em>focus.number_exposures = 7</em></dt>
  <dd>Number of exposures in focus sequence</dd>

  <dt><em>focus.focus_step = 30</em></dt>
  <dd>Number of focus steps between each exposure in a frame</dd>

  <dt><em>focus.detector_shift = 10</em></dt>
  <dd>Number of rows to shift detector for each focus step</dd>

  <dt><em>focus.focus_position</em></dt>
  <dd>Current focus position</dd>

  <dt><em>focus.exposure_time = 1.0</em></dt>
  <dd>Exposure time (seconds)</dd>

  <dt><em>focus.focus_component = "instrument"</em></dt>
  <dd>Focus component for motion - "instrument" or "telescope"</dd>

  <dt><em>focus.focus_type = "absolute"</em></dt>
  <dd>Focus type, "absolute" or "step"</dd>

  <dt><em>focus.set_pars_called = 1</em></dt>
  <dd>Flag to not prompt for focus position</dd>

  <dt><em>focus.move_delay = 3</em></dt>
  <dd>Delay in seconds between focus moves</dd>
</dl>
