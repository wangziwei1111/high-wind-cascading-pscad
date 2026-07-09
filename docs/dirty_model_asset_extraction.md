# Dirty Model Asset Extraction

The dirty PSCAD model is a dirty-but-working reference, not the new main model.

## Repository Audit Result

- No committed clean IEEE39 PSCAD project file was found by `rg --files`.
- Existing metadata in `data/reference/pscad_source_file_inventory.json` records local restricted PSCAD assets outside or under ignored external working-copy paths.
- `docs/PSCAD_SOURCE_FILE_AUDIT.md` identifies `C:\pscad_work\pnnl_39_3ibr_pscad46_strip5\PSCAD\3IBR.pscx` as a parseable local PNNL 3IBR PSCAD 4.6.2 project.
- Restricted PSCAD projects and libraries must not be blindly edited or committed.

## Extract From Dirty Reference

1. PSCAD method used to call MATLAB.
2. MATLAB path setup and version assumptions.
3. MATLAB m-file entry point and call signature.
4. Fixed input vector or struct packing order.
5. Fixed output command vector or struct unpacking order.
6. Breaker command fan-out pattern from returned MATLAB commands.
7. Measurement wiring that has already produced valid voltage, current, power, frequency, and status signals.
8. Breaker online/offline status feedback wiring.
9. Existing run metadata needed to compare MATLAB command time with PSCAD breaker action time.

## Do Not Extract

1. GUI line overload protection logic.
2. GUI LVRT/HVRT judgement logic.
3. GUI UFLS/UVLS logic.
4. GUI generator protection timers.
5. Temporary comparators.
6. Temporary delay blocks.
7. Temporary relay networks.
8. Experimental display blocks.
9. Duplicate signal wires.
10. Debug leftovers and ad hoc analysis panels.

## Manual Extraction Record

For each extracted asset, record:

- Dirty reference path and model checksum.
- PSCAD page/subpage name.
- Signal or breaker name in the dirty model.
- New clean mapping ID from `mapping/*.csv`.
- Whether the asset is verified, inferred, or pending PSCAD GUI confirmation.

