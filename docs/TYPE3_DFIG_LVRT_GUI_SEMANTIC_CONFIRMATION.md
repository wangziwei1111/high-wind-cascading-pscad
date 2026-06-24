# Type-3 DFIG LVRT GUI Signal Semantic Confirmation

Date: 2026-06-24

This document records the manual GUI semantic confirmation performed by the user for the Type-3 DFIG LVRT internal signals. Codex did not use Computer Use, did not open or operate PSCAD GUI, did not Build/Run, and did not modify any PSCAD model, `.pscx/.pslx/XML`, fault element, fault parameter, output channel, controller, main circuit, or Dblk/Vwind support logic.

The confirmation was performed on the existing PSCAD workspace by user screenshots only. Static evidence was checked from the generated Fortran and existing repository audit files.

## Source Materials

- Current PSCAD page path: `3IBR:Main(0):P1(0):P3(0)`
- Type-3 instance: `Type3WTG_Lib:Type3_WTG_Avg`
- Generated code directory: `C:\pscad_work\pnnl_39_3ibr_pscad46_strip5\PSCAD\3IBR.gf46`
- Existing analysis: `docs/TYPE3_DFIG_DEEP_FAULT_INTERNAL_RESPONSE.md`
- Existing JSON: `data/reference/type3_dfig_deep_fault_internal_response.json`
- Existing audit: `docs/TYPE3_DFIG_LVRT_INTERNAL_SIGNAL_AUDIT.md`

## Screenshot Index

| ID | Screenshot | GUI content used |
|---|---|---|
| S01 | `C:\Users\24186\AppData\Local\Temp\codex-clipboard-051c1c3f-5067-41ce-b7f9-304dbab67191.png` | `Type3_WTG_Avg` definition page, including `Crowbar Protection` and `DFIG_Converters_Avg` area |
| S02 | `C:\Users\24186\AppData\Local\Temp\codex-clipboard-43dbfd67-c5a7-46f4-8ae8-7cef7a1c71c8.png` | `DFIG_Converters_Avg` definition page |
| S03 | `C:\Users\24186\AppData\Local\Temp\codex-clipboard-00bb14ff-9574-4934-9f25-20e2117c23ec.png` | `DFIG_Converters_Avg` Crowbar wrapper: `Ecap_fltrd`, `I_RS`, `Blk`, `S1`, `Crow_Enab`, `Icrow_bar`, `Time_crowbar`, `Vdc_crowbar_on`, `Rcrow`, `Lcrow` |
| S04 | `C:\Users\24186\AppData\Local\Temp\codex-clipboard-9adbf338-b32f-4541-b675-35939fc94389.png` | `Crowbar_prot` full definition overview |
| S05 | `C:\Users\24186\AppData\Local\Temp\codex-clipboard-b3456d37-3283-4670-a5da-f15b709a2e91.png` | `Crowbar_prot` logic: `Iovercur`, `V-Ecap`, `Reset`, `Mono_out`, `Crow_Enab`, `S1`, `S1o` |
| S06 | `C:\Users\24186\AppData\Local\Temp\codex-clipboard-a73edb0f-4bed-447f-b603-d22ccc1991b4.png` | `Crowbar_prot` power branch: `S1` gate, crowbar resistor, `Icrowbar`, `Crowbar current` |
| S07 | `C:\Users\24186\AppData\Local\Temp\codex-clipboard-8849501c-d982-444a-9502-e51b1d90c693.png` | DC-link and chopper area: `Ecap`, `Ecap_fltrd`, `Chopper`, `Vdc_chop_on/off`, `Vdc_base`, `R_chopper` |
| S08 | `C:\Users\24186\AppData\Local\Temp\codex-clipboard-6e598489-7a33-4d39-bb5e-6a3da5c181fd.png` | `Type3_WTG_Avg` source of `Vdc_Base = 1.45 [kV]` |
| S09 | `C:\Users\24186\AppData\Local\Temp\codex-clipboard-f9998793-f383-4062-b805-9cb9da3b58d1.png` | `Chopper` definition: `BRK_CHP` gate command and `BRK_CHOP` output |
| S10 | `C:\Users\24186\AppData\Local\Temp\codex-clipboard-3f649936-1862-48f9-9fb5-a20651895563.png` | `I_RS` multimeter at rotor-side terminal, arrow direction toward `RABC` |
| S11 | `C:\Users\24186\AppData\Local\Temp\codex-clipboard-3be2f397-6456-44a6-9957-1070c9a0d808.png` | `Iconv` ammeter at grid-side converter terminal, arrow direction toward converter |
| S12 | `C:\Users\24186\AppData\Local\Temp\codex-clipboard-d5ccf79f-6811-473b-9b71-c2467de78ad6.png` | `Crowbar current` measurement inside `Crowbar_prot` power branch |

