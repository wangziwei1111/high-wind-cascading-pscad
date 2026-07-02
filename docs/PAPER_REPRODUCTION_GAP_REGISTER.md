# Paper reproduction gap register

| gap_id | paper requirement | current gap | risk if ignored | required evidence | recommended stage | not-yet-permitted claim |
| --- | --- | --- | --- | --- | --- | --- |
| G01 | IEEE39 buses 33/35/38 wind replacement | No one-to-one topology/source correspondence | False strict-reproduction claim | Branch/bus/source map and ratings | topology trace | strict topology reproduction |
| G02 | Bus-29 three-phase benchmark fault | Current fault is not traced to bus 29 | Wrong scenario identity | Target electrical boundary and timing | after observability | paper baseline reproduced |
| G03 | Flow redistribution after source trip | No audited branch P/Q/I/loading set | Causal bridge cannot be observed | Real-line measurements and signal semantics | branch observability only | network redistribution validated |
| G04 | Inverse-time overload protection | No real-line input or relay | Relay would be disconnected from evidence | E003 transcription plus G03 | future shadow relay | line protection validated |
| G05 | Transmission-line opening | No audited target-line breaker boundary | Unsafe premature actuation | Target-line breaker state and rollback | after shadow validation | line-trip cascade reproduced |
| G06 | UFLS/UVLS | No audited frequency/load-shed interfaces | Load behavior could be misclassified | Frequency, load and shed-state channels | deferred shadow monitors | load shedding validated |
| G07 | Conventional generator protection | No audited paper-threshold trip path | Generator dynamics may be mistaken for protection | Terminal V/f and shadow criteria | deferred | generator protection validated |
| G08 | Temporary-overvoltage line action | No 1.3 p.u. no-delay path | DFIG voltage logic could be misused | Target-bus voltage and related-line mapping | deferred | TOV protection validated |
| G09 | 20 s scenario and parameter sweeps | Current evidence uses fixed 5 s interface scenarios | Results are not comparable to paper tables | Completed mechanisms and scenario manifest | final integration | paper scenario matrix reproduced |
| G10 | SVC/STATCOM mitigation | Devices absent; unmitigated chain incomplete | Mitigation could hide missing mechanism | Baseline chain plus device/controller provenance | last | voltage-support performance validated |

当前三来源受控时序与 V/P/Q Run 属于基础设施验证和记录性动态证据，不构成
论文的自然连锁故障复现。后续顺序必须由原文的故障—保护—网络重分布—后续
保护链条决定。

## Stage-two preflight addendum

G03 remains open. Four genuine TLines were traced, but no eligible branch had
an existing P/Q/I transfer-signal path. `PL16` was rejected because it measures
load branch `E_16_0_1`, not transmission line `E_16_19_1`, and has no Q/I
outputs. No model capability or reproduction-fidelity level changed.

## Full-network TLine P/Q/I observability implementation addendum

G03 is no longer a raw-observability construction gap. The trial project now
contains statically audited dual-end P/Q/I monitor-only outputs for all 31
genuine network `TLine` instances. The remaining G03 boundary is dynamic:
power-flow redistribution, loading ratio, overload candidate screening, and
causal propagation are still unavailable until a future Run and offline
analysis use the audited raw channels.

G04 and G05 remain open. No overload relay, inverse-time logic, breaker
command, or transmission-line trip mechanism was added in this stage.
