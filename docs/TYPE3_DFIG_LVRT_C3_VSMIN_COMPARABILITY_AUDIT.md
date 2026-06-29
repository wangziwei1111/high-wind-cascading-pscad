# Type-3 DFIG LVRT C3 VSMIN Comparability Audit

## Status

```text
execution_status = type3_lvrt_c3_vsmin_comparability_audit_complete
overall_closed_loop_coverage = partial
legacy_C3_acceptance_status = fail
command_state_chain_status = pass
decision_window_VSMIN_status = pass
full_run_historical_reference_status = fail
reference_comparability_status = needs_explanation
post_breaker_network_response_status = pass
```

This was a zero-run audit. PSCAD was not started, Built, Run, saved, or
modified. All values were parsed from existing archived `.inf/.out` files.

## Archives

```text
Current C3:
C:\pscad_work\lvrt_closed_loop_coverage\20260628_220356\C3_R4_duration_trip_breaker

Historical pre-breaker R4:
C:\pscad_work\lvrt_trip_request_matrix\20260628_111429\R4_r0p10_d1p25_8s
```

Both archives reach 8.0 s and contain the signals required for a like-for-like
decision-window comparison. The historical R4 contains TRIP_REQUEST and
VSMIN_MEM but no TRIP_LATCH or FINAL_BRK_CMD channel and no equivalent
breaker-open event.

## Decision Window

Definition:

```text
[LOWV_first_s, TRIP_REQUEST_first_s) = [2.01 s, 3.04 s)
```

The action sample at 3.04 s is strictly excluded.

| Metric | Current C3 | Historical R4 |
| --- | ---: | ---: |
| VSMIN_MEM minimum | 0.40784436868089 pu at 3.03 s | 0.40784436868089 pu at 3.03 s |
| VIBR1_2 minimum | 0.40784436868089 pu at 3.03 s | 0.40784436868089 pu at 3.03 s |
| TALLOW at last pre-request sample | 1.0332657239352 s at 3.03 s | 1.0332657239352 s at 3.03 s |
| TIMER_S at last pre-request sample | 1.0264125000025 s | 1.0264175000025 s |

The VSMIN absolute difference is `0.0 pu`, within the existing `0.02 pu`
tolerance. Therefore `decision_window_VSMIN_status = pass`.

This result describes the voltage memory actually seen before the protection
request. It does not use any breaker-open sample.

## Transition Window

TRIP_REQUEST and BRK_STATE first change at the same 10 ms output sample:

```text
transition_window = same_sample
sample_time = 3.04 s
TRIP_REQUEST = 1
TRIP_LATCH = 1
FINAL_BRK_CMD = 1
BRK_STATE = 2 (open-state indication)
VSMIN_MEM = 0.39576861791652 pu
VIBR1_2 = 0.39576861791652 pu
```

A shared output sample cannot resolve strict causality inside PSCAD internal
substeps. It verifies discrete-output ordering and consistency only.

The complete duration-based command-and-state chain remains dynamically
validated:

```text
DURATION_EXCEEDED -> TRIP_REQUEST -> TRIP_LATCH
-> FINAL_BRK_CMD -> BRK_STATE
```

## Post-Breaker Window

Definition:

```text
[BRK_STATE_first_open_s, simulation_end_s] = [3.04 s, 8.0 s]
```

```text
VSMIN_MEM post-breaker minimum = 0.3301161303713 pu at 3.26 s
VIBR1_2 post-breaker minimum = 0.33022509231603 pu at 3.25 s
VSMIN_MEM [3.20 s, 3.32 s] minimum = 0.3301161303713 pu at 3.26 s
VSMIN_MEM current full-event minimum = 0.3301161303713 pu at 3.26 s
```

The current full-event minimum occurs after BRK_STATE opened at 3.04 s and
near nominal fault clearing at 3.25 s.

## Historical Comparison

The historical R4 full-event minimum is `0.37950852707963 pu at 3.26 s`,
consistent with the retained `0.379649 pu` record. The current full-event
minimum differs by about `0.0493924 pu` from the raw historical waveform and
about `0.049533 pu` from the retained reference.

The raw numeric full-event windows are aligned in time, but their topology is
not equivalent after 3.04 s: the current run opens BRK_DFIG, while the
historical version has no equivalent breaker-open event. Consequently:

```text
decision_window_like_for_like_comparison = pass
full_run_like_for_like_comparison = fail
post_breaker_window_comparison = not_applicable
reference_comparability_status = needs_explanation
```

The original full-run C3 check is retained unchanged:

```text
legacy_C3_failed_check = VSMIN_MEM_minimum_matches_reference
legacy_C3_full_run_VSMIN_MEM_minimum = 0.3301161303713 pu
legacy_reference = 0.379649 pu
legacy_tolerance = 0.02 pu
legacy_C3_acceptance_status = fail
```

## Conclusion

The C3 duration-based command-and-state chain passes dynamically. The
protection-decision-window VSMIN comparison also passes against the raw
historical R4 waveform. However, the legacy full-run historical reference
check remains failed, and post-breaker current data are not strictly
interchangeable with the historical no-breaker topology. This audit does not
promote C3 or overall closed-loop coverage to pass.
