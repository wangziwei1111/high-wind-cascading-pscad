# Stage 10C compiled-network and initial-state difference audit

## Result

Classification: `B_intended_PAPER_OVL1_closed_state_difference_quantified_but_not_proven_causal`. This was a zero-GUI, zero-Build, zero-Run, zero-model-change audit.

The local Stage-4 and Stage-9 compiled graphs preserve the same N29 fault boundary and the same BRK_DFIG stamp. Stage 9 intentionally adds the PAPER_OVL1 breaker between E_28_29_1 and N29. No wrong phase, ground, bypass, endpoint, or non-intended series/shunt element was located.

## Local compiled network and RON

- Stage 4 E_28_29_1 ends at N29 through its original compiled internal nodes.
- Stage 9 E_28_29_1 ends at N29 through PAPER internal nodes `NT_83/NT_84`; generated code stamps the closed breaker at `RON=0.001 ohm`.
- BRK_DFIG is identical in both generated files: `RON=0.001 ohm`, `ROFF=1e6 ohm`, branch offsets `+19..21`.
- Exact full local Y reconstruction is not defensible because `P3.map` is absent. However, `E_28_29_1.tli` explicitly states `RXB p.u./m`, length `0.001 m`, voltage `345 kV`, and base `100 MVA`.
- Reconstructed line R/X are `0.00166635/0.017972775 ohm`, with `|Z|=0.0180498577 ohm`. PAPER RON is `60.011%` of line R and `5.540%` of |Z|; it raises |Z| by `0.663%`.
- RON is therefore the unique quantified closed-state initialization candidate. Its direction is consistent with weaker coupling, but it is not yet proven to be the sole cause of the meshed-network flow and VIBR changes.

## Pre-fault state

DFIG pre-fault V/P/Q means differ by less than 1%, but E_28_29_1 P and I means differ by approximately 51%-52%, including in the 0.40-0.49 s settled pre-fault slice. This proves a different local operating point, not its cause. Adjacent E_26_29_1 and E_26_28_1 channels are included to support later source tracing. Values remain raw recorded units because `.inf` units are blank.

## Fault-period transfer

| Run | VIBR min | VIBR mean | cumulative VIBR < 0.9 | DFIG open |
|---|---:|---:|---:|---:|
| Stage 4 | 0.852549674 | 0.863934813 | 1.990 s | 2.43 s |
| Stage 9 | 0.910510719 | 0.940002 | 0.000 s | not observed |

N29 voltage itself is not a runtime channel. The audit can compare DFIG PCC `VIBR1_2` and adjacent branch responses, but cannot directly compare the N29 fault voltage. That missing transfer observation prevents attribution to a unique physical model difference.

## Decision

No model edit, Build, or additional Run is justified yet. RON is now traced as the only quantified closed-state candidate, but classification B requires separate breaker numerical-stability evidence and causal sensitivity evidence before changing it. Directly lowering RON now would still be trial-and-error tuning.

Validated: N29 fault -> real-flow E_28_29_1 protection -> 5 s timer -> physical line opening.

Not validated: N29 fault -> physical DFIG LVRT disconnect/source loss -> first line trip.

Stage 9 therefore remains a line-first-trip protection subchain. Until a future run proves a physical DFIG event before E_28_29_1 opening, it is not a complete paper-style accident chain. No real PNNL thermal capacity, real setting/coordination, second trip, natural cascade, or strict reproduction is claimed.
