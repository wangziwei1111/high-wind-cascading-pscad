# Type-3 DFIG No-Fault Measurement Baseline

Date: 2026-06-24

## Scope

This record documents the current PSCAD 4.6.2 `3IBR` case after the Type-3 DFIG replacement branch and after the external output-channel completion for `Dblk_DFIG`, `Vwind`, and `BRK_DFIG` breaker status. The final verification run was performed without changing the main electrical topology, Type-3 parameters, Dblk/Vwind support logic, `BRK_DFIG`, `XFMR_DFIG_22_33`, old IBR state, protection, fault, MATLAB, or cascading-logic settings.

Current case:

`C:\pscad_work\pnnl_39_3ibr_pscad46_strip5\PSCAD\3IBR.pscx`

Generated run artifact root:

`C:\pscad_work\pnnl_39_3ibr_pscad46_strip5\PSCAD\3IBR.gf46`

P3 page:

`3IBR:Main(0):P1(0):P3(0)`

## Current Measurement Definitions

| Baseline signal | Exported channel | File / column | Unit / base | Source and convention | Status |
|---|---|---|---|---|---|
| `DFIG_P_MW` | `PIBR1_2` | `3IBR_01.out` col 5 | MW-scale PSCAD P output | `master:multimeter` ID `1263266056` at P3 x=774 y=990 near the Type-3 branch; positive under current meter orientation | GUI/static and 20 s run confirmed |
| `DFIG_Q_MVAr` | `QIBR1_2` | `3IBR_01.out` col 7 | MVAr-scale PSCAD Q output | Same meter; negative Q is the current meter sign convention | GUI/static and 20 s run confirmed |
| `DFIG_V_PU_OR_KV` | `VIBR1_2` | `3IBR_01.out` col 3 | pu-like RMS on 22 kV meter base | Same meter; not directional | GUI/static and 20 s run confirmed |
| `DFIG_F_HZ` | `SPD30` | `3IBR_01.out` col 2 | Hz candidate | System frequency candidate held at 60 Hz; distinct from Type-3 internal `Freq_PLL` | 20 s run confirmed as system candidate |
| `DFIG_DBLK_CMD` | `DFIG_DBLK_CMD` | `3IBR_02.out` col 10 | logic | Branch sample from existing `compare(X=0.2, OL=0, OH=1) -> Dblk_DFIG` wire; `P3.f` line 1881 assigns `Dblk_DFIG` | GUI and full 20 s run confirmed |
| `DFIG_VWIND_MS` | `DFIG_VWIND_MS` | `3IBR_02.out` col 8 | m/s | Branch sample from existing `Rate_Limiter -> Vwind` wire; `P3.f` line 1863 assigns `Vwind` | GUI and full 20 s run confirmed |
| `DFIG_BRK_STATE` | `DFIG_BRK_STATE` | `3IBR_02.out` col 9 | logic | `BRK_DFIG` internal A-phase status output; single-pole operation is disabled, so A phase represents the three-phase breaker. Current convention: `0 = closed` | GUI and full 20 s run confirmed |

## Key PSCAD Objects

- Type-3 instance: `Type3WTG_Lib:Type3_WTG_Avg`, ID `2147003001`, P3 x=1080 y=936.
- Dblk support: `time-sig` ID `146328259` -> `compare` ID `1776838349`, `X=0.2`, `OL=0`, `OH=1` -> `Dblk_DFIG` data label ID `1031105444`.
- Vwind support: `windSpeed` variable ID `887206944`, `Value=11.0`, -> `Rate_Limiter` ID `808965454`, `IR=10 [1/s]`, `DR=5 [1/s]` -> `Vwind` data label ID `697683388`.
- Breaker/transformer: `BRK_DFIG` breaker ID `521858026`; `XFMR_DFIG_22_33` transformer ID `113665858`.
- P/Q/V meter: `master:multimeter` ID `1263266056`, `BaseV=22 [kV]`, `P=PIBR1_2`, `Q=QIBR1_2`, `Vrms=VIBR1_2`.

## Run Configuration - Output-Channel-Complete 20 s Rerun

- Duration: 20 s.
- Solution time step: 5 us.
- Channel plot step: 4150 us.
- PSCAD GUI evidence from user screenshot: `0 Errors`, `0 Warnings`, `EMTDC run completed`, `Solve Time = 110ms`.
- Latest `.out` files: `3IBR_01.out` through `3IBR_35.out`.
- Numeric time range: `0.0 s` to `19.99885 s`, `4820` samples in `3IBR_01.out`.
- Mapping source: latest `3IBR.inf` PGB descriptors, cross-checked against generated `P3.f` assignments. The practical PSCAD `.out` layout is 10 channels per `3IBR_NN.out` file after the time column.

