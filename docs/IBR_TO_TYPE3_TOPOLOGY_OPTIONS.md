# IBR to Type-3 Topology Options

## Grid Boundary Comparison

| Item | PNNL IBR_AVM_2_1_1 | Type-3 Average | Conclusion |
|---|---|---|---|
| High-voltage grid bus | GBUS30/N30 branch, upstream `E_2_30_1` 345 kV side | Standalone grid source/POC, not reusable as grid | Do not copy Type-3 grid source |
| Medium-voltage branch | PNNL 22 kV after 345/22 transformer | Type-3 `VLL_Gr`/`Vbase`, example about 33 kV | Needs voltage adaptation |
| Low-voltage converter terminal | PNNL IBR step-down side `0.6 kV` | Type-3 converter/machine internals include about `0.69 kV` plus internal transformer | Do not direct-wire blindly |
| PNNL transformer set | 345/22 kV plus 22/0.6 kV | Internal 3-winding transformer inside `Type3_WTG_Avg` | Avoid duplicate/contradictory transformers |
| Rated branch capacity | Candidate local step-down `110.4 MVA`; upstream `100 MVA` | Example default `UN=100`, `Rated_MW=2 MW`, `Machine_MVA=2.5 MVA` from GUI/user observation; file maps `No_WTG=UN`, `Pbase=Rated_MW`, `Mrating=Machine_MVA` | Scale Type-3 to target branch before run |
| Enable/block | IBR has `Inputs` and `Flags`; no simple verified `Dblk` external port | `Dblk` top-level parameter | Use Type-3 `Dblk` and an external breaker for trial |

## Option A: Keep Full PNNL Branch, Set Type-3 Vbase to 0.6 kV

This retains PNNL 345/22 kV transformer, series reactor, and 22/0.6 kV transformer, then attempts to make the Type-3 aggregate look like the old low-voltage converter.

- Electrical feasibility: low.
- Initial power-flow consistency: weak unless extensive internal Type-3 scaling is changed.
- Preserves original IBR physical location: yes.
- Adds duplicate transformer risk: high, because Type-3 already contains internal machine/converter transformer structure.
- Voltage-level risk: high; `Vbase=33 kV` is tied to Type-3 HV/grid interface, not the 0.6 kV converter terminal.
- Future breaker/LVRT convenience: poor.
- Recommendation: exclude as first trial.

Evidence class: inferred from verified Type-3 internal transformer and PNNL 22/0.6 kV branch.

## Option B: Keep PNNL 345/22 kV Upstream, Connect Type-3 at 22 kV via Adaptation

This keeps the PNNL 345/22 kV transformer and upstream network, removes or bypasses the old IBR low-voltage converter-side branch, and connects the Type-3 wind-farm AC interface at the PNNL 22 kV collection point through either adjusted `Vbase=22 kV` or a small 22/33 kV wind-farm step-up transformer.

- Electrical feasibility: medium-high.
- Initial power-flow consistency: best after setting `UN`, `Rated_MW`, and `Machine_MVA` near the replaced IBR branch.
- Preserves original IBR connection location: yes, at the same 22 kV branch behind GBUS30/N30.
- Adds duplicate transformer risk: moderate if a 22/33 transformer is added; lower if Type-3 `Vbase` can be safely adjusted to 22 kV after GUI confirmation.
- Voltage-level risk: manageable and explicit.
- Future breaker/LVRT convenience: good; breaker can be placed at the 22 kV wind-farm collector boundary.
- Recommendation: preferred first manual trial.

Evidence class: verified_from_model_file for transformer/port facts; inferred for recommended adaptation.

## Option C: Keep Only PNNL Upstream Grid, Reuse More Type-3 Standalone Network

This removes most of the old IBR branch and imports Type-3's standalone transformer/cable/POC arrangement behind GBUS30/N30.

- Electrical feasibility: medium.
- Initial power-flow consistency: uncertain because standalone source, transformer, cable, and POC were tuned for an isolated example.
- Preserves original IBR connection location: partially.
- Adds duplicate transformer risk: high unless carefully stripped.
- Voltage-level risk: medium-high.
- Future breaker/LVRT convenience: good, but at the cost of more topology disturbance.
- Recommendation: reversible fallback only if Option B cannot initialize.

Evidence class: inferred from verified Type-3 standalone test components.

## Recommended and Rollback Choices

Preferred first scheme: Option B.

Rollback scheme: restore the untouched PNNL 3IBR baseline and abandon the trial copy; if another attempt is needed, use Option C only in a separate copy.
