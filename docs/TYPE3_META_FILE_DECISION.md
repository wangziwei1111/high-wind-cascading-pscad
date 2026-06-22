# Type-3 Meta-File Decision

## Decision

C. `Copy as Meta-File` does not apply to this scenario. Use the official PSCAD Library/Definition import method instead.

## Why

Official/local PSCAD v4.6 documentation uses `Copy as Meta-File or Bitmap` for copying visual selections, plotting objects, meters, or canvas areas into reports as image-like clipboard data. It does not create or import PSCAD component/module definitions.

Official/local PSCAD documentation identifies the definition migration file format as PSCAD Definition file `*.psdx`, imported through the Definitions branch with `Import Definition(s)...`. For module hierarchies, the relevant command is `Export with Dependents`.

## Official Evidence

Local:

- `C:\Program Files (x86)\PSCAD46\help\UserGuides\PSCAD Users Guide (V4.6).pdf`, pages 181-182.
- Extracted snippets: `data/reference/local_pscad_v46_pdf_keyword_hits.json`.

Official web:

- Definitions branch: `https://www.pscad.com/webhelp/PSCAD/The_Application_Environment/The_Workspace/The_Projects_Section.htm`
- Import/export definitions: `https://www.pscad.com/webhelp/PSCAD/Features_and_Operations/Components_and_Modules/Importing_Exporting_Definitions.htm`
- Copy/transfer hierarchies: `https://www.pscad.com/webhelp/PSCAD/Features_and_Operations/Copying_and_Transferring_Module_Hierarchies.htm`

## Applicable Preconditions

- Both Type-3 case and `Type3WTG_Lib` library are loaded in the same PSCAD workspace.
- `Type3WTG_Lib` is a Library Project, not a Case Project.
- The source definition is selected in the Type-3 Case project's Definitions branch, not merely on the schematic canvas.
- The top definition is `Type3_WTG_Avg` or the equivalent module definition behind the visible "Type 3 Average" instance.
- Export uses `Export with Dependents`, not plain `Export As...`, because Type-3 is a hierarchy.

## Risks

- If the user exports from `Main` or copies the whole schematic, standalone test network objects may be included.
- If only plain `Export As...` is used, child definitions may be missing.
- If a name conflict exists in `Type3WTG_Lib`, PSCAD may prompt for rename/overwrite decisions; stop and screenshot.
- If the library is not loaded when opening 3IBR, instances may appear unresolved or as placards.
- If imported definitions remain under the case namespace instead of the library namespace, the original error will recur.

## Exact Next Click Steps

Use the detailed operation card in `docs/TYPE3_LIBRARY_IMPORT_PROCEDURE.md`.

Short version:

1. In the Type-3 case project's Definitions branch, right-click `Type3_WTG_Avg`.
2. Choose `Export with Dependents`.
3. Save a temporary `*.psdx` outside Git, for example `C:\pscad_work\type3_wtg_v46_trial\Type3_WTG_Avg_with_dependents.psdx`.
4. In `Type3WTG_Lib` project's Definitions branch, right-click `Definitions`.
5. Choose `Import Definition(s)...`.
6. Select the saved `*.psdx`.
7. Verify imported definitions, save `Type3WTG_Lib`.

## Failure Rollback

- If export/import prompts about duplicate definitions, cancel and screenshot.
- If imported definitions look incomplete, close `Type3WTG_Lib` without saving and restart from a fresh copy of the blank library.
- If 3IBR later shows unresolved references, load `Type3WTG_Lib` first, then use `Switch Reference...` or `Edit Reference...` only after the library definitions are confirmed.

## Never Do

- Do not click `Copy as Meta-File` for migration.
- Do not paste the Type-3 module directly from one Case project into another Case project.
- Do not edit `.pscx`/`.pslx` XML manually.
- Do not import standalone `V_source`, `BusPOC`, `POC Fault`, `Terminal Fault`, or cable/test graph panels into the library.