## 0-1 s External Signal Checks

| Signal | File / column | Observation | Pass |
|---|---|---|---|
| `DFIG_DBLK_CMD` | `3IBR_02.out` col 10 | `0` at t=0 and t=0.19920 s; changes to `1` at t=0.20335 s | Yes |
| `DFIG_VWIND_MS` | `3IBR_02.out` col 8 | 11.0 m/s at t=0, t=0.19920 s, t=0.20335 s, and final sample | Yes |
| `DFIG_BRK_STATE` | `3IBR_02.out` col 9 | 0 throughout checked startup interval; current convention `0 = closed` | Yes |
| `SPD30` | `3IBR_01.out` col 2 | 60 Hz throughout checked startup interval | Yes |

## 19-20 s Statistics - Output-Channel-Complete 20 s Rerun

| Baseline signal | Exported channel | File / column | Unit | Min | Mean | Max | Range | Assessment |
|---|---|---|---|---:|---:|---:|---:|---|
| `DFIG_P_MW` | `PIBR1_2` | `3IBR_01.out` col 5 | MW | 199.052585 | 199.084370 | 199.116004 | 0.063419 | Stable, expected 200 MW aggregate order |
| `DFIG_Q_MVAr` | `QIBR1_2` | `3IBR_01.out` col 7 | MVAr | -18.822086 | -18.788477 | -18.752378 | 0.069709 | Stable under current sign convention |
| `DFIG_V_PU_OR_KV` | `VIBR1_2` | `3IBR_01.out` col 3 | pu-like | 0.999809 | 0.999876 | 0.999965 | 0.000156 | Stable near 1.0 pu |
| `DFIG_F_HZ` | `SPD30` | `3IBR_01.out` col 2 | Hz | 60.000000 | 60.000000 | 60.000000 | 0.000000 | System frequency candidate, not Type-3 internal PLL |
| `DFIG_DBLK_CMD` | `DFIG_DBLK_CMD` | `3IBR_02.out` col 10 | logic | 1.000000 | 1.000000 | 1.000000 | 0.000000 | Enabled and steady |
| `DFIG_VWIND_MS` | `DFIG_VWIND_MS` | `3IBR_02.out` col 8 | m/s | 11.000000 | 11.000000 | 11.000000 | 0.000000 | Stable at commanded wind speed |
| `DFIG_BRK_STATE` | `DFIG_BRK_STATE` | `3IBR_02.out` col 9 | logic | 0.000000 | 0.000000 | 0.000000 | 0.000000 | Closed-state convention remains 0 |

## Baseline Decision

Output-channel-complete 20 s no-fault baseline: **passed**.

Pass evidence:

- PSCAD GUI showed `0 Errors`, `0 Warnings`, and `EMTDC run completed`.
- All latest `.out` files end at approximately 20 s (`19.99885 s`).
- `DFIG_DBLK_CMD` changes from 0 to 1 immediately after the 0.2 s comparator threshold.
- `DFIG_VWIND_MS` is stable at 11 m/s.
- `DFIG_BRK_STATE` remains 0, documented as the current closed-state convention.
- `PIBR1_2` mean over 19-20 s is 199.084370 MW.
- `VIBR1_2` mean over 19-20 s is 0.999876 pu-like.
- `SPD30` remains 60 Hz.

The model is now ready to move into a controlled fault/LVRT preparation stage, provided the next stage preserves this baseline as the no-fault reference and treats `SPD30` as a system-frequency candidate distinct from the Type-3 internal `Freq_PLL`.

## Historical Notes Before Output-Channel Completion

Earlier baseline records marked external `Dblk_DFIG`, `Vwind`, and `BRK_DFIG` as not directly exported. That limitation is now historical. The current confirmed channels are:

- `Dblk_DFIG` external command -> `DFIG_DBLK_CMD`.
- `Vwind` external wind-speed signal -> `DFIG_VWIND_MS`.
- `BRK_DFIG` breaker internal status -> `DFIG_BRK_STATE` with `0 = closed` in this setup.

## Residual Risks

- `DFIG_F_HZ` is represented by `SPD30` as a system-frequency candidate. Type-3 internal `Freq_PLL` must not be used as a substitute for POC/system frequency unless explicitly documented.
- `DFIG_BRK_STATE=0` is the observed PSCAD breaker closed-state convention for this case and should be carried forward in plots and fault logic notes.
- P/Q sign convention follows the existing meter orientation and should be rechecked before comparing against external power-flow sign conventions.
