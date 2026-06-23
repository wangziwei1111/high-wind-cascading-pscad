# Type-3 DFIG No-Fault Measurement Baseline

Date: 2026-06-23

## Scope

This record audits the current PSCAD 4.6.2 `3IBR` case after the first Type-3 DFIG branch replacement. No electrical topology, Type-3 parameters, Dblk/Vwind support logic, transformer parameters, protection, fault, MATLAB, or cascading-logic settings were changed in this pass.

Timestamp backup created before GUI inspection:

`C:\pscad_work\backups\PSCAD_before_type3_nofault_baseline_20260623_201625`

Current case:

`C:\pscad_work\pnnl_39_3ibr_pscad46_strip5\PSCAD\3IBR.pscx`

## Measurement Definitions

| Baseline name | Current exported channel | Source | File / column | Unit / base | Sign convention | Status |
|---|---|---|---|---|---|---|
| `DFIG_P_MW` | `PIBR1_2` | `master:multimeter` ID `1263266056`, P output at P3 x=774 y=990 | `3IBR.gf46\3IBR_01.out`, column 5 | MW-scale PSCAD output; meter BaseV=22 kV, S=1 MVA | Positive in current meter orientation; observed +199 MW export after replacement | GUI/static confirmed enough for baseline |
| `DFIG_Q_MVAr` | `QIBR1_2` | same multimeter ID `1263266056`, Q output | `3IBR.gf46\3IBR_01.out`, column 7 | MVAr-scale PSCAD output | Observed negative Q means current meter convention imports/absorbs reactive under this wiring | GUI/static confirmed enough for baseline |
| `DFIG_V_PU_OR_KV` | `VIBR1_2` | same multimeter ID `1263266056`, Vrms output | `3IBR.gf46\3IBR_01.out`, column 3 | pu-like RMS around 1.0 on 22 kV base | Not directional | GUI/static confirmed enough for baseline |
| `DFIG_F_HZ` | `SPD30` and `Freq_PLL` | P3 system candidate and Type-3 internal PLL candidate | `3IBR_01.out` col 2; `3IBR_30.out` col 9 | Hz | Not directional | Usable candidates; exact POC frequency output still should be confirmed |
| `DFIG_DBLK_CMD` | `DFIG_DBLK_CMD` | External `Dblk_DFIG` command sampled from the existing `compare -> Dblk_DFIG` control wire | `3IBR.gf46\3IBR.inf` PGB desc present; generated `P3.f` assigns `PGB(IPGB+19)=Dblk_DFIG` | logic | 0 before enable, 1 after enable | Exported and short-run verified |
| `DFIG_VWIND_MS` | `DFIG_VWIND_MS` | External `Vwind` sampled from the existing `Rate_Limiter -> Vwind` control wire | `3IBR.gf46\3IBR.inf` PGB desc present; generated `P3.f` assigns `PGB(IPGB+17)=Vwind` | m/s | Not directional | Exported and short-run verified |
| `DFIG_BRK_STATE` | `DFIG_BRK_STATE` | `BRK_DFIG` breaker internal A-phase status output, used as representative because single-pole operation is disabled | `3IBR.gf46\3IBR.inf` PGB desc present; generated `P3.f` assigns `PGB(IPGB+18)=REAL(DFIG_BRK_STATE)` | logic | In this breaker model/state convention, 0 corresponds to the observed closed state during no-fault operation | Exported and short-run verified |

## PSCAD Page Evidence

P3 path:

`3IBR:Main(0):P1(0):P3(0)`

Key objects:

- Type-3 instance: `Type3WTG_Lib:Type3_WTG_Avg`, ID `2147003001`, P3 x=1080 y=936.
- P/Q/V meter: `master:multimeter`, ID `1263266056`, P3 x=774 y=990, `BaseV=22 [kV]`, `P=PIBR1_2`, `Q=QIBR1_2`, `Vrms=VIBR1_2`.
- Dblk support: `time-sig` ID `146328259` -> `compare` ID `1776838349`, `X=0.2`, `OL=0`, `OH=1` -> `Dblk_DFIG` data label ID `1031105444`.
- Vwind support: `windSpeed` variable ID `887206944`, `Value=11.0`, -> `Rate_Limiter` ID `808965454`, `IR=10 [1/s]`, `DR=5 [1/s]` -> `Vwind` data label ID `697683388`.
- DFIG breaker and transformer: `BRK_DFIG` breaker ID `521858026`, `XFMR_DFIG_22_33` transformer ID `113665858`.
- Added external output channels after the original baseline pass: `DFIG_DBLK_CMD`, `DFIG_VWIND_MS`, and `DFIG_BRK_STATE`. These were added by GUI only as branch/output measurements; main electrical topology and Type-3 parameters were not changed.

Screenshot filenames: no new binary screenshots were committed in this pass. The GUI inspection screenshots remain in the Codex/PSCAD session only.

## Run Configuration

Run artifacts used:

`C:\pscad_work\pnnl_39_3ibr_pscad46_strip5\PSCAD\3IBR.gf46`

Observed run messages:

- `0 Errors`
- `0 Warnings`
- `EMTDC run completed`
- `Solve Time = 94ms`
- Output files last written: 2026-06-23 18:44:38 local time.

The exported data range in `3IBR_01.out` is 0.0 s to 19.99885 s with 4820 numeric samples.

## 0-1 s Checks

