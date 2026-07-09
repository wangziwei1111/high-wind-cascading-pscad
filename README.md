# high-wind-cascading-pscad

Independent clean-rebuild framework for cascading-failure studies in a high wind-penetration IEEE 39-bus system, based on traceable PSCAD model evidence and offline-testable MATLAB protection logic.

This repository does not contain redistributed third-party PSCAD projects unless their redistribution rights are explicitly confirmed. PSCAD assembly, wiring, compilation, initialization, and simulation must be completed manually in PSCAD GUI and recorded as validation evidence.

## Current Route

The current project route is:

```text
offline MATLAB protection iteration + PSCAD feedback replay
```

or, equivalently:

```text
offline quasi-dynamic protection loop
```

The live PSCAD-MATLAB runtime coupling used by the paper is not the current
project target because the required PSCAD 4.6.2 + MATLAB 2016b environment is
not reliably reproducible here. This repository must not claim that the original
live runtime interface has been completed.

The substitute route preserves the core mechanism:

- PSCAD performs the electromagnetic transient physical run.
- MATLAB evaluates protection decisions from exported PSCAD observations.
- PSCAD executes scheduled breaker feedback in a replay run.
- MATLAB audits the resulting event chain.

The current minimum verified loop is WFFB1: a WF38-side PSCAD three-phase fault
produces a voltage trace, MATLAB computes `WF38_TRIP_TIME = 2.02 s`, and PSCAD
feedback replay opens the WF38 breaker at `2.02 s` while WF33/WF35 remain online.

## Current clean rebuild scope

- A previous dirty-but-working PSCAD-MATLAB interaction model is treated as a frozen reference for interface extraction.
- This phase is not a from-zero proof that PSCAD can call MATLAB.
- The goal is to extract the already verified interface capability from the dirty GUI and rebuild around a clean boundary.
- The new architecture is Clean PSCAD Plant + PSCAD Interface Shell + MATLAB Protection Kernel + Audit & Replay Layer.
- PSCAD GUI should keep only the physical system, real breakers, measurement points, and the minimal interface shell.
- MATLAB owns protection judgement, timers, ordering, event-chain construction, and audit/replay exports.
- This repository does not fabricate PSCAD closed-loop results.
- Until PSCAD 4.6.2 + MATLAB 2016b are run locally with recorded evidence, this repository must not claim completed thesis reproduction.

## Recommended base model

Use the PNNL Enhanced IEEE 39-Bus System three-IBR PSCAD project as the network base, subject to user verification in PSCAD GUI and license review. Replace or bypass IBR blocks manually only after validating the project can open, load libraries, compile, and run in PSCAD.

## Clean rebuild entry points

- Strategy: `docs/clean_rebuild_strategy.md`
- Dirty asset extraction: `docs/dirty_model_asset_extraction.md`
- PSCAD cleanliness rules: `docs/pscad_gui_cleanliness_rules.md`
- Interface shell design: `docs/pscad_interface_shell_design.md`
- Signal contract: `docs/pscad_matlab_signal_contract.md`
- Breaker rules: `docs/breaker_mapping_rules.md`
- Offline loop route: `docs/OFFLINE_PSCAD_MATLAB_PROTECTION_LOOP.md`
- Live coupling boundary: `docs/LIVE_COUPLING_LIMITATION_AND_SUBSTITUTE.md`
- WFFB1 evidence: `docs/WFFB1_REAL_FAULT_FEEDBACK_EVIDENCE.md`
- Mapping tables: `mapping/*.csv`
- MATLAB main entry: `matlab/pscad_cascade_step.m`

## Quick MATLAB test

```matlab
cd matlab
run_protection_unit_tests
```
