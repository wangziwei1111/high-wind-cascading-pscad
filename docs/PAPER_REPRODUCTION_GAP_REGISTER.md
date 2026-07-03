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

褰撳墠涓夋潵婧愬彈鎺ф椂搴忎笌 V/P/Q Run 灞炰簬鍩虹璁炬柦楠岃瘉鍜岃褰曟€у姩鎬佽瘉鎹紝涓嶆瀯鎴?
璁烘枃鐨勮嚜鐒惰繛閿佹晠闅滃鐜般€傚悗缁『搴忓繀椤荤敱鍘熸枃鐨勬晠闅溾€斾繚鎶も€旂綉缁滈噸鍒嗗竷鈥斿悗缁?
淇濇姢閾炬潯鍐冲畾銆?

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

## Paper-aligned 20 s baseline fault static configuration addendum

G02 is no longer an unconfigured static fault gap. The trial project now reuses
the existing `master:tfaultn` component and statically configures it as the
paper-aligned baseline disturbance: three-phase fault at the structurally
aligned P3 `N29` target, `TF=0.50 s`, `DF=2.00 s`, clearing at `2.50 s`.
Build-generated `P3.dta` confirms N29 phase-to-ground fault branches, and
`P3.f` confirms the timing logic.

G09 is also no longer contradicted at the static project-setting level because
`Duration of Run` is now 20 s. It remains dynamically unvalidated: no Run was
performed in this stage, and no paper cascade outcome, load shedding, line
overload, generator protection, or mitigation-performance claim is permitted.

## Paper-aligned 20 s dynamic Run addendum

G03 has advanced from static construction to raw dynamic observability. The
single approved 20 s Run was parsed offline, and all 31 network TLines have
usable terminal A/B P/Q/I window metrics. This provides evidence for raw
network-wide branch response observation only.

G04 and G05 remain open. No line loading ratio, inverse-time overload relay,
line breaker command, or transmission-line trip mechanism exists. The dynamic
Run therefore cannot be cited as overload validation, branch-trip validation,
natural cascade propagation, or strict thesis reproduction.

## Full-network TLine rating/loading addendum

G03 now has offline loading-ratio evidence for all 31 current-model TLines,
using exact generated `.tli` `Total MVA Rating` records and the existing
stage-four 20 s Run. This closes the rating-basis part of the raw observability
gap for the current PSCAD adaptation.

G04 remains open because no overload relay, inverse-time delay, thermal memory,
or trip criterion exists. G05 remains open because no transmission-line breaker
command or line-opening boundary has been implemented. Ratio-above-one
observations are therefore not overload proof and not line-protection evidence.

## Stage-five-B semantic correction

The later TLine Total MVA semantic audit reclassified the uniform `100.0 MVA`
field as `uniform_model_value_or_default_parameter`, not a verified continuous
thermal or protection-grade rating. Therefore previous S/100 MVA values must be
read as a `100-MVA-normalized apparent-power response index`, not an overload
ratio. `E_28_29_1` remains only the highest normalized apparent-power response
line. Shadow overload relay modeling is blocked until auditable per-line
continuous thermal limits, or a reproducible paper-to-current-model rating
mapping, are available.

## Stage-six thermal-limit recovery result

Stage six recovered exact branch identity mapping from the current PSCAD TLines
to the PNNL 3IBR RAW network branch table, but did not recover usable continuous
thermal limits: all mapped current-network branch RATE fields are zero.  The
safe quantity remains the `100-MVA-normalized apparent-power response index`;
`protection-grade loading ratio` remains unavailable, and shadow relay modeling
remains blocked.

## Stage seven paper-calibrated equivalent first-trip attempt

Status: `paper_calibrated_first_trip_parser_fallback`.  Selected line `E_28_29_1` with equivalent capacity `7.872883989661206` and 1.1 + 5 s fallback logic. Generated code confirms the trial relay/breaker chain, but runtime PGB waveforms were unavailable; therefore no dynamic flow-driven trip or actual breaker-open causality is claimed.

## Stage eight runtime observability and dynamic result

Runtime Output Channel observability passed: all 13 canonical `PAPER_OVL1_*` channels are readable over 0-20 s. Dynamic classification is `stage8_pre_fault_false_trip`: `ABOVE_THRESHOLD` never asserted, while timer, trip request, breaker command, and open state were present at t=0. Flow-driven first-trip causality is not proven, no post-trip redistribution ranking is valid, and strict reproduction remains `not_achieved`.
## Stage nine short-run initialization repair and first trip

Status: `stage9_short_run_flow_driven_first_trip_pass`. The 9.0 s Run has healthy pre-fault initialization and records the equivalent E_28_29_1 threshold-to-timer-to-breaker first-trip chain. This remains a paper-calibrated equivalent protection result, not a verified PNNL thermal rating, real protection setting, second trip, or natural cascade. Strict reproduction remains `not_achieved`.
## Stage 10A DFIG event consistency and paper sequence

Status: `stage10_read_only_audit_complete_dfig_actual_no_trip_in_stage9`. Stage 4 contains a physical DFIG opening and matching event packet at 2.43 s; Stage 9 contains neither before the E_28_29_1 opening at 7.51 s. The channels are present and readable, so this is not an observability/parser failure. The verified signal-level cause is that Stage-9 fault-period VIBR1_2 stayed above the unchanged 0.9 duration-LVRT threshold. Stage 9 validates only the flow-driven E_28_29_1 protection subchain. Until a physical DFIG event precedes the first line trip, it is not a complete paper-style accident-chain reproduction.
## Stage 10B fault-to-DFIG static fallback

Decision: `no_defensible_electrical_difference_found`. XML geometry alone suggested a gap, but generated `P3.dta` proves the Stage-9 breaker and fault remain on the compiled `N29(1..3)` boundary. No permitted single interface repair is defensible, so GUI, Build, and Run are blocked. Strict reproduction remains `not_achieved`.
## Stage 10C compiled network and initial-state audit

Classification: `E_evidence_insufficient_to_identify_defensible_model_change`. The compiled N29 boundary and frozen DFIG breaker stamps match; PAPER breaker RON is non-dominant. Runtime evidence nevertheless shows an approximately 51% pre-fault E_28_29_1 P/I difference while DFIG V/P/Q remain close. This is a real initial-operating-point discrepancy, but available artifacts do not identify its unique model cause. No model edit, Build, or Run is authorized; trial-and-error tuning would weaken reproduction credibility.
