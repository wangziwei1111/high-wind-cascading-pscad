# IBR3_TRIAL single-opening dynamic validation

Date: 2026-07-02

## Scope

This task executed exactly one approved PSCAD Run in the independent
`3IBR_DFIG1_TRIAL` project. No modules, pages, breakers, event packets,
collectors, chronology monitors, or Output Channels were added or edited.

The only approved temporary model change was:

```text
IBR3_TRIAL__OPEN_STIMULUS test-enable Constant: 0 -> 1
```

After parsing the run result, the project was restored to:

```text
IBR3_TRIAL__OPEN_STIMULUS test-enable Constant: 0
```

## Run scenario

```text
Scenario: IBR3_TRIAL_SINGLE_OPENING_DEFAULT_SCENARIO
IBR2_TRIAL test enable: 0
IBR3_TRIAL test enable during run: 1
IBR3 open time: 5.0 s
IBR3 event packet cause code: 5
Simulation duration: 5.0 s
Solution time step: 5 us
Channel plot step: 10000 us
```

## Dynamic result

Classification:

```text
PASS
```

Observed parsed evidence:

| Signal / relationship | Parsed result |
| --- | --- |
| IBR2_TRIAL_TEST_ENABLE | Held at 0 |
| IBR3_TRIAL_TEST_ENABLE | Held at 1 during the run |
| IBR3_TRIAL_TEST_OPEN_REQUEST | First became 1 at 5.0 s |
| IBR3_TRIAL_BRK_CMD | First became 1 at 5.0 s |
| IBR3_TRIAL_BRK_STATE | Crossed the open threshold at 5.0 s; final value 2 |
| IBR3_TRIAL_BRK_OPEN_BOOL | First became 1 at 5.0 s |
| IBR3_TRIAL_SOURCE_AVAILABLE | Changed from 1 to 0 at 5.0 s |
| IBR3_TRIAL_CASCADE_EVENT_VALID | First became 1 at 5.0 s |
| IBR3_TRIAL_CASCADE_EVENT_CAUSE_CODE | Final value 5 |
| IBR3_TRIAL_CASCADE_FIRST_EVENT_TIME_S | Final value 5.0 s |
| CASCADE3_MONITOR_CAUSE_CODE_IBR3_TRIAL | Final value 5 |
| CASCADE3_MONITOR_CHRONOLOGY_CONSISTENT | Held at 1 |

CASCADE3 chronology observed an existing first event at 2.01603 s and the IBR3
trial event as the second timed event at 5.0 s. The final first-to-second gap
was 2.98397 s; third event time and second-to-third gap remained `-1`.

## Restoration and static final state

Final read-only audit status:

```text
execution_status = completed_pass_with_pscad_post_restore_metadata_drift
```

Main project SHA remained protected:

```text
CBA120BB167CB7FA6C4A1AE4471268850AB61761EC1877EB7B87015627FE9DAB
```

Trial SHA values:

```text
pre-run baseline: 469103EF282C97CF7735D0E4BB8665A6D57FA453A6AA7F5BA86B5770951CDE92
during temporary run-enable state: B9F8CCE9B6C43F57644DF4693D0D651815FB6DBCC2706F9D48A0882DEA705E42
post-restore: C03DAA211B591923F533554C9951503096677BCF52547D13A10C4B431E69A349
```

The post-restore trial SHA differs from the pre-run SHA because PSCAD rewrote
project metadata/date and display values during Save/Build. The final audit
separately verified the protected control/interface values:

- IBR3 test-enable Constant restored to 0.
- IBR3 open time remains 5.0 s.
- IBR3 event packet cause code remains 5.
- IBR2 test-enable Constant remains 0.
- Output Channel count remains 253.
- MATLAB, fourth source, virtual source, and autoreclose were not added.

## Artifacts

- `analysis/pscad_tools/preflight_ibr3_single_opening_dynamic_run.py`
- `analysis/pscad_tools/parse_ibr3_single_opening_dynamic_run.py`
- `analysis/pscad_tools/audit_ibr3_single_opening_dynamic_run.py`
- `data/validation/ibr3_single_opening_pre_run_manifest.json`
- `data/validation/ibr3_trial_single_opening_run_summary.json`
- `data/validation/ibr3_trial_single_opening_run_channels.csv`
- `data/validation/ibr3_trial_single_opening_run_metrics.csv`
- `data/validation/ibr3_trial_single_opening_final_audit.json`

Raw PSCAD `.out`, `.inf`, `.sav`, and `.gf46` files are not committed. The
restore Build overwrote/removed the raw PGB Output Channel files, so the
repository stores the parsed summaries only.

## Claim boundary

This run only validates one IBR3_TRIAL trial-only local-opening chain under the
fixed model, default fault, and run settings used here.

It does not prove:

- three-source cascade propagation,
- physical causality direction,
- system stability,
- protection coordination setting validity,
- MATLAB coupling,
- general applicability beyond this one run.
