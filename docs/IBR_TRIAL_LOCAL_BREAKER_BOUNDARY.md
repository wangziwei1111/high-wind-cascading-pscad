# IBR Trial Local Breaker Boundary

## Status

```text
execution_status = trial_ibr_breaker_boundary_static_fallback
trial_project_status = created
ibr_branch_mapping_status = pass
local_breaker_boundary_status = not_constructed
breaker_state_semantics_status = not_constructed
output_channel_status = not_constructed
control_path_isolation_status = unavailable_after_main_integrity_failure
main_project_integrity_status = fail
dynamic_behavior_status = unavailable
second_source_event_status = not_constructed
dual_source_collector_status = not_constructed
```

The trial project was created and trial Build artifacts are present, but the
task stopped before breaker insertion because the protected main project SHA
changed after stage A.

## Project Evidence

```text
Protected main project:
C:\pscad_work\pnnl_39_3ibr_pscad46_strip5\PSCAD\3IBR.pscx

Protected main SHA-256:
9A4D8B4594CDEAC3085E34BE64A6A52DA0CB626FE91E37240D0C8CE74F6D33DB

Observed main SHA-256 after stage A:
97AE9A99E199734510352DACBDE6120BBC411356C244C3DEA0ED8B01AB2B7906

Trial project:
C:\pscad_work\pnnl_39_3ibr_pscad46_strip5\PSCAD\3IBR_DFIG1_TRIAL.pscx

Trial SHA-256 after stage A:
62A9202F708402A850F6810797C852A54CD7D627D77B691749C4C6512CAEEF15
```

Because the main-project integrity gate failed, no further PSCAD GUI
construction is allowed in this task.

## Planned Interface

The selected trial source remains:

```text
Source ID: IBR2_TRIAL
Target IBR: IBR_AVM_2_1_1_1
P/Q/V observables: VIBR2, PIBR2, QIBR2
Planned breaker: BRK_IBR2_TRIAL
```

Planned interface table:

| Signal | Type | Initial value | Meaning | Dynamic status |
| --- | --- | ---: | --- | --- |
| `IBR2_TRIAL_BRK_CMD` | bool/code | proven closed command value | trial local breaker command | Not constructed |
| `IBR2_TRIAL_BRK_STATE` | state | proven initial closed state | trial local breaker actual state | Not constructed |
| `IBR2_TRIAL_BRK_OPEN_BOOL` | bool | 0 | standardized actual open state | Not constructed |
| `IBR2_TRIAL_SOURCE_AVAILABLE` | bool | 1 | trial IBR branch availability | Not constructed |

No second-source event packet exists yet. No dual-source collector exists yet.

## Stop Reason

The task rules require stopping if the protected main project SHA changes.
That condition occurred after the trial project creation stage. This document
therefore records a static fallback, not a completed local breaker boundary.

## Claim Boundary

No PSCAD Run was performed in this task. No dynamic breaker response, source
electrical isolation, second-source event, dual-source collector behavior,
multi-machine cascade propagation, physical field breaker behavior, or MATLAB
coupling was validated.

No Type-3 LVRT logic, `BRK_DFIG`, `FINAL_BRK_CMD`, second-source event packet,
or dual-source collector change is claimed by this fallback.

## Main-Project SHA Delta Audit Addendum

```text
main_project_integrity_status =
main_project_nonfunctional_metadata_difference

functional_equivalence_status =
supported

trial_resumption_eligibility =
eligible_for_separate_task
```

The SHA delta audit found 181 XML differences, all classified as
`nonfunctional_metadata_or_display_change` (`revisor`, `date`, or `z`
metadata/display-order fields). It found no component, connection, parameter,
test-parameter, or Output Channel differences.

No breaker construction was resumed in that audit task. `BRK_IBR2_TRIAL` and
the four planned `IBR2_TRIAL_*` status-interface signals remain not
constructed.
