# Type-3 DFIG LVRT Breaker Command Validation

## Status

```text
execution_status = brk_command_state_validation_unavailable
run_status = completed
acceptance_status = unavailable
```

The single allowed R5 run completed to 5.0 s. The available output channels
show that `DFIG_LVRT_TRIP_REQUEST`, `DFIG_LVRT_TRIP_LATCH`, and
`DFIG_BRK_STATE` all changed at 2.02 s, and the breaker state remained open to
the end of the run. However, `DFIG_LVRT_FINAL_BRK_CMD` was absent from the
run-time `3IBR.inf`, so criteria that require its measured waveform are
unavailable. Static generated-source evidence is not substituted for that
missing dynamic channel.

## Scope

```text
Project: C:\pscad_work\pnnl_39_3ibr_pscad46_strip5\PSCAD\3IBR.pscx
Page: 3IBR:Main(0):P1(0):P3(0)
Branch: codex/lvrt-trip-request-progress
Task-start SHA-256: 00C72FAAE357F113DC26C486180A7AA374AACA81BC698B87D9FAB3D706AF1DF9
Final active SHA-256: DA4518483523C1BCAFF2A74AAC356B29B53F9642A8E9D7E9E44FCDA2E96F90E6
Backup: C:\pscad_work\backups\type3_lvrt_brk_command_20260628_201729\3IBR.pscx
Run archive: C:\pscad_work\lvrt_brk_command_validation\20260628_201729\R5_breaker_command_validation
Snapshot: external/pscad_snapshot_20260628_lvrt_brk_command_state_validated/pnnl_39_3ibr_pscad46_strip5_PSCAD/3IBR.pscx
```

The backup SHA-256 matched the task-start project SHA-256. No rollback was
performed.

## Command Structure

The original breaker command was audited as a constant zero command:

```text
Constant 0
-> Gain 1
-> DFIG_LVRT_EXISTING_BRK_CMD
-> threshold 0.5 comparator
-> DFIG_LVRT_EXISTING_BRK_CMD_BOOL
```

The validated trip latch enters the final command through a separate Boolean
conversion:

```text
DFIG_LVRT_TRIP_LATCH_MEM
-> Gain 1
-> DFIG_LVRT_TRIP_LATCH
-> threshold 0.5 comparator
-> DFIG_LVRT_TRIP_LATCH_BOOL
```

The two Boolean signals are added and limited to the range 0 to 1:

```text
DFIG_LVRT_FINAL_BRK_CMD =
LIMIT(0, 1,
  DFIG_LVRT_EXISTING_BRK_CMD_BOOL
  + DFIG_LVRT_TRIP_LATCH_BOOL)

BRK_DFIG = 1.0 * DFIG_LVRT_FINAL_BRK_CMD
```

The generated `P3.f` confirms that `BRK_DFIG` has this sole command
assignment. `DFIG_LVRT_TRIP_REQUEST` does not directly drive the breaker.

## Build Record

| Stage | Errors | Warnings | Messages | Result |
| --- | ---: | ---: | ---: | --- |
| A initial read-only sampling | 1 | 46 | unavailable | signal-name contention |
| A Gain-isolated sampling | 0 | unavailable | unavailable | pass |
| B initial command synthesis | 1 | 37 | unavailable | floating latch input |
| B wire-only repair | 1 | 37 | unavailable | undefined latch alias remained |
| B canonical latch alias repair | 0 | unavailable | unavailable | pass |
| C sole breaker command integration | 0 | unavailable | unavailable | pass |
| Final post-run Output Channel Build | 0 | unavailable | unavailable | pass |

Warnings and message counts not visible in the supplied successful Build
records are reported as unavailable rather than inferred.

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
```

These are also the task-start values, so final parameter restoration required
no value change. A final Build was performed without another Run.

## Dynamic Evidence

| Criterion | Status | Evidence |
| --- | --- | --- |
| A1 run reached 5 s | pass | `simulation_end_s = 5.0` |
| A2 trip request asserted near R5 event | pass | first high at 2.02 s |
| A3 latch set after request without startup set | pass | first high at 2.02 s; prefault max 0 |
| A4 final command zero prefault | unavailable | FINAL channel absent from run-time INF |
| A5 final command high after latch | unavailable | FINAL channel absent from run-time INF |
| A6 latch-to-final timing | unavailable | FINAL channel absent from run-time INF |
| A7 breaker opens after final command | unavailable | FINAL timing unavailable |
| A8 breaker not open before final command | unavailable | FINAL timing unavailable |
| A9 breaker state holds open | pass | state opens at 2.02 s and remains high |
| A10 original command preserved; no startup opening | pass | startup maxima both 0 |
| A11 latch-final-breaker ordering | unavailable | middle waveform unavailable |
| A12 P/Q evidence recorded | pass | both channels parsed |

Numeric evidence:

```text
TRIP_REQUEST first high = 2.02 s
TRIP_LATCH first high = 2.02 s
EXISTING_BRK_CMD first open = unavailable (never asserted)
FINAL_BRK_CMD first open = unavailable (channel missing)
BRK_STATE first open = 2.02 s
BRK_STATE holds open = true
startup EXISTING_BRK_CMD max = 0.0
startup BRK_STATE max = 0.0
PIBR1_2 prefault mean = 189.89013181934155
QIBR1_2 prefault mean = -15.494975081477733
PIBR1_2 post-open mean = -2.339824966276821
QIBR1_2 post-open mean = -1.1889435089549205
```

The P/Q values are supporting electrical-response evidence only. They are not
used alone to claim physical turbine isolation.

## Post-Run Static Completion

After the only allowed Run, the missing `DFIG_LVRT_FINAL_BRK_CMD` Output
Channel was added and a Build completed with zero errors. The final project
therefore contains the channel for a future validation, but this post-run
addition does not make the present R5 result a pass.

## Runtime Assessment

The archived output reached 5.0 s. No `Ungrounded subsystem` or abnormal EMTDC
termination is evidenced by this completed run. The prior run artifacts were
archived before the final Build removed active `.inf/.out` files.

## Conclusion

```text
BRK_DFIG command-and-state response was partially observed in PSCAD.
Overall dynamic validation is unavailable because the measured
DFIG_LVRT_FINAL_BRK_CMD waveform is missing from the sole allowed R5 run.
```

Do not restate this result as a validated physical field breaker, an actual
physical turbine disconnection, or definitive isolation of the entire Type-3
generator.

## Safety

```text
BRK_DFIG main-circuit parameters were not modified.
No automatic reclosing was introduced.
No MATLAB coupling was added.
No .gf46/.out/.inf/screenshots/local run directories were committed.
```
