# Branch raw measurements for the paper-aligned cascade path

## Result

`execution_status = branch_raw_measurements_static_fallback`.

The read-only preflight traced four genuine transmission-line candidates:

- `E_2_3_1`, N2-N3
- `E_1_2_1`, N1-N2
- `E_2_25_1`, N2-N25
- `E_16_19_1`, N16-N19

The first three are incident on N2, which receives the DFIG GBUS30 path through
transformer `E_2_30_1`. The fourth is the first overloaded line named in thesis
Table 2-2.

None of these TLine objects exposes an existing, semantically confirmed P/Q/I
transfer-signal path. Their row definitions contain line-constant components
only. The nearby `PL16` signal is explicitly excluded: it belongs to the
`E_16_0_1` load-branch multimeter, enables P only, and is not a measurement of
transmission line `E_16_19_1`.

Because this stage forbids adding meters, calculation blocks, modules, or line
parameter changes, no PSCAD GUI stage was authorized. No Output Channel was
added and the existing count remains 262.

## Scope boundary

This task did not add raw transmission-line P/Q/I observability. It did not
calculate loading ratio in PSCAD, add overload criteria, add inverse-time
protection, connect line breakers, Build, or Run.

Future loading ratio may be calculated offline only after raw P/Q/I signals,
measurement terminal, units, and rating semantics are independently audited:

```text
loading_ratio_i = abs(I_measured) / I_limit
loading_ratio_s = sqrt(P_measured^2 + Q_measured^2) / S_limit
```

Power-flow redistribution, changing line loading, satisfaction of the paper's
overload condition, line protection action, line trip, natural cascade,
physical causality, stability, and protection coordination remain unavailable.

## Safe resolution

A future task must explicitly authorize minimal inline branch meters (still no
Page Module), or identify an authoritative native TLine measurement interface.
Only after two real lines have confirmed P/Q/I semantics may the original
`branch observability only` stage proceed.
