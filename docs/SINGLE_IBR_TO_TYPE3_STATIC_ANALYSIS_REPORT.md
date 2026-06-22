# Single IBR to Type-3 Static Analysis Report

Date: 2026-06-22

## Actual Project Files

- PNNL 3IBR: `C:\pscad_work\pnnl_39_3ibr_pscad46_strip5\PSCAD\3IBR.pscx` - XML parsed, verified_from_model_file.
- Type-3 Average: `C:\Users\24186\Documents\动态模型\external\type3-wtg-v46\WORKING_COPY\Type3WindTurbine_TRIAL\Type3_Ave_Nov_2018.pscx` - XML parsed, verified_from_model_file.

No PSCAD drawing file was modified, generated, rewritten, saved, or committed.

## Core Findings

- The current PNNL file has three `IBR_AVM_2_1_1` instances on page `P3`. The candidate for the first trial is instance `475433949` at `x=990, y=990`; this is inferred from its alignment with the `E_2_30_1` GBUS30/N30 branch and must be confirmed visually before editing.
- `IBR_AVM_2_1_1` exposes `out`, `Inputs`, `Flags`, and `fPLL`; it does not expose a parsed `fGFM` port in the current definition.
- The Type-3 core block is `Type3_WTG_Avg`, with a single external 3-phase natural electrical port `AC_sys`.
- Type-3 top-level parameter bindings include `Dblk`, `freq`, `VLL_Gr=Vbase`, `No_WTG=UN`, `Pbase=Rated_MW`, `Vwind=Vwind`, and `Mrating=Machine_MVA`.
- Type-3 standalone grid items (`V_source`, `BusPOC`, standalone transformer/cable, POC/terminal fault panels) should not be copied into IEEE-39 for the first no-fault trial.

## Required Professional Answers

1. Can we delete only the blue IBR circle and keep everything else?
   - Not blindly. In the trial copy, the old IBR block must not remain in parallel, but the 22/0.6 kV low-voltage branch should be reviewed because it may become inappropriate for Type-3. Evidence: verified_from_model_file + inferred.

2. Can Type-3 Average connect directly to the old 0.6 kV PNNL IBR terminal?
   - No for the first trial. Type-3 `Vbase` maps to the wind-farm HV/grid interface, while internal converter/machine voltage is separate. Evidence: verified_from_model_file.

3. What does Type-3 33 kV `Vbase` correspond to?
   - It corresponds to `VLL_Gr`, the Type-3 aggregate AC/grid-side interface into the internal transformer, not the 0.6/0.69 kV converter terminal. Evidence: verified_from_model_file.

4. Should the PNNL 22/0.6 kV transformer be kept?
   - Preferred Option B removes or bypasses it in the trial copy and connects Type-3 at the 22 kV collector boundary, or through a new 22/33 kV transformer. Evidence: inferred from verified transformer structures.

5. Is a new 22/33 kV or 0.6/33 kV wind-farm transformer needed?
   - A 22/33 kV transformer is the reasonable fallback if Type-3 cannot be safely set to `Vbase=22 kV`. A 0.6/33 kV transformer is not preferred because it preserves the old converter-side voltage boundary. Evidence: inferred.

6. Which Type-3 standalone components must be stripped?
   - Strip/avoid `V_source`, standalone `BusPOC`, `POC Fault`, `Terminal Fault`, and standalone grid-source context. Treat cable/standalone transformer as reusable only after explicit impedance/voltage review. Evidence: verified_from_model_file.

7. How should `Pini/Pord/Qord` be used?
   - Use them as calibration targets and documentation references, not direct wires. Type-3 should first initialize using native `Vwind`, `Rated_MW`, `Machine_MVA`, `UN`, and internal `Pref_pu/Qref_pu` controls. Evidence: verified_from_model_file + inferred.

8. Can `DB/DBLK` connect directly to `Dblk`?
   - Not directly. Type-3 has `Dblk` and internal `DBlk_Rsc/Gsc/Rtr`, but semantics and timing are not proven identical to PNNL `DB/DBLK`. Use Type-3 native `Dblk` plus an external breaker for first trial. Evidence: verified_from_model_file.

9. Is GBUS30/N30 the best first DFIG trial point?
   - It is acceptable as the planned first point because the user already identified it and the static file shows a clear transformer/reactor/IBR branch. However, the static parser did not compare all three IBR candidates dynamically; final choice needs GUI confirmation. Evidence: verified_from_model_file + inferred.

10. What is the minimum-change, easiest-to-converge, LVRT-friendly scheme?
    - Option B: keep PNNL upstream GBUS30/N30 and 345/22 kV network, use a trial breaker at the 22 kV collector boundary, connect Type-3 `AC_sys` through either `Vbase=22 kV` or an explicit 22/33 kV transformer. Evidence: verified_from_model_file + inferred.

## User's First Five PSCAD GUI Actions

1. Duplicate the successful PNNL baseline into `3IBR_DFIG1_TRIAL`.
2. Open the trial copy and confirm it still runs before changes.
3. Screenshot and record the candidate branch around `IBR_AVM_2_1_1` instance `475433949`.
4. Open Type-3 Average and record `Type3_WTG_Avg` parameters and `AC_sys`.
5. Choose Option B variant: direct `Vbase=22 kV` adaptation or explicit 22/33 kV transformer.

## GUI-Only Confirmations Still Required

- Exact bus wiring order for PNNL `Inputs` and `Flags`.
- Exact source of `Pini`, `Pord`, `Qord`, `Sbase`, `INV_Vbase`, and `DB/DBLK`.
- Whether Type-3 `Vbase=22 kV` is accepted without hidden scaling side effects.
- Whether instance `475433949` is exactly the GBUS30/N30 visual candidate selected by the user.
- First no-fault initialization after manual replacement.

## Generated Artifacts

See:

- `docs/PSCAD_SOURCE_FILE_AUDIT.md`
- `docs/IBR_AVM_2_1_1_STATIC_MAP.md`
- `docs/TYPE3_AVERAGE_STATIC_MAP.md`
- `docs/IBR_TO_TYPE3_TOPOLOGY_OPTIONS.md`
- `docs/IBR_TO_TYPE3_RECOMMENDED_ARCHITECTURE.md`
- `docs/IBR_TO_TYPE3_SIGNAL_MAPPING.md`
- `docs/MANUAL_SINGLE_IBR_TO_TYPE3_DFIG_REPLACEMENT.md`
- `docs/PSCAD_GUI_REPLACEMENT_CHECKLIST.md`
- `docs/DFIG1_TRIAL_ACCEPTANCE_CRITERIA.md`
- `docs/DFIG1_TRIAL_ROLLBACK_PROCEDURE.md`
- `config/ibr_avm_to_type3_signal_mapping.yaml`
- `data/reference/*.json`
- `data/reference/*.csv`
- `scripts/analyze_pscad_ibr_type3_mapping.py`
