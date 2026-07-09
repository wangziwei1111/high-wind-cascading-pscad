# Validation Against Thesis

This clean rebuild does not claim completed thesis reproduction until PSCAD 4.6.2 and MATLAB 2016b are run locally with recorded evidence.

## Validation Sequence

1. Dirty-reference interface capability is documented.
2. Clean PSCAD physical network contains no migrated GUI protection brain.
3. Breaker mapping tables are complete.
4. PSCAD packs `obs` according to `docs/pscad_matlab_signal_contract.md`.
5. MATLAB receives `obs` and returns `cmd` through `pscad_cascade_step`.
6. PSCAD routes commands to physical breakers.
7. PSCAD feeds actual online states back on the next interface step.
8. MATLAB exports `event_chain`.
9. MATLAB command times and PSCAD breaker action times can be aligned.
10. The bus-29 three-phase fault scenario produces comparable event types, causal order, and propagation mechanism.

## Initial Scenario

- Initial fault: bus 29 three-phase short circuit.
- Fault duration: 2.0 s.
- Total simulated time: 20 s.
- First-stage target: event class and causal order alignment, not exact timestamp matching.

## Required Exports

Each run should export:

- `results/obs_trace.csv`
- `results/cmd_trace.csv`
- `results/breaker_action_trace.csv`
- `results/event_chain.csv`
- `results/run_summary.json`
- `results/validation_report.md`

