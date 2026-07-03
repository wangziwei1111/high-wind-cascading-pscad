# Stage 13 next paper-aligned mechanism decision

Selected next path: `extend_runtime_before_third_line_path`

Confidence: `medium`

No PSCAD model change, Build, or Run was performed in Stage 13.

Boundary: this is a path freeze only, not a third-trip or UFLS/UVLS validation.

## Why this path is selected

The paper evidence supports later-stage overloaded-line protection, wind/source loss, UFLS/UVLS, generator protection and topology/islanding consequences as possible cascade mechanisms. In the current Stage-12 runtime, the only mechanism with a direct, model-consistent post-second-trip trace is the TLine raw P/Q-derived stress ranking.

`E_9_39_1` is the strongest candidate after `E_26_29_1` opens, but the existing 20 s runtime does not contain a defensible 5 s continuous high-stress interval after the second trip. Therefore the next paper-aligned step is not to add a third relay immediately; it is to extend/inspect runtime evidence before authorizing a third physical line-protection model.

## Why other paths are rejected now

- `third_line_protection_path`: rejected for immediate modeling because the candidate is not yet `third_line_candidate_ready`.
- `ufls_uvls_observability_first_path`: not selected as the next mechanism because current line-risk evidence is stronger; UFLS/UVLS still lacks direct system-frequency and network-wide voltage observability.
- `generator_protection_observability_first_path`: rejected because conventional-generator protection precursors are not directly observed.
- `topology_partition_consequence_path`: rejected because compiled topology plus breaker states indicate `connected_after_second_trip`.
- `no_defensible_post_second_trip_escalation`: rejected because W4 raw P/Q-derived stress does rise in a separable way for several candidate lines.

## Next-stage modeling implication

No new physical PSCAD model is justified by Stage 13 itself. The next stage should first obtain enough runtime evidence to decide whether a third line protection should be physically modeled. If that later evidence satisfies the sustained-window criterion, only then should a third relay/breaker be introduced.
