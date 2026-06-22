# PSCAD Source File Audit

Date: 2026-06-22

This audit is read-only. No PSCAD project, library, workspace, generated build directory, or model binary was modified, copied into Git, or saved by automation.

## Main Project Files

| Project | Main file | Parse status | Evidence |
|---|---|---|---|
| PNNL 3IBR | `C:\pscad_work\pnnl_39_3ibr_pscad46_strip5\PSCAD\3IBR.pscx` | XML parsed | verified_from_model_file |
| Official Type-3 Average | `C:\Users\24186\Documents\动态模型\external\type3-wtg-v46\WORKING_COPY\Type3WindTurbine_TRIAL\Type3_Ave_Nov_2018.pscx` | XML parsed | verified_from_model_file |

The user-provided PNNL directory path ended with `...\PSCAD\3IBR`, but the actual main project file is one level higher at `...\PSCAD\3IBR.pscx`.

## PNNL 3IBR Local Files

| File | Role | Commit status | Evidence |
|---|---|---|---|
| `3IBR.pscx` | Main PSCAD project | external restricted, do not commit | verified_from_project_structure |
| `ETRAN.pslx` | E-TRAN namespace/library file | external restricted, do not commit | verified_from_project_structure |
| `ETRAN46.pslx` | E-TRAN v4.6 namespace/library file | external restricted, do not commit | verified_from_project_structure |
| `ETRAN_GF46.lib` | E-TRAN Fortran library for GFortran 4.6 flow | external restricted, do not commit | verified_from_project_structure |
| `IEEE39bus_original_Modified5.dyr` | Dynamic data input | external restricted, do not commit | verified_from_project_structure |
| `3IBR.gf46/` | Generated EMTDC/GFortran build directory | external generated output, do not commit | verified_from_project_structure |
| `3IBR.gf42/` | Legacy/generated build directory | external generated output, do not commit | verified_from_project_structure |

The file inventory with size, SHA-256, modification time, and repository membership is in `data/reference/pscad_source_file_inventory.json`.

## Type-3 Average Local Files

| File | Role | Commit status | Evidence |
|---|---|---|---|
| `Type3_Ave_Nov_2018.pscx` | Official Type-3 average project | official external model, do not commit | verified_from_project_structure |
| `Type3_Dlt_Nov_2018.pscx` | Official Type-3 detailed project | official external model, do not commit | verified_from_project_structure |
| `Type3_windTurbine.pswx` | Official PSCAD workspace | official external model, do not commit | verified_from_project_structure |
| `Type3_Ave_Nov_2018.gf46/` | Generated build output | generated output, do not commit | verified_from_project_structure |

## Dependency Findings

- PNNL depends on project-local definitions inside `3IBR.pscx`, plus E-TRAN definitions and the local `ETRAN_GF46.lib` library. Evidence: `ETRAN:*` components and same-directory E-TRAN files are present. Status: verified_from_model_file / verified_from_project_structure.
- Type-3 Average is largely self-contained in its `.pscx` with project-local definitions such as `Type3_WTG_Avg`, `DFIG_Converters_Avg`, `WindTurbine_MechModel`, `Rotor_side_Controls`, `Grid_side_Controls`, `Crowbar_prot`, `Chopper`, `Cable_1`, and `Cable_3`. Status: verified_from_model_file.
- Type-3 standalone test network contains external grid source, POC bus, transformer, cable, and fault panels. These are not automatically portable into PNNL and must be separated from the wind-farm core during manual integration. Status: verified_from_model_file.

## Safe Handling Rule

Only commit audit metadata, scripts, Markdown, JSON, CSV, and YAML. Do not commit `.pscx`, `.pslx`, `.pswx`, `.psl`, `.lib`, `.gf46`, `.out`, `.snp`, `.obj`, `.dll`, `.exe`, license files, or copied official/PNNL model content.
