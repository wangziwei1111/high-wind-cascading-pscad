# Model vs backend observability policy

Any content used only for event ordering, risk ranking, protection-timer audit,
post-run candidate screening, topology post-processing, result presentation, or
paper-alignment reporting must be implemented first as backend parsing.

It must not be added to PSCAD as a new model, monitor, event packet, timer,
Output Channel, or GUI object unless it is necessary to change the electrical
network state or to create a physical causal path that cannot be recovered from
existing runtime outputs.

PSCAD model changes are reserved for mechanisms that materially affect the
simulation, such as relay-driven breaker openings, load shedding, generator
protection, source disconnection, topology changes, or compensation devices.

The Stage-12 `PAPER_CHAIN_MODEL_MONITOR_WAIVED_OFFLINE_PARSER` decision follows
this rule: chronology is observational only, so it is reconstructed from
runtime breaker-state and event channels rather than added as another PSCAD
monitor.

Stage 15 keeps the same split. The three wind-farm LVRT modules and their
breakers are permitted because they create physical source-disconnection
causality. Chronology, first-trip classification, initial power-loss summaries,
and post-trip TLine rankings remain backend-only and must be reconstructed from
the 15 minimum runtime channels plus existing branch observability, not from a
new PSCAD chronology collector.
