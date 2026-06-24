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

## GUI / Current-Run Confirmation Addendum - 2026-06-23

This addendum reflects the current PSCAD GUI state and 20 s no-fault run artifacts under:

`C:\pscad_work\pnnl_39_3ibr_pscad46_strip5\PSCAD\3IBR.gf46`

### Confirmed Enough For No-Fault Baseline

| Requested baseline signal | Accepted current channel | Evidence | Status |
|---|---|---|---|
| `DFIG_P_MW` | `PIBR1_2`, PGB 4, `3IBR_01.out` column 5 | Current `3IBR.pscx` has `master:multimeter` ID `1263266056` at P3 x=774 y=990 with `BaseV=22 [kV]`, `P=PIBR1_2`, `Q=QIBR1_2`, `Vrms=VIBR1_2`; it sits on the replaced first Type-3 branch 22 kV side before `BRK_DFIG`. 19-20 s mean is 199.084 MW. | GUI/static confirmed for baseline |
| `DFIG_Q_MVAr` | `QIBR1_2`, PGB 6, `3IBR_01.out` column 7 | Same meter ID `1263266056`; 19-20 s mean is -18.788 MVAr under current meter sign convention. | GUI/static confirmed for baseline |
| `DFIG_V_PU_OR_KV` | `VIBR1_2`, PGB 2, `3IBR_01.out` column 3 | Same meter ID `1263266056`; 19-20 s mean is 0.999876 on the 22 kV meter base. | GUI/static confirmed for baseline |
| `DFIG_F_HZ` | `SPD30`, PGB 1, `3IBR_01.out` column 2; secondary `Freq_PLL`, PGB 298, `3IBR_30.out` column 9 | `SPD30` is exactly 60.0 Hz over 19-20 s. `Freq_PLL` is a Type-3 internal PLL candidate averaging 60.050236 Hz. | Candidate accepted for baseline only; POC frequency still needs explicit channel if required |

### Still Not Directly Exported

| Requested baseline signal | Direct `.inf` match | Current substitute | Limitation |
|---|---|---|---|
| `DFIG_DBLK` / external `Dblk_DFIG` | none | `Dblk_VdcCtrl` and `Dblk_Rotor` internal Type-3 channels | They show internal enable/blocking behavior, not the exact external `Dblk_DFIG` label. Their first `>=0.5` times are about 0.40255 s and 0.60175 s due internal model delays. |
| `DFIG_VWIND_MS` / external `Vwind` | none | static GUI/XML source `windSpeed=11.0 -> Rate_Limiter(IR=10, DR=5) -> Vwind` | No `.out` column exists for the actual `Vwind` label. |
| `DFIG_BRK_STATE` / external `BRK_DFIG` | none | internal `BRK ord`, PGB 225, `3IBR_23.out` column 6 | This is not the external `BRK_DFIG` three-phase breaker state. The branch was visually closed and carried power, but no direct breaker-state output was exported. |

Baseline conclusion: the 20 s no-fault electrical run is stable and passes, but the measurement baseline is not fully hardened until explicit GUI output channels are added for `Dblk_DFIG`, `Vwind`, and `BRK_DFIG`, or their substitutes are formally accepted with limitations.

## Manual Output Channel Completion Addendum - 2026-06-23

The three missing external channels were added manually in PSCAD GUI on the current local `3IBR` case, without changing the main electrical topology, Type-3 parameters, Dblk/Vwind support logic, `BRK_DFIG`, `XFMR_DFIG_22_33`, or remaining IBR branches.

### Added Channels

| Added channel | Source signal | GUI/source-code evidence | Units | Status |
|---|---|---|---|---|
| `DFIG_DBLK_CMD` | External command on the existing `compare(X=0.2, OL=0, OH=1) -> Dblk_DFIG` wire | `3IBR.inf` has `PGB(3) Output Desc="DFIG_DBLK_CMD"`; generated `P3.f` assigns `PGB(IPGB+19)=Dblk_DFIG` | logic | Added and short-run verified |
| `DFIG_VWIND_MS` | External wind speed on the existing `Rate_Limiter -> Vwind` wire | `3IBR.inf` has `PGB(4) Output Desc="DFIG_VWIND_MS"`; generated `P3.f` assigns `PGB(IPGB+17)=Vwind` | m/s | Added and short-run verified |
| `DFIG_BRK_STATE` | `BRK_DFIG` breaker internal A-phase status output; A phase represents the three-phase breaker because `Single Pole operation = No` | `3IBR.inf` has `PGB(1) Output Desc="DFIG_BRK_STATE"`; generated `P3.f` assigns `PGB(IPGB+18)=REAL(DFIG_BRK_STATE)` | logic | Added and short-run verified |

### Short-Run Evidence

The current post-edit `.out` files extend to `t=0.24485 s`. They are sufficient to verify channel wiring and the 0.2 s Dblk edge, but not a new full no-fault steady-state run.

| Time (s) | `DFIG_VWIND_MS` | `DFIG_BRK_STATE` | `DFIG_DBLK_CMD` |
|---:|---:|---:|---:|
| 0.00000 | 11 | 0 | 0 |
| 0.19920 | 11 | 0 | 0 |
| 0.20335 | 11 | 0 | 1 |
| 0.24485 | 11 | 0 | 1 |

Use the earlier 20 s baseline artifacts for steady-state `PIBR1_2`, `QIBR1_2`, `VIBR1_2`, and frequency statistics. Do not use the post-edit `0.24485 s` files as a 5 s or 20 s steady-state evidence set.
## Final Output-Channel-Complete 20 s Confirmation - 2026-06-24

This section supersedes the earlier `Still Not Directly Exported` and short-run-only notes for `Dblk_DFIG`, `Vwind`, and `BRK_DFIG`. The current local PSCAD run completed a full 20 s no-fault verification after the GUI output-channel additions.

Run evidence from the user's PSCAD screenshot:

- `0 Errors`
- `0 Warnings`
- `EMTDC run completed`
- `Solve Time = 110ms`

Latest artifact root:

`C:\pscad_work\pnnl_39_3ibr_pscad46_strip5\PSCAD\3IBR.gf46`

All latest `3IBR_*.out` files end at `19.99885 s`.

| Requested signal | Confirmed exported channel | PGB | File | Column | Units | Generated-code evidence | 20 s status |
|---|---|---:|---|---:|---|---|---|
| external `Dblk_DFIG` command | `DFIG_DBLK_CMD` | 19 | `3IBR_02.out` | 10 | logic | `P3.f` line 1881: `PGB(IPGB+19) = Dblk_DFIG` | GUI and full 20 s run confirmed; edge at 0.20335 s |
| external `Vwind` | `DFIG_VWIND_MS` | 17 | `3IBR_02.out` | 8 | m/s | `P3.f` line 1863: `PGB(IPGB+17) = Vwind` | GUI and full 20 s run confirmed; 19-20 s mean 11.0 m/s |
| `BRK_DFIG` breaker status | `DFIG_BRK_STATE` | 18 | `3IBR_02.out` | 9 | logic | `P3.f` line 1877: `PGB(IPGB+18) = REAL(DFIG_BRK_STATE)` | GUI and full 20 s run confirmed; 0 means closed in this setup |

The original P/Q/V baseline channels remain accepted for this no-fault baseline: `PIBR1_2`, `QIBR1_2`, and `VIBR1_2`. The system frequency candidate remains `SPD30`; Type-3 internal `Freq_PLL` must not be substituted for POC/system frequency without an explicit note.
