# Type-3 Average Static Map

## Project and Top-Level Block

| Item | Value | Evidence |
|---|---|---|
| Main file | `external/type3-wtg-v46/WORKING_COPY/Type3WindTurbine_TRIAL/Type3_Ave_Nov_2018.pscx` | verified_from_project_structure |
| Project name/version | `Type3_Ave_Nov_2018`, PSCAD project version `4.6.3` | verified_from_model_file |
| Core wind-farm definition | `Type3_WTG_Avg` | verified_from_model_file |
| Top-level core instance | `Type3_Ave_Nov_2018:Type3_WTG_Avg`, id `1408725072`, in `Main` | verified_from_model_file |
| External electrical port | `AC_sys`, natural 3-phase electrical | verified_from_model_file |

The project opens in PSCAD 4.6.2 according to the user's GUI run result. The file itself records project version `4.6.3`; compatibility is therefore verified by user run, while the raw file version is verified from model file.

## Top-Level Parameters

| GUI/user concept | Parsed parameter | Example binding/value | Evidence |
|---|---|---|---|
| Enable/block | `Dblk` | `Dblk` | verified_from_model_file |
| Nominal frequency | `freq` | `freq` | verified_from_model_file |
| AC-side base voltage | `VLL_Gr` | `Vbase` | verified_from_model_file |
| Number of WTGs | `No_WTG` | `UN` | verified_from_model_file |
| Rated MW per WTG/HV terminal active power | `Pbase` | `Rated_MW` | verified_from_model_file |
| Wind speed | `Vwind` | `Vwind` | verified_from_model_file |
| Machine MVA | `Mrating` | `Machine_MVA` | verified_from_model_file |
| Cut-in wind speed | `vWcutin` | `3.0 [m/s]` | verified_from_model_file |
| Cut-out wind speed | `vWcutout` | `25.0 [m/s]` | verified_from_model_file |
| Maximum slip | `Slip_max` | `0.3` | verified_from_model_file |

## Core Internal Subsystems to Keep With the Wind Farm

| Subsystem | Evidence |
|---|---|
| `DFIG_Converters_Avg` | contains stator/rotor electrical ports, grid-side and rotor-side converter controls, DC link, chopper, crowbar, filters | verified_from_model_file |
| `WindTurbine_MechModel` | mechanical turbine, pitch, wind speed, speed/power interfaces | verified_from_model_file |
| `Rotor_side_Controls` | `DBlk_Rtr`, `Pref_pu`, `Qref_pu`, PLL-related controls | verified_from_model_file |
| `Grid_side_Controls` | `DBlk_Gr`, `V_GSC`, `I_GSC`, `Q_GSC`, DC voltage/reactive controls | verified_from_model_file |
| `Crowbar_prot` | DC crowbar voltage/time/current protection | verified_from_model_file |
| `Chopper` | DC chopper voltage thresholds and resistor | verified_from_model_file |

## Standalone Test Environment to Strip or Avoid Duplicating

| Standalone item | Why not directly copy into IEEE-39 | Evidence |
|---|---|---|
| `master:source3` / `V_source` | represents the standalone external grid; PNNL already has the IEEE-39 grid | verified_from_model_file |
| `BusPOC` | standalone POC label/measurement context; PNNL has its own bus/measurement context | verified_from_model_file |
| Main-page `master:xfmr-3p2w` | test-system transformer, not automatically the correct PNNL branch transformer | verified_from_model_file |
| `Cable_1` / `Cable_3` | standalone cable model; may be reused only after impedance/voltage review | verified_from_model_file |
| `POC Fault` / `Terminal Fault` panels | test fault controls, not first no-fault integration artifacts | verified_from_model_file |

## Important Voltage Clue

Inside `Type3_WTG_Avg`, a 3-winding transformer maps `V1=VLL_Gr`, `V2=V_nom_con`, and `V3=V_nom_gen`; the converter/machine parameters include `Vacbase=0.69 [kV]`, `V_nom_con`, and `V_nom_gen`. Therefore `Vbase=33 kV` in the standalone example should be treated as the wind-farm grid/HV-side interface voltage for the Type-3 aggregate, not as a direct 0.6 kV converter terminal. Status: verified_from_model_file.
