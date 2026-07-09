# Stage 15 single GUI refactor / Build / Run sheet

Only follow this sheet after reading the Stage15 static manifests. Do not modify the protected main project or the legacy trial.

## 1. Open and Save As

Open:

```text
C:\pscad_work\pnnl_39_3ibr_pscad46_strip5\_backups\stage7_before_paper_calibrated_first_trip\PSCAD\3IBR_DFIG1_TRIAL.pscx
```

Immediately use PSCAD `Save As` and save to:

```text
C:\pscad_work\pnnl_39_3ibr_pscad46_strip5\PSCAD\3IBR_PAPER_WF33_35_38_TRIAL.pscx
```

## 2. Restore bus30 synchronous generator

- Copy one existing synchronous generator instance shell such as `G_33_0_1_DYR`.
- Paste it at the bus30 source location/interface.
- Rebind the pasted instance definition/name to `G_30_0_1_DYR`.
- Confirm the parameters are from G30: `P=250`, `Q=146.456`, `Volts=1.0475`, `Name=Wang_30`.
- Remove or disable any bus30 DFIG/IBR injection path. Do not leave bus30 DFIG/IBR in parallel.

## 3. Replace bus33 / bus35 / bus38 source branches

- Replace `G_33_0_1_DYR` with `WF33`.
- Replace `G_35_0_1_DYR` with `WF35`.
- Replace `G_38_0_1_DYR` with `WF38`.
- Use per-bus replacement P/Q:
  - WF33: P=632, Q=123.3861
  - WF35: P=650, Q=225.0912
  - WF38: P=830, Q=41.0678

## 4. Create reusable LVRT module

Create one reusable module:

```text
PAPER_WF_LVRT_TRIP
```

Instantiate exactly:

```text
WF33_LVRT_TRIP
WF35_LVRT_TRIP
WF38_LVRT_TRIP
```

Each instance input must be only its own PCC voltage. No shared state, no shared timer, no one-shot, no fixed-time trigger, no old OVL signal.

LVRT rule:

```text
Vs <= 0.20: immediate trip request
0.20 < Vs < 0.90: t_allow = 0.625 + ((Vs - 0.20)/(0.90 - 0.20))*(2.0 - 0.625)
Vs >= 0.90 and Vs < 1.10: reset/healthy low-voltage state if not already latched
1.10 <= Vs < 1.20: t_allow = 10.0 s high-voltage branch
1.20 <= Vs < 1.25: t_allow = 1.0 s high-voltage branch
1.25 <= Vs < 1.30: t_allow = 0.5 s high-voltage branch
Vs >= 1.30: immediate trip request
```

## 5. Add exactly 15 Output Channels

- WF33_PCC_V
- WF33_PCC_P
- WF33_PCC_Q
- WF33_LVRT_TRIP_REQUEST
- WF33_BRK_STATE
- WF35_PCC_V
- WF35_PCC_P
- WF35_PCC_Q
- WF35_LVRT_TRIP_REQUEST
- WF35_BRK_STATE
- WF38_PCC_V
- WF38_PCC_P
- WF38_PCC_Q
- WF38_LVRT_TRIP_REQUEST
- WF38_BRK_STATE

## 6. Settings then Build

- Solution Time Step: `50 us`
- Plot Step: `0.01 s`
- Run Duration: `20.0 s`

Save, then Build. If Build errors require new design choices, stop and report the exact error.

After Build Errors = 0, run:

```text
tools\stage15_pre_run_gate.cmd
```
