# Type-3 DFIG Deep Three-Phase Fault Internal Response: GUI Semantic Backfill

## Scope And Sources

This document integrates the GUI-confirmed signal semantics from `docs/TYPE3_DFIG_LVRT_GUI_SEMANTIC_CONFIRMATION.md` and `data/reference/type3_dfig_lvrt_gui_semantic_confirmation.json` into the existing 5 s deep-fault internal response analysis.

Only interpretation text, confidence labels, and limitations were updated. The `.out` data, `.inf` mapping, statistics, fault settings, output channels, PSCAD models, controllers, and main circuit were not modified. No Computer Use, PSCAD GUI operation, Build, or Run was performed for this backfill.

Data sources:

- `data/reference/type3_dfig_deep_fault_internal_response.json`
- `data/reference/type3_dfig_deep_fault_internal_response_summary.csv`
- `docs/TYPE3_DFIG_DEEP_FAULT_5S_SMOKE_TEST.md`
- `docs/TYPE3_DFIG_LVRT_INTERNAL_SIGNAL_AUDIT.md`
- `docs/TYPE3_DFIG_LVRT_GUI_SEMANTIC_CONFIRMATION.md`
- `data/reference/type3_dfig_lvrt_gui_semantic_confirmation.json`

## Semantic Confirmation Status

The following signals are upgraded from candidate-only interpretation to GUI-confirmed semantics:

- `Ecap_Det`: DC-link physical voltage in kV. It can be used as `DFIG_VDC_KV`.
- `Edc_pu`: DC-link per-unit voltage based on `Vdc_base = 1.45 kV`. It can be used as `DFIG_VDC_PU`.
- `BRK_CHOP`: active-high chopper switch command/state. `1=active`, `0=inactive`.
- `S1`: formal crowbar switch command/state. It can be reported as `DFIG_CROWBAR_STATE`. `1=crowbar switch commanded active/on`, `0=inactive/off`.
- `Crowbar current:1..3`: crowbar branch current.
- `I_RS:1..3`: RSC / rotor-side converter terminal three-phase current. The arrow points toward the `RABC` terminal.
- `Iconv:1..3`: GSC / grid-side converter terminal three-phase current. Positive direction is from the AC filter / grid-side node toward the grid-side converter.

Limitations that remain:

- `Reset`, `Mono_out`, and `Iovercur` are intermediate crowbar logic signals. They must not be used as the actual crowbar state.
- The positive direction of `Crowbar current:1..3` is still not confirmed.
- The exact A/B/C mapping of vector indices `1..3` for `I_RS`, `Iconv`, and `Crowbar current` is not phase-by-phase confirmed.
- `BRK_CHOP` confirms a chopper command/state pulse, but chopper branch current and resistor power were not exported, so chopper energy dissipation is not quantified.
- `SPD30` remains a system-frequency candidate. `Freq_PLL` remains a Type-3 internal PLL candidate. They must not be mixed.

## PGB Mapping Method And Statistical Windows

The mapping remains based on the latest `3IBR.gf46/3IBR.inf`. Every 10 PGB channels correspond to one `.out` file, and the first column of each `.out` file is time. The fixed statistical windows are:

- Pre-fault: `1.8-2.0 s`
- During fault: `2.0-2.15 s`
- Post-fault: `4.0-5.0 s`

The current output end time is `4.9966 s`.

## External POC Response Overview

