# Stage 8 PAPER_OVL1 output observability root cause

Generated: 2026-07-03T15:38:13

## Deterministic root cause

`PAPER_OVL1_ABOVE_THRESHOLD` is connected to an Output Channel, but that Output Channel is titled incorrectly.

- Component ID: `518433536`
- Current title: `PAPER_OVL1_RELAY_ENABLE`
- Source label: `PAPER_OVL1_ABOVE_THRESHOLD`
- Location: `x=2916, y=1980`
- Required title: `PAPER_OVL1_ABOVE_THRESHOLD`

There is also a separate real relay-enable Output Channel:

- Component ID: `865554842`
- Current title: `PAPER_OVL1_RELAY_ENABLE`
- Source label: `PAPER_OVL1_RELAY_ENABLE`
- Location: `x=3168, y=1980`

So the canonical runtime title set is not unique and complete: `PAPER_OVL1_RELAY_ENABLE` is duplicated, and `PAPER_OVL1_ABOVE_THRESHOLD` is missing as a title.

## Runtime output file evidence

At the Stage 7 result point:

- Expected `.inf`: `C:\pscad_work\pnnl_39_3ibr_pscad46_strip5\PSCAD\3IBR_DFIG1_TRIAL.gf46\3IBR_DFIG1_TRIAL.inf`; exists = `False`
- Expected `3IBR_DFIG1_TRIAL_NN.out` count = `0`
- Existing `E_*` Line Constants `.out` count = `31`

The Line Constants `.out` files are not PSCAD Output Channel PGB runtime waveforms. Gate A therefore repairs title/PGB observability first, then requires a Build-only pre-run gate before allowing one Run.

## Minimal GUI repair

Only rename Output Channel component ID `518433536` from `PAPER_OVL1_RELAY_ENABLE` to `PAPER_OVL1_ABOVE_THRESHOLD`. Keep its input connected to `PAPER_OVL1_ABOVE_THRESHOLD`.

Do not change the selected line, equivalent capacity, threshold, timer, relay internals, breaker position, or breaker command polarity.
