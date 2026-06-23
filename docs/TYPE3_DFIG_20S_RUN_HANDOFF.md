# Type-3 DFIG Replacement Trial: 20 s No-Fault Run Handoff

Date: 2026-06-23

This document records the current PSCAD progress so the next assistant or operator can continue without re-discovering the state.

## Current Status

The first PNNL 3IBR IBR replacement trial has reached a successful 20 s no-fault run.

Observed PSCAD result:

- Build Messages: 0 Errors, 0 Warnings
- EMTDC run completed
- Solve Time: 94 ms
- Total live nodes: 193
- Runtime duration: 20 s
- Solution time step: 5 us
- Channel plot step: 4150 us
- Main output files were written under `C:\pscad_work\pnnl_39_3ibr_pscad46_strip5\PSCAD\3IBR.gf46`

Last sampled values from `3IBR_01.out` near 20 s:

| Time (s) | Frequency (Hz) | V pu approx | P Type-3 branch (MW) | Q Type-3 branch (MVAr) |
|---:|---:|---:|---:|---:|
| 19.99885 | 60.00000 | 0.99991 | 199.069 | -18.765 |

The Type-3 branch active power is consistent with the aggregation setting `No_WTG = 100` and `Pbase = 2.0 MW`, i.e. about 200 MW total.

## PSCAD Workspace State

The current working PSCAD case is:

```text
C:\pscad_work\pnnl_39_3ibr_pscad46_strip5\PSCAD\3IBR.pscx
```

The workspace was loaded with:

```text
C:\pscad_work\pnnl_39_3ibr_pscad46_strip5\PSCAD\ETRAN46.pslx
C:\pscad_work\type3_wtg_v46_trial\Type3WTG_Lib.pslx
C:\pscad_work\pnnl_39_3ibr_pscad46_strip5\PSCAD\3IBR.pscx
```

Do not commit or redistribute the PSCAD model files, PSCAD library files, generated `.gf46` directory, official Type-3 model, PNNL model, or ETRAN library.

## Implemented Trial Topology

The first IBR branch on P3 was replaced by a library-referenced official Type-3 average wind turbine instance.

The retained upstream boundary is the existing GBUS30/N30 side and the original upstream 345/22 kV interface.

The new trial branch is:

```text
22 kV collector node
  -> BRK_DFIG three-phase breaker
  -> XFMR_DFIG_22_33 two-winding transformer
  -> Type3WTG_Lib:Type3_WTG_Avg AC_sys terminal
```

The original local `22/0.6 kV + IBR_AVM` branch for the replaced first IBR was removed from the active electrical topology. Other IBR branches were not intentionally modified.

## Type-3 Instance Parameters

The Type-3 instance should have these parameter values:

| Parameter | Value |
|---|---|
| Dblk | `Dblk_DFIG` |
| freq | `60` |
| VLL_Gr | `33` |
| No_WTG | `100` |
| Pbase | `2.0` |
| Vwind | `Vwind` |
| Mrating | `2.5` |

The DFIG control support on P3 is:

```text
TIME/time-sig -> compare(X=0.2, OL=0, OH=1) -> Dblk_DFIG
```

The wind-speed support on P3 is:

```text
windSpeed = 11.0 -> Rate Limiter(IR=10 [1/s], DR=5 [1/s]) -> Vwind
```

## New Transformer Assumption

The new DFIG transformer is a temporary trial assumption and must not be presented as a paper-derived or official validated value.

Name:

```text
XFMR_DFIG_22_33
```

Settings:

| Field | Value |
|---|---|
| Rated MVA | 250.0 MVA |
| Frequency | 60 Hz |
| Winding 1 voltage | 22 kV |
| Winding 2 voltage | 33 kV |
| Winding 1 type | Y |
| Winding 2 type | Y |
| Positive sequence leakage reactance | 0.1 pu |
| Copper losses | 0.005 pu |
| Eddy current losses | 0.0001 pu |
| Ideal transformer model | Yes |
| Tap changer | None |
| Saturation | Disabled |

Required label for reports:

```text
TEMPORARY 22/33 kV DFIG TRANSFORMER ASSUMPTION
```

## Evidence Captured During Run

The user provided PSCAD screenshots showing:

- 20 s duration and 5 us timestep
- 0 Errors and 0 Warnings
- EMTDC run completed
- Type-3 branch approximately 199 MW and -18.8 MVAr near the end of the run
- Type-3 branch connected through `BRK_DFIG` and `XFMR_DFIG_22_33`

Local generated output evidence:

```text
C:\pscad_work\pnnl_39_3ibr_pscad46_strip5\PSCAD\3IBR.gf46\3IBR_01.out
```

Last visible tail near 20 s:

```text
19.98225  60.00000  ...  199.06999  ...  -18.76063 ...
19.98640  60.00000  ...  199.05895  ...  -18.80098 ...
19.99055  60.00000  ...  199.10002  ...  -18.81441 ...
19.99470  60.00000  ...  199.11034  ...  -18.77663 ...
19.99885  60.00000  ...  199.06912  ...  -18.76482 ...
```

## Known Caveats

- The new 22/33 kV, 250 MVA transformer impedance is a temporary debugging assumption.
- This is a first no-fault operating trial, not yet a validated reproduction of the paper's cascading-failure scenario.
- The current project contains graph blocks and page-layout artifacts that may be outside the visible PSCAD page; use Search and the generated overview image when navigating.
- PSCAD can be slow or appear stuck if a 20 s run is restarted immediately after a stopped run. A later rerun completed successfully.

## Suggested Next Stage

Recommended next stage:

1. Preserve a backup of the current working PSCAD folder before any new edits.
2. Export or capture clean evidence screenshots:
   - P3 topology around GBUS30/N30 and Type-3 branch
   - Type-3 parameter window
   - `Dblk_DFIG` and `Vwind` support logic
   - Transformer parameter window
   - Build Messages with 0 Errors / 0 Warnings
   - 20 s run completion
3. Add formal measurement channels for Type-3 P, Q, V, frequency, `Dblk_DFIG`, `Vwind`, and breaker state if not already plotted in a clear results panel.
4. Run a repeat 20 s no-fault verification after backup.
5. Only after the no-fault evidence package is stable, begin the next controlled disturbance or cascading-failure setup stage.

