# Stage 10D N29 Endpoint Repair and DFIG Trip Validation

## Result

The repair passed its compiled-topology gate and its single 3.0 s dynamic
validation. `E_26_29_1` terminal B changed from compiled bus 19 to bus 1
(`N29`), while the PAPER breaker remained in series with `E_28_29_1` and was
not bypassed.

The 3.0 s Run recorded all three physical DFIG-disconnection indicators at
2.44 s:

- `DFIG_LVRT_FINAL_BRK_CMD`: 0 to 1;
- `DFIG_LVRT_TRIP_CONFIRMED`: 0 to 1;
- `DFIG_BRK_STATE`: 0 to 2.

This is within one 0.01 s output sample of the retained Stage-4 reference trip
at 2.43 s.

## Root cause and repair

The earlier audit concentrated on the inserted PAPER breaker and the
`E_28_29_1` path. It missed a separate endpoint regression: the B terminal of
`E_26_29_1` had compiled to an isolated bus 19 instead of N29. The schematic
could look connected while generated `P3.dta` still assigned the wrong bus.

The minimal repair was to place an electrical **Node Label** named `N29` on the
B-side conductor of `E_26_29_1`. It was not a control Data Label. The rebuilt
TLine section now records terminal B on bus 1, and the local branch table
records all three `NT_80` phases connected to `N29`.

## Permanent Build gate

After every physical breaker insertion, TLine endpoint move, conductor edit,
or node-label edit:

1. Build before Run.
2. Inspect generated `P3.dta`, not only the schematic canvas.
3. Verify both compiled bus numbers for every affected TLine.
4. Verify all three phases join the intended named node.
5. Verify the new breaker remains in series and is not bypassed.
6. Block the Run if any endpoint is assigned to an unexpected anonymous bus.

This gate is mandatory because visual wire contact in PSCAD 4.6 is not proof
of compiled electrical connectivity.

## Claim boundary

The result proves that the N29 endpoint was restored and the DFIG physically
disconnected. The LVRT timer was already accumulating before 2.0 s, so this
short run does not prove that the 2.0 s fault alone caused the trip. Strict
paper-sequence reproduction therefore remains unclaimed.

Raw PSCAD and generated runtime files remain outside Git under the repository's
third-party artifact policy. Their SHA-256 identities and derived evidence are
stored in `data/validation/stage10d_n29_endpoint_repair_final_audit.json`.
