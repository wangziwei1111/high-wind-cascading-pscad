# IBR to Type-3 Signal Mapping

| PNNL IBR signal/parameter | Type-3 signal/parameter | Mapping status | Unit/scaling | Direct connection? | Notes |
|---|---|---|---|---|---|
| `Sbase` | `Machine_MVA`, `UN`, `Rated_MW` via `Mrating`, `No_WTG`, `Pbase` | convertible_with_verified_scaling | MVA/MW aggregate scaling | No | Match aggregate MVA/MW to replaced IBR branch; do not wire as a signal. |
| `Pini` | `Vwind`, `Rated_MW`, initial power reference/internal initialization | requires_manual_controller_adaptation | MW or pu depending control page | No | Type-3 has wind/mechanical initialization, not a simple IBR `Pini` clone. |
| `Pord` | `Pref_pu` inside rotor-side/control path | requires_manual_controller_adaptation | pu on Type-3 machine/base | No | Name similarity is insufficient; first trial should use Type-3 native initialization. |
| `Qord` | `Q_ord`, `Qref_pu`, `qmode`, voltage/reactive controls | requires_manual_controller_adaptation | MVAR/pu mode-dependent | No | Decide voltage-control or Q-control mode manually after no-fault run. |
| `Pfcmd` | No verified top-level equivalent | no_direct_equivalent | N/A | No | Type-3 grid-side converter normally handles reactive/DC link; PF command needs custom controller adaptation. |
| `DB` / `DBLK` | `Dblk`, `DBlk_Rsc`, `DBlk_Gsc`, `DBlk_Rtr` | requires_manual_controller_adaptation | integer block/deblock semantics | No | Semantics differ; use Type-3 native `Dblk` plus external breaker. |
| `QIBR` | Type-3 measured/exported Q signals | unresolved | MVAR or pu | No | Static scan confirms Q controls but not a direct external replacement signal. |
| `INV_Vbase` | `Vbase` / `VLL_Gr` | convertible_with_verified_scaling | kV L-L | No | `Vbase` is grid/HV-side Type-3 AC interface, not PNNL 0.6 kV converter terminal. |
| `fPLL` | Type-3 internal PLL frequency/control variables | no_direct_equivalent | Hz/pu internal | No | Type-3 PLL is internal to DFIG controls. |
| `fGFM` | No parsed IBR external port in current definition | no_direct_equivalent | N/A | No | Treat any old `fGFM` reference as stale until GUI proves otherwise. |
| PNNL P/Q/V measurements | Type-3 P/Q/V graph/import/export signals | requires_manual_controller_adaptation | MW/MVAR/kV/pu | No | Recreate measurement taps manually at the trial POC. |
| External trip/block | External 3-phase breaker plus `Dblk` | convertible_with_verified_scaling | integer/breaker status | No direct signal reuse | Best first safety boundary is a breaker at the 22 kV collector side. |

Key rule: no signal is directly wire-equivalent merely because names look similar.
