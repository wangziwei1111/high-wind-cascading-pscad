# Paper-aligned 20 s baseline fault scenario

Date: 2026-07-03

This stage statically configures the trial project for the paper's baseline
fault scenario. It does not claim a dynamic reproduction of the paper cascade.
No PSCAD Run was performed in this stage.

## Paper evidence

| Evidence | Location | Static requirement used here |
| --- | --- | --- |
| E009 | Section 2.5, p.15 / PDF p.23, Fig. 2-7 | Paper scenarios are run for 20 s. |
| E010 | Section 2.5, pp.16-17 / PDF pp.24-25, Table 2-2 | Baseline chain begins with a 0.50 s, 2 s, three-phase fault near bus 29. |
| E017 | Section 2.5, p.16 / PDF p.24, Table 2-2 | Initial fault location is near bus 29. |
| E018 | Section 2.5, p.16 / PDF p.24, Table 2-2 | Initial fault lasts 2.0 s. |

## Static PSCAD configuration

Only `3IBR_DFIG1_TRIAL.pscx` was changed. `3IBR.pscx` remained byte-identical
to the protected baseline:

`CBA120BB167CB7FA6C4A1AE4471268850AB61761EC1877EB7B87015627FE9DAB`

The trial project was changed from the full-network TLine measurement baseline
SHA:

`A9DC610D20C61022CDE2F2D73612C12499FB7E5D29C43562BA08D9D89EADF360`

to:

`F81959EA62211FF9C1536C8481B67675AFE4DDCC3C56E804D048731A4B88A300`

The existing `master:tfaultn` component was reused. No new fault component,
line, breaker, protection, control module, or Output Channel was added.

| Item | Value |
| --- | --- |
| Fault component | existing `master:tfaultn`, id `413214904` |
| Fault target | structurally aligned N29 boundary in P3 |
| Fault type | three-phase fault (`E3PHFLT1_*` Build code present) |
| Fault start | 0.50 s |
| Fault duration | 2.00 s |
| Fault clear time | 2.50 s |
| Duration of Run | 20 s |
| Solution time step | 5 us, preserved |
| Channel plot step | 10000 us, preserved |

Build-generated evidence confirms the fault is connected to N29 phases:

- `P3.dta` contains N29(1), N29(2), and N29(3) branches to ground;
- `P3.f` contains the three-phase fault execution call;
- `P3.f` contains timing logic for `0.5` and `0.5+2.0`.

## Preserved observability and trial defaults

The final audit reports:

- XML Output Channel count remains 448;
- all 31 genuine network TLine dual-end P/Q/I measurement groups remain present;
- IBR2 and IBR3 trial opening stimulus defaults remain disabled/preserved:
  - `IBR2_TEST_ENABLE = 0`;
  - `IBR3_TEST_ENABLE = 0`;
  - `IBR2_TEST_OPEN_TIME_S = 4.0`;
  - `IBR3_TEST_OPEN_TIME_S = 5.0`.

## Audit artifacts

- `analysis/pscad_tools/preflight_paper_aligned_fault_scenario.py`
- `analysis/pscad_tools/audit_paper_aligned_fault_scenario_static.py`
- `data/validation/paper_aligned_fault_scenario_preflight.json`
- `data/validation/paper_aligned_fault_scenario_final_audit.json`
- `data/validation/paper_aligned_fault_scenario_fault_trace.csv`
- `data/validation/paper_aligned_fault_scenario_channel_trace.csv`
- `data/validation/paper_aligned_fault_scenario_tline_measurement_trace.csv`
- `data/reference/paper_fault_scenario_evidence_extract.json`
- `data/reference/current_trial_fault_component_trace.json`
- `data/reference/paper_fault_target_mapping.json`
- `data/reference/paper_aligned_fault_scenario_design.json`

## Claim boundary

This stage achieves `paper_aligned_static_fault_scenario_configured`.

It does not claim natural cascade reproduction, power-flow redistribution
validation, line overload validation, line trip or relay reproduction,
UFLS/UVLS/generator-protection reproduction, or STATCOM/SVC mitigation
reproduction.

Those claims require a future dynamic Run and offline analysis using the
already audited full-network TLine measurement layer.

## Dynamic Run follow-up

The future dynamic Run described above has now been executed once by the user
and parsed offline. The Run confirms a valid 0-20 s output time axis, preserves
the protected main and trial project hashes, and provides complete full-network
TLine terminal A/B P/Q/I window metrics for 31 branches.

The dynamic evidence is documented in
`docs/PAPER_ALIGNED_20S_DYNAMIC_RUN_AND_TLINE_RESPONSE.md` and audited in
`data/validation/paper_aligned_20s_dynamic_run_final_audit.json`.

The claim boundary remains deliberately narrow: raw branch P/Q/I response was
observed, but line loading ratio, overload, relay operation, branch trip,
natural cascade propagation, protection coordination, voltage-support
performance, system stability, and strict paper reproduction remain
unvalidated.
