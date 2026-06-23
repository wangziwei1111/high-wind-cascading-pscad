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
| `DFIG_DBLK` | No direct `Dblk_DFIG` output. Internal `Dblk_VdcCtrl` and `Dblk_Rotor` used as evidence only | Type-3 internal PGBs, not the external `Dblk_DFIG` label | `3IBR_23.out` cols 9 and 10 | logic | Not directional | Not fully exported |
| `DFIG_VWIND_MS` | No direct output channel | External `Vwind` label exists at P3 x=360 y=1134 but has no same-name PGB in `3IBR.inf` | none | m/s | Not directional | Not exported |
| `DFIG_BRK_STATE` | No direct `BRK_DFIG` output. Internal `BRK ord` exists but is not the external breaker state | `BRK_DFIG` constant/label and breaker are visible in PSCAD, but no same-name PGB | external none; internal `3IBR_23.out` col 6 | logic | 0 command corresponds to the present closed no-fault branch in this run | Not fully exported |

## PSCAD Page Evidence

P3 path:

`3IBR:Main(0):P1(0):P3(0)`

Key objects:

- Type-3 instance: `Type3WTG_Lib:Type3_WTG_Avg`, ID `2147003001`, P3 x=1080 y=936.
- P/Q/V meter: `master:multimeter`, ID `1263266056`, P3 x=774 y=990, `BaseV=22 [kV]`, `P=PIBR1_2`, `Q=QIBR1_2`, `Vrms=VIBR1_2`.
- Dblk support: `time-sig` ID `146328259` -> `compare` ID `1776838349`, `X=0.2`, `OL=0`, `OH=1` -> `Dblk_DFIG` data label ID `1031105444`.
- Vwind support: `windSpeed` variable ID `887206944`, `Value=11.0`, -> `Rate_Limiter` ID `808965454`, `IR=10 [1/s]`, `DR=5 [1/s]` -> `Vwind` data label ID `697683388`.
- DFIG breaker and transformer: `BRK_DFIG` breaker ID `521858026`, `XFMR_DFIG_22_33` transformer ID `113665858`.

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

No-fault electrical run: passed.

Measurement hardening: not fully passed.

Reason: P/Q/V/f are available and stable, but the requested external channels `Dblk_DFIG`, `Vwind`, and `BRK_DFIG` were not successfully exported as explicit `.out` channels in this pass. Internal Type-3 channels provide partial evidence for Dblk and breaker order, but they are not equivalent to the external P3 labels requested for the baseline.

Do not proceed to controlled fault tests until one of the following is done in PSCAD GUI:

1. Add explicit PGB/output channels wired to `Dblk_DFIG`, `Vwind`, and `BRK_DFIG`, then rerun 20 s.
2. Or document an accepted alternative measurement convention that uses internal Type-3 channels and a constant breaker command, with the limitation clearly acknowledged.

## Unresolved Risks

- `DFIG_BRK_STATE` still lacks a direct external breaker-state channel.
- `DFIG_VWIND_MS` still lacks a direct `Vwind` output channel.
- `DFIG_DBLK` still lacks a direct `Dblk_DFIG` output channel; internal Dblk channels have additional model delays and are not substitutes for the external enable command.
- `DFIG_F_HZ` is currently represented by candidates (`SPD30`, `Freq_PLL`) rather than a newly named POC frequency channel.
