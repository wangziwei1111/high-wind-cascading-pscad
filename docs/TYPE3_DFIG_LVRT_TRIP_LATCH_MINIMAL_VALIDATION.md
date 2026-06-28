# Type-3 DFIG LVRT Trip-Latch Minimal Validation

## Status

execution_status: `trip_latch_minimal_validation_fail`

This round implemented and ran a single manual PSCAD R5 validation for the new
monitoring-only signals:

```text
DFIG_LVRT_TRIP_LATCH
trip-aware DFIG_LVRT_CLEAR
```

The R5 PSCAD run completed and the `.inf/.out` files were parsed, but the new
trip-latch and trip-aware CLEAR behavior did not pass acceptance.

## Scope

```text
Project: C:\pscad_work\pnnl_39_3ibr_pscad46_strip5\PSCAD\3IBR.pscx
Page:    3IBR:Main(0):P1(0):P3(0)
Branch:  codex/lvrt-trip-request-progress
Run root: C:\pscad_work\lvrt_trip_latch_minimal\20260628_171834
R5 archive: C:\pscad_work\lvrt_trip_latch_minimal\20260628_171834\R5_trip_latch_minimal
Final active SHA-256: A5E371C4F02CBEDF1C5E861A1C217D148106D3A5FFBC3858E0EB2BFF5B89E17F
Snapshot: external/pscad_snapshot_20260628_lvrt_trip_latch_minimal_failed/pnnl_39_3ibr_pscad46_strip5_PSCAD/3IBR.pscx
```

The manual PSCAD model work added `DFIG_LVRT_TRIP_LATCH` and changed CLEAR into
a trip-aware CLEAR candidate.  No `BRK_DFIG` command integration was added.

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
| TRIP_LATCH remains zero before fault | fail | `DFIG_LVRT_TRIP_LATCH` first high from 0 s = 0.01 s; prefault max = 1 |
| TRIP_LATCH sets from R5 trip request | fail | Latch was already high before the 2.02 s trip request |
| TRIP_LATCH holds after set | pass | It remained high after the event, but the set timing is invalid |
| CLEAR suppressed after trip latch | fail | `DFIG_LVRT_CLEAR` post-LOWV max = 1 |
| TIMER_S not reset after LOWV recovery | pass | `DFIG_LVRT_TIMER_S` post-LOWV value = 0.2670600000001 s |
| VSMIN_MEM not reset to 1 after LOWV recovery | pass | `DFIG_LVRT_VSMIN_MEM` post-LOWV max = 0.000079121171421309 |
| DFIG_BRK_STATE unchanged | pass | `DFIG_BRK_STATE_changed_after_startup = false` |
| PIBR1_2 / QIBR1_2 not cut off | pass | P/Q remain nonzero after the event |

Overall:

```text
Type-3 LVRT trip-latch monitoring minimal validation: fail
```

## Numeric Evidence

```text
VIBR1_2 minimum = 0.057826191277082 pu at 2.08 s
LOWV window = 2.01 s to 2.17 s
IMMTRIP first = 2.02 s
DURATION_EXCEEDED first = unavailable
TRIP_REQUEST first = 2.02 s
TRIP_REQUEST startup pulse = 0.01 s to 0.02 s
TRIP_LATCH first high from 0 s = 0.01 s
TRIP_LATCH prefault max from 0.03 s to 1.99 s = 1.0
CLEAR post-LOWV max = 1.0
DFIG_BRK_STATE changed after startup = false
PIBR1_2 mean 4.0-5.0 s = 199.19493366746346
QIBR1_2 mean 4.0-5.0 s = -21.624779208403286
```

## Interpretation

The R5 event itself is still consistent with the previously validated
TRIP_REQUEST behavior: the severe voltage dip drives `DFIG_LVRT_IMMTRIP`, and
`DFIG_LVRT_TRIP_REQUEST` asserts at 2.02 s.  However, the new latch is set by a
startup pulse before the external low-voltage event, so this run cannot validate
`DFIG_LVRT_TRIP_LATCH` as a clean trip-request latch.

The trip-aware CLEAR candidate also did not pass: after LOWV recovery, the
parsed `DFIG_LVRT_CLEAR` channel returned high even though the latch was already
high.  Therefore the CLEAR suppression behavior cannot be accepted from this
run.

## Artifacts

```text
analysis/pscad_tools/analyze_type3_dfig_lvrt_trip_latch_minimal_validation.py
data/reference/type3_dfig_lvrt_trip_latch_minimal_validation.json
data/reference/type3_dfig_lvrt_trip_latch_minimal_validation_summary.csv
docs/TYPE3_DFIG_LVRT_TRIP_LATCH_MINIMAL_VALIDATION.md
```

The PSCAD `.inf/.out` files were archived locally under
`C:\pscad_work\lvrt_trip_latch_minimal\20260628_171834\R5_trip_latch_minimal`
and were not added to Git.

## Safety Notes

```text
No BRK_DFIG command integration.
No physical breaker opening.
No actual turbine disconnection.
No MATLAB coupling.
```

## Recommended Follow-Up

The next model-editing round should fix two items before another R5 run:

1. Prevent startup transients from setting `DFIG_LVRT_TRIP_LATCH`.
2. Verify that `DFIG_LVRT_CLEAR` is driven by `DFIG_LVRT_CLEAR_BASE AND DFIG_LVRT_NOT_TRIP_LATCH` at the existing CLEAR consumers.

Do not proceed to BRK_DFIG command synthesis from this failed minimal validation.
