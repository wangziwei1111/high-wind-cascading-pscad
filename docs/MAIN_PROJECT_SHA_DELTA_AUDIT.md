# Main Project SHA Delta Audit

## Status

```text
execution_status = main_project_sha_delta_audit_complete
baseline_status = pass
raw_byte_identity_status = fail
xml_parse_status = pass
component_inventory_status = pass
connectivity_equivalence_status = pass
critical_scope_status = pass
output_channel_integrity_status = pass
functional_equivalence_status = supported
main_project_integrity_status = main_project_nonfunctional_metadata_difference
trial_resumption_eligibility = eligible_for_separate_task
```

This was a zero-GUI, zero-Build, zero-Run, read-only audit. PSCAD was not
started, no PSCAD project was saved, and no `.pscx` file was modified.

## Baseline Location

The protected baseline was located by exact byte SHA-256 match:

```text
Baseline path:
C:\pscad_work\backups\ibr_trial_local_breaker_boundary_20260629_204521\3IBR.pscx

Baseline SHA-256:
9A4D8B4594CDEAC3085E34BE64A6A52DA0CB626FE91E37240D0C8CE74F6D33DB

Baseline size:
3489935 bytes
```

The same SHA also exists in the earlier cascade-event bus snapshot and in the
`two_real_source_cascade_collector_20260629_202809` local backup. No approximate
baseline was used.

## Current Main Project

```text
Current main path:
C:\pscad_work\pnnl_39_3ibr_pscad46_strip5\PSCAD\3IBR.pscx

Current SHA-256:
97AE9A99E199734510352DACBDE6120BBC411356C244C3DEA0ED8B01AB2B7906

Current size:
3489955 bytes

Matches previous observed SHA:
true
```

The raw byte hash differs from the protected baseline. The file is 20 bytes
larger than the protected baseline.

## Structural Comparison

| Item | Baseline | Current | Delta |
| --- | ---: | ---: | ---: |
| Components | 2349 | 2349 | 0 |
| Wires | 1533 | 1533 | 0 |
| Output Channels | 203 | 203 | 0 |
| Pages | 20 | 20 | 0 |
| Definitions | 51 | 51 | 0 |
| Critical objects | 632 | 632 | 0 |

The audit found no component additions, deletions, replacements, parameter
changes, connection changes, or Output Channel configuration changes.

## Difference Classification

| Classification | Count |
| --- | ---: |
| `nonfunctional_metadata_or_display_change` | 181 |
| `functional_control_or_network_change` | 0 |
| `test_parameter_change` | 0 |
| `output_channel_change` | 0 |
| `unclassified_difference` | 0 |

All 181 XML differences are limited to:

```text
revisor metadata
Definition date metadata
z visual stacking/display-order attributes
```

No functional or unclassified differences were found.

## Output Channel Audit

```text
output_channel_integrity_status = pass
output_channel_delta_keys = []
```

All Output Channel titles, associated signal names, transfer/save settings,
scale factors, units, display limits, and raw parameter sets were identical
between the protected baseline and the current main project.

## P3.f Boundary

The existing generated Fortran file was recorded only as auxiliary evidence:

```text
P3.f:
C:\pscad_work\pnnl_39_3ibr_pscad46_strip5\PSCAD\3IBR.gf46\P3.f

P3.f SHA-256:
A5FC7668B2C257BF948F52AC3661C8C8CB28C243B5A9D96A9035241964873B67
```

The audit did not regenerate `P3.f`. Functional equivalence is based on `.pscx`
structure, parameters, connections, and Output Channel comparison, not on the
generated Fortran alone.

## Trial Status

```text
Trial path:
C:\pscad_work\pnnl_39_3ibr_pscad46_strip5\PSCAD\3IBR_DFIG1_TRIAL.pscx

Trial SHA-256:
62A9202F708402A850F6810797C852A54CD7D627D77B691749C4C6512CAEEF15

trial_xml_parse_status = pass
trial_breaker_boundary_status = not_constructed
trial_has_BRK_IBR2_TRIAL = false
trial_has_IBR2_TRIAL_BRK_CMD = false
trial_has_IBR2_TRIAL_BRK_STATE = false
trial_has_IBR2_TRIAL_BRK_OPEN_BOOL = false
trial_has_IBR2_TRIAL_SOURCE_AVAILABLE = false
```

The trial project still does not contain the planned local breaker boundary or
the four planned status-interface signals.

## Conclusion

The current main project is supported as functionally equivalent to the
protected baseline by static evidence. Its SHA delta is attributable to
nonfunctional metadata/display differences only.

```text
main_project_integrity_status =
main_project_nonfunctional_metadata_difference

trial_resumption_eligibility =
eligible_for_separate_task
```

This does not resume breaker construction in the current audit. The trial may
be reconsidered only in a separate explicitly approved task.

## Claim Boundary

No PSCAD GUI was opened. No Build was performed. No Run was performed. No main
project or trial project was modified. No `BRK_IBR2_TRIAL` was created. No
second-source event packet, dual-source collector, virtual source, automatic
reclose, MATLAB coupling, or dynamic multi-machine behavior was created or
validated.
