# Type-3 DFIG LVRT Protection-State And Cascade-Export Interface

## Status

```text
execution_status = protection_state_interface_static_audit_complete
structure_status = pass
control_path_isolation_status = pass
output_channel_status = pass
dynamic_behavior_status = unavailable
```

The Type-3 LVRT protection-state and cascade-export interface was manually
constructed in PSCAD and statically Build-verified. No new PSCAD dynamic run
was performed, no multi-machine cascade behavior was validated, and no MATLAB
coupling was added.

## Scope And Evidence

```text
Project: C:\pscad_work\pnnl_39_3ibr_pscad46_strip5\PSCAD\3IBR.pscx
Page: 3IBR:Main(0):P1(0):P3(0)
Task-start SHA-256: 0FB0F7E3927C1E5863F0692F6223DCF8152987BAE99AB83134DF1955C2713F17
Final SHA-256: 891DE753AE9C76AF3F7196278C80AAEC324BDB40EED84F552AAE1F2950E4836C
Final Build errors: 0
Final Build warnings/messages: unavailable (exact counts were not supplied)
PSCAD Run performed in this task: no
```

The audit reads the final project XML and generated `P3.f`. It does not edit
or execute PSCAD. The generated source confirms:

```text
IMM cause request = IMMTRIP_BOOL_MON * ARMED_BOOL_MON
Duration cause request = DURATION_BOOL_MON * ARMED_BOOL_MON
Both cause-latch initial values = 0.0
TRIP_CAUSE_CODE = 2 * IMM cause latch + 1 * duration cause latch
TRIP_CONFIRMED = TRIP_LATCH_BOOL_MON * FINAL_CMD_BOOL * BRK_OPEN_BOOL
CASCADE_AVAILABLE = NOT BRK_OPEN_BOOL
BRK_DFIG = 1.0 * DFIG_LVRT_FINAL_BRK_CMD
```

The pre-existing protected component parameters found in the task-start
baseline remain unchanged. The new interface only samples existing signals
and does not drive `TRIP_REQUEST`, `TRIP_LATCH`, `CLEAR`, `FINAL_BRK_CMD`, or
`BRK_DFIG`.

## Interface Table

| Signal | Type | Meaning | Initial value | Control impact | Dynamic status |
| --- | --- | --- | ---: | --- | --- |
| `DFIG_LVRT_TRIP_CAUSE_IMM_LATCH` | bool | Armed immediate-trip cause latched | 0 | None | No new run |
| `DFIG_LVRT_TRIP_CAUSE_DURATION_LATCH` | bool | Armed duration cause latched | 0 | None | No new run |
| `DFIG_LVRT_TRIP_CAUSE_CODE` | code | Cause code 0/1/2/3 | 0 | None | No new run |
| `DFIG_LVRT_ORIGINAL_CMD_OPEN_BOOL` | bool | Original command requests open | 0 | None | No new run |
| `DFIG_LVRT_FINAL_CMD_BOOL` | bool | Final breaker-open command | 0 | None | No new run |
| `DFIG_LVRT_BRK_OPEN_BOOL` | bool | Breaker open state | 0 | None | No new run |
| `DFIG_LVRT_TRIP_CONFIRMED` | bool | Latch, final command, and breaker-open confirmation | 0 | None | No new run |
| `DFIG_LVRT_CASCADE_AVAILABLE` | bool | DFIG branch remains available | 1 | None | No new run |

All eight Output Channels use `Transfer Data = Yes`, `Scale Factor = 1.0`,
and `Multiple Run Save = All runs`. Boolean display limits are `[0, 1.2]`;
the cause-code display limits are `[0, 3.2]`.

## Cause Code

```text
0 = no LVRT cause recorded
1 = duration cause only
2 = immediate-trip cause only
3 = both causes reached their latch conditions
```

Code 3 is diagnostic. It does not by itself prove a model error or select one
cause as primary.

## Deferred Dynamic Validation Matrix

| Case | IMM latch | Duration latch | Code | Final command | Breaker open | Confirmed | Available |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| R5 immediate trip | 1 | 0 | 2 | 1 | 1 | 1 | 0 |
| C3 duration trip | 0 | 1 | 1 | 1 | 1 | 1 | 0 |
| C2 ride-through | 0 | 0 | 0 | 0 | 0 | 0 | 1 |
| C1 no fault | 0 | 0 | 0 | 0 | 0 | 0 | 1 |

These are static expectations only. No new PSCAD dynamic run was performed
in this task.

## Preserved Historical Results

```text
C1 no-fault = pass
C2 ride-through = pass
R5 immediate trip-to-breaker = pass
C3 duration command-and-state chain = pass
legacy C3 full-run VSMIN reference check = fail
overall closed-loop coverage = partial
decision-window VSMIN comparison = pass
reference comparability = needs_explanation
```

This task does not claim validated multi-machine cascading, dynamic cause-code
behavior, MATLAB integration, physical field-breaker operation, or actual
turbine isolation.

## Cascade-Event Bus Addendum

A later zero-run static task constructed the next monitor-only layer:

```text
Type-3 LVRT cascade-event bus and single-source collector:
statically constructed and Build-verified.

No new dynamic PSCAD validation was performed.
No multi-machine cascade behavior was validated.
No MATLAB coupling was added.
```

The new source event packet reads this protection-state interface without
feeding back into the LVRT or breaker command path:

```text
DFIG_LVRT_CASCADE_EVENT_VALID = DFIG_LVRT_TRIP_CONFIRMED
DFIG_LVRT_CASCADE_EVENT_CAUSE_CODE = DFIG_LVRT_TRIP_CAUSE_CODE
DFIG_LVRT_CASCADE_EVENT_BRK_OPEN = DFIG_LVRT_BRK_OPEN_BOOL
DFIG_LVRT_CASCADE_SOURCE_AVAILABLE = DFIG_LVRT_CASCADE_AVAILABLE
DFIG_LVRT_CASCADE_FIRST_EVENT_TIME_S = first captured EVENT_VALID time
```

The single-source collector currently represents only `TYPE3_DFIG_1`; no
second source, synthetic source, multi-machine cascade behavior, or MATLAB
coupling was added. See `TYPE3_DFIG_LVRT_CASCADE_EVENT_BUS.md`.
