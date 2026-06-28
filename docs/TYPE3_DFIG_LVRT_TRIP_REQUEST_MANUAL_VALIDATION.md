# Type-3 DFIG LVRT Trip-Request Manual Validation

## Status

execution_status: `trip_request_manual_validation_partial_or_fallback`

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
Final active SHA-256:   EEC7883194B1C57CFF4CB89524CAFEC0FA00A9C3B9414D893CCA605C0217939D
Snapshot: external/pscad_snapshot_20260628_lvrt_trip_request_manual_validated/pnnl_39_3ibr_pscad46_strip5_PSCAD/3IBR.pscx
```

The final active PSCAD project was restored to the task-start SHA after the partial validation attempt.

## Case Results

| Case | Scenario | Run status | Acceptance | Key result |
| --- | --- | --- | --- | --- |
| R1 | no fault, 5 s | parsed | pass | No LOWV, no IMMTRIP, no duration exceed, no trip request. |
| R2 | 0.10 ohm, 0.75 s, 8 s | parsed | pass | Ride-through; TRIP_REQUEST stayed 0. |
| R3 | 0.10 ohm, 1.00 s, 8 s | parsed | pass | Duration exceed and TRIP_REQUEST asserted at 3.05 s. |
| R4 | 0.10 ohm, 1.25 s, 8 s | parsed | pass | TRIP_REQUEST asserted at 3.04 s before fault clear. |
| R5 | 0.01 ohm, 0.15 s, 5 s | unavailable | unavailable | PSCAD reload/build path failed before a valid R5 `.out` set was produced. |

## Numeric Evidence

| Case | VIBR1_2 min | VSMIN_MEM min | TALLOW representative | DURATION_EXCEEDED first | TRIP_REQUEST first | Breaker state changed |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| R1 | 0.9934519975 | 1.0000000000 | 2.0000000000 | unavailable | unavailable | false |
| R2 | 0.4591604156 | 0.4584382954 | 1.1956323528 | unavailable | unavailable | false |
| R3 | 0.4125552269 | 0.4121259457 | 1.1472058271 | 3.05 | 3.05 | false |
| R4 | 0.3795860053 | 0.3795085271 | 1.1044831135 | 3.04 | 3.04 | false |
| R5 | unavailable | unavailable | unavailable | unavailable | unavailable | unavailable |

For R2-R4, `DFIG_LVRT_TALLOW_S` stayed within `[0.625, 2.000]` and did not show a positive step rise during the LOWV window.

## R5 Fallback

R5 was not marked pass.  After reopening PSCAD from the restored project file and library, GUI Build failed with:

```text
203 Errors / 40 Warnings / 33 Messages
```

The first visible errors included `master:select` signal type conversion messages, `master:ammeter` unresolved/open-circuit messages, and `No branches to ground found in subsystem 1`.

A separate read-only fallback attempt copied a previously successful generated EMTDC directory, patched the generated `P3.f` constants to `0.01 ohm` and `0.15 s`, and rebuilt successfully with `make`.  Direct execution of the rebuilt `3IBR.exe` produced no `3IBR_*.out` files because the executable requires a PSCAD runtime session.  Therefore R5 remains `unavailable`.

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