| Signal | PGB | .out | Col | Unit | Confirmed meaning | Pre mean | Fault min | Fault mean | Fault max | Fault max abs | Peak time (s) | Post mean | Confidence | Semantic conclusion | Limitation |
|---|---:|---|---:|---|---|---:|---:|---:|---:|---:|---:|---:|---|---|---|
| VIBR1_2 | 2 | 3IBR_01.out | 3 | pu candidate |  |  |  |  |  |  |  |  | high |  | Mapped from latest inf/out; physical sign and exact base may still require GUI confirmation. |
| PIBR1_2 | 4 | 3IBR_01.out | 5 | MW |  |  |  |  |  |  |  |  | high |  | Mapped from latest inf/out; physical sign and exact base may still require GUI confirmation. |
| QIBR1_2 | 6 | 3IBR_01.out | 7 | MVAr |  |  |  |  |  |  |  |  | high |  | Mapped from latest inf/out; physical sign and exact base may still require GUI confirmation. |
| SPD30 | 1 | 3IBR_01.out | 2 | Hz candidate | System-frequency candidate used as external comparison signal. |  |  |  |  |  |  |  | medium |  | Do not mix with Type-3 internal Freq_PLL; exact measurement source remains to be confirmed. |
| DFIG_IFLT_A_KA | 19 | 3IBR_02.out | 10 | kA |  |  |  |  |  |  |  |  | high |  | Mapped from latest inf/out; physical sign and exact base may still require GUI confirmation. |
| DFIG_IFLT_B_KA | 18 | 3IBR_02.out | 9 | kA |  |  |  |  |  |  |  |  | high |  | Mapped from latest inf/out; physical sign and exact base may still require GUI confirmation. |
| DFIG_IFLT_C_KA | 17 | 3IBR_02.out | 8 | kA |  |  |  |  |  |  |  |  | high |  | Mapped from latest inf/out; physical sign and exact base may still require GUI confirmation. |
| DFIG_DBLK_CMD | 22 | 3IBR_03.out | 3 | logic |  |  |  |  |  |  |  |  | medium |  | Mapped from latest inf/out; physical sign and exact base may still require GUI confirmation. |
| DFIG_BRK_STATE | 21 | 3IBR_03.out | 2 | logic, 0=closed by current project convention |  |  |  |  |  |  |  |  | medium |  | Mapped from latest inf/out; physical sign and exact base may still require GUI confirmation. |
| DFIG_VWIND_MS | 20 | 3IBR_02.out | 11 | m/s |  |  |  |  |  |  |  |  | medium |  | Mapped from latest inf/out; physical sign and exact base may still require GUI confirmation. |

`DFIG_IFLT_A/B/C_KA` are external fault-element currents. They are not RSC, GSC, rotor, or crowbar internal currents. The maximum absolute external fault current during the fault window is about `197.602619 kA`.

## DC-link And Chopper Response

| Signal | PGB | .out | Col | Unit | Confirmed meaning | Pre mean | Fault min | Fault mean | Fault max | Fault max abs | Peak time (s) | Post mean | Confidence | Semantic conclusion | Limitation |
|---|---:|---|---:|---|---|---:|---:|---:|---:|---:|---:|---:|---|---|---|
| Ecap_Det | 256 | 3IBR_26.out | 7 | kV | GUI-confirmed DC-link physical voltage. |  |  |  |  |  |  |  | high | DFIG_VDC_KV: DC-link voltage Ecap_Det in kV. | Sampling/filtering can cause a small difference from Edc_pu * Vdc_base; chopper energy is not measured. |
| Edc_pu | 284 | 3IBR_29.out | 5 | pu | GUI-confirmed DC-link per-unit voltage based on Vdc_base=1.45 kV. |  |  |  |  |  |  |  | high | DFIG_VDC_PU: Edc_pu = Edc / Vdc_base. | Use with Vdc_base=1.45 kV from GUI confirmation; not a grid-voltage pu quantity. |
| BRK_CHOP | 328 | 3IBR_33.out | 9 | logic | GUI-confirmed active-high chopper switch command/state. |  |  |  |  |  |  |  | high | 1=chopper command/state active; 0=inactive. | Chopper branch current/resistor power was not exported, so actual dissipated energy is not quantified. |

GUI confirmation upgrades the DC-link interpretation from candidate to confirmed. `Edc_pu` peaks at `1.427780` during the fault. With `Vdc_base = 1.45 kV`, this corresponds to `2.070281 kV`, which is consistent with the `Ecap_Det` peak of `2.070126 kV`; the absolute difference is about `0.000154 kV`. Therefore, the deep fault clearly raises the DC-link voltage.

