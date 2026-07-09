# Type-3 DFIG LVRT Cascade-Event Bus And Single-Source Collector

## Status

```text
execution_status = cascade_event_bus_static_audit_complete
structure_status = pass
control_path_isolation_status = pass
output_channel_status = pass
dynamic_behavior_status = unavailable
multi_source_behavior_status = unavailable
```

Type-3 LVRT cascade-event bus and single-source collector statically
constructed and Build-verified.

No new dynamic PSCAD validation was performed.
No multi-machine cascade behavior was validated.
No MATLAB coupling was added.

## Scope And Evidence

```text
Project: C:\pscad_work\pnnl_39_3ibr_pscad46_strip5\PSCAD\3IBR.pscx
Page: 3IBR:Main(0):P1(0):P3(0)
Source ID: TYPE3_DFIG_1
Task-start SHA-256: 891DE753AE9C76AF3F7196278C80AAEC324BDB40EED84F552AAE1F2950E4836C
Final SHA-256: 9A4D8B4594CDEAC3085E34BE64A6A52DA0CB626FE91E37240D0C8CE74F6D33DB
Final Build errors: 0
Final Build warnings/messages: unavailable
PSCAD Run performed in this task: no
```

The audit reads the final project XML and generated `P3.f`. It does not edit
or execute PSCAD. PSCAD internal signal names are shortened where needed, but
Output Channel titles expose the full interface names.

## Interface Table

| Signal | Layer | Type | Initial value | Meaning | Dynamic status |
| --- | --- | --- | ---: | --- | --- |
| `DFIG_LVRT_CASCADE_EVENT_VALID` | source | bool | 0 | Confirmed LVRT opening event | No new run |
| `DFIG_LVRT_CASCADE_EVENT_CAUSE_CODE` | source | code | 0 | LVRT cause code for this source | No new run |
| `DFIG_LVRT_CASCADE_EVENT_BRK_OPEN` | source | bool | 0 | Breaker actually open for this source | No new run |
| `DFIG_LVRT_CASCADE_SOURCE_AVAILABLE` | source | bool | 1 | Current source availability state | No new run |
| `DFIG_LVRT_CASCADE_FIRST_EVENT_TIME_S` | source | real | -1 | First confirmed event time | No new run |
| `CASCADE_MONITOR_ANY_TRIP` | collector | bool | 0 | Any trip among connected real sources | No new run |
| `CASCADE_MONITOR_ANY_BRK_OPEN` | collector | bool | 0 | Any breaker open among connected real sources | No new run |
| `CASCADE_MONITOR_AVAILABLE_SOURCE_COUNT` | collector | count | 1 | Count of currently available real connected sources | No new run |
| `CASCADE_MONITOR_FIRST_EVENT_TIME_S` | collector | real | -1 | Current single-source first event time | No new run |
| `CASCADE_MONITOR_CAUSE_CODE_DFIG1` | collector | code | 0 | Cause code for current Type-3 DFIG source | No new run |

## Source Event Packet

The current source packet is monitor-only and reads the existing protection
state interface:

```text
DFIG_LVRT_CASCADE_EVENT_VALID =
  DFIG_LVRT_TRIP_CONFIRMED

DFIG_LVRT_CASCADE_EVENT_CAUSE_CODE =
  DFIG_LVRT_TRIP_CAUSE_CODE

DFIG_LVRT_CASCADE_EVENT_BRK_OPEN =
  DFIG_LVRT_BRK_OPEN_BOOL

DFIG_LVRT_CASCADE_SOURCE_AVAILABLE =
  DFIG_LVRT_CASCADE_AVAILABLE
```

Because PSCAD rejected several long internal signal names, these full field
names are exposed through Output Channel titles. The internal implementation
uses:

```text
DFIG_LVRT_CAS_CAUSE_CODE      -> DFIG_LVRT_CASCADE_EVENT_CAUSE_CODE
DFIG_LVRT_CAS_SRC_AVAIL       -> DFIG_LVRT_CASCADE_SOURCE_AVAILABLE
DFIG_LVRT_CAS_FIRST_TIME_S    -> DFIG_LVRT_CASCADE_FIRST_EVENT_TIME_S
```

The cause-code definition is inherited unchanged:

```text
0 = no LVRT cause recorded
1 = duration cause only
2 = immediate-trip cause only
3 = both causes latched
```

## First Event Time

`DFIG_LVRT_CASCADE_FIRST_EVENT_TIME_S` records the first simulation time at
which `DFIG_LVRT_CASCADE_EVENT_VALID` becomes true. The memory initial value
is `-1.0 s`, meaning no confirmed event has yet been captured.

The generated source confirms:

```text
DFIG_LVRT_CAS_TIME_UNSET = 1 when DFIG_LVRT_CAS_TIME_MEM < 0
DFIG_LVRT_CAS_TIME_CAP =
  DFIG_LVRT_CASCADE_EVENT_VALID * DFIG_LVRT_CAS_TIME_UNSET

if DFIG_LVRT_CAS_TIME_CAP = 1:
  DFIG_LVRT_CAS_TIME_NEXT = TIME
else:
  DFIG_LVRT_CAS_TIME_NEXT = DFIG_LVRT_CAS_TIME_MEM

IF (TIMEZERO) DFIG_LVRT_CAS_TIME_MEM = -1.0
DFIG_LVRT_CAS_FIRST_TIME_S = 1.0 * DFIG_LVRT_CAS_TIME_MEM
```

