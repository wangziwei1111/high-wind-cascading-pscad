# Next Stage Handoff

This project has a working PNNL 3IBR baseline in PSCAD v4.6.2. The next stage must not begin until a Type-3 DFIG WTG example has been legally obtained and independently verified.

## Entry Conditions for Single-IBR Replacement Trial

Start a single IBR replacement trial only after all conditions are true:

1. The original 3IBR project has completed an EMTDC run.
2. The official Type-3 WTG example has independently completed a no-fault run in PSCAD v4.6.2.
3. `docs/TYPE3_WTG_PORT_RECORD_TEMPLATE.md` has been filled out.
4. One target IBR replacement location has been documented, including bus, transformer, breaker, capacity, and measurement terminals.
5. A separate `3IBR_DFIG1_TRIAL` working copy has been created.
6. MATLAB has not been connected.
7. LVRT, line protection, UFLS, and UVLS have not been enabled or modified.

## Non-Goals for the Acquisition Stage

- Do not modify the 3IBR project.
- Do not replace an IBR.
- Do not connect the Type-3 model to IEEE-39.
- Do not implement LVRT or cascading-fault logic.
- Do not commit official PSCAD model files.

## Recommended Next Artifact

After the independent Type-3 run succeeds, create a short trial-readiness note with:

- Official package filename and SHA-256.
- Screenshot of PSCAD v4.6.2 opening the Type-3 project.
- Screenshot of successful build/run.
- Completed port/interface table.
- Proposed target IBR location for the first isolated replacement experiment.
