# Full-network TLine dual-end P/Q/I measurement layer

## Scope

This stage adds a monitor-only, native PSCAD measurement layer for every genuine
network-level transmission `TLine` in the `3IBR_DFIG1_TRIAL.pscx` trial project.
It covers the full P3 network inventory, not a preselected subset of likely
overload candidates.

The implemented observability is terminal A/B real power, reactive power, and
RMS current: six scalar Output Channels per included TLine.

This stage does not implement line loading ratio, overload detection,
inverse-time protection, line tripping, breaker commands, control feedback,
automatic reclosing, SVC, STATCOM, MATLAB coupling, or any fourth/virtual
source. No PSCAD Run was performed.

## Static audit result

| Item | Result |
| --- | --- |
| Main project SHA | `CBA120BB167CB7FA6C4A1AE4471268850AB61761EC1877EB7B87015627FE9DAB` |
| Trial project final SHA | `A9DC610D20C61022CDE2F2D73612C12499FB7E5D29C43562BA08D9D89EADF360` |
| Included genuine network TLines | 31 |
| Native meters | 62 |
| New TLine Output Channels | 186 |
| Existing Output Channels preserved | 262 |
| Final XML Output Channels | 448 |
| Generated map PGBS | 624, including vector-channel expansion |
| Run status | `not_performed` |

Primary evidence:

- `data/reference/full_network_tline_inventory.csv`
- `data/reference/native_tline_measurement_component_assessment.csv`
- `data/reference/full_network_tline_measurement_design.json`
- `data/validation/full_network_tline_measurement_final_audit.json`
- `data/validation/full_network_tline_measurement_channel_trace.csv`
- `data/validation/full_network_tline_measurement_semantic_trace.csv`
- `data/validation/full_network_tline_measurement_coverage_matrix.csv`

## Native component and semantics

The measurement layer uses PSCAD 4.6 `master:multimeter`, qualified from the
installed Master Library. For each TLine end, one native meter is inserted at
the physical line boundary.

The configured signal outputs are:

- `P`: three-phase real power;
- `Q`: three-phase reactive power;
- `Crms`: three-phase RMS current magnitude.

P and Q are p.u. on the 100 MVA base. The current output is numerically in kA
because `BaseA = 1.0 [kA]`. P/Q sign follows the native meter orientation:
positive from meter terminal A toward meter terminal B. Current is a
non-negative RMS magnitude.

## Channel naming rule

For branch `E_x_y_1`, the six monitor-only Output Channels are:

```text
E_x_y_1_A_P
E_x_y_1_A_Q
E_x_y_1_A_I
E_x_y_1_B_P
E_x_y_1_B_Q
E_x_y_1_B_I
```

The final trace CSVs provide every branch-to-channel-to-Fortran mapping.

## Paper-alignment boundary

This stage closes the previous raw branch-observability gap for full-network
P/Q/I monitoring. It does not validate power-flow redistribution, loading
ratio, overload status, line protection, line trips, natural cascade
propagation, physical causality, stability, protection coordination, voltage
support performance, or MATLAB coupling.

Future loading ratio and overload-candidate screening must be performed only
after a dedicated dynamic Run, using the audited raw dual-end P/Q/I channels
and separately audited line-capacity evidence. No loading or protection logic
was added inside PSCAD in this stage.
