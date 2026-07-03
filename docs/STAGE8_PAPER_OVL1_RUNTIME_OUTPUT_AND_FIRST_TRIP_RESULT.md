# Stage 8 PAPER_OVL1 runtime output and first-trip result

Generated: 2026-07-03T17:03:43

## Result

- Classification: `stage8_pre_fault_false_trip`
- Runtime output repair: **pass** (`.inf` present, 64 numbered `.out` files, 13/13 canonical channels readable)
- Time axis: `0.0` to `20.0` s at `0.01` s
- Main project SHA unchanged: `True`

## Dynamic evidence

`PAPER_OVL1_ABOVE_THRESHOLD` never asserted and the maximum pre-fault loading index was only
`0.033318204657287`. Nevertheless, `TIMER_STATE`, `TRIP_REQUEST`, and
`BRK_CMD` were already asserted at `t=0`, and `BRK_STATE=2` (open) was present at the first
sample. Therefore there is no valid threshold -> timer -> trip -> breaker transition to rank.

Generated-code evidence agrees with the waveform: timer output `RT_18` drives the latch set
input, latch Q is exported as `TRIP_REQ`, and the observed timer output starts high. This is a
pre-fault false trip, not a flow-driven first trip. No second Run is requested.

## Claim boundary

Stage 8 proves runtime Output Channel observability only. It does not prove flow-driven protection: the timer/latch/command chain is asserted at t=0 while ABOVE_THRESHOLD remains zero. The capacity is paper-calibrated equivalent capacity, not a PNNL continuous thermal rating or real protection setting.

This result does not validate real line thermal capacity, real protection settings or
coordination, a second trip, natural cascading propagation, stability, UFLS/UVLS, conventional
generator protection, MATLAB coupling, SVC/STATCOM, or strict paper reproduction.