This is a static structural check only. The first-event time has not been
dynamically validated in this task.

## Single-Source Collector

The current collector accepts only `TYPE3_DFIG_1`. It is not a whole-system
cascade bus and it does not include synthetic future sources.

```text
CASCADE_MONITOR_ANY_TRIP =
  DFIG_LVRT_CASCADE_EVENT_VALID

CASCADE_MONITOR_ANY_BRK_OPEN =
  DFIG_LVRT_CASCADE_EVENT_BRK_OPEN

CASCADE_MONITOR_AVAILABLE_SOURCE_COUNT =
  1.0 * DFIG_LVRT_CASCADE_SOURCE_AVAILABLE

CASCADE_MONITOR_FIRST_EVENT_TIME_S =
  DFIG_LVRT_CASCADE_FIRST_EVENT_TIME_S

CASCADE_MONITOR_CAUSE_CODE_DFIG1 =
  DFIG_LVRT_CASCADE_EVENT_CAUSE_CODE
```

The source-count value is the number of currently available real sources
connected to this collector. Since only `TYPE3_DFIG_1` exists in this
collector, the value is limited to `0` or `1`.

## Output Channels

The ten new Output Channels use `Transfer Data = Yes`, `Scale Factor = 1.0`,
`Multiple Run Save = All runs`, and `Use signal name as title = No`.

Boolean channels use display limits `[0, 1.2]`; cause-code channels use
`[0, 3.2]`; first-event time channels use `[-1.2, 10.2]`; the source-count
channel uses `[0, 1.2]`.

## Control Isolation

The audit confirms the existing command path is preserved:

```text
RT_23 =
  DFIG_LVRT_EXISTING_BRK_CMD_BOOL + DFIG_LVRT_TRIP_LATCH_BOOL

DFIG_LVRT_FINAL_BRK_CMD = LIMIT(0.0, 1.0, RT_23)
BRK_DFIG = 1.0 * DFIG_LVRT_FINAL_BRK_CMD
```

No new packet or collector signal drives `TRIP_REQUEST`, `TRIP_LATCH`,
`CLEAR`, `FINAL_BRK_CMD`, or `BRK_DFIG`.

## Future Multi-Source Naming Rule

Future real sources should use:

```text
<source>_CASCADE_EVENT_VALID
<source>_CASCADE_EVENT_CAUSE_CODE
<source>_CASCADE_EVENT_BRK_OPEN
<source>_CASCADE_SOURCE_AVAILABLE
<source>_CASCADE_FIRST_EVENT_TIME_S
```

Examples such as `TYPE3_DFIG_2_CASCADE_EVENT_VALID`,
`TYPE4_WTG_1_CASCADE_EVENT_VALID`, and `IBR_1_CASCADE_EVENT_VALID` are naming
examples only. They were not created in PSCAD.

Future collector expansion should use:

```text
ANY_TRIP = MAX(all real source EVENT_VALID)
ANY_BRK_OPEN = MAX(all real source EVENT_BRK_OPEN)
AVAILABLE_SOURCE_COUNT = SUM(all real source SOURCE_AVAILABLE)
EARLIEST_EVENT_TIME = minimum nonnegative FIRST_EVENT_TIME_S across real sources only
CAUSE_CODE per source = separate per-source fields
```

Do not add cause codes across sources and interpret the sum as one protection
reason.

## Deferred Dynamic Validation Matrix

These are static interface expectations only. No dynamic PSCAD validation was
performed in this task.

| Case | EVENT_VALID | EVENT_CAUSE_CODE | EVENT_BRK_OPEN | SOURCE_AVAILABLE | FIRST_EVENT_TIME_S | ANY_TRIP | ANY_BRK_OPEN | AVAILABLE_SOURCE_COUNT | COLLECTOR_FIRST_EVENT_TIME_S | CAUSE_CODE_DFIG1 |
| --- | ---: | ---: | ---: | ---: | --- | ---: | ---: | ---: | --- | ---: |
| R5 immediate trip | 1 | 2 | 1 | 0 | approximately 2.02 | 1 | 1 | 0 | approximately 2.02 | 2 |
| C3 duration trip | 1 | 1 | 1 | 0 | approximately 3.04 | 1 | 1 | 0 | approximately 3.04 | 1 |
| C2 ride-through | 0 | 0 | 0 | 1 | -1 | 0 | 0 | 1 | -1 | 0 |
| C1 no fault | 0 | 0 | 0 | 1 | -1 | 0 | 0 | 1 | -1 | 0 |

## Claim Boundary

This task does not validate multi-machine cascade propagation, dynamic event
time behavior, dynamic cause-code behavior, field breaker operation, physical
turbine isolation, or MATLAB integration.

## 2026-06-30 trial dual-source extension

The independent trial retains this source-1 packet unchanged and adds
`IBR2_TRIAL` as a second real monitor source. The collector statically combines
two event-valid, breaker-open, availability, per-source cause, and first-event
time interfaces. No Run was performed.