## A. Crowbar Actual State Semantics

### GUI-confirmed facts

- The shortest GUI hierarchy is `Type3_WTG_Avg -> DFIG_Converters_Avg -> Crowbar_prot`.
- In `DFIG_Converters_Avg`, the `Crowbar` module takes `Ecap_fltrd`, `I_RS`, `Blk`, `Crow_Enab`, `Time_crowbar`, `Icrow_bar`, `Vdc_crowbar_on`, `Rcrow`, and `Lcrow`, and exports `S1`.
- In `Crowbar_prot`, `Iovercur` is the output of a rotor-current magnitude comparator against `Ir_limit`.
- `V-Ecap` is the output of a DC-link voltage comparator against `Vdc_crowbar_on`.
- `Reset` is a reset/control signal in the latch/monostable logic chain.
- `Mono_out` is the output of the monostable block and is not the final crowbar switch state.
- `S1` is produced after the monostable, `Blk`, and `Crow_Enab` gating logic.
- `S1` is connected to the actual crowbar power electronic switch gate in the power branch.
- `S1` is also exported as `S1o`.
- `Crowbar current:1..3` is measured inside the `Crowbar_prot` power branch from `Icrowbar`.

### Static-code evidence

- `Crowbar_prot.f:192` records PGB output `Iovercur`.
- `Crowbar_prot.f:205` records PGB output `Reset`.
- `Crowbar_prot.f:273` records PGB output `S1`.
- `Crowbar_prot.f:284` records PGB output `Mono_out`.
- `Crowbar_prot.f:303` calls `PESWITCH1_EXE(..., S1, ...)`, confirming that `S1` drives a power electronic switch.
- `Crowbar_prot.f:384` assigns `S1o = S1`.
- `Crowbar_prot.f:520-522` reads `Icrowbar(1..3)` from crowbar branch currents.
- `Crowbar_prot.f:524` records PGB output `Crowbar current`.

### Final semantic conclusion

`S1` is the best formal signal for `DFIG_CROWBAR_STATE` in this model.

The logic direction is:

- `S1 = 1`: crowbar switch command/state active, crowbar power electronic switch is commanded on.
- `S1 = 0`: crowbar switch command/state inactive.

`Mono_out`, `Reset`, and `Iovercur` are intermediate logic signals and must not be used as the formal crowbar actual state.

For the current 5 s deep-fault run, the offline result showed `S1 = 0` and near-zero `Crowbar current:1..3`; therefore the report may state that the crowbar did not show confirmed actual conduction in that run. It may not claim crowbar action based only on `Reset` or `Mono_out`.

## B. DC-link Voltage Unit, Base, and Chopper Semantics

### GUI-confirmed facts

- `Ecap` is connected to the DC-link capacitor node in `DFIG_Converters_Avg`.
- `Ecap` is filtered to `Ecap_fltrd`.
- `Ecap_fltrd` feeds both `Crowbar` and `Chopper`.
- `Vdc_chop_on = 1.15 * Vdc_base`.
- `Vdc_chop_off = 1.11 * Vdc_base`.
- `Vdc_Base` is supplied in the outer `Type3_WTG_Avg` page by a constant value `1.45 [kV]`.
- The `Chopper` page shows `BRK_CHP` connected to the chopper power switch gate and `BRK_CHOP` as the corresponding output channel.

### Static-code evidence

- `DFIG_Converters_Avg.f:17` and `DFIG_Converters_Avg.f:66` pass `Vdc_base` as an input parameter.
- `DFIG_Converters_Avg.f:342` computes `Vdc_chop_on = 1.15 * Vdc_base`.
- `DFIG_Converters_Avg.f:369` computes `Vdc_chop_off = 1.11 * Vdc_base`.
- `DFIG_Converters_Avg.f:539` calls `Crowbar_protDyn(..., Ecap_fltrd, ..., Vdc_crowbar_on, ...)`.
- `DFIG_Converters_Avg.f:553` calls `ChopperDyn(Ecap_fltrd, Vdc_chop_on, Vdc_chop_off, R_chopper)`.
- `DFIG_Converters_Avg.f:973` records PGB output `Ecap_Det`.
- `Grid_side_Controls.f:318` computes `Edc_pu = Edc / Vdc_base`.
- `Chopper.f:145` records PGB output `BRK_CHOP`.

### Final semantic conclusion

- `DFIG_VDC_KV` should correspond to `Ecap_Det`.
- `DFIG_VDC_PU` should correspond to `Edc_pu`.
- `Vdc_base = 1.45 kV`.
- The current deep-fault peak `Edc_pu = 1.427780` corresponds to approximately `1.427780 * 1.45 = 2.070281 kV`, which matches the parsed `Ecap_Det` peak of about `2.070126 kV candidate`.
- `BRK_CHOP = 1` is confirmed as the chopper switch command/state active; `BRK_CHOP = 0` is inactive.

