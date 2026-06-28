# Type-3 DFIG LVRT Breaker Command Dynamic Validation

## Status

```text
execution_status = brk_command_state_validation_pass
run_status = completed
acceptance_status = pass
```

The single R5 evidence-recheck run completed to 5.0 s and its run-time
`3IBR.inf` contains `DFIG_LVRT_FINAL_BRK_CMD`. All B1-B13 dynamic acceptance
checks pass.

This result supersedes the preceding `unavailable` result, which lacked the
measured final-command channel. The PSCAD model was not modified during this
recheck and no second recheck Run was performed.

## Scope

```text
Project: C:\pscad_work\pnnl_39_3ibr_pscad46_strip5\PSCAD\3IBR.pscx
Page: 3IBR:Main(0):P1(0):P3(0)
Branch: codex/lvrt-trip-request-progress
Active project SHA-256: DA4518483523C1BCAFF2A74AAC356B29B53F9642A8E9D7E9E44FCDA2E96F90E6
Backup: C:\pscad_work\backups\type3_lvrt_final_brk_cmd_recheck_20260628_213352\3IBR.pscx
Run archive: C:\pscad_work\lvrt_final_brk_cmd_recheck\20260628_213352\R5_final_brk_cmd_recheck
```

The active and backup SHA-256 values match. The active SHA also matches the
previous round's final SHA, confirming that this recheck did not alter the
PSCAD model.

## Command Structure

The previously audited command path remains unchanged:

```text
DFIG_LVRT_EXISTING_BRK_CMD_BOOL
+ DFIG_LVRT_TRIP_LATCH_BOOL
-> Hard Limiter [0, 1]
-> DFIG_LVRT_FINAL_BRK_CMD
-> Gain 1
-> BRK_DFIG
```

Equivalent generated equations:

```text
DFIG_LVRT_FINAL_BRK_CMD =
LIMIT(0, 1,
  DFIG_LVRT_EXISTING_BRK_CMD_BOOL
  + DFIG_LVRT_TRIP_LATCH_BOOL)

BRK_DFIG = 1.0 * DFIG_LVRT_FINAL_BRK_CMD
```

The measured signal path, rather than these static equations, is used for the
dynamic acceptance decision.

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

The user performed one Build and one Run. Build errors were zero because the
Run was permitted and completed. Exact warning and message counts were not
supplied and are recorded as unavailable.

## Dynamic Evidence

| Criterion | Status | Evidence |
| --- | --- | --- |
| B1 run reached 5 s | pass | `simulation_end_s = 5.0` |
| B2 trip request near event | pass | first high at 2.02 s |
| B3 latch after request; no startup set | pass | first high at 2.02 s; prefault max 0 |
| B4 final command zero prefault | pass | prefault max 0 |
| B5 final command high after latch | pass | first high at 2.02 s |
| B6 latch-to-final timing | pass | delay 0.0 s |
| B7 breaker opens after final command | pass | state first open at 2.02 s |
| B8 breaker not open before command | pass | same output sample, not earlier |
| B9 breaker state holds open | pass | remains high through 5.0 s |
| B10 no startup false opening | pass | startup FINAL and state maxima both 0 |
| B11 latch-final-state ordering | pass | `2.02 <= 2.02 <= 2.02 s` |
| B12 original command preserved | pass | original command prefault max below 0.5 |
| B13 P/Q evidence recorded | pass | both channels parsed |

## Numeric Evidence

```text
simulation_end_s = 5.0
TRIP_REQUEST_first_s = 2.02
TRIP_LATCH_first_s = 2.02
FINAL_BRK_CMD_first_open_s = 2.02
BRK_STATE_first_open_s = 2.02
TRIP_LATCH_to_FINAL_BRK_CMD_delay_s = 0.0
FINAL_BRK_CMD_to_BRK_STATE_delay_s = 0.0
TRIP_LATCH_prefault_max = 0.0
FINAL_BRK_CMD_prefault_max = 0.0
startup_existing_command_max = 0.0
startup_final_command_max = 0.0
startup_brk_state_max = 0.0
BRK_STATE_holds_open = true
PIBR1_2_pre_fault_mean = 189.89013181934155
PIBR1_2_post_open_mean = -2.339824966276821
QIBR1_2_pre_fault_mean = -15.494975081477733
QIBR1_2_post_open_mean = -1.1889435089549205
```

The three state transitions occur at the same 10 ms output sample. This is
accepted by the task's discrete-sample timing rule and does not imply a
negative command-to-state delay.

P/Q values are supporting electrical-response evidence only. They are not
used alone to claim physical turbine isolation.

## Runtime Assessment

The archived output reaches 5.0 s. No EMTDC Runtime Error, abnormal
termination, or `Ungrounded subsystem` condition is evidenced by this run.

## Conclusion

```text
BRK_DFIG command-and-state response validated in PSCAD.
```

This statement applies only to the modeled PSCAD command and state response.
It does not validate a physical field breaker, actual physical turbine
disconnection, or definitive isolation of the entire Type-3 generator.

## Artifacts

```text
analysis/pscad_tools/analyze_type3_dfig_lvrt_brk_command_validation.py
data/reference/type3_dfig_lvrt_brk_command_validation.json
data/reference/type3_dfig_lvrt_brk_command_validation_summary.csv
docs/TYPE3_DFIG_LVRT_BRK_COMMAND_VALIDATION.md
```

Raw `.inf/.out` files and logs remain only in the local run archive and are
not committed.

## Safety

```text
No PSCAD control logic was modified during this recheck.
BRK_DFIG main-circuit parameters were not modified.
No automatic reclosing was introduced.
No MATLAB coupling was added.
No .gf46/.out/.inf/screenshots/local run directories were committed.
```

## Closed-Loop Coverage Follow-Up

The later C1/C2/C3 closeout is partial. C1 dynamically confirms that
`FINAL_BRK_CMD` and `BRK_STATE` remain low in the no-fault case. C2 was blocked
by a Build error before Run, and C3 was skipped by the mandatory stop rule.
Therefore the prior R5 immediate-trip pass remains valid, while ride-through
and duration-based closed-loop coverage remain unavailable in this round.

See `docs/TYPE3_DFIG_LVRT_CLOSED_LOOP_COVERAGE.md`. The follow-up does not
downgrade or overwrite the archived R5 measurements.
