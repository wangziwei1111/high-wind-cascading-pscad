# Stage 9 short-run initialization repair and first-trip result

Generated: 2026-07-03T18:05:11

## Result

- Classification: `stage9_short_run_flow_driven_first_trip_pass`
- Runtime: one `9.0 s` Run, `0.01 s` plot step, 13/13 PAPER_OVL1 channels readable
- t=0: ABOVE/TIMER/TRIP/BRK_CMD/BRK_STATE = `0/0/0/0/0`
- Pre-fault maximum loading index: `0.68318585709206`; false trip: `False`
- Threshold and timer accumulation start: `2.51 s`
- Timer completion / trip request / breaker command / actual open: `7.51 / 7.51 / 7.51 / 7.51 s`
- Continuous delay to completion: `5.0 s`
- DFIG cascade event in this 9 s runtime: `None` (not observed)

The command and breaker state change share the same 0.01 s output sample. Generated code establishes command-to-breaker dependence, so causality passes at output resolution.

## Top-10 post-trip high-stress response trends

1. `E_26_28_1`: delta raw S `-21.4245`, delta I `-2.03622`
2. `E_26_27_1`: delta raw S `-9.62617`, delta I `-1.3674`
3. `E_16_17_1`: delta raw S `-7.99614`, delta I `-1.31567`
4. `E_17_27_1`: delta raw S `-7.14032`, delta I `-1.09955`
5. `E_2_25_1`: delta raw S `-5.23338`, delta I `-0.782566`
6. `E_16_19_1`: delta raw S `-3.76753`, delta I `-0.646954`
7. `E_3_4_1`: delta raw S `-2.83852`, delta I `-0.470376`
8. `E_16_21_1`: delta raw S `-2.18025`, delta I `-0.388605`
9. `E_8_9_1`: delta raw S `1.96116`, delta I `0.303581`
10. `E_2_3_1`: delta raw S `1.91486`, delta I `0.317734`

These are raw post-trip response trends only, not verified overloads or second-trip candidates.

## Claim boundary

This Stage-9 result validates a trial-only, paper-calibrated equivalent first-trip chain. It does not establish PNNL continuous thermal capacity, real overload or protection settings/coordination, a second trip, natural cascading, or strict paper reproduction.
