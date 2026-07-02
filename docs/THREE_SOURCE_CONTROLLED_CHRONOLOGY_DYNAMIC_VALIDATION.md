# Three-Source Controlled Chronology Dynamic Validation

## Scope

This task performed exactly one approved PSCAD Run in the independent
`3IBR_DFIG1_TRIAL` project. No modules, pages, breakers, event packets,
collector logic, chronology monitor logic, or Output Channels were added or
modified.

The run temporarily enabled both trial-only local-opening stimuli:

```text
IBR2_TRIAL_TEST_ENABLE = 1
IBR2_TRIAL_TEST_OPEN_TIME_S = 4.0 s

IBR3_TRIAL_TEST_ENABLE = 1
IBR3_TRIAL_TEST_OPEN_TIME_S = 5.0 s
```

After parsing, both test enables were restored to 0 and the trial project was
rebuilt without a second Run.

## Result

```text
controlled_three_event_order_status = pass
source_a_dynamic_status = pass
source_b_dynamic_status = pass
source_c_dynamic_status = pass
three_source_collector_dynamic_status = pass
three_event_chronology_dynamic_status = pass
final_audit_status = pass
```

The parsed events were strictly ordered:

| Source | Meaning | Parsed first-event time | Cause |
| --- | --- | ---: | ---: |
| A | existing TYPE3_DFIG_1 default event | 2.01603 s | 2 |
| B | IBR2_TRIAL trial-only local opening | 4.000005 s | 4 |
| C | IBR3_TRIAL trial-only local opening | 5.0 s | 5 |

The chronology outputs matched the controlled timing interface:

| CASCADE3 chronology field | Parsed result |
| --- | ---: |
| evented source count | 3 |
| timed event source count | 3 |
| first event time | 2.01603 s |
| second event time | 4.000005 s |
| third event time | 5.0 s |
| first-to-second gap | 1.983975 s |
| second-to-third gap | 0.999995 s |
| first-source code | 1 |
| order-class code | 4 |
| chronology consistent | 1 |

## Evidence files

- `data/validation/three_source_controlled_chronology_pre_run_manifest.json`
- `data/validation/three_source_controlled_chronology_run_summary.json`
- `data/validation/three_source_controlled_chronology_run_channels.csv`
- `data/validation/three_source_controlled_chronology_run_metrics.csv`
- `data/validation/three_source_controlled_chronology_comparison.json`
- `data/validation/three_source_controlled_chronology_comparison.csv`
- `data/validation/three_source_controlled_chronology_final_audit.json`

## Boundary of the claim

This validates only one controlled timing-interface scenario in the fixed
trial model: the existing default DFIG event plus independently scheduled
IBR2_TRIAL and IBR3_TRIAL local-opening stimuli.

It does not validate natural cascade propagation, DFIG-to-IBR2 causality,
DFIG-to-IBR3 causality, IBR2-to-IBR3 causality, physical causality direction,
system stability, protection coordination, MATLAB coupling, or general
applicability.
