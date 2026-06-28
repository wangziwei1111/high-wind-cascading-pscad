# Type-3 DFIG LVRT Closed-Loop Coverage

## Status

```text
execution_status = type3_lvrt_closed_loop_coverage_partial
C1 no-fault = pass
C2 R2 ride-through = unavailable
C3 R4 duration trip-to-breaker = unavailable
model_integrity = model_integrity_needs_explanation
```

The no-fault command-and-state path was dynamically validated. The coverage
matrix did not close because C2 produced a Build error before Run; the
mandatory stop rule therefore prevented C2 and C3 runs.

## Execution Scope

All PSCAD interactions were performed by Codex through Computer Use. The user
was not asked to click PSCAD, change parameters, Build, Run, copy artifacts,
inspect waveforms, execute Python, or run Git.

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
Final active SHA-256: 10A3B91EE96B8C3BC6FB32D049D6EEB28C9F0923CFFB72BFDBB1F5EC257A9CEB
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

The final SHA does not match the task-start SHA. A read-only comparison shows
saved run-display/revision changes and an active `master:gain` instance with
ID `65646757` that is absent from the task-start on-disk backup. No direct XML
repair or backup substitution was performed. The final model state is thus
`model_integrity_needs_explanation`.

## Build Record

| Stage | Errors | Warnings | Messages | Decision |
| --- | ---: | ---: | ---: | --- |
| Precheck | 0 | 46 | 119 | permitted C1 |
| C1 | 0 | 46 | 119 | permitted one Run |
| C1 Run compile | 0 | 0 | 11 | Run completed |
| C2 | 1 | 37 | 33 | Run prohibited; stop matrix |
| Final restored-parameter Build | 2 | 37 | 33 | integrity needs explanation |

The C2 Build error identified `master:gain` ID `65646757` with a floating
`IN:Dim` input. The final Build reported the same component twice: an `RT_24`
source conflict and a floating `IN:Dim` input.

No EMTDC Runtime Error, `Ungrounded subsystem`, or abnormal Run termination
occurred. C2 did not reach Run.

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

## C2 And C3

C2 R2 was configured through the GUI for `0.10 ohm`, `2.0 s`, `0.75 s`, and
`8.0 s`, but Build failed. It was not Run, so every C2 dynamic criterion is
`unavailable`.

C3 R4 was not configured or Run because the mandatory stop rule took effect
after the C2 Build error. Every C3 dynamic timing and breaker-state criterion
is `unavailable`.

## Prior R5 Evidence

The prior R5 evidence remains valid and separate:

```text
TRIP_REQUEST first = 2.02 s
TRIP_LATCH first = 2.02 s
FINAL_BRK_CMD first = 2.02 s
BRK_STATE first open = 2.02 s
BRK_STATE holds open = true
```

It validates the immediate-trip command-and-state path in PSCAD, but does not
replace missing C2 ride-through or C3 duration-based evidence.

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