`BRK_CHOP` is confirmed as an active-high chopper switch command/state. It changes during the fault window, so this run contains an active chopper command pulse. However, because chopper branch current and resistor power were not exported, this result must not be used to quantify confirmed chopper energy dissipation.

## Crowbar Response

| Signal | PGB | .out | Col | Unit | Confirmed meaning | Pre mean | Fault min | Fault mean | Fault max | Fault max abs | Peak time (s) | Post mean | Confidence | Semantic conclusion | Limitation |
|---|---:|---|---:|---|---|---:|---:|---:|---:|---:|---:|---:|---|---|---|
| Iovercur | 321 | 3IBR_33.out | 2 | logic | Rotor overcurrent comparator output inside Crowbar_prot; intermediate logic only. |  |  |  |  |  |  |  | high | Intermediate crowbar protection logic, not actual crowbar state. | Do not interpret as crowbar inserted/conducting. |
| Reset | 322 | 3IBR_33.out | 3 | logic | Reset/control signal in Crowbar_prot latch/monostable chain; intermediate logic only. |  |  |  |  |  |  |  | high | Intermediate reset logic, not actual crowbar state. | Do not interpret Reset changes as crowbar insertion. |
| S1 | 323 | 3IBR_33.out | 4 | logic | GUI-confirmed formal crowbar switch command/state signal. |  |  |  |  |  |  |  | high | 1=crowbar switch commanded active/on; 0=inactive/off. | In this run S1 stayed 0, so no confirmed crowbar insertion was observed. |
| Mono_out | 324 | 3IBR_33.out | 5 | logic | Monostable output inside Crowbar_prot; intermediate logic only. |  |  |  |  |  |  |  | high | Intermediate pulse/hold logic, not actual crowbar state. | Do not interpret Mono_out changes as crowbar insertion unless S1/current confirm it. |
| Crowbar current:1 | 318 | 3IBR_32.out | 9 | kA | GUI-confirmed crowbar branch current. |  |  |  |  |  |  |  | high | Crowbar branch current channel. | Positive direction and exact A/B/C vector-index mapping still require GUI confirmation; in this run magnitude stayed near zero. |
| Crowbar current:2 | 319 | 3IBR_32.out | 10 | kA | GUI-confirmed crowbar branch current. |  |  |  |  |  |  |  | high | Crowbar branch current channel. | Positive direction and exact A/B/C vector-index mapping still require GUI confirmation; in this run magnitude stayed near zero. |
| Crowbar current:3 | 320 | 3IBR_32.out | 11 | kA | GUI-confirmed crowbar branch current. |  |  |  |  |  |  |  | high | Crowbar branch current channel. | Positive direction and exact A/B/C vector-index mapping still require GUI confirmation; in this run magnitude stayed near zero. |

GUI confirmation identifies `S1` as the formal crowbar switch command/state signal. In future reports it may be named `DFIG_CROWBAR_STATE`. The logic convention is `S1=1` for crowbar switch commanded active/on and `S1=0` for inactive/off.

In this 5 s deep-fault run, `Reset` and `Mono_out` changed, but they are intermediate protection-chain quantities. `Iovercur=0`, `S1=0`, and `Crowbar current:1..3` stayed near zero, with maximum absolute value about `0.000010188132 kA`. The formal conclusion is therefore: no confirmed crowbar switch insertion or crowbar branch conduction was observed in this run. `Reset` or `Mono_out` changes must not be interpreted as crowbar insertion.

## RSC/GSC Currents And Current-Limit Candidate Response

### RSC Terminal Current

