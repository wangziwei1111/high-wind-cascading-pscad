# Stage 13 post-second-trip state diagnosis

No PSCAD model change, Build, or Run was performed. Stage 12 runtime outputs were used as the authoritative input.

## Runtime input

- Source run: Stage 12 unique 20 s / 50 us run.
- Runtime time axis: 0.00 to 20.00 s, 2001 samples, 0.01 s plot step.
- Event sequence used as fixed input: N29 fault 0.50 to 2.50 s, DFIG open 2.44 s, PAPER_OVL1 open 7.53 s, PAPER_OVL2 open 12.60 s.
- The Stage-12 `PAPER_CHAIN_MODEL_MONITOR_WAIVED_OFFLINE_PARSER` waiver is accepted; chronology is reconstructed in the backend from existing breaker-state/event channels.

## Main findings

- Top line-risk candidate after the second trip: `E_9_39_1` with `third_line_candidate_requires_longer_run`.
- Frequency status: `frequency_risk_not_observed`.
- Voltage status: `local_voltage_response_only`.
- Source/generator status: DFIG disconnect is directly observed; other source/generator mechanisms are not directly observed.
- Topology status after removing `E_28_29_1` and `E_26_29_1`: `connected_after_second_trip`.

All line-risk values are raw P/Q-derived response metrics, not real loading or thermal overload.

## Line-risk interpretation

The strongest post-second-trip raw P/Q-derived candidate is `E_9_39_1`.
Its W4 mean rises above W3, so the post-second-trip line-risk direction is real enough to preserve.
However, the audited continuous high-stress span in the existing 20 s run is shorter than the 5.0 s protection-delay criterion, so Stage 13 does not authorize a third physical relay/breaker yet.

This is why the candidate class is:

```text
third_line_candidate_requires_longer_run
```

not:

```text
third_line_candidate_ready
```

## Frequency, voltage, source and topology boundaries

- Frequency: no direct system-frequency observable is available with enough semantic certainty to claim UFLS or conventional generator under-frequency protection.
- Voltage: available voltage observables are local/wind-PCC/generator-terminal style channels, not network-wide low-voltage coverage.
- Source/generator status: DFIG disconnection is directly observed; other wind-farm trips, synchronous-generator trips and conventional generator protection are not directly observed.
- Topology: compiled topology plus actual breaker state remains connected after the two line trips; no islanding consequence path is justified from Stage 12 alone.
