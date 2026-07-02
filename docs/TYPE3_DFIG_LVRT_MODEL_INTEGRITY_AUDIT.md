# Type-3 DFIG LVRT Model Integrity Audit

## Status

```text
execution_status = type3_lvrt_model_integrity_audit_complete
model_integrity_status = model_integrity_nonfunctional_metadata_difference
functional_equivalence = proven_for_audited_structure_and_parameters
```

This was a read-only, zero-run audit. Neither PSCAD project was written,
formatted, restored, opened in PSCAD, Built, Run, or saved.

## Compared Files

```text
Exact task-start backup:
C:\pscad_work\backups\type3_lvrt_closed_loop_coverage_20260628_220356\3IBR.pscx
SHA-256 = DA4518483523C1BCAFF2A74AAC356B29B53F9642A8E9D7E9E44FCDA2E96F90E6
size = 3421312 bytes

Current active project:
C:\pscad_work\pnnl_39_3ibr_pscad46_strip5\PSCAD\3IBR.pscx
SHA-256 = 0FB0F7E3927C1E5863F0692F6223DCF8152987BAE99AB83134DF1955C2713F17
size = 3421306 bytes
```

The start and final byte hashes are different. The backup was accepted only
after its SHA matched the required task-start SHA exactly.

## Structural Comparison

Both files parse as XML. The audit compared project/definition metadata,
component IDs/types/titles/pages, direct parameters, component vertices, wire
geometry, Output Channel settings, and critical LVRT/breaker object matches.

| Inventory | Task-start backup | Current active |
| --- | ---: | ---: |
| Component instances | 4583 | 4583 |
| Wires | 1437 | 1437 |
| Output Channels | 185 | 185 |
| Critical-keyword objects | 83 | 83 |
| Duplicate component keys | 0 | 0 |

```text
Output Channel titles added = 0
Output Channel titles removed = 0
Output Channel parameter changes = 0
Critical object keys added = 0
Critical object keys removed = 0
Wire/connection differences = 0
```

No functional control, network, fault-test parameter, BRK_DFIG circuit
parameter, or Output Channel difference was detected.

## Difference Classification

The raw files contain 128 classified structural/value differences:

| Category | Count |
| --- | ---: |
| functional_control_or_network_change | 0 |
| test_parameter_change | 0 |
| nonfunctional_metadata_or_display_change | 128 |
| unclassified_difference | 0 |

The 128 nonfunctional differences are:

```text
50 definition revision/view metadata changes
38 component layout/description/revision metadata changes
37 display stacking/layout changes
2 saved BRK_DFIG P/Q run-display value changes
1 project revision metadata change
```

The timed-fault values serialize as `2.0 [s]` versus `2.0` and `0.15 [s]`
versus `0.15`; the parser verifies numeric equality rather than treating unit
annotation formatting as a parameter change.

The saved BRK_DFIG P/Q values are runtime display values under the enabled
`DisPQ` display option. All breaker command, timing, resistance, state, and
network parameters are compared separately and remain unchanged.

## Gain ID 65646757

```text
task-start backup presence = 0
current active presence = 0
conclusion = absent_from_exact_task_start_backup_and_current_active_project
```

The transient floating `master:gain` ID `65646757` that blocked the earlier
Build is absent from both the exact task-start backup and the current active
project. Its presence is not a remaining model difference.

## Integrity Conclusion

The byte hashes remain different, so byte identity is not claimed. Within the
audited XML structure and parameters, every detected difference is directly
classified as nonfunctional revision, layout, stacking, or saved run-display
metadata. There are no functional, test-parameter, Output Channel, wire, or
unclassified differences.

Therefore the evidence supports:

```text
model_integrity_status = model_integrity_nonfunctional_metadata_difference
```

This conclusion is limited to the audited PSCAD project structure and
parameters. It is not a physical hardware, turbine-isolation, multi-machine,
or MATLAB validation claim.