| Signal | Export used | Observation | Pass |
|---|---|---|---|
| External `Dblk_DFIG` | Not exported | Cannot directly prove the external label transition from `.out` in this pass. Static PSCAD logic remains `time-sig -> compare(X=0.2, OL=0, OH=1) -> Dblk_DFIG`. | No |
| Internal Dblk evidence | `Dblk_VdcCtrl`, `Dblk_Rotor` | Both internal Dblk-related channels move from 0 to 1 within the first second, but with internal delays around 0.40255 s and 0.60175 s. | Evidence only |
| `Vwind` | Not exported | External source is static GUI/XML-confirmed as `windSpeed=11.0 -> Rate Limiter(IR=10, DR=5) -> Vwind`, but no output column exists. | No |
| `BRK_DFIG` | Not exported | Branch remained closed visually and power flowed, but there is no direct external breaker-state output. | No |

## External Output Channel Completion Addendum

Date: 2026-06-23, after the original 20 s baseline run.

Three external signal output channels were manually added in PSCAD GUI:

- `DFIG_DBLK_CMD`: output channel branched from the existing `compare(X=0.2, OL=0, OH=1) -> Dblk_DFIG` control wire. The original Dblk wire remains intact.
- `DFIG_VWIND_MS`: output channel branched from the existing `Rate_Limiter(IR=10, DR=5) -> Vwind` control wire. The original Vwind wire remains intact.
- `DFIG_BRK_STATE`: `BRK_DFIG` breaker internal A-phase status output was named `DFIG_BRK_STATE`, then exported through a same-name Data Label and output channel. Single-pole operation is disabled, so A-phase status is used as the three-phase breaker status representative.

Build/run evidence from the user's PSCAD screenshot after these output-only edits:

- `0 Errors`
- `0 Warnings`
- `EMTDC run completed`
- `Solve Time = 47ms`

Generated-file evidence from `C:\pscad_work\pnnl_39_3ibr_pscad46_strip5\PSCAD\3IBR.gf46`:

```text
3IBR.inf:
PGB(1) Output Desc="DFIG_BRK_STATE" Group="P3" Units="logic"
PGB(3) Output Desc="DFIG_DBLK_CMD"  Group="P3" Units="logic"
PGB(4) Output Desc="DFIG_VWIND_MS"  Group="P3" Units="m/s"

P3.f:
PGB(IPGB+17) = Vwind
PGB(IPGB+18) = REAL(DFIG_BRK_STATE)
PGB(IPGB+19) = Dblk_DFIG
```

Short-run output evidence:

The post-edit `.out` files available during this audit extend to `t=0.24485 s`, not the full requested 5 s. This is sufficient to verify the Dblk command edge and the existence/value of the added channels, but it is not used as a new steady-state statistics run.

| Time (s) | `DFIG_VWIND_MS` | `DFIG_BRK_STATE` | `DFIG_DBLK_CMD` |
|---:|---:|---:|---:|
| 0.00000 | 11 | 0 | 0 |
| 0.19920 | 11 | 0 | 0 |
| 0.20335 | 11 | 0 | 1 |
| 0.24485 | 11 | 0 | 1 |

Interpretation:

- `DFIG_DBLK_CMD` changes from 0 to 1 immediately after 0.2 s, as intended.
- `DFIG_VWIND_MS` is 11 m/s during the checked interval.
- `DFIG_BRK_STATE` remains 0; based on the breaker Animation States showing all phases closed and the DFIG branch carrying power, 0 is the current closed-state convention for this output.
- Full 19-20 s P/Q/V/f steady-state evidence still comes from the earlier completed 20 s no-fault baseline, because the post-edit files only cover the short startup interval.

## 19-20 s Statistics

| Signal | File column | Min | Mean | Max | Range | Assessment |
|---|---:|---:|---:|---:|---:|---|
| `SPD30` | `3IBR_01.out` col 2 | 60.000000 | 60.000000 | 60.000000 | 0.000000 | Stable frequency candidate |
| `VIBR1_2` | `3IBR_01.out` col 3 | 0.999809 | 0.999876 | 0.999965 | 0.000156 | Stable 22 kV-side voltage candidate |
| `PIBR1_2` | `3IBR_01.out` col 5 | 199.052585 | 199.084370 | 199.116004 | 0.063419 | Stable, expected 200 MW aggregate order |
| `QIBR1_2` | `3IBR_01.out` col 7 | -18.822086 | -18.788477 | -18.752378 | 0.069709 | Stable under current sign convention |
| `Freq_PLL` | `3IBR_30.out` col 9 | 60.042693 | 60.050236 | 60.057537 | 0.014844 | Stable Type-3 internal PLL frequency candidate |
| `Dblk_VdcCtrl` | `3IBR_23.out` col 9 | 1.000000 | 1.000000 | 1.000000 | 0.000000 | Internal Dblk evidence only |
| `Dblk_Rotor` | `3IBR_23.out` col 10 | 1.000000 | 1.000000 | 1.000000 | 0.000000 | Internal Dblk evidence only |
| `BRK ord` | `3IBR_23.out` col 6 | 0.000000 | 0.000000 | 0.000000 | 0.000000 | Internal Type-3 breaker-order candidate, not external `BRK_DFIG` |

## Baseline Decision

No-fault electrical run: passed based on the earlier full 20 s run.

External measurement-channel hardening: passed for `DFIG_DBLK_CMD`, `DFIG_VWIND_MS`, and `DFIG_BRK_STATE` after manual GUI output-channel completion.

Important limitation: the post-edit output files inspected here only run to `0.24485 s`, so they validate channel existence and the Dblk startup edge, but do not replace the earlier full 20 s no-fault steady-state statistics.

## Unresolved Risks

- `DFIG_F_HZ` is currently represented by candidates (`SPD30`, `Freq_PLL`) rather than a newly named POC frequency channel.
- The post-output-channel validation files only extend to `0.24485 s`; use the earlier full 20 s run for steady-state P/Q/V/f evidence.
- `DFIG_BRK_STATE=0` corresponds to the observed closed-state convention in this PSCAD breaker setup; document this convention when plotting or comparing status logic.
