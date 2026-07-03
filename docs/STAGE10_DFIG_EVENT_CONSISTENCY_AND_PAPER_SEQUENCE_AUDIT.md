# Stage 10A DFIG event consistency and paper-sequence audit

Generated: 2026-07-03T18:28:12

## Outcome

This was a strictly read-only, zero-Build, zero-Run, zero-GUI audit. Stage 4 contains a real DFIG breaker opening and a matching event packet at the 0.01 s output resolution. Stage 9 contains neither: all required channels are present and readable, but remain inactive. Therefore the answer is **B: the DFIG actually did not trip in Stage 9**.

The decisive mechanism is the unchanged LVRT duration input. During the 0.50-2.50 s fault window, Stage-4 `VIBR1_2` fell to `0.852549674` and the duration trigger asserted at `2.43 s`; Stage-9 `VIBR1_2` stayed at or above `0.910510719`, above the `0.9` low-voltage threshold, so its duration trigger, trip latch, breaker state, availability transition, and event packet all correctly remained inactive.

## Locked runtime sources

| Run | Runtime source | Samples / horizon / plot step | Trial SHA |
|---|---|---|---|
| Stage 4 | `C:\pscad_work\pnnl_39_3ibr_pscad46_strip5\_backups\stage7_before_paper_calibrated_first_trip\PSCAD` | 2001 / 20.0 s / 0.01 s | `F81959EA62211FF9C1536C8481B67675AFE4DDCC3C56E804D048731A4B88A300` |
| Stage 9 | `C:\pscad_work\pnnl_39_3ibr_pscad46_strip5\PSCAD\3IBR_DFIG1_TRIAL.gf46` | 901 / 9.0 s / 0.01 s | `F2A3C1012D8261805C03F688CCC2E8BFBCE68A80D1ACC352CAFA666B149744A0` |

## DFIG dynamic comparison (raw recorded units)

| Window | Run | V min/mean/max | P min/mean/max | Q min/mean/max |
|---|---|---|---|---|
| pre_fault | stage4 | 7.90159e-05 / 0.880286 / 1.01371 | -21.808 / -2.51569 / -6.1759e-06 | -0.0418478 / 25.951 / 37.6078 |
| pre_fault | stage9 | 7.90159e-05 / 0.877521 / 1.01073 | -21.8981 / -2.5084 / -6.1759e-06 | -0.0404047 / 25.7963 / 37.3828 |
| fault | stage4 | 0.85255 / 0.863935 / 1.00369 | -9.30955 / 151.147 / 203.239 | -40.5207 / -16.5678 / 48.9641 |
| fault | stage9 | 0.910511 / 0.940002 / 1.00079 | -30.7758 / 157.884 / 202.746 | -44.668 / 56.1869 / 73.9473 |
| post_fault_short | stage4 | 0.694335 / 0.935688 / 1.21613 | -2.66744 / 0.110375 / 7.16518 | -6.02653 / 0.000838316 / 7.80912 |
| post_fault_short | stage9 | 0.76258 / 0.956035 / 1.1907 | 177.155 / 198.685 / 213.58 | 44.9952 / 62.2794 / 88.1194 |
| pre_first_trip_redistribution | stage4 | 0.726724 / 0.956006 / 1.19171 | -0.000939334 / -0.000452961 / -0.000109274 | -0.000261057 / -6.57233e-08 / 0.000262586 |
| pre_first_trip_redistribution | stage9 | 0.781859 / 0.979067 / 1.19959 | 180.971 / 199.165 / 215.361 | 43.3257 / 60.3874 / 73.8745 |


The `.inf` unit fields for these channels are blank; the values above are therefore reported only as raw PSCAD recorded values, not relabelled as MW, Mvar, or p.u.

## Paper-event-order comparison

| Paper mechanism link | Stage 4 evidence | Stage 9 evidence | Pass | Sequence consistent | Minimum allowed next change |
|---|---|---|---|---|---|
| N29 three-phase fault | 0.50-2.50 s | 0.50-2.50 s | yes | yes | none |
| Physical DFIG LVRT/source loss | breaker/event/availability at 2.43 s | no breaker or availability transition | no | no | align fault-to-DFIG physical interface |
| Power-flow redistribution after DFIG loss | DFIG P/Q collapses after 2.43 s | DFIG P/Q remains substantial | no | no | same as above |
| First-line flow-driven protection | not present in this older baseline | threshold 2.51 s; actual open 7.51 s | subchain only | no, because DFIG did not precede it | preserve relay; do not time-force it |
| Initial post-open response | not applicable | observed after 7.51 s | yes for subchain | no for full paper chain | none beyond upstream alignment |

## Decision

- Sequence class: `dfig_not_observed_before_first_trip`.
- Root-cause class: `B_actual_no_trip_due_verified_lvrt_input_difference`.
- This is not missing output, parser failure, or event-packet mismatch.
- Fault component and DFIG LVRT/breaker settings are unchanged. The relevant verified model boundary difference is the later PAPER breaker/relay topology on `E_28_29_1`; the signal-level proof is conclusive, while exact attribution of the upstream voltage-transfer change remains bounded to `fault_to_dfig_interface_alignment` until that interface is statically aligned.
- Next unique Run duration: `9.0 s`, because the expected first-line opening is about `7.51 s`, leaving `1.49 s` of post-open observation.
- No synthetic event, fixed-time DFIG trip, fixed-time line trip, or packet-only repair is permitted.

The Stage-9 first-line protection subchain is validated, but it must not be described as a complete paper-style accident-chain reproduction until a physical DFIG event is proven to precede it.
