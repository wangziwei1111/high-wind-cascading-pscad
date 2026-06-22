# PSCAD Case-to-Library Migration Research

Date: 2026-06-22

Scope: PSCAD X4 v4.6.2 component/module definition migration only. No IEEE-39 wiring, no IBR replacement, no PSCAD GUI automation, and no direct PSCAD XML migration.

## Research Conclusion

The correct PSCAD-supported mechanism for moving a module definition hierarchy from a case project into a library project is the Definitions branch mechanism:

1. Export the module definition as a PSCAD Definition file (`*.psdx`).
2. For a module hierarchy, use `Export with Dependents`.
3. Import that `*.psdx` into the destination library project's Definitions branch using `Import Definition(s)...`.

`Copy as Meta-File` is not the definition migration mechanism. It is a graphics/reporting command that copies a selected visual object or canvas area as a Windows metafile/bitmap image.

## Evidence Sources

### Local PSCAD v4.6 Documentation

Local manual:

`C:\Program Files (x86)\PSCAD46\help\UserGuides\PSCAD Users Guide (V4.6).pdf`

Extracted local evidence is stored in:

`data/reference/local_pscad_v46_pdf_keyword_hits.json`

Relevant findings:

- Page 181: definitions can be exchanged by saving a Definition (`*.psdx`) file; a definition file contains XML elements defining the component/module as it appears in `.pscx` or `.pslx`.
- Page 181: import is through the workspace primary window, Definitions branch, `Import Definition(s)...`.
- Page 182: export is through Definitions branch, desired definition, `Export As...`.
- Page 182: `Export with Dependents` includes dependent module definitions for module hierarchies.
- Page 211: `Copy Transfer` copies a module hierarchy and top-level instance parameter values.
- Page 182 and page 298: `Copy as Meta-File or Bitmap` is a visual/image export path, not a definition import path.

### Official PSCAD Web Help

- Official Definitions branch page states that case/library projects have Definitions branches; user-defined component definitions should be stored in library projects, not case projects.
- It documents `Import Definition(s)...` for `*.psdx`/older `*.cmp`, `Paste`, `Export As...`, `Copy with Dependents`, and `Export with Dependents`.
- Official Importing/Exporting Definitions page states that definitions are imported/exported as `*.psdx`.
- Official Copying and Transferring Module Hierarchies page states that `Copy with Dependents` includes child module definitions and custom component definitions in dependent modules, and that `Copy Transfer` includes top-level instance parameter information.
- Official Definition Referencing page documents `Switch Reference...` and `Edit Reference...` for relinking instances to loaded definitions.

URLs:

- `https://www.pscad.com/webhelp/PSCAD/The_Application_Environment/The_Workspace/The_Projects_Section.htm`
- `https://www.pscad.com/webhelp/PSCAD/Features_and_Operations/Components_and_Modules/Importing_Exporting_Definitions.htm`
- `https://www.pscad.com/webhelp/PSCAD/Features_and_Operations/Copying_and_Transferring_Module_Hierarchies.htm`
- `https://www.pscad.com/webhelp/PSCAD/Features_and_Operations/Components_and_Modules/Linking_and_Re-linking_Definitions.htm`

## Mechanism Summary

| Mechanism | Official purpose | Applies here? | Notes |
|---|---|---|---|
| `Copy as Meta-File` | Copy visual selection to Windows metafile/bitmap for reports | No | Not a PSCAD component definition transfer. |
| `Export As...` | Export one definition to `*.psdx` | Partially | Insufficient if `Type3_WTG_Avg` has child module definitions. |
| `Export with Dependents` | Export module hierarchy and dependent module definitions to `*.psdx` | Yes, preferred | Best match for Type-3 hierarchy. |
| `Import Definition(s)...` | Import `*.psdx`/old `*.cmp` into a project Definitions branch | Yes | Use on `Type3WTG_Lib`, not on 3IBR case. |
| `Copy with Dependents` | Copy module definition hierarchy between loaded projects | Possible | GUI clipboard route; less auditable than `*.psdx`. |
| `Copy Transfer` / `Paste Transfer` | Copy hierarchy plus top-most module instance parameter values from an instance | Possible for scratch experiments | Useful if preserving the exact example instance values is required, but not the cleanest library import path. |
| `Switch Reference...` / `Edit Reference...` | Relink an existing instance to a loaded definition | Later only | Use after the library definition exists and is loaded. |

## Type-3-Specific Static Evidence

`scripts/inspect_type3_component_definition_dependencies.py` found:

- Core definition: `Type3_WTG_Avg`.
- Transitive project-local definition count: 15.
- The core module exposes the external 3-phase port `AC_sys`.
- The core hierarchy includes `DFIG_Converters_Avg`, `WindTurbine_MechModel`, `Synchronization`, `LLTX_SCALER_Xpu`, `Rotor_side_Controls`, `Grid_side_Controls`, `Crowbar_prot`, `Chopper`, `Filter`, `ConvBridge_Avg`, `PI_AntiWindUp`, `PI_AntiWindUp_2`, `CP_curve_T7`, and `V_dip_sig`.
- Standalone `Main` page objects such as `V_source`, standalone source/transformer/cable/BusPOC/test faults are outside the `Type3_WTG_Avg` definition closure and should not be imported when exporting only the core definition with dependents.

Machine-readable evidence:

`data/reference/pscad_case_library_evidence.json`

## Practical Answer

Use `Export with Dependents` from the source case's `Type3_WTG_Avg` definition, import the resulting `.psdx` into `Type3WTG_Lib`, save the library, then load `Type3WTG_Lib` alongside the 3IBR trial case and instantiate from the library definition.

Do not use `Copy as Meta-File`.
