# Type-3 Library GUI Trial Checklist

This checklist is for a user-executed GUI trial. Do not automate these actions.

## Before Export

- [ ] PSCAD v4.6.2 Professional is open.
- [ ] `Type3_Ave_Nov_2018` Case is loaded from `C:\pscad_work\type3_wtg_v46_trial`.
- [ ] `Type3WTG_Lib` Library is loaded.
- [ ] `3IBR.pscx` baseline is not being edited.
- [ ] Workspace autosave is understood/controlled.

## Export from Type-3 Case

- [ ] Open `Type3_Ave_Nov_2018 -> Definitions`.
- [ ] Locate `Type3_WTG_Avg`.
- [ ] Right-click `Type3_WTG_Avg`.
- [ ] Confirm menu contains `Export with Dependents`.
- [ ] Use `Export with Dependents`.
- [ ] Save `.psdx` outside Git.

## Import into Library

- [ ] Open `Type3WTG_Lib -> Definitions`.
- [ ] Right-click `Definitions`.
- [ ] Select `Import Definition(s)...`.
- [ ] Select exported `.psdx`.
- [ ] Stop if duplicate/overwrite prompts appear.

## Library Completeness

- [ ] `Type3_WTG_Avg` exists in `Type3WTG_Lib`.
- [ ] `DFIG_Converters_Avg` exists.
- [ ] `WindTurbine_MechModel` exists.
- [ ] `Synchronization` exists.
- [ ] `Rotor_side_Controls` exists.
- [ ] `Grid_side_Controls` exists.
- [ ] `Crowbar_prot` exists.
- [ ] `Chopper` exists.
- [ ] `AC_sys` port is visible in `Type3_WTG_Avg`.
- [ ] Required parameters are visible.

## Standalone Exclusion

- [ ] No standalone `V_source` was intentionally copied.
- [ ] No standalone `BusPOC` was intentionally copied.
- [ ] No POC/Terminal Fault panels were intentionally copied.
- [ ] No IEEE-39 wiring was changed.

## Instance Reference Smoke Check

- [ ] Load a scratch Case or trial Case.
- [ ] Keep Type3WTG_Lib loaded.
- [ ] Create instance from `Type3WTG_Lib -> Definitions -> Type3_WTG_Avg`.
- [ ] Paste it disconnected.
- [ ] Verify reference namespace is `Type3WTG_Lib`.
- [ ] Do not connect it to IEEE-39 in this task.
