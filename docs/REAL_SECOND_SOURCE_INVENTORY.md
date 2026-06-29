# Real Second-Source Inventory

## Status

```text
real_second_source_inventory_status = no_qualified_candidate
second_source_qualification_status = fail
selected_source = none
execution_scope = read-only PSCAD inventory
pscad_run_performed = no
pscad_project_modified_by_script = no
```

No qualified real second source was found for a monitor-only cascade adapter in
the current project state.  Because no candidate passed all seven qualification
gates, no PSCAD GUI expansion, no dual-source collector modification, and no
dynamic Run are allowed by this task.

## Evidence Scope

```text
Project: C:\pscad_work\pnnl_39_3ibr_pscad46_strip5\PSCAD\3IBR.pscx
Page: 3IBR:Main(0):P1(0):P3(0)
Project SHA-256: 9A4D8B4594CDEAC3085E34BE64A6A52DA0CB626FE91E37240D0C8CE74F6D33DB
Generated Fortran inspected: C:\pscad_work\pnnl_39_3ibr_pscad46_strip5\PSCAD\3IBR.gf46\P3.f
Inventory script: analysis/pscad_tools/inventory_real_cascade_sources.py
JSON evidence: data/reference/real_second_source_inventory.json
CSV summary: data/reference/real_second_source_inventory_summary.csv
```

The inventory reads the active PSCAD XML and the already-generated `P3.f`. It
does not edit `.pscx`, does not invoke PSCAD Build, and does not run EMTDC.

## Qualification Gates

A candidate second source must pass all of these gates:

| Gate | Required evidence |
| --- | --- |
| `distinct_electrical_source` | Different real injection branch from `TYPE3_DFIG_1` |
| `local_open_state_available` | Exposed local breaker/switch/isolation state for that source |
| `open_state_semantics_proven` | Static evidence for what value means open |
| `initial_closed_state_proven` | Static evidence the source is not initially open |
| `P_or_Q_or_V_observable` | At least one source-related P, Q, or V observable |
| `monitor_only_access` | State can be monitored without changing existing control |
| `not_shared_system_switch` | Not a shared bus, system, fault, line, load, or grid switch |

## Candidate Summary

| Candidate | Type | P/Q/V observable | Local open state | Decision |
| --- | --- | --- | --- | --- |
| `TYPE3_DFIG_1` | Protected Type-3 DFIG source | `VIBR1_2`, `PIBR1_2`, `QIBR1_2` | `DFIG_BRK_STATE` via `BRK_DFIG` | Excluded: already source 1 and protected |
| `IBR_AVM_2_1_1_1` | Existing IBR control module | `VIBR2`, `PIBR2`, `QIBR2` | none found | Excluded: no actual local open-state output |
| `IBR_AVM_2_1_1_2` | Existing IBR control module | `VIBR3`, `PIBR3`, `QIBR3` | none found | Excluded: no actual local open-state output |
| `G_31_0_1_DYR` | DYR generator | unavailable | none found | Excluded: no actual local open-state output |
| `G_32_0_1_DYR` | DYR generator | unavailable | none found | Excluded: no actual local open-state output |
| `G_33_0_1_DYR` | DYR generator | unavailable | none found | Excluded: no actual local open-state output |
| `G_34_0_1_DYR` | DYR generator | unavailable | none found | Excluded: no actual local open-state output |
| `G_35_0_1_DYR` | DYR generator | unavailable | none found | Excluded: no actual local open-state output |
| `G_36_0_1_DYR` | DYR generator | unavailable | none found | Excluded: no actual local open-state output |
| `G_37_0_1_DYR` | DYR generator | unavailable | none found | Excluded: no actual local open-state output |
| `G_38_0_1_DYR` | DYR generator | unavailable | none found | Excluded: no actual local open-state output |
| `G_39_0_1_DYR` | DYR generator | unavailable | none found | Excluded: no actual local open-state output |
| `BRK` | Existing breaker component | none | no `SBRA/SBRB/SBRC` state output | Excluded: breaker is not a qualified source packet input |
| `Trip` | Existing breaker component | none | no `SBRA/SBRB/SBRC` state output | Excluded: breaker is not a qualified source packet input |

The project also contains 12 `master:peswitch` instances. They are excluded as
internal power-electronics or switching elements because they do not expose a
source-local actual open-state signal suitable for a real second-source event
packet.

## Closest Candidates

`TYPE3_DFIG_1` is the only object with both source observability and an exposed
actual breaker state, but it is the already-protected source 1. It cannot be
reused as the second source.

The two `IBR_AVM_2_1_1` instances have nearby P/Q/V observables, but no exposed
local breaker, switch, or isolation-state output was found. They therefore fail
the `local_open_state_available` and `open_state_semantics_proven` gates.

The DYR generators are real source components, but the inventory found no
source-local actual open-state signal and no static open-state semantics tied to
each generator branch. They cannot be used for the monitor-only second-source
adapter without adding or exposing real state structure outside this task.

## Stop Decision

Because no candidate passed all seven gates:

```text
No second-source event packet was created.
No two-real-source collector was built.
No Output Channels were added for a second source.
No PSCAD Build or Run was requested for this task.
No Type-3 LVRT, FINAL_BRK_CMD, BRK_DFIG, fault logic, or main circuit structure was modified.
```

The next valid engineering step is to decide whether the PSCAD model should
expose a real local open-state signal for an existing non-DFIG source branch.
That would be a separate modeling task and must not be represented by a
constant, a command-only label, or a shared system switch.