| Signal | PGB | .out | Col | Unit | Confirmed meaning | Pre mean | Fault min | Fault mean | Fault max | Fault max abs | Peak time (s) | Post mean | Confidence | Semantic conclusion | Limitation |
|---|---:|---|---:|---|---|---:|---:|---:|---:|---:|---:|---:|---|---|---|
| I_RS:1 | 257 | 3IBR_26.out | 8 | kA | GUI-confirmed RSC / rotor-side converter terminal three-phase current. |  |  |  |  |  |  |  | high | RSC terminal current; arrow points toward RABC terminal. | Exact A/B/C vector-index mapping still requires phase-by-phase GUI confirmation; not RMS unless measurement definition explicitly says so. |
| I_RS:2 | 258 | 3IBR_26.out | 9 | kA | GUI-confirmed RSC / rotor-side converter terminal three-phase current. |  |  |  |  |  |  |  | high | RSC terminal current; arrow points toward RABC terminal. | Exact A/B/C vector-index mapping still requires phase-by-phase GUI confirmation; not RMS unless measurement definition explicitly says so. |
| I_RS:3 | 259 | 3IBR_26.out | 10 | kA | GUI-confirmed RSC / rotor-side converter terminal three-phase current. |  |  |  |  |  |  |  | high | RSC terminal current; arrow points toward RABC terminal. | Exact A/B/C vector-index mapping still requires phase-by-phase GUI confirmation; not RMS unless measurement definition explicitly says so. |

GUI confirmation identifies `I_RS:1..3` as the RSC / rotor-side converter terminal three-phase currents. The arrow points toward the `RABC` terminal. The three-phase maximum absolute value during the fault is about `1.715329 kA`; this is upgraded from candidate to confirmed RSC terminal-current peak. The exact index-to-phase mapping still requires GUI confirmation. These values must not be called RMS unless the measurement definition explicitly states RMS.

### GSC Terminal Current

| Signal | PGB | .out | Col | Unit | Confirmed meaning | Pre mean | Fault min | Fault mean | Fault max | Fault max abs | Peak time (s) | Post mean | Confidence | Semantic conclusion | Limitation |
|---|---:|---|---:|---|---|---:|---:|---:|---:|---:|---:|---:|---|---|---|
| Iconv:1 | 263 | 3IBR_27.out | 4 | kA | GUI-confirmed GSC / grid-side converter terminal three-phase current. |  |  |  |  |  |  |  | high | GSC terminal current; positive direction from AC filter/grid-side node toward grid-side converter. | Exact A/B/C vector-index mapping still requires phase-by-phase GUI confirmation; not RMS unless measurement definition explicitly says so. |
| Iconv:2 | 264 | 3IBR_27.out | 5 | kA | GUI-confirmed GSC / grid-side converter terminal three-phase current. |  |  |  |  |  |  |  | high | GSC terminal current; positive direction from AC filter/grid-side node toward grid-side converter. | Exact A/B/C vector-index mapping still requires phase-by-phase GUI confirmation; not RMS unless measurement definition explicitly says so. |
| Iconv:3 | 265 | 3IBR_27.out | 6 | kA | GUI-confirmed GSC / grid-side converter terminal three-phase current. |  |  |  |  |  |  |  | high | GSC terminal current; positive direction from AC filter/grid-side node toward grid-side converter. | Exact A/B/C vector-index mapping still requires phase-by-phase GUI confirmation; not RMS unless measurement definition explicitly says so. |

GUI confirmation identifies `Iconv:1..3` as the GSC / grid-side converter terminal three-phase currents. Positive direction is from the AC filter / grid-side node toward the grid-side converter. The three-phase maximum absolute value during the fault is about `1.532807 kA`; this is upgraded from candidate to confirmed GSC terminal-current peak. The exact index-to-phase mapping still requires GUI confirmation.

### Current-Limit And Control Candidates

`Voltage_dip`, `Low_Cu_Manag`, `Imax_d_pu`, `Id_pu_Gsc`, and `Iq_pu_Gsc` show fault-window responses and can support future current-limit interpretation. Their exact control meanings, sampling positions, and duplicate signal distinctions still need additional GUI localization before formal use.

## Mechanical Side, Internal Blocking, And PLL Response

