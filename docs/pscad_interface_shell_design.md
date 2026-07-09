# PSCAD Interface Shell Design

The PSCAD interface shell is deliberately small. It is a transport layer between the plant and MATLAB.

## PSCAD To MATLAB

Pack one complete observation bundle per interface period:

- Bus voltage and frequency arrays.
- Line current, power, loading, and online arrays.
- Wind PCC voltage, power, and online arrays.
- Generator voltage, frequency, and online arrays.
- Load voltage, frequency, and online arrays.
- Windowed min/max values needed by protection logic.
- Simulation time and interface step.

## MATLAB Call

Preferred MATLAB entry point:

```matlab
[cmd, state, events] = pscad_cascade_step(t, dt, obs, state, settings)
```

PSCAD should call MATLAB once per interface period, not once per line or device.

## MATLAB To PSCAD

Unpack `cmd` and route commands by mapping table:

- `cmd.line_trip_cmd(k)` opens `BR_LINE_k_FROM` and `BR_LINE_k_TO`.
- `cmd.wind_disconnect_cmd(k)` opens the wind-farm outlet breaker.
- `cmd.gen_trip_cmd(k)` opens the generator outlet breaker.
- `cmd.load_shed_cmd(k)` opens the configured load-stage switches according to `cmd.load_shed_fraction(k)`.
- `cmd.tov_line_trip_cmd(k)` opens the associated line breakers.

## Feedback

The next observation must report actual PSCAD online state. MATLAB must not assume a breaker opened only because it issued a command.

