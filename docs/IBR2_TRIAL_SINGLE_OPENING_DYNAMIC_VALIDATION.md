# IBR2_TRIAL Single-Opening Dynamic Validation

## Scope

This validation used exactly one approved PSCAD Run in the independent
`3IBR_DFIG1_TRIAL` project. It temporarily enabled only the IBR2 trial-local
opening stimulus:

```text
IBR2_TRIAL_TEST_ENABLE = 1
IBR3_TRIAL_TEST_ENABLE = 0
IBR2_TRIAL_TEST_OPEN_TIME_S = 4.0 s
IBR3_TRIAL_TEST_OPEN_TIME_S = 5.0 s
```

After parsing, both trial test enables were restored to 0 and the trial was
rebuilt. No second Run was performed after restoration.

## Result

```text
dynamic_run_status = pass
ibr2_source_b_chain_dynamic_status = pass
ibr3_default_disabled_isolation_status = pass
collector_and_chronology_dynamic_status = pass
final_audit_status = pass
```

The parsed run shows the source-B trial-only chain:

| Checkpoint | Parsed result |
| --- | ---: |
| IBR2 test enable | 1.0 during the single Run |
| IBR2 open request first asserted | 4.0 s |
| IBR2 breaker command first asserted | 4.0 s |
| IBR2 trial breaker state/open monitor first changed | 4.0 s |
| IBR2 event valid first asserted | 4.01 s |
| IBR2 packet first-event time | 4.000005 s |
| IBR2 packet cause code | 4 |

The existing DFIG event remained first at 2.01603 s. The CASCADE3 chronology
monitor therefore reported IBR2_TRIAL as the second timed event:

| CASCADE3 monitor field | Parsed result |
| --- | ---: |
| first event time | 2.01603 s |
| second event time | 4.000005 s |
| third event time | -1 |
| first-to-second gap | 1.983975 s |
| IBR2 cause code passthrough | 4 |
| chronology consistent | 1 |

IBR3 remained disabled and non-evented throughout this Run.

## Evidence files

- `data/validation/ibr2_trial_single_opening_run_summary.json`
- `data/validation/ibr2_trial_single_opening_run_channels.csv`
- `data/validation/ibr2_trial_single_opening_run_metrics.csv`
- `data/validation/ibr2_enabled_vs_default_disabled_run_comparison.json`
- `data/validation/ibr2_enabled_vs_default_disabled_run_comparison.csv`
- `data/validation/ibr2_trial_single_opening_final_audit.json`

## Boundary of the claim

This validates only the IBR2_TRIAL source-B trial-only local-opening path in
the fixed trial model: test enable, opening request, breaker command, actual
trial breaker state/open monitor, source availability, IBR2 event packet,
three-source collector, and three-event chronology outputs.

It does not validate natural DFIG-to-IBR2 cascade propagation, physical
causality direction, system stability, protection coordination, MATLAB
coupling, or general applicability.

## Three-source controlled chronology follow-up: 2026-07-02

A later approved single Run enabled both IBR2_TRIAL and IBR3_TRIAL
trial-only stimuli. IBR2_TRIAL remained the second event at 4.000005 s in the
strict three-event chronology. See
`docs/THREE_SOURCE_CONTROLLED_CHRONOLOGY_DYNAMIC_VALIDATION.md`.

## Production audit target correction: 2026-07-02

A later read-only audit correction distinguishes the real IBR2_TRIAL
production path from module-test harness objects. The corrected target uses
the production `IBR2_TEST_ENABLE`, `IBR2_TRIAL_BRK_CMD`, `BRK_IBR2_TRIAL`,
`IBR2_CAS_*`, and `IBR2_TRIAL_CASCADE_*` interfaces. See
`docs/IBR2_PRODUCTION_PATH_AUDIT_CORRECTION.md`.
