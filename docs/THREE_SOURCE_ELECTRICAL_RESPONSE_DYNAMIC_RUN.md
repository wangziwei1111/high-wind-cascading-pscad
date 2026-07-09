# Three-source controlled electrical-response dynamic Run

## Result

`electrical_response_observability_status = pass`.

Exactly one approved PSCAD Run was performed. The existing DFIG event and the
independently enabled IBR2/IBR3 trial-only opening stimuli produced three
parseable event records and nine parseable V/P/Q traces. IBR3 `OPEN_TIME_S`
was temporarily set to 4.5 s to retain its post-event window. After parsing,
both trial enables were restored to 0, IBR3 `OPEN_TIME_S` was restored to
5.0 s, and the trial was rebuilt without another Run.

## Event record

| Source | First-event time (s) | Cause | Request | Command | Actual open | Event valid |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| DFIG (A) | 2.016030 | 2 | existing event | existing path | 2.02 | 2.02 |
| IBR2_TRIAL (B) | 4.000005 | 4 | 4.00 | 4.00 | 4.00 | 4.01 |
| IBR3_TRIAL (C) | 4.500000 | 5 | 4.50 | 4.50 | 4.50 | 4.50 |

The collector reported three evented and three timed sources with cause codes
2/4/5. Chronology reported A < B < C, first-source code 1, order-class code 4,
and consistency 1.

## Recorded electrical trajectory metrics

The table below shows the monitored source corresponding to each event. Values
retain the original signal scale; no pu, MW, or Mvar unit is asserted.

| Event/source | Quantity | Pre mean | Early-post mean | Late-post mean | Early minus pre | Late minus pre | Maximum post deviation |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| A / DFIG | V | 0.970950 | 0.319721 | 0.960157 | -0.651229 | -0.010793 | 0.917313 |
| A / DFIG | P | 202.296781 | -104.329935 | -1.046078 | -306.626715 | -203.342859 | 360.549938 |
| A / DFIG | Q | 12.125804 | -17.453175 | -0.333873 | -29.578978 | -12.459676 | 211.705766 |
| B / IBR2 | V | 1.103751 | 5.611758 | 5.309723 | 4.508007 | 4.205972 | 4.652582 |
| B / IBR2 | P | 40.557566 | 0.659545 | 0.000013 | -39.898020 | -40.557552 | 40.557557 |
| B / IBR2 | Q | -9.093944 | 0.187382 | 0.000001 | 9.281326 | 9.093945 | 10.615564 |
| C / IBR3 | V | 1.121596 | 5.738605 | 5.456139 | 4.617009 | 4.334543 | 4.711797 |
| C / IBR3 | P | 52.229415 | 2.051476 | 0.000021 | -50.177939 | -52.229394 | 52.229406 |
| C / IBR3 | Q | -11.324974 | -0.562975 | -0.000002 | 10.761999 | 11.324972 | 11.324975 |

All 27 event-by-channel combinations are preserved in
`data/validation/three_source_electrical_response_metrics.csv`. Every
combination has non-empty pre `[t-0.20,t-0.02]`, early-post
`[t+0.02,t+0.20]`, and late-post `[t+0.22,t+0.45]` windows.

## Integrity and restoration

- Main project SHA-256 remained
  `CBA120BB167CB7FA6C4A1AE4471268850AB61761EC1877EB7B87015627FE9DAB`.
- Output Channel count remained 262, including all nine monitor-only channels.
- Final IBR2/IBR3 test enables are 0.
- Final IBR2 opening time is 4.0 s; final IBR3 `OPEN_TIME_S` is 5.0 s.
- Restore Build completed with zero reported errors and no subsequent Run.

## Claim boundary

These are recorded electrical trajectory metrics around explicitly controlled
event times. This Run does not validate natural cascade propagation, physical
causality direction, system stability, protection coordination, voltage
support performance, MATLAB coupling, or general applicability.

