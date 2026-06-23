# Output Channel Candidates

Scope: candidates inferred from `.inf`, `.out`, current `3IBR.pscx`, and component naming. No GUI verification was performed.

## PGB-to-OUT Mapping Assumption
- `3IBR.inf` enumerates PGB channels in order. The `3IBR_01.out` file has time plus 10 values, so this audit maps PGB 1-10 to `3IBR_01.out` columns 2-11, PGB 11-20 to `3IBR_02.out`, etc. This mapping must be confirmed against PSCAD output export settings if exact plotting is required.

## Candidate Channels
| Signal target | Candidate desc | File | Column | Units | Measurement location / reason | Direction/sign confidence | Overall confidence | GUI confirmation needed |
|---|---|---|---:|---|---|---|---|---|
| frequency/PLL candidate | `SPD30` (PGB 1, group `P3`) | `external/pscad_snapshot_20260623/pnnl_39_3ibr_pscad46_strip5_PSCAD/3IBR.gf46/3IBR_01.out` | 2 | `` | P3 speed/frequency-related candidate; unit empty | unknown; PSCAD meter orientation must be checked | low | yes |
| Type-3 V / POC V candidate | `VIBR1_2` (PGB 2, group `P3`) | `external/pscad_snapshot_20260623/pnnl_39_3ibr_pscad46_strip5_PSCAD/3IBR.gf46/3IBR_01.out` | 3 | `` | P3 first IBR/DFIG branch candidate after replacement naming convention | unknown; PSCAD meter orientation must be checked | medium | yes |
| Type-3 P / POC P candidate | `PIBR1_2` (PGB 4, group `P3`) | `external/pscad_snapshot_20260623/pnnl_39_3ibr_pscad46_strip5_PSCAD/3IBR.gf46/3IBR_01.out` | 5 | `` | P3 first IBR/DFIG branch candidate after replacement naming convention | unknown; PSCAD meter orientation must be checked | medium | yes |
| Type-3 Q / POC Q candidate | `QIBR1_2` (PGB 6, group `P3`) | `external/pscad_snapshot_20260623/pnnl_39_3ibr_pscad46_strip5_PSCAD/3IBR.gf46/3IBR_01.out` | 7 | `` | P3 first IBR/DFIG branch candidate after replacement naming convention | unknown; PSCAD meter orientation must be checked | medium | yes |
| Type-3 Q / POC Q candidate | `Q30` (PGB 17, group `P3`) | `external/pscad_snapshot_20260623/pnnl_39_3ibr_pscad46_strip5_PSCAD/3IBR.gf46/3IBR_02.out` | 8 | `` | P3 GBUS30/N30 measurement candidate near replaced branch | unknown; PSCAD meter orientation must be checked | medium | yes |
| Type-3 P / POC P candidate | `P30` (PGB 18, group `P3`) | `external/pscad_snapshot_20260623/pnnl_39_3ibr_pscad46_strip5_PSCAD/3IBR.gf46/3IBR_02.out` | 9 | `` | P3 GBUS30/N30 measurement candidate near replaced branch | unknown; PSCAD meter orientation must be checked | medium | yes |
| Type-3 V / POC V candidate | `V30` (PGB 19, group `P3`) | `external/pscad_snapshot_20260623/pnnl_39_3ibr_pscad46_strip5_PSCAD/3IBR.gf46/3IBR_02.out` | 10 | `` | P3 GBUS30/N30 measurement candidate near replaced branch | unknown; PSCAD meter orientation must be checked | medium | yes |
| frequency/PLL candidate | `PLL_f` (PGB 124, group `IBR_AVM_2_1_1`) | `external/pscad_snapshot_20260623/pnnl_39_3ibr_pscad46_strip5_PSCAD/3IBR.gf46/3IBR_13.out` | 5 | `` | contains Freq/PLL in channel desc | unknown; PSCAD meter orientation must be checked | medium | yes |
| frequency/PLL candidate | `PLL_f_1` (PGB 173, group `IBR_AVM_2_1_1`) | `external/pscad_snapshot_20260623/pnnl_39_3ibr_pscad46_strip5_PSCAD/3IBR.gf46/3IBR_18.out` | 4 | `` | contains Freq/PLL in channel desc | unknown; PSCAD meter orientation must be checked | medium | yes |
| breaker/chopper status candidate | `BRK ord` (PGB 225, group `Type3_WTG_Avg`) | `external/pscad_snapshot_20260623/pnnl_39_3ibr_pscad46_strip5_PSCAD/3IBR.gf46/3IBR_23.out` | 6 | `` | contains Dblk/BRK in channel desc | unknown; PSCAD meter orientation must be checked | high | yes |
| Dblk/internal blocking candidate | `Dblk_VdcCtrl` (PGB 228, group `Type3_WTG_Avg`) | `external/pscad_snapshot_20260623/pnnl_39_3ibr_pscad46_strip5_PSCAD/3IBR.gf46/3IBR_23.out` | 9 | `` | contains Dblk/BRK in channel desc | unknown; PSCAD meter orientation must be checked | high | yes |
| Dblk/internal blocking candidate | `Dblk_Rotor` (PGB 229, group `Type3_WTG_Avg`) | `external/pscad_snapshot_20260623/pnnl_39_3ibr_pscad46_strip5_PSCAD/3IBR.gf46/3IBR_23.out` | 10 | `` | contains Dblk/BRK in channel desc | unknown; PSCAD meter orientation must be checked | high | yes |
| frequency/PLL candidate | `Freq_PLL` (PGB 298, group `Rotor_side_Controls`) | `external/pscad_snapshot_20260623/pnnl_39_3ibr_pscad46_strip5_PSCAD/3IBR.gf46/3IBR_30.out` | 9 | `` | contains Freq/PLL in channel desc | unknown; PSCAD meter orientation must be checked | medium | yes |
| frequency/PLL candidate | `slpangPLL` (PGB 300, group `Rotor_side_Controls`) | `external/pscad_snapshot_20260623/pnnl_39_3ibr_pscad46_strip5_PSCAD/3IBR.gf46/3IBR_30.out` | 11 | `` | contains Freq/PLL in channel desc | unknown; PSCAD meter orientation must be checked | medium | yes |
| frequency/PLL candidate | `Phis PLL` (PGB 301, group `Rotor_side_Controls`) | `external/pscad_snapshot_20260623/pnnl_39_3ibr_pscad46_strip5_PSCAD/3IBR.gf46/3IBR_31.out` | 2 | `` | contains Freq/PLL in channel desc | unknown; PSCAD meter orientation must be checked | medium | yes |
| breaker/chopper status candidate | `BRK_CHOP` (PGB 322, group `Chopper`) | `external/pscad_snapshot_20260623/pnnl_39_3ibr_pscad46_strip5_PSCAD/3IBR.gf46/3IBR_33.out` | 3 | `` | contains Dblk/BRK in channel desc | unknown; PSCAD meter orientation must be checked | high | yes |