| Signal | PGB | .out | Col | Unit | Confirmed meaning | Pre mean | Fault min | Fault mean | Fault max | Fault max abs | Peak time (s) | Post mean | Confidence | Semantic conclusion | Limitation |
|---|---:|---|---:|---|---|---:|---:|---:|---:|---:|---:|---:|---|---|---|
| Wpu | 254 | 3IBR_26.out | 5 | pu candidate |  |  |  |  |  |  |  |  | high |  | Mapped from latest inf/out; physical sign and exact base may still require GUI confirmation. |
| Dblk_VdcCtrl | 234 | 3IBR_24.out | 5 | logic candidate |  |  |  |  |  |  |  |  | medium |  | Requires GUI semantic confirmation before using as formal internal LVRT explanation. |
| Dblk_Rotor | 235 | 3IBR_24.out | 6 | logic candidate |  |  |  |  |  |  |  |  | medium |  | Requires GUI semantic confirmation before using as formal internal LVRT explanation. |
| Freq_PLL | 304 | 3IBR_31.out | 5 | Hz-like internal PLL candidate | Type-3 internal PLL frequency candidate. |  |  |  |  |  |  |  | medium |  | Confirmed only as internal PLL candidate from signal context; do not use as replacement for SPD30/system frequency. |

`Wpu` has a pre-fault mean of about `1.205632` and a post-fault mean of about `1.200021`, so the mechanical-speed indicator returns close to its pre-fault level after fault clearing. `Dblk_VdcCtrl` and `Dblk_Rotor` keep their current logic values in this run, but their exact converter blocking scopes are not fully confirmed. `Freq_PLL` ranges from about `51.000000` to `69.000000` during the fault window; it is a Type-3 internal PLL candidate and must not replace `SPD30` as a system-frequency interpretation.

## Confirmed Facts

- The POC voltage has a deep sag: `VIBR1_2` fault-window minimum is about `0.057865`, and the fault-window mean is about `0.137288`.
- DC-link voltage rises clearly: `Edc_pu` peak is `1.427780`, and `Ecap_Det` peak is `2.070126 kV`.
- `BRK_CHOP` is an active-high chopper switch command/state, and it has an active pulse during the fault window.
- `S1` is the formal crowbar command/state. Because `S1=0` and crowbar branch current is near zero, no confirmed crowbar insertion is observed in this run.
- `I_RS:1..3` and `Iconv:1..3` are confirmed RSC and GSC terminal currents, with fault-window maximum absolute values of about `1.715329 kA` and `1.532807 kA`.
- `DFIG_IFLT_A/B/C_KA` are external fault-element currents, not internal converter or crowbar currents.

## Static Inferences

- The response chain can be described as: deep POC voltage sag -> DC-link rise -> chopper command pulse -> significant RSC/GSC terminal-current increase -> post-fault recovery of P/V/speed indicators.
- Changes in `Reset` and `Mono_out` show internal activity in the crowbar protection chain, but because `S1=0` and crowbar current is near zero, they do not prove crowbar insertion.
- `Dblk_VdcCtrl` and `Dblk_Rotor` remain useful internal blocking candidates, but they should not yet be used to prove the exact blocking state of a specific converter.

## Items Still Requiring GUI Confirmation

- Exact phase mapping of `I_RS:1..3`, `Iconv:1..3`, and `Crowbar current:1..3` to A/B/C.
- Positive direction of `Crowbar current`.
- Chopper branch current, resistor power, or energy dissipation.
- Exact physical source of `SPD30` and its distinction from `Freq_PLL`.
- Sampling-location differences among duplicated internal `Iqr_pu`, `Pg_pu`, and `Qg_pu` candidates.

## Conclusion And Limits

After GUI semantic backfill, the 5 s deep three-phase ground-fault result supports a stronger LVRT interpretation chain: during `2.0-2.15 s`, the system experiences a deep POC voltage sag, Type-3 DC-link voltage rises, the chopper command becomes active, RSC/GSC terminal currents increase significantly, and P/V/mechanical-speed indicators recover after fault clearing. For crowbar behavior, the formal state `S1` remains 0 and crowbar branch current stays near zero. Therefore the correct conclusion is that this run does not show confirmed crowbar insertion or crowbar branch conduction.

These conclusions update signal semantics only. They do not alter any simulation data, output mapping, or fault setting.
