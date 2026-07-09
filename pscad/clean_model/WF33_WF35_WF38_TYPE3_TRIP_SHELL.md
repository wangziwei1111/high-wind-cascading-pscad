# WF33/WF35/WF38 Type-3 Trip Shell

## Source Model

The trip-shell files were copied from the protected clean baseline:

- Source: `PNNL_39_WF33_WF35_WF38_Type3_all_run_ok.pscx`
- Source: `PNNL_39_WF33_WF35_WF38_Type3_all_run_ok.psmx`

The source baseline was not modified.

## New Model Files

- `PNNL_39_WF33_WF35_WF38_Type3_trip_shell.pscx`
- `PNNL_39_WF33_WF35_WF38_Type3_trip_shell.psmx`

Current status: these files are a clean PSCAD copy for the paper-style MATLAB-driven wind-farm trip shell. The PSCAD GUI command wiring has not yet been manually completed in PSCAD.

## Intended PSCAD Interface Points

PSCAD should provide MATLAB with the following vectors in fixed order:

1. WF33
2. WF35
3. WF38

PSCAD -> MATLAB:

- `simulation_time_s`
- `interface_dt_s`
- `wind_pcc_voltage_pu[3]`
- `wind_active_power_MW[3]`
- `wind_online[3]`
- Optional: `wind_breaker_status[3]`

MATLAB -> PSCAD:

- `wind_disconnect_cmd[3]`

PSCAD remains responsible for opening the real wind-farm breaker and feeding back offline status on the next interface step.

## Logical Breaker Mapping

See `mapping/wind_trip_shell_map.csv`.

Logical names:

- `wind_33`: bus 33, command `wind_disconnect_cmd[1]`, logical breaker `BR_WF33`
- `wind_35`: bus 35, command `wind_disconnect_cmd[2]`, logical breaker `BR_WF35`
- `wind_38`: bus 38, command `wind_disconnect_cmd[3]`, logical breaker `BR_WF38`

The existing PSCAD milestone uses WF-prefixed signal names. The mapping table records the bridge between the paper-style logical interface and the current PSCAD names.

## Paper VRT Criterion

For each online wind farm, let `Vs` be the PCC voltage in per unit.

- `Vs <= 0.20`: trip immediately
- `Vs >= 1.30`: trip immediately
- `0.20 < Vs < 0.90`: delay is linearly interpolated from 0.625 s at 0.20 pu to 2.0 s at 0.90 pu
- `1.25 <= Vs < 1.30`: delay is 0.5 s
- `1.20 <= Vs < 1.25`: delay is 1.0 s
- `1.10 <= Vs < 1.20`: delay is 10.0 s
- `0.90 <= Vs <= 1.10`: normal region; the timer resets

MATLAB owns the VRT decision and timer. PSCAD only measures, calls MATLAB, receives the trip command, opens the breaker, and reports breaker/online feedback.

## Verification Status

- Verification A, no-command baseline PSCAD Run: passed on the source `all_run_ok` model before this shell copy.
- Verification B, manual WF38 trip in PSCAD: not yet run. The PSCAD GUI command input and breaker latch still need to be wired manually.
- Verification C, MATLAB offline VRT input tests: passed with MATLAB R2025a using `matlab/tests/testWindVRTTripShell.m`.

## Not Implemented In This Stage

- Full paper Table 2-2 bus 29 three-phase fault chain
- 46-line overload protection in PSCAD
- UFLS/UVLS
- Conventional generator protection
- Transient overvoltage line tripping
- Fault-chain event ordering and candidate fault screening
- Verified PSCAD4.6.2 + MATLAB2016b closed-loop execution
