# high-wind-cascading-pscad

Independent reproduction framework for cascading-failure studies in a high wind-penetration IEEE 39-bus system, based on publicly traceable PSCAD model sources and offline-testable MATLAB protection logic.

This repository does not contain redistributed third-party PSCAD projects unless their redistribution rights are explicitly confirmed. PSCAD assembly, wiring, compilation, initialization, and simulation must be completed manually in PSCAD GUI and recorded as validation evidence.

## Phase 1 scope

- Audit public PSCAD-capable model sources.
- Extract traceable parameters from Xu Youxin (2024).
- Provide a manual PSCAD assembly and validation plan.
- Implement MATLAB protection logic that can be unit-tested without PSCAD.
- Define a future PSCAD-MATLAB interface contract without claiming closed-loop integration.

## Recommended base model

Use the PNNL Enhanced IEEE 39-Bus System three-IBR PSCAD project as the network base, subject to user verification in PSCAD GUI and license review. Replace or bypass IBR blocks manually only after validating the project can open, load libraries, compile, and run in PSCAD.

## Quick MATLAB test

```matlab
cd matlab
run_protection_unit_tests
```

