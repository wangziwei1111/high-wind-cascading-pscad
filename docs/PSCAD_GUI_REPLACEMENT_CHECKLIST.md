# PSCAD GUI Replacement Checklist

- [ ] Open baseline PNNL project and confirm no edits are pending.
- [ ] Create and open `3IBR_DFIG1_TRIAL`.
- [ ] Confirm trial copy runs before replacement.
- [ ] Screenshot candidate P3 branch around instance `475433949`.
- [ ] Record 345/22 kV transformer, 22 kV reactor, 22/0.6 kV transformer, and IBR port data.
- [ ] Open Type-3 Average standalone project.
- [ ] Record `Type3_WTG_Avg` top-level parameters and `AC_sys` port.
- [ ] Decide Option B variant: `Vbase=22 kV` or new 22/33 kV transformer.
- [ ] Add an external breaker at the collector boundary.
- [ ] Remove/bypass old IBR only in the trial copy.
- [ ] Do not copy standalone `V_source`, `POC Fault`, `Terminal Fault`, or Type-3 test grid.
- [ ] Run no-fault, no MATLAB, no LVRT, no protection automation.
- [ ] Save screenshots and run log outside Git or as redacted documentation only.
