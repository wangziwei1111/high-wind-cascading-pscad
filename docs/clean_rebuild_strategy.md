# Clean Rebuild Strategy

This repository is now organized around a clean rebuild rather than continued growth of the dirty PSCAD GUI model.

## Objective

Extract the already proven PSCAD-MATLAB interface pattern from the dirty-but-working reference, then rebuild the IEEE 39-bus high-wind cascading-failure study as four layers:

1. Clean PSCAD Plant: electromagnetic network, breakers, sources, loads, faults, and measurements only.
2. PSCAD Interface Shell: measurement packing, MATLAB call, command fan-out, breaker status feedback, and raw trace export.
3. MATLAB Protection Kernel: all protection judgement, timers, latches, event ordering, cascade logic, and command generation.
4. Audit & Replay Layer: obs/cmd/breaker/event/run-summary exports for review and replay.

## Current Repository Finding

The git repository contains scripts, docs, config files, MATLAB protection modules, validation artifacts, and metadata about local PSCAD assets. It does not contain the main PNNL IEEE39 PSCAD project as a committed source file. Existing audit metadata points to local restricted PSCAD files outside the repo, especially `C:\pscad_work\pnnl_39_3ibr_pscad46_strip5\PSCAD\3IBR.pscx`.

Therefore this clean rebuild commit does not claim that a PSCAD project has been rebuilt or closed-loop simulated. It provides the clean contract, MATLAB backend, mapping tables, and manual PSCAD rebuild checklist.

## Migration Rule

Only these capabilities should be extracted from the dirty reference:

- Proven PSCAD-to-MATLAB call mechanism.
- MATLAB path and entry-point configuration.
- Input/output vector packing format.
- MATLAB command return path.
- Breaker command wiring pattern.
- Measurement and online-status feedback wiring pattern.

Do not migrate the dirty GUI protection logic, timing networks, experimental comparators, relay meshes, dashboards, or debug wires.

