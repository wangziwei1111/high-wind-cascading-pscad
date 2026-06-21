# MATLAB Interface Spec

Current implementation is an offline stub only.

Future PSCAD -> MATLAB variables:

- `time_s`
- `bus_voltage_pu`
- `bus_frequency_hz`
- `line_loading_pu`
- `breaker_status`
- `wind_poc_voltage_pu`
- `wind_active_power_mw`
- `device_voltage_pu`

Future MATLAB -> PSCAD neutral commands:

- `trip_line`
- `shed_load`
- `disconnect_wind_farm`
- `trip_generator`
- `trip_device`

The MATLAB package does not call PSCAD. `cfm.PscadBridgeStub` only documents interface fields and supports mock inputs for offline unit testing.

