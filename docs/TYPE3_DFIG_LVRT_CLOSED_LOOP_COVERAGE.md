# Type-3 DFIG LVRT Closed-Loop Coverage

## Status

```text
execution_status = type3_lvrt_closed_loop_coverage_partial
C1 no-fault = pass
C2 R2 ride-through = pass
C3 R4 duration trip-to-breaker = fail
model_integrity = model_integrity_nonfunctional_metadata_difference
```

The no-fault and ride-through paths were dynamically validated. The C3
duration-based command-and-state chain also passed, but the formal C3 result
is fail because its measured VSMIN_MEM minimum exceeded the specified
historical-reference tolerance. The complete matrix therefore remains partial.

## Execution Scope

The initial C1 run was performed by Codex through Computer Use. After the
floating Gain was restored, the user manually performed the supplemental C2
and C3 GUI parameter changes, Builds, and Runs. Codex archived and analyzed
all run artifacts and handled all repository work.

No LVRT logic, Output Channel, BRK_DFIG main-circuit parameter, automatic
reclosing logic, Type3WTG_Lib content, or MATLAB coupling was intentionally
changed. R5 was not rerun.

## Baseline And Integrity

```text
Project: C:\pscad_work\pnnl_39_3ibr_pscad46_strip5\PSCAD\3IBR.pscx
Page: 3IBR:Main(0):P1(0):P3(0)
Branch: codex/lvrt-trip-request-progress
Task-start SHA-256: DA4518483523C1BCAFF2A74AAC356B29B53F9642A8E9D7E9E44FCDA2E96F90E6
Backup SHA-256: DA4518483523C1BCAFF2A74AAC356B29B53F9642A8E9D7E9E44FCDA2E96F90E6
Final active SHA-256: 0FB0F7E3927C1E5863F0692F6223DCF8152987BAE99AB83134DF1955C2713F17
```

The task-start parameters were restored through the PSCAD GUI:

```text
Fault type = ABC-to-ground
Fault ON Resistance = 0.01 ohm
Fault start = 2.0 s
Fault duration = 0.15 s
Fault OFF Resistance = 1.0E6 ohm
Wind speed = 11 m/s
Solution time step = 5 us
Total simulation time = 5.0 s
```

The final SHA does not match the task-start SHA. The previously floating
`master:gain` ID `65646757` is no longer present. A read-only comparison still
shows saved revision and run-display differences from the task-start on-disk
backup. No direct XML repair or backup substitution was performed. Before the
structural audit, this was conservatively recorded as
`model_integrity_needs_explanation`; the later addendum classifies the observed
differences using direct XML evidence.

## Build Record

| Stage | Errors | Warnings | Messages | Decision |
| --- | ---: | ---: | ---: | --- |
| Precheck | 0 | 46 | 119 | permitted C1 |
| C1 | 0 | 46 | 119 | permitted one Run |
| C1 Run compile | 0 | 0 | 11 | Run completed |
| Initial C2 attempt | 1 | 37 | 33 | Run prohibited; stop matrix |
| Supplemental recovery Build | 0 | 46 | 119 | permitted C2 |
| Supplemental C2 | 0 | unavailable | unavailable | Run completed |
| Supplemental C3 | 0 | unavailable | unavailable | Run completed |
| Final restored-parameter Build | 0 | unavailable | unavailable | user reported completed |

The initial C2 Build error identified `master:gain` ID `65646757` with a
floating `IN:Dim` input. The user restored the Gain and supplied a recovery
Build screenshot showing `0 Errors / 46 Warnings / 119 Messages`. Exact
warning/message counts for the later C2, C3, and final Builds were not supplied.

No EMTDC Runtime Error, `Ungrounded subsystem`, or abnormal Run termination
occurred in the completed supplemental runs.

## C1 No-Fault Evidence

The single C1 run reached 5.000 s. Its archived `3IBR.inf` contains all 15
required signals. All C1 checks pass.

```text
VIBR1_2 minimum after 0.5 s = 0.99350715027154 pu
VSMIN_MEM minimum after 0.5 s = 1.0 pu
LOWV, IMMTRIP, DURATION_EXCEEDED = 0
TRIP_REQUEST, TRIP_LATCH = 0
EXISTING_BRK_CMD, FINAL_BRK_CMD, BRK_STATE = 0
PIBR1_2 post-event-window mean = 199.04263076352905
QIBR1_2 post-event-window mean = -16.45742835365371
```

This validates the no-fault, no-false-opening behavior in PSCAD for the
archived C1 run.

## C2 Ride-Through

C2 R2 completed to 8.0 s and all checks pass:

```text
LOWV interval = 2.01 to 3.10 s
VIBR1_2 minimum = 0.45866329080834 pu
VSMIN_MEM minimum = 0.45843829537505 pu
TALLOW range = 1.1326466513557 to 2.0 s
IMMTRIP, DURATION_EXCEEDED, TRIP_REQUEST = 0
TRIP_LATCH, FINAL_BRK_CMD, BRK_STATE = 0
PIBR1_2 post-event mean = 199.0569662232042
```

CLEAR, TIMER_S, and VSMIN_MEM recovered correctly after LOWV ended. No
ride-through false opening occurred.

## C3 Duration-Based Trip

C3 R4 completed to 8.0 s. Every command-and-state check passes:

```text
DURATION_EXCEEDED first = 3.04 s
TRIP_REQUEST first = 3.04 s
TRIP_LATCH first = 3.04 s
FINAL_BRK_CMD first = 3.04 s
BRK_STATE first open = 3.04 s
TRIP_LATCH to FINAL_BRK_CMD delay = 0.0 s
FINAL_BRK_CMD to BRK_STATE delay = 0.0 s
TRIP_LATCH, FINAL_BRK_CMD, and BRK_STATE hold through 8.0 s
IMMTRIP does not assert
```

The request precedes nominal fault clearing at 3.25 s. P/Q fall after breaker
opening and are retained only as supporting electrical-response evidence.

Formal C3 acceptance is `fail` because `VSMIN_MEM minimum =
0.3301161303713 pu`, an absolute difference of about 0.049533 pu from the
specified 0.379649 pu reference. The minimum occurs at 3.26 s, after the
3.04 s breaker opening and near fault clearing. This voltage-reference failure
does not erase the separately passing command-and-state sequence.

## Prior R5 Evidence

The prior R5 evidence remains valid and separate:

```text
TRIP_REQUEST first = 2.02 s
TRIP_LATCH first = 2.02 s
FINAL_BRK_CMD first = 2.02 s
BRK_STATE first open = 2.02 s
BRK_STATE holds open = true
```

It validates the immediate-trip command-and-state path in PSCAD and remains
separate from the new C2/C3 evidence.

## Command Priority And Claim Boundary

Static command-composition audit passed. The original command source is
constant 0 in the tested model, so a dynamic original-command-open stimulus
was not performed.

This result does not validate field hardware, certify a physical breaker,
prove actual turbine isolation, validate multi-machine cascading, or validate
MATLAB co-simulation. P/Q are supporting electrical-response evidence only.

## Artifacts

```text
analysis/pscad_tools/analyze_type3_dfig_lvrt_closed_loop_coverage.py
data/reference/type3_dfig_lvrt_closed_loop_coverage.json
data/reference/type3_dfig_lvrt_closed_loop_coverage_summary.csv
docs/TYPE3_DFIG_LVRT_CLOSED_LOOP_COVERAGE.md
```

Raw `.inf/.out` files and logs remain only under the local run root and are
not committed.

## C3 VSMIN Comparability Addendum

The zero-run comparability audit found the raw historical R4 archive and
applied the same pre-request window to both runs:

```text
decision window = [2.01 s, 3.04 s)
current VSMIN minimum = 0.40784436868089 pu at 3.03 s
historical VSMIN minimum = 0.40784436868089 pu at 3.03 s
decision-window absolute difference = 0.0 pu
decision_window_VSMIN_status = pass
```

The current full-event minimum `0.3301161303713 pu at 3.26 s` occurs after
BRK_STATE opened at 3.04 s. The historical R4 has no equivalent breaker-open
event. Therefore the legacy full-run reference check remains `fail`, while
`reference_comparability_status = needs_explanation`. C3 and overall coverage
remain unchanged; see `TYPE3_DFIG_LVRT_C3_VSMIN_COMPARABILITY_AUDIT.md`.

## Model Integrity Addendum

A read-only XML/structure audit compared the exact task-start backup with the
current active project. All 128 detected differences are revision, layout,
display stacking, or saved run-display metadata. There are zero functional,
test-parameter, Output Channel, wire, or unclassified differences. Gain ID
`65646757` is absent from both projects.

```text
model_integrity_status = model_integrity_nonfunctional_metadata_difference
```

The byte SHA values remain different; byte identity is not claimed. See
`TYPE3_DFIG_LVRT_MODEL_INTEGRITY_AUDIT.md`.

## Protection-State Interface Addendum

A zero-run static audit verified the newly added monitor-only protection-state
and cascade-export interface:

```text
structure_status = pass
control_path_isolation_status = pass
output_channel_status = pass
dynamic_behavior_status = unavailable
```

This addendum does not alter the scenario matrix. C1 and C2 remain pass, the
C3 command-and-state chain remains pass, the legacy C3 full-run VSMIN check
remains fail, and overall closed-loop coverage remains partial. The interface
has not been dynamically validated in C1/C2/C3/R5 and does not establish
multi-machine cascade behavior.

## Cascade-Event Bus Addendum

A zero-run static audit verified the monitor-only cascade-event source packet
and current single-source collector:

```text
structure_status = pass
control_path_isolation_status = pass
output_channel_status = pass
dynamic_behavior_status = unavailable
multi_source_behavior_status = unavailable
```

This addendum does not alter the scenario matrix. C1 and C2 remain pass, the
C3 command-and-state chain remains pass, the legacy C3 full-run VSMIN check
remains fail, and overall closed-loop coverage remains partial. No new PSCAD
Run was performed, and the collector has not validated multi-machine cascade
behavior.

## Trial dual-source static interface addendum

The independent trial now exposes two real-source event interfaces and static
ordering logic. Historical C1/C2/C3/R5 results and overall coverage are
unchanged. Dual-source dynamic behavior and cascade propagation remain
unavailable because no new Run was performed.

## Trial chronology-monitor addendum

The default-disabled IBR2 test stimulus and chronology monitor do not change
the historical C1/C2/C3/R5 scenario results or the partial overall coverage
status. Their static structure and nine Output Channels pass audit, while
dynamic source-2 opening, event timing, dual-source interaction, and cascade
propagation remain unavailable.

## IBR3 three-source static addendum

The trial-only third-source deployment and three-source collector pass static
structure, control-isolation, and Output Channel audits. Historical
C1/C2/C3/R5 results and partial overall coverage are unchanged. IBR3 dynamic
opening, physical isolation, three-source interaction, and causal cascade
propagation remain unavailable because no new PSCAD Run occurred.