## Explicit Signals Without Direct PGB Channel Match
- `Dblk_DFIG`: XML objects `[('1031105444', 'master:datalabel', '360', '1062')]`; `.inf` direct desc matches `[]`. Candidate status: no direct PGB channel found in the current `.inf`; add/verify explicit output channel in GUI if time-series export is needed.
- `Vwind`: XML objects `[('697683388', 'master:datalabel', '360', '1134')]`; `.inf` direct desc matches `[]`. Candidate status: no direct PGB channel found in the current `.inf`; add/verify explicit output channel in GUI if time-series export is needed.
- `BRK_DFIG`: XML objects `[('521858026', 'master:breaker3', '864', '990'), ('1046505114', 'master:datalabel', '918', '1026')]`; `.inf` direct desc matches `[]`. Candidate status: no direct PGB channel found in the current `.inf`; add/verify explicit output channel in GUI if time-series export is needed.

## Recommended GUI Checks
- Confirm whether `VIBR1_2`, `PIBR1_2`, and `QIBR1_2` now measure the Type-3 replacement branch after the old first IBR removal.
- Confirm meter arrow orientation around `BRK_DFIG`/`XFMR_DFIG_22_33` for P/Q sign convention.
- Add explicit PGB/output channels for `Dblk_DFIG`, `Vwind`, and `BRK_DFIG` if those signals must be reported from `.out` files.
