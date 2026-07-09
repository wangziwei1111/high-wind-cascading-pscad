# Stage 17 Offline Feedback Replay Route

Stage 17 formalizes the project route as offline MATLAB protection iteration
plus PSCAD feedback replay.

This stage does not continue pursuing live PSCAD-MATLAB runtime coupling. The
current objective is to make the already verified WFFB1 loop repeatable,
auditable, and extensible to later line overload, load shedding, generator
protection, and multi-event chain studies.

## Scope

- Document why live coupling is not the current project route.
- Pin WFFB1 as the minimal verified evidence.
- Standardize the two-run or multi-run workflow.
- Standardize MATLAB trip schedule output.
- Standardize PSCAD feedback replay expectations.
- Standardize event-chain audit outputs.
- Reserve interfaces for line overload protection without implementing the full
  cascading-failure chain in this stage.

## Route

```text
Run A: PSCAD physical disturbance
MATLAB: protection decision and trip schedule export
Run B: PSCAD feedback replay
MATLAB: event-chain audit
```

Run A must not apply the trip schedule. Run B must use the same physical
disturbance and apply the scheduled breaker operations.

## Current Evidence

The current verified loop is WFFB1:

- WF38-side three-phase fault.
- Fault window: `2.0 s` to `2.15 s`.
- Fault resistance: `0.01 ohm`.
- MATLAB VRT result:
  - `WF38_TRIP_TIME = 2.02 s`
  - `WF35_TRIP_TIME = 99 s`
  - `WF33_TRIP_TIME = 99 s`
- PSCAD feedback replay:
  - `WF38_TRIP_CMD` transition at `2.02 s`
  - `WF38_BRK_STATE` transition at `2.02 s`
  - no WF33/WF35 false trip
  - WF38 active power falls to approximately `0 MW`

See `docs/WFFB1_REAL_FAULT_FEEDBACK_EVIDENCE.md`.

## Non-Goals

- Do not claim live PSCAD-MATLAB runtime coupling.
- Do not claim full paper bus-29 cascading-chain reproduction.
- Do not commit PSCAD project files or runtime artifacts.
- Do not commit paper full text.
