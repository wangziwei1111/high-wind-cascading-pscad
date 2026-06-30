# IBR Trial Local Breaker Boundary

## Current status

The independent `3IBR_DFIG1_TRIAL.pscx` project now contains a statically
Build-verified local physical breaker boundary for the real `IBR2_TRIAL`
branch. The protected main project was unchanged.

```text
execution_status = trial_local_breaker_boundary_static_build_verified
main_project_integrity_status = pass
local_breaker_boundary_status = pass
no_parallel_bypass_status = pass
output_channel_status = pass
dynamic_behavior_status = unavailable
second_source_event_status = not_constructed
dual_source_collector_status = not_constructed
```

Detailed evidence is in `docs/IBR2_TRIAL_LOCAL_BREAKER_BOUNDARY.md` and
`data/reference/ibr2_trial_local_breaker_boundary.json`.

The main project still has no qualified monitor-only second source. No PSCAD
Run was performed, so dynamic breaker action, actual source disconnection,
event timing, multi-machine propagation, cascade behavior, and MATLAB remain
unvalidated.
