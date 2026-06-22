# Type-3 Library Failure Recovery

## If `Export with Dependents` Is Missing

Stop. Do not use `Copy as Meta-File`.

Capture:

- Screenshot of `Type3_Ave_Nov_2018 -> Definitions`.
- Screenshot of the right-click menu on `Type3_WTG_Avg`.
- Screenshot of the visible outer `Type 3 Average` instance properties.

Possible causes:

- The selected object is an instance, not the definition.
- The definition name is not exactly `Type3_WTG_Avg`.
- The object is a component definition rather than a module definition.

## If `.psdx` Import Prompts for Duplicate Names

Stop and cancel.

Recovery:

1. Close `Type3WTG_Lib` without saving.
2. Reopen the blank library.
3. Decide whether to rename the library namespace or import into a fresh library.
4. Do not overwrite definitions without a documented reason.

## If Imported Library Is Missing Child Definitions

Likely cause: plain `Export As...` was used instead of `Export with Dependents`.

Recovery:

1. Close `Type3WTG_Lib` without saving.
2. Re-export from `Type3_WTG_Avg` using `Export with Dependents`.
3. Re-import into a clean library.

## If 3IBR Still Reports Case-to-Case Definition Error

Likely cause: the pasted instance still references `Type3_Ave_Nov_2018:Type3_WTG_Avg`.

Recovery:

1. Delete the disconnected failed instance from the trial case.
2. Ensure `Type3WTG_Lib` is loaded.
3. Create the instance from `Type3WTG_Lib -> Definitions -> Type3_WTG_Avg`.
4. If needed, use `Switch Reference...` or `Edit Reference...` to point to `Type3WTG_Lib`, but only after the library definition is verified.

## If PSCAD Crashes or Saves Bad State

1. Close PSCAD.
2. Preserve screenshots and any `.psdx` file for diagnosis.
3. Reopen the untouched baseline projects.
4. Recreate `Type3WTG_Lib` from a clean copy.
5. Do not reuse a partially imported library unless it was saved before the failure and verified.

## Files Never to Commit

- `*.psdx` exported from official Type-3 model unless redistribution rights are confirmed.
- `*.pscx`, `*.pslx`, `*.pswx`, `*.lib`.
- `*.gf46`, `*.out`, `*.snp`, `*.obj`, `*.dll`, `*.exe`.
