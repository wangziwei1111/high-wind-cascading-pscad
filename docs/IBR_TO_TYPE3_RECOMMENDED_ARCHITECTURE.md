# Recommended Architecture: Single IBR to Type-3 DFIG Trial

## Recommendation

Use a separate `3IBR_DFIG1_TRIAL` working copy. Keep the PNNL upstream GBUS30/N30 network and the 345/22 kV transformer. Do not keep the old `IBR_AVM_2_1_1` converter block in parallel with the Type-3 wind farm. Place the Type-3 wind-farm boundary at the 22 kV collector side, using either:

1. Type-3 `Vbase=22 kV` if GUI inspection confirms the official block accepts this as the `VLL_Gr` grid/HV-side parameter without invalidating internal converter scaling.
2. A new explicit 22/33 kV wind-farm step-up transformer if preserving the official 33 kV example setting is safer.

Evidence:

- PNNL branch has verified 345/22 kV and 22/0.6 kV transformers around the candidate IBR branch.
- Type-3 core has a top-level 3-phase `AC_sys` port and internal transformer/converter structure.
- Type-3 standalone network has a separate grid source, POC, transformer, cable, and fault panels that should not be duplicated into IEEE-39.

## First Trial Boundary

Recommended manual boundary:

`GBUS30/N30 -> existing PNNL 345/22 kV transformer -> 22 kV collector/trial breaker -> Type3_WTG_Avg AC_sys`

If `Vbase=22 kV` is not accepted or yields unreasonable initialization, insert:

`22 kV collector -> trial breaker -> new 22/33 kV transformer -> Type3_WTG_Avg AC_sys at 33 kV`

## Explicit Exclusions

- Do not connect Type-3 directly to the old PNNL 0.6 kV converter terminal.
- Do not copy Type-3 `V_source` into IEEE-39.
- Do not copy Type-3 standalone `POC Fault` or `Terminal Fault` panels for the first no-fault trial.
- Do not run MATLAB, LVRT, overload protection, UFLS/UVLS, SVC/STATCOM, or cascading logic in this stage.

## Risk Notes

- The static parser cannot prove the exact `Inputs` bus ordering into the PNNL IBR. Treat user GUI observations as starting notes and verify in PSCAD before deletion.
- The first trial should target stable no-fault initialization, not exact dynamic equivalence.
- Keep an external breaker between PNNL and Type-3 as the first safe trip/isolation point.
