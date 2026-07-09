# Type-3 DFIG LVRT Trip-Request Manual Validation

## Status

execution_status: `trip_request_manual_validation_success`

This run validates the external LVRT trip-request monitoring signals only:

```text
DFIG_LVRT_TALLOW_S
DFIG_LVRT_DURATION_EXCEEDED
DFIG_LVRT_TRIP_REQUEST
```

No `TRIP_LATCH` logic was implemented in this round.  `DFIG_LVRT_CLEAR` was not modified.  `BRK_DFIG` was not connected to the monitoring logic, and no physical breaker opening or turbine disconnection was validated.

## Project State

```text
Project: C:\pscad_work\pnnl_39_3ibr_pscad46_strip5\PSCAD\3IBR.pscx
Page:    3IBR:Main(0):P1(0):P3(0)
Branch:  codex/lvrt-trip-request-progress
Run root: C:\pscad_work\lvrt_trip_request_matrix\20260628_111429
Initial active SHA-256: EEC7883194B1C57CFF4CB89524CAFEC0FA00A9C3B9414D893CCA605C0217939D
Final active SHA-256:   17AEB3DE4C7BBAD5D69DF94AD07BF6681FEF193A70228B57DCBBE0E0E5A1A38B
Snapshot: external/pscad_snapshot_20260628_lvrt_trip_request_manual_validated/pnnl_39_3ibr_pscad46_strip5_PSCAD/3IBR.pscx
```

The final active PSCAD project reflects the successful R5 validation scenario:
`0.01 ohm / 0.15 s / 5 s`, with Build `0 Errors / 2 Warnings / 12 Messages`.

## Case Results

| Case | Scenario | Run status | Acceptance | Key result |
| --- | --- | --- | --- | --- |
| R1 | no fault, 5 s | parsed | pass | No LOWV, no IMMTRIP, no duration exceed, no trip request. |
| R2 | 0.10 ohm, 0.75 s, 8 s | parsed | pass | Ride-through; TRIP_REQUEST stayed 0. |
| R3 | 0.10 ohm, 1.00 s, 8 s | parsed | pass | Duration exceed and TRIP_REQUEST asserted at 3.05 s. |
| R4 | 0.10 ohm, 1.25 s, 8 s | parsed | pass | TRIP_REQUEST asserted at 3.04 s before fault clear. |
| R5 | 0.01 ohm, 0.15 s, 5 s | parsed | pass | IMMTRIP drove TRIP_REQUEST at 2.02 s. |

## Numeric Evidence

| Case | VIBR1_2 min | VSMIN_MEM min | TALLOW representative | DURATION_EXCEEDED first | TRIP_REQUEST first | Breaker state changed |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| R1 | 0.9934519975 | 1.0000000000 | 2.0000000000 | unavailable | unavailable | false |
| R2 | 0.4591604156 | 0.4584382954 | 1.1956323528 | unavailable | unavailable | false |
| R3 | 0.4125552269 | 0.4121259457 | 1.1472058271 | 3.05 | 3.05 | false |
| R4 | 0.3795860053 | 0.3795085271 | 1.1044831135 | 3.04 | 3.04 | false |
| R5 | 0.0578261913 | 0.0578231959 | 0.6750736873 | unavailable | 2.02 | false |

For R2-R4, `DFIG_LVRT_TALLOW_S` stayed within `[0.625, 2.000]` and did not show a positive step rise during the LOWV window.

## R5 Evidence

The later manual R5 run completed and produced valid `.inf/.out` files.  The
R5 Build status visible in PSCAD was:

```text
0 Errors / 2 Warnings / 12 Messages
```

The parsed R5 result showed:

```text
VIBR1_2 minimum = 0.0578261913 pu at 2.08 s
DFIG_LVRT_IMMTRIP first = 2.02 s
DFIG_LVRT_DURATION_EXCEEDED first = unavailable
DFIG_LVRT_TRIP_REQUEST first = 2.02 s
DFIG_BRK_STATE changed after startup = false
```

This confirms that R5 trip request was produced by the immediate-trip path,
not by duration exceedance.

## Output Files

```text
analysis/pscad_tools/analyze_type3_dfig_lvrt_trip_request_manual_validation.py
data/reference/type3_dfig_lvrt_trip_request_manual_validation.json
data/reference/type3_dfig_lvrt_trip_request_manual_validation_summary.csv
external/pscad_snapshot_20260628_lvrt_trip_request_manual_validated/pnnl_39_3ibr_pscad46_strip5_PSCAD/3IBR.pscx
```

Temporary `.gf46`, `.out`, `.inf`, screenshots, and binary outputs were not added to Git.

## Safety Notes

```text
No TRIP_LATCH implementation.
No DFIG_LVRT_CLEAR modification.
No BRK_DFIG command integration.
No physical breaker opening.
No actual turbine disconnection.
No MATLAB coupling.
```