The deep-fault report may upgrade the chopper statement from "logic candidate" to "chopper switch command pulse observed." If the final paper needs physical energy dissipation, a chopper branch current or resistor power should still be checked separately.

## C. RSC, GSC, and Crowbar Current Phase/Direction Semantics

### RSC current `I_RS:1..3`

GUI and search results confirmed:

- `I_RS` is generated by a `multimeter` in `DFIG_Converters_Avg`, instance `1634455167`.
- The sticky note in `DFIG_Converters_Avg` states that `I_RS` and `V_RS` are measured at the rotor-side converter terminal.
- The user screenshot shows the current arrow pointing toward the `RABC` terminal.

Static-code evidence:

- `DFIG_Converters_Avg.f:926-928` reads `I_RS(1..3)` from branch currents.
- `DFIG_Converters_Avg.f:977-980` writes `I_RS` to PGB outputs.

Conclusion:

- `I_RS:1..3` is confirmed as rotor-side converter / rotor-side terminal three-phase current.
- The sign convention visible in GUI is positive in the arrow direction toward `RABC`.
- The exact A/B/C phase mapping of vector indices `1..3` follows PSCAD three-phase vector ordering, but was not independently opened in the multimeter parameter dialog; keep exact phase-name mapping as "not separately confirmed."

### GSC current `Iconv:1..3`

GUI and search results confirmed:

- `Iconv` is generated by an `ammeter` in `DFIG_Converters_Avg`, instance `2143509644`.
- The sticky note in `DFIG_Converters_Avg` states that `Iconv` and `V_GS` are measured at the grid-side converter terminal.
- The user screenshot shows the current arrow from the `SABC`/AC filter side toward the grid-side converter.

Static-code evidence:

- `DFIG_Converters_Avg.f:913-915` reads `Iconv(1..3)` from branch currents.
- `DFIG_Converters_Avg.f:989-992` writes `Iconv` to PGB outputs.

Conclusion:

- `Iconv:1..3` is confirmed as grid-side converter terminal three-phase current.
- The sign convention visible in GUI is positive from the AC filter/grid-side node toward the converter.
- Exact A/B/C phase-name mapping remains not separately confirmed beyond PSCAD vector ordering.

### Crowbar current `Crowbar current:1..3`

GUI confirmed:

- `Crowbar current` is displayed in the `Crowbar_prot` page and is located beside the crowbar power branch.
- `Icrowbar` is the signal feeding the `Crowbar current` output channel.

Static-code evidence:

- `Crowbar_prot.f:520-522` reads `Icrowbar(1..3)` from crowbar branch currents.
- `Crowbar_prot.f:524-527` writes `Crowbar current` to PGB outputs.

Conclusion:

- `Crowbar current:1..3` is confirmed as crowbar branch current.
- The exact sign direction was not visually confirmed because the screenshot did not show a current arrow on the `Icrowbar` measurement itself.
- The 5 s deep-fault result showed near-zero `Crowbar current:1..3`, consistent with `S1 = 0`.

## Upgrades to Existing Deep-Fault Interpretation

The following statements may be upgraded from candidate to stronger conclusions:

- `S1` is the formal `DFIG_CROWBAR_STATE` signal for this model.
- In the current 5 s deep-fault run, `S1 = 0` plus near-zero `Crowbar current:1..3` supports "no confirmed crowbar conduction."
- `Ecap_Det` is the DC-link voltage in kV for this model.
- `Edc_pu` is the DC-link per-unit voltage using `Vdc_base = 1.45 kV`.
- `BRK_CHOP = 1` is the chopper switch command/state active.
- `I_RS:1..3` and `Iconv:1..3` are confirmed RSC and GSC terminal current channels, respectively.
- `Crowbar current:1..3` is confirmed as crowbar branch current.

The following must remain qualified:

- Exact A/B/C mapping of vector indices `1..3` was not independently confirmed through each meter's parameter dialog.
- `Crowbar current:1..3` sign direction was not visually confirmed.
- Physical chopper energy dissipation still requires branch current or resistor power if needed.
- `SPD30` remains a system-frequency candidate and must not be confused with Type-3 internal `Freq_PLL`.

## Cannot Conclude

- Do not conclude that Crowbar acted in the current 5 s deep-fault run.
- Do not use `Reset`, `Mono_out`, or `Iovercur` as `DFIG_CROWBAR_STATE`.
- Do not treat external `DFIG_IFLT_A/B/C_KA` as RSC, GSC, rotor, or Crowbar current.
- Do not claim exact phase names for `I_RS:1..3`, `Iconv:1..3`, or `Crowbar current:1..3` unless the PSCAD meter/vector phase mapping is separately confirmed.
