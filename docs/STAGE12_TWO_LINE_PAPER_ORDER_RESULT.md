# Stage 12 two-line paper-order result

## Result

- Final class: `stage12_two_line_paper_order_pass`
- Selected second line: `E_26_29_1`
- Paper target status: `paper_event_order_proxy`
- Capacity status: paper-calibrated effective capacity, not a recovered PNNL thermal rating.
- PAPER_CHAIN model monitor: waived by user; chronology is reconstructed offline from runtime channels.

## Frozen OVL2 parameters

| Quantity | Value |
|---|---:|
| pre-first-trip max raw S | 18.6638061611 |
| post-first-trip 5 s floor raw S | 21.5145147339 |
| threshold T | 20.0891604475 |
| paper-calibrated effective capacity | 18.2628731341 |
| threshold multiplier | 1.1 |
| definite delay | 5.0 s |

## Runtime chronology

| Event | Time (s) |
|---|---:|
| Fault applied | 0.50 |
| DFIG actual breaker open | 2.44 |
| DFIG source availability lost | 2.44 |
| Fault cleared | 2.50 |
| PAPER_OVL1 pickup | 2.53 |
| PAPER_OVL1 actual open | 7.53 |
| PAPER_OVL2 pickup | 7.60 |
| PAPER_OVL2 timer done | 12.60 |
| PAPER_OVL2 actual open | 12.60 |

Offline chronology:

- evented source count: `3`
- first event time: `2.44`
- second event time: `7.53`
- third event time: `12.6`
- order class code: `4`
- chronology consistent: `True`
- first-to-second gap: `5.09` s
- second-to-third gap: `5.069999999999999` s

## Network response boundary

The CSV files report raw P/Q-derived response trends only. They do not assert real overload, real thermal rating violation, third trip, natural cascade completion, or protection coordination.

Top late-window observation candidates are recorded in `data/derived/stage12_late_network_response.csv`.
