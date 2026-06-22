# Manual Single IBR to Type-3 DFIG Replacement

This is a manual PSCAD GUI plan only. Do not execute it on the baseline project.

## Stage 0: Freeze Baseline

- Keep the successful PNNL 3IBR run as read-only baseline.
- Create a complete manual copy named `3IBR_DFIG1_TRIAL`.
- Confirm the copy opens and still runs before any replacement.
- Do not modify `C:\pscad_work\pnnl_39_3ibr_pscad46_strip5\PSCAD\3IBR.pscx`.

## Stage 1: Record Before Editing

- Screenshot P3 around the candidate `IBR_AVM_2_1_1` instance `475433949`.
- Record the upstream `E_2_30_1` 345/22 kV transformer parameters.
- Record the 22 kV series inductor and 22/0.6 kV transformer parameters.
- Record IBR `Inputs`, `Flags`, `out`, and `fPLL` ports.
- Open Type-3 Average and record `Type3_WTG_Avg` parameters: `Dblk`, `freq`, `Vbase`, `UN`, `Rated_MW`, `Vwind`, `Machine_MVA`.

## Stage 2: Create Manual Wiring Trial

- Preserve PNNL upstream grid and 345/22 kV transformer.
- Remove or bypass only the old converter-side IBR part in the trial copy after documentation.
- Do not leave the old IBR and Type-3 connected in parallel.
- Copy the complete `Type3_WTG_Avg` core block and required project-local definitions using PSCAD GUI mechanisms only.
- Do not copy `V_source`, standalone `BusPOC`, `POC Fault`, `Terminal Fault`, or standalone grid fault panels.
- Place a 3-phase breaker at the new wind-farm collector boundary.
- First run: no MATLAB, no LVRT, no line protection, no UFLS/UVLS, no cascading logic.

## Stage 3: Steady-State Calibration

- Set Type-3 aggregate MW/MVA near the replaced IBR target.
- Use PNNL frequency `60 Hz`.
- Choose either `Vbase=22 kV` at `AC_sys` or a new 22/33 kV transformer with Type-3 `Vbase=33 kV`.
- Use Type-3 native initialization first; do not force PNNL `Pord/Qord` into Type-3 controls.
- Accept first-pass P/Q mismatch only if voltages remain physical and the run is stable.

## Stage 4: Minimal Disturbance Verification

- Run no-fault for at least 20 s.
- Verify 0 errors and EMTDC run completion.
- Verify POC voltage, P, Q, frequency, and Type-3 status.
- Only after no-fault success, test one manual breaker trip or one mild fault.
- Do not enable automatic LVRT or cascading protection in this stage.

## Stage 5: Entry Conditions for LVRT Stage

Proceed only if:

- 0 errors.
- No-fault EMTDC run completed.
- No numerical divergence.
- Initial P/Q close to target.
- POC voltage is reasonable.
- External breaker safely disconnects the wind farm.
- The other two IBR branches are not unexpectedly disturbed.
