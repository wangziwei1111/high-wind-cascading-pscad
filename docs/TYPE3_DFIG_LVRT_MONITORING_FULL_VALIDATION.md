# Type-3 DFIG LVRT Monitoring Full Validation

## Task Scope

This run attempted to extend the existing Type-3 DFIG external LVRT monitoring scaffold from `VIBR1_2 -> LOWV -> IMMTRIP -> TIMER_S -> VSMIN_MEM` to the full monitoring-only chain:

```text
VSMIN_MEM -> TALLOW_S -> DURATION_EXCEEDED -> TRIP_REQUEST -> TRIP_LATCH
```

The task explicitly did not connect, disconnect, reroute, inspect, or drive the `BRK_DFIG` command line.

## Computer Use

Computer Use was used for PSCAD GUI operations: PSCAD was inspected, closed without saving stale in-memory state, relaunched, loaded through the Open dialog, and Build was attempted from the GUI.

## PSCAD Hashes And Backup

Initial active PSCAD SHA-256:

```text
02F3B8FCB5A53286886447C2EA1D0EA1C2E4F7AA0B42CC4FA694D2C5BD884202
```

Final active PSCAD SHA-256:

```text
02F3B8FCB5A53286886447C2EA1D0EA1C2E4F7AA0B42CC4FA694D2C5BD884202
```

Initial backup:

```text
C:\pscad_work\backups\type3_lvrt_monitoring_full_20260627_121401\3IBR.pscx
```

Stage edit backup:

```text
C:\pscad_work\backups\type3_lvrt_monitoring_full_stage_edit_20260627_121604\3IBR.pscx
```

Final snapshot:

```text
external/pscad_snapshot_20260627_lvrt_monitoring_full/pnnl_39_3ibr_pscad46_strip5_PSCAD/3IBR.pscx
```

## Build Information

Initial PSCAD Build view:

```text
0 Errors
2 Warnings
13 Messages
```

The two warnings are the already known `XFMR_DFIG_22_33` suspicious floating-terminal warnings.

The attempted full-monitoring edit did not remain Build-clean after unattended PSCAD reload. PSCAD showed a failed Build in the temporary workspace. Per the safety rule, the active project was restored to the stage-start Build=0 project instead of retaining the failed edit.

Final status is therefore:

```text
monitoring_logic_safe_fallback
```

## VSMIN Dynamic Validation

`DFIG_LVRT_VSMIN_MEM` was not promoted to canonical `Vs_min_latched` in this run. No post-edit scenario-local `3IBR.inf` and `3IBR_*.out` files were available after rollback, so the VSMIN waveform checks are recorded as `unavailable`, not pass.

## Attempted Implementation

The attempted, non-retained implementation used only monitoring logic:

```text
TALLOW_RAW = 0.625 + ((DFIG_LVRT_VSMIN_MEM - 0.20) / 0.70) * 1.375
DFIG_LVRT_TALLOW_S = clamp(TALLOW_RAW, 0.625, 2.000)
DFIG_LVRT_DURATION_EXCEEDED = DFIG_LVRT_LOWV AND (DFIG_LVRT_TIMER_S >= DFIG_LVRT_TALLOW_S)
DFIG_LVRT_TRIP_REQUEST = DFIG_LVRT_IMMTRIP OR DFIG_LVRT_DURATION_EXCEEDED
DFIG_LVRT_TRIP_LATCH = latched(TRIP_REQUEST), initial 0
DFIG_LVRT_CLEAR = NOT DFIG_LVRT_LOWV AND NOT DFIG_LVRT_TRIP_LATCH
```

This implementation was rolled back and is not present in the final `.pscx`.

## Validation Matrix

All five required scenarios are unavailable in this fallback:

```text
E1 5 s no fault: unavailable
E2 0.10 ohm / 0.75 s / 8 s: unavailable
E3 0.10 ohm / 1.00 s / 8 s: unavailable
E4 0.10 ohm / 1.25 s / 8 s: unavailable
E5 0.01 ohm / 0.15 s / 5 s: unavailable
```

No unavailable item is counted as pass.

## Breaker Status

No `BRK_DFIG` command connection was made. No actual breaker opening was tested. No monitoring signal was written as an actual disconnection or turbine trip.

## Restoration

The final project was restored by copying back the exact stage-start PSCAD file. This restores the stage-start fault parameters, total simulation time, time step, and monitoring scaffold state.

## Limitations

The full monitoring chain remains future work. The next attempt should load the original PSCAD project/library context before editing, verify a Build-clean minimal TALLOW-only insertion first, and only then add duration and latch logic in separate Build checkpoints.
