# DFIG1 Trial Acceptance Criteria

The first single-DFIG replacement trial is acceptable only if all criteria hold:

- PSCAD build/run completes with 0 errors.
- No-fault EMTDC run completes for at least 20 s.
- No numerical divergence or non-physical voltage/frequency drift.
- Wind-farm POC voltage is within a reasonable engineering range around the pre-replacement bus voltage.
- Aggregate P and Q are close enough for first-pass calibration and trend in the expected direction.
- Manual wind-farm breaker can disconnect the Type-3 branch safely.
- The two remaining IBRs continue to initialize and run.
- No MATLAB, LVRT, automatic line protection, UFLS/UVLS, or cascading logic is enabled.

Unaccepted states:

- Direct Type-3 connection to the old 0.6 kV converter terminal without transformer/voltage review.
- Parallel operation of old IBR block and new Type-3 block at the same branch.
- Reuse of Type-3 standalone source as part of IEEE-39.
