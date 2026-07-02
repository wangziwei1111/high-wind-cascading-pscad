# Type-3 DFIG LVRT Trip-Latch Minimal Validation

## Status

execution_status: `trip_latch_minimal_validation_pass`

This round implements and validates the monitoring-only `DFIG_LVRT_TRIP_LATCH`
and trip-aware `DFIG_LVRT_CLEAR` behavior using the single allowed R5 PSCAD run.

## Scope

```text
Project: C:\pscad_work\pnnl_39_3ibr_pscad46_strip5\PSCAD\3IBR.pscx
Page:    3IBR:Main(0):P1(0):P3(0)
Branch:  codex/lvrt-trip-request-progress
Run root: C:\pscad_work\lvrt_trip_latch_minimal\20260628_171834
R5 archive: C:\pscad_work\lvrt_trip_latch_minimal\20260628_171834\R5_trip_latch_fix_validation
Final active SHA-256: 00C72FAAE357F113DC26C486180A7AA374AACA81BC698B87D9FAB3D706AF1DF9
Snapshot: external/pscad_snapshot_20260628_lvrt_trip_latch_minimal_validated/pnnl_39_3ibr_pscad46_strip5_PSCAD/3IBR.pscx
```

The PSCAD model fix adds an armed gate before the latch input:

```text
TIME > 0.5 s -> DFIG_LVRT_ARMED

DFIG_LVRT_TRIP_REQUEST
DFIG_LVRT_ARMED
-> Multiplier
-> DFIG_LVRT_TRIP_REQUEST_ARMED
-> TRIP_LATCH set comparator
```

The old CLEAR output channel is now named `DFIG_LVRT_CLEAR_BASE`, while the
final trip-aware CLEAR output channel is named `DFIG_LVRT_CLEAR`.

## R5 Scenario

```text
Fault type = ABC-to-ground
Fault ON Resistance = 0.01 ohm
Fault start = 2.0 s
Fault duration = 0.15 s
Fault OFF Resistance = 1.0E6 ohm
Wind speed = 11 m/s
Solution time step = 5 us
Total simulation time = 5.0 s
Channel plot step = 10000 us
```

## Result

| Item | Status | Evidence |
| --- | --- | --- |
| R5 run reached 5 s | pass | simulation_end_s = 5.0 |
| R5 immediate trip request path | pass | `DFIG_LVRT_IMMTRIP` first = 2.02 s; `DFIG_LVRT_TRIP_REQUEST` first = 2.02 s |
| Duration-exceeded path stays inactive | pass | `DFIG_LVRT_DURATION_EXCEEDED` did not assert after startup ignore |
| TRIP_LATCH initial sample is zero | pass | `DFIG_LVRT_TRIP_LATCH` at 0.0 s = 0 |
| TRIP_LATCH remains zero before fault | pass | prefault max from 0.03 s to 1.99 s = 0 |
| TRIP_LATCH sets from R5 trip request | pass | `DFIG_LVRT_TRIP_LATCH` first high = 2.02 s |
| TRIP_LATCH holds after set | pass | `DFIG_LVRT_TRIP_LATCH_holds_after_trip_request = true` |
| CLEAR suppressed after trip latch | pass | `DFIG_LVRT_CLEAR` post-LOWV max = 0 |
| TIMER_S not reset after LOWV recovery | pass | `DFIG_LVRT_TIMER_S` post-LOWV value = 0.1676450000001 s |
| VSMIN_MEM not reset to 1 after LOWV recovery | pass | `DFIG_LVRT_VSMIN_MEM` post-LOWV max = 0.057823195871257 |
| DFIG_BRK_STATE unchanged | pass | `DFIG_BRK_STATE_changed_after_startup = false` |
| PIBR1_2 / QIBR1_2 not cut off | pass | P/Q remain nonzero after the event |

Overall:

```text
Type-3 LVRT trip-latch monitoring minimally validated.
```

## Numeric Evidence

```text
VIBR1_2 minimum = 0.057826191277082 pu at 2.08 s
VSMIN_MEM minimum = 0.057823195871257 pu at 2.09 s
LOWV window = 2.01 s to 2.17 s
IMMTRIP first = 2.02 s
DURATION_EXCEEDED first = unavailable
TRIP_REQUEST first = 2.02 s
TRIP_REQUEST startup pulse = 0.01 s to 0.02 s
TRIP_LATCH first high from 0 s = 2.02 s
TRIP_LATCH prefault max from 0.03 s to 1.99 s = 0.0
CLEAR post-LOWV max = 0.0
DFIG_BRK_STATE changed after startup = false
PIBR1_2 mean 4.0-5.0 s = 199.19493366746346
QIBR1_2 mean 4.0-5.0 s = -21.624779208403286
```

## Interpretation

The original `DFIG_LVRT_TRIP_REQUEST` still has a startup pulse at 0.01-0.02 s,
but `DFIG_LVRT_ARMED` blocks it from the latch input.  The latch remains low
before the external low-voltage event and first asserts with the R5 trip request
at 2.02 s.

After LOWV recovery, `DFIG_LVRT_CLEAR` remains suppressed while the latch is
high.  The timer and VSMIN memory therefore do not reset after the latched trip
request in this monitoring-only validation.

## Artifacts

```text
analysis/pscad_tools/analyze_type3_dfig_lvrt_trip_latch_minimal_validation.py
data/reference/type3_dfig_lvrt_trip_latch_minimal_validation.json
data/reference/type3_dfig_lvrt_trip_latch_minimal_validation_summary.csv
docs/TYPE3_DFIG_LVRT_TRIP_LATCH_MINIMAL_VALIDATION.md
```

The PSCAD `.inf/.out` files were archived locally under
`C:\pscad_work\lvrt_trip_latch_minimal\20260628_171834\R5_trip_latch_fix_validation`
and were not added to Git.

## Safety Notes

```text
No BRK_DFIG command integration.
No physical breaker opening.
No actual turbine disconnection.
No MATLAB coupling.
```

## Next Step

This validates monitoring behavior only.  It does not authorize or implement
any `BRK_DFIG` command synthesis.
