# Trial IBR Breaker Insertion Feasibility

## Status

```text
trial_project_status = not_created_at_mapping_time
ibr_branch_mapping_status = pass
selected_source = IBR2_TRIAL
selected_candidate = IBR_AVM_2_1_1_1
pscad_run_performed = no
```

This feasibility pass was performed before trial breaker construction. It only
maps candidate IBR branches and does not edit PSCAD files.

## Candidate Scope

Only the two existing `IBR_AVM_2_1_1` branches were eligible:

| Candidate | Source ID | P/Q/V observables | Decision |
| --- | --- | --- | --- |
| `IBR_AVM_2_1_1_1` | `IBR2_TRIAL` | `VIBR2`, `PIBR2`, `QIBR2` | selected |
| `IBR_AVM_2_1_1_2` | `IBR3_TRIAL` | `VIBR3`, `PIBR3`, `QIBR3` | qualified but not selected |

Both candidates passed the static branch-mapping gates. `IBR2_TRIAL` was
selected because it is the lower-numbered branch and has the same complete
observable set as `IBR3_TRIAL`.

## Selected Trial Branch

```text
Source ID: IBR2_TRIAL
Target IBR component: IBR_AVM_2_1_1_1
Target IBR component id: 1220231535
Page path: 3IBR:Main(0):P1(0):P3(0)
P/Q/V observables: VIBR2, PIBR2, QIBR2
Trial breaker name: BRK_IBR2_TRIAL
```

Recommended trial-only insertion point:

```text
Insert a series three-phase breaker on the IBR2_TRIAL local branch between
the 0.6 kV side of transformer E_2_30_1 (component id 275469438) and the
low-voltage multimeter that exports VIBR2, PIBR2, and QIBR2
(component id 1433370859).
```

Planned trial-only status signals:

```text
IBR2_TRIAL_BRK_CMD
IBR2_TRIAL_BRK_STATE
IBR2_TRIAL_BRK_OPEN_BOOL
IBR2_TRIAL_SOURCE_AVAILABLE
```

## Static Gate Results

| Gate | IBR2_TRIAL | IBR3_TRIAL |
| --- | --- | --- |
| `electrical_branch_traceable` | pass | pass |
| `safe_series_insertion_point` | pass | pass |
| `not_shared_bus_or_system_switch` | pass | pass |
| `no_parallel_bypass_after_insertion` | pass | pass |
| `P_or_Q_or_V_observable` | pass | pass |
| `separate_from_TYPE3_DFIG_1` | pass | pass |
| `trial_only_scope_possible` | pass | pass |

## Claim Boundary

This feasibility result does not mean a breaker was inserted. It only means a
trial-local insertion point was identified for manual PSCAD construction.

No PSCAD Run was performed. No second-source event packet, cause code,
first-event time, or dual-source collector was created.
