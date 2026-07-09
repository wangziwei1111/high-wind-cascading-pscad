# Offline MATLAB Protection Iteration + PSCAD Feedback Replay

This project route replaces live PSCAD-MATLAB runtime coupling for the current
environment.

The formal loop is:

```text
PSCAD physical run
-> export observation trace
-> MATLAB protection decision
-> generate trip schedule
-> PSCAD feedback replay / Multiple-Run execution
-> export feedback trace
-> MATLAB event-chain audit
```

This route may also be called an offline quasi-dynamic protection loop. It must
not be described as live PSCAD-MATLAB runtime coupling unless a future PSCAD
4.6.2 + MATLAB 2016b environment runs the real-time interface and records
evidence.

## Why This Route

The paper route used PSCAD 4.6.2 with MATLAB 2016b to call MATLAB `.m` files
during the simulation. That environment is old, difficult to reproduce, and not
stable on the current machine. The current verified machine can run PSCAD
physical cases and can run MATLAB R2025a offline, but live runtime coupling is
not a reliable project target.

Offline feedback replay preserves the essential mechanism:

- PSCAD computes the electromagnetic transient physical response.
- MATLAB performs the protection judgement and timing.
- PSCAD executes real breaker feedback in a replay run.
- MATLAB audits the resulting event chain.

## Standard Workflow

### Run A: Physical Disturbance Run

Inputs:

- Clean PSCAD three-wind-farm model.
- Real physical disturbance, such as a WF38-side three-phase fault.
- No MATLAB trip schedule applied.

Outputs:

- `obs_trace.csv` or equivalent exported data.
- Required columns:
  - `time_s`
  - `WF33_PCC_VPU`
  - `WF35_PCC_VPU`
  - `WF38_PCC_VPU`
  - `WF33_P_MW`
  - `WF35_P_MW`
  - `WF38_P_MW`
  - `WF33_ONLINE`
  - `WF35_ONLINE`
  - `WF38_ONLINE`

### MATLAB Decision Step

Inputs:

- Run A observation trace.

Processing:

- Apply the paper voltage ride-through criterion.
- Compute one trip action time per wind farm.
- Use `99 s` or `NaN` for targets that do not trip in the replay window.

Outputs:

- `trip_schedule.csv` with at least:
  - `target_id`
  - `target_type`
  - `action`
  - `trip_time_s`
  - `source_protection`
  - `measured_value_at_decision`
  - `criterion`
  - `notes`

### Run B: Feedback Replay Run

Inputs:

- The same PSCAD physical scenario.
- MATLAB-generated trip schedule.
- PSCAD breaker command implementation that executes the scheduled trip times.

Outputs:

- `feedback_trace.csv` or equivalent exported data.
- Required columns:
  - `time_s`
  - `WF33_TRIP_CMD`
  - `WF35_TRIP_CMD`
  - `WF38_TRIP_CMD`
  - `WF33_BRK_STATE`
  - `WF35_BRK_STATE`
  - `WF38_BRK_STATE`
  - `WF33_P_MW`
  - `WF35_P_MW`
  - `WF38_P_MW`

### Audit Step

Inputs:

- `obs_trace`
- `trip_schedule`
- `feedback_trace`

Outputs:

- `event_chain.csv`
- `run_summary.json`
- `validation_report.md`

## Future Interfaces

The offline loop is intentionally extensible. Later stages should add:

- `line_loading_trace`
- `line_trip_schedule`
- `load_shed_schedule`
- `generator_trip_schedule`
- event-chain merger
- multi-pass PSCAD feedback replay workflow

Planned ordering:

- Stage 18: line overload trip schedule.
- Stage 19: low-frequency and low-voltage load shedding schedules.
- Stage 20: conventional generator protection schedules.
- Stage 21: multi-event bus-29 three-phase fault chain reproduction.
