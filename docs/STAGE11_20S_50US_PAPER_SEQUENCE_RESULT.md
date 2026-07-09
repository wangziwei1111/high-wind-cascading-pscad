# Stage 11 20 s / 50 us paper-like sequence validation

## Result

- Final class: `stage11_20s_50us_paper_order_first_trip_pass`
- Runtime output status: `stage11_20s_50us_runtime_outputs_detected`
- Fault window: `0.50 s` to `2.50 s`
- Observed time span: `0.00 s` to `20.00 s`, plot step `0.01 s`
- Claim boundary: this is a 50 us numerical run. It verifies this configuration's event order, not equivalence to a separate 5 us run.

## Event chronology

| Event | Time (s) |
|---|---:|
| Fault applied | 0.50 |
| Fault cleared | 2.50 |
| DFIG LVRT trip / breaker open | 2.44 |
| DFIG source availability lost | 2.44 |
| E_28_29_1 loading index first >= 1.1 | 2.53 |
| PAPER_OVL1 5 s timer done | 7.53 |
| PAPER_OVL1 breaker open | 7.53 |

The pre-fault interval is explicitly `0.00 <= t < 0.50 s`; DFIG trip latch, command, breaker state, and cascade event valid all remain zero there, while source availability remains one.

## Network response boundary

The TLine response CSV files report raw P/Q/I-derived trends only. No thermal rating or relay claim is made from those raw trends in this stage.
