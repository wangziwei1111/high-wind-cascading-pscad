# WF33/WF35/WF38 Type-3 PSCAD Milestone

This directory contains the PSCAD milestone model:

- `PNNL_39_WF33_WF35_WF38_Type3_all_run_ok.pscx`
- `PNNL_39_WF33_WF35_WF38_Type3_all_run_ok.psmx`

Milestone status:

- Replaced the original thermal generators at buses 33, 35, and 38 with Type-3 average wind farms.
- Used equal active-power replacement against the original generator outputs:
  - WF33: 632 MW target, `No_WTG = 316`, transformer `790 MVA`
  - WF35: 650 MW target, `No_WTG = 325`, transformer `812.5 MVA`
  - WF38: 830 MW target, `No_WTG = 415`, transformer `1037.5 MVA`
- Confirmed PSCAD Build and Run complete successfully.
- Confirmed steady-state outputs are close to the replacement targets:
  - WF33 active power about 629 MW
  - WF35 active power about 647 MW
  - WF38 active power about 825 MW
  - WTG-side voltages are near 33 kV
  - wind-farm breakers remain closed

Protection status:

- MATLAB/PSCAD voltage ride-through and cascading protection logic is not implemented in this milestone model.
- This model is intended as the clean electrical starting point before adding MATLAB-driven protection and trip commands.
