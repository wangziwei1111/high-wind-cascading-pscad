# PSCAD-MATLAB Signal Contract

## MATLAB Entry Point

```matlab
function [cmd, state, events] = pscad_cascade_step(t, dt, obs, state, settings)
```

`obs` is supplied by PSCAD. `cmd` is returned to PSCAD. `state` is persistent MATLAB state for timers, latches, and history. `events` contains only newly generated events for the current step.

## Required Observation Fields

| Field | Size | Meaning |
|---|---:|---|
| `bus_voltage_pu` | 39 | Bus RMS voltage in pu |
| `bus_frequency_Hz` | 39 | Bus frequency |
| `line_current_A` | 46 | Line current |
| `line_power_MW` | 46 | Line active power |
| `line_loading_pu` | 46 | Loading ratio versus thermal limit |
| `line_online` | 46 | Actual PSCAD line status |
| `wind_pcc_voltage_pu` | 3 | Wind PCC voltage |
| `wind_power_MW` | 3 | Wind active power |
| `wind_online` | 3 | Actual wind outlet status |
| `gen_voltage_pu` | nGen | Generator terminal voltage |
| `gen_frequency_Hz` | nGen | Generator frequency |
| `gen_online` | nGen | Actual generator status |
| `load_voltage_pu` | nLoad | Load-bus voltage |
| `load_frequency_Hz` | nLoad | Load-bus frequency |
| `load_online` | nLoad | Load stage status |
| `bus_voltage_max_pu` | 39 | Windowed bus-voltage maximum |
| `wind_pcc_voltage_min_pu` | 3 | Windowed wind PCC minimum |
| `wind_pcc_voltage_max_pu` | 3 | Windowed wind PCC maximum |
| `simulation_time_s` | 1 | Simulation time |
| `interface_dt_s` | 1 | Interface period |

## Required Command Fields

| Field | Size | Meaning |
|---|---:|---|
| `line_trip_cmd` | 46 | Line trip command |
| `wind_disconnect_cmd` | 3 | Wind-farm disconnect command |
| `gen_trip_cmd` | nGen | Generator trip command |
| `load_shed_cmd` | nLoad | Load-shedding command |
| `load_shed_fraction` | nLoad | Cumulative shed fraction |
| `tov_line_trip_cmd` | 46 | Transient-overvoltage line trip |
| `any_action` | 1 | Any command asserted |
| `simulation_stop_cmd` | 1 | Stop request |

