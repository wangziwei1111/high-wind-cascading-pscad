# Type-3 WTG Local Discovery

Date: 2026-06-22

This local discovery pass searched for an already available PSCAD Type-3 DFIG / WTG example that could be used later for independent PSCAD v4.6.2 verification.

## Scope

Searched roots:

- `C:\Users\24186\Documents`
- `C:\Users\24186\Downloads`
- `C:\Users\24186\Desktop`
- `C:\Program Files`
- `C:\Program Files (x86)`
- Current project directory, including `external/`

File extensions considered:

- `.pscx`
- `.pslx`
- `.psl`
- `.pswx`
- `.lib`
- `.zip`
- `.rar`
- `.7z`
- `.pdf`

Keywords considered:

- `Type 3`
- `Type-3`
- `Type3`
- `Type_3`
- `WTG`
- `Wind Turbine`
- `WindTurbine`
- `DFIG`
- `V46`
- `Crowbar`
- `WindFarm`
- `Wind Farm`
- `Wind Park`
- `WindPark`

## Result

No local candidate files were found.

The machine does not currently appear to contain the official PSCAD Type-3 WTG V46 example package under the audited locations. No PSCAD project, library, archive, or PDF matching the Type-3 WTG acquisition criteria was copied, opened, modified, or imported into the current 3IBR project.

The machine-readable inventory is stored in:

`data/reference/type3_wtg_local_inventory.json`

## Safety Notes

- A PDF technical document alone is not a runnable PSCAD model.
- A `.pscx` file must not be separated from its associated PSCAD libraries, data files, and workspace resources.
- If the official package is later downloaded, keep the original archive/extraction under `external/type3-wtg-v46/ORIGINAL_DOWNLOAD_DO_NOT_EDIT/` and use `external/type3-wtg-v46/WORKING_COPY/` for PSCAD GUI trials.
