# DFIG1 Trial Rollback Procedure

1. Stop PSCAD simulation.
2. Close the trial project without saving if the bad edit has not been intentionally saved.
3. Reopen the untouched PNNL 3IBR baseline.
4. Confirm the baseline still builds/runs.
5. If the trial copy was saved and is unusable, delete only the trial copy after verifying its absolute path.
6. Recreate `3IBR_DFIG1_TRIAL` from the baseline and restart at Stage 1 documentation.

Never roll back by editing the baseline project in place.
