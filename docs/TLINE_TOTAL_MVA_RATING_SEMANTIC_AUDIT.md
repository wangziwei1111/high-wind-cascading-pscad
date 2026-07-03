# TLine Total MVA Rating semantic audit

Generated: 2026-07-03T03:52:46

This audit rechecks the stage-five assumption that every real PSCAD TLine
`Total MVA Rating = 100.0 MVA` can be used as a continuous thermal or
protection-grade line rating.

## Result

- Final semantic classification: `uniform_model_value_or_default_parameter`
- Safe numerical interpretation: `100-MVA-normalized apparent-power response index`
- Protection-grade loading ratio: unavailable
- Shadow relay modeling readiness: blocked
- Blocking reason: `Total MVA Rating lacks verified continuous thermal / protection-grade semantics`

## Exact source

The field is traced to each TLine's XML `MVA` parameter in
`3IBR_DFIG1_TRIAL.pscx`; PSCAD generation writes it into each generated
`E_*.tli` file as `Total MVA Rating = 100.0`.

No local evidence was found that this uniform value is an independently
verified per-line continuous thermal limit. No generated runtime code path was
found that uses this field for thermal timing, warning, relay comparison,
limiting, breaker command, or branch trip.

## Sanity check

- Pre-fault index > 1: 25 lines
- Pre-fault index > 2: 17 lines
- Pre-fault index > 5: 2 lines

The P/Q -> S -> 100 MVA conversion chain still stands as a normalized response
index because P/Q were already audited as per-unit signals on a 100 MVA system
base. It does not stand as a protection-grade overload ratio.

## Stage-five correction

Earlier stage-five numeric files are retained for traceability, but their
interpretation is corrected. `E_28_29_1` may currently be called the highest
normalized apparent-power response line, not a future shadow-overload candidate.

## Stage-six thermal-limit recovery result

Stage six recovered exact branch identity mapping from the current PSCAD TLines
to the PNNL 3IBR RAW network branch table, but did not recover usable continuous
thermal limits: all mapped current-network branch RATE fields are zero.  The
safe quantity remains the `100-MVA-normalized apparent-power response index`;
`protection-grade loading ratio` remains unavailable, and shadow relay modeling
remains blocked.
