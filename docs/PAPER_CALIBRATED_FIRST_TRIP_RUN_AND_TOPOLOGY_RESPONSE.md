# Paper-calibrated first-trip run and topology response

Generated: 2026-07-03T15:24:50

## Result

- Execution status: `paper_calibrated_first_trip_parser_fallback`
- Selected TLine: `E_28_29_1`
- Equivalent capacity: `7.872883989661206`
- Threshold multiplier: `1.1`
- Protection curve: `paper-inspired definite-time fallback`
- Delay: `5.0 s`

## What was verified

The generated PSCAD code contains the trial-only relay and breaker boundary:

- Relay subroutine generated: `True`
- Relay inputs use `E_28_29_1` dual-end P/Q signals: `True`
- Three-phase breaker generated: `True`
- Breaker uses `PAPER_OVL1_BRK_CMD`: `True`
- Breaker state signal generated: `True`

## Parser fallback boundary

The single user stage did not leave parsable PSCAD Output Channel runtime files:

`The run directory contains updated TLine Line Constants .out files, but no PSCAD Output Channel .inf or 3IBR_DFIG1_TRIAL_NN.out files for PGB waveform parsing.`

Therefore this audit does not claim that the full chain
real TLine P/Q -> loading index -> timer -> trip request -> breaker command -> actual breaker open
was dynamically observed.

## Claim boundary

This stage documents a trial-only paper-calibrated equivalent protection attempt. It does not represent PNNL real continuous thermal capacity or true protection-setting validation.

This stage is a paper-constrained equivalent-protection adaptation.  It does not verify
PNNL continuous thermal limits, true thermal overload, true protection settings,
protection coordination, a second line trip, natural cascading propagation,
UFLS/UVLS, conventional generator protection, MATLAB coupling, SVC/STATCOM, or strict
paper reproduction.
