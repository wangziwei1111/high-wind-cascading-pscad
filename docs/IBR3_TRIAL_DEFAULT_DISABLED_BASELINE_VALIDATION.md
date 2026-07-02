# IBR3_TRIAL default-disabled baseline validation

Date: 2026-07-02

## Scope

This task executed exactly one PSCAD baseline Run with both trial test stimuli
left in their default-disabled state:

```text
IBR2_TRIAL_TEST_ENABLE = 0
IBR3_TRIAL_TEST_ENABLE = 0
```

No PSCAD model parameters, Constants, wiring, pages, modules, breakers, event
packets, collectors, chronology monitors, or Output Channels were modified.

## Baseline run result

```text
dynamic_baseline_status = pass
stimulus_specific_contrast_status = pass
```

The run was parsed from PSCAD Output Channel files generated at
`2026-07-02T15:15:18+08:00`.

| Signal / relationship | Default-disabled result |
| --- | --- |
| IBR2_TRIAL_TEST_ENABLE | Held at 0 |
| IBR3_TRIAL_TEST_ENABLE | Held at 0 |
| IBR3_TRIAL_TEST_OPEN_REQUEST | Held at 0 |
| IBR3_TRIAL_BRK_CMD | Held at 0 |
| IBR3_TRIAL_BRK_STATE | Stayed below open threshold 0.5 |
| IBR3_TRIAL_BRK_OPEN_BOOL | Held at 0 |
| IBR3_TRIAL_SOURCE_AVAILABLE | Held at 1 |
| IBR3_TRIAL_CASCADE_EVENT_VALID | Held at 0 |
| IBR3_TRIAL_CASCADE_EVENT_CAUSE_CODE | Held at 0 |
| IBR3_TRIAL_CASCADE_EVENT_BRK_OPEN | Held at 0 |
| IBR3_TRIAL_CASCADE_SOURCE_AVAILABLE | Held at 1 |
| IBR3_TRIAL_CASCADE_FIRST_EVENT_TIME_S | Held at -1 |
| CASCADE3_MONITOR_CAUSE_CODE_IBR3_TRIAL | Held at 0 |

The existing default scenario DFIG event signature remained parseable:

```text
DFIG first event time = 2.01603 s
DFIG cause code = 2
IBR2 cause code = 0
IBR3 cause code = 0
CASCADE3 evented source count = 1
CASCADE3 timed event source count = 1
CASCADE3 first event source code = 1
CASCADE3 second event time = -1
CASCADE3 third event time = -1
CASCADE3 chronology consistent = 1
```

## Enabled-vs-disabled contrast

The previous enabled-stimulus run observed:

```text
IBR3 test enable = 1
IBR3 open request = 5.0 s
IBR3 actual opening = 5.0 s
IBR3 event valid = 5.0 s
IBR3 cause code = 5
CASCADE3 second event time = 5.0 s
```

This default-disabled baseline observed:

```text
IBR3 test enable = 0
IBR3 open request = absent
IBR3 actual opening = absent
IBR3 event valid = absent
IBR3 cause code = 0
CASCADE3 second event time = -1
```

Together, the paired runs support the narrow conclusion that, in the current
fixed trial model and default run configuration, the IBR3 5.0 s local-opening
event is specific to the trial test stimulus being enabled and is absent when
that stimulus is default-disabled.

## Static integrity

Main project SHA:

```text
CBA120BB167CB7FA6C4A1AE4471268850AB61761EC1877EB7B87015627FE9DAB
```

Trial SHA before and after this baseline Run:

```text
C03DAA211B591923F533554C9951503096677BCF52547D13A10C4B431E69A349
```

No PSCAD metadata/display drift was detected in this run. Output Channel count
remained 253.

## Artifacts

- `analysis/pscad_tools/preflight_ibr3_default_disabled_baseline_run.py`
- `analysis/pscad_tools/parse_ibr3_default_disabled_baseline_run.py`
- `analysis/pscad_tools/audit_ibr3_default_disabled_baseline_run.py`
- `data/validation/ibr3_default_disabled_baseline_pre_run_manifest.json`
- `data/validation/ibr3_default_disabled_baseline_run_summary.json`
- `data/validation/ibr3_default_disabled_baseline_run_channels.csv`
- `data/validation/ibr3_default_disabled_baseline_run_metrics.csv`
- `data/validation/ibr3_enabled_vs_disabled_run_comparison.json`
- `data/validation/ibr3_enabled_vs_disabled_run_comparison.csv`
- `data/validation/ibr3_default_disabled_baseline_final_audit.json`

Raw PSCAD `.out`, `.inf`, `.sav`, and `.gf46` files are not committed.

## Claim boundary

This baseline and the paired enabled-vs-disabled contrast do not prove:

- DFIG caused IBR3 behavior,
- IBR3 caused DFIG behavior,
- cascade propagation,
- physical causality direction,
- system stability,
- protection coordination,
- MATLAB coupling,
- general applicability.
