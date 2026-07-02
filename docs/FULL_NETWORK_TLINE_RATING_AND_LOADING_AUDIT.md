# Full-network TLine rating basis and offline loading-ratio audit

## Scope

This stage is a pure offline analysis stage. It did not modify PSCAD, did not
Build, did not Run, did not add Output Channels, did not add meters, and did
not add relay, breaker, protection, control, or feedback logic.

The analysis reuses the existing stage-four 20 s N29 three-phase fault Run.

## Baseline and evidence sources

| item | result |
| --- | --- |
| Main model SHA | `CBA120BB167CB7FA6C4A1AE4471268850AB61761EC1877EB7B87015627FE9DAB` |
| Trial model SHA | `F81959EA62211FF9C1536C8481B67675AFE4DDCC3C56E804D048731A4B88A300` |
| Run reused | existing paper-aligned 20 s Run only |
| TLine inventory | 31 genuine network TLines |
| Raw TLine signals | 186 = 31 lines x A/B x P/Q/I |
| XML Output Channels | 448 |

The one-time baseline manifest is
`data/validation/tline_rating_loading_baseline_manifest.json`.

## Rating basis

All 31 TLine instances have generated PSCAD `.tli` files with exact line names
and:

- `Voltage Rating (kV L-L RMS) = 345.0`
- `Total MVA Rating = 100.0`

This stage qualifies these as apparent-power rating bases for the exact current
PSCAD TLine instances. The external RAW RATE fields for the network branches
are zero and are treated as unspecified, not as usable line ratings and not as
conflicting positive ratings.

| rating class | count |
| --- | ---: |
| qualified apparent-power rating | 31 |
| qualified current rating | 0 |
| insufficient rating basis | 0 |
| conflicting rating basis | 0 |

Because no exact continuous current limit was found, current-based loading was
not computed.

## Loading formula

The audited `master:multimeter` semantics give P/Q in p.u. on the 100 MVA
system base. Since each TLine `.tli` gives `Total MVA Rating = 100.0`, the
power-type limit is:

`S_limit_pu = 100 MVA / 100 MVA = 1.0`

For each sample:

`S_A(t) = sqrt(P_A(t)^2 + Q_A(t)^2)`

`S_B(t) = sqrt(P_B(t)^2 + Q_B(t)^2)`

`L_S(t) = max(S_A(t), S_B(t)) / 1.0`

This is an offline descriptive ratio. It is not an in-model protection signal.

## Top 10 post-clear loading candidates

Ranking priority is:

1. `post_clear_late_loading_max`
2. `post_clear_late_loading_mean`
3. `post_clear_early_loading_max`
4. `post_clear_early_loading_mean`

| rank | branch | post-clear late max | post-clear late mean | post-clear early max | post-clear early mean |
| ---: | --- | ---: | ---: | ---: | ---: |
| 1 | E_28_29_1 | 15.362954 | 12.944167 | 19.695969 | 16.450952 |
| 2 | E_16_17_1 | 15.288151 | 10.610411 | 14.891539 | 9.828690 |
| 3 | E_17_27_1 | 15.131367 | 11.541806 | 15.376205 | 11.552268 |
| 4 | E_2_25_1 | 14.938274 | 5.448964 | 13.109556 | 6.838769 |
| 5 | E_26_27_1 | 14.767174 | 11.872888 | 15.636231 | 11.468552 |
| 6 | E_26_28_1 | 14.008591 | 11.716418 | 17.800938 | 13.332810 |
| 7 | E_26_29_1 | 13.926571 | 12.018243 | 18.667519 | 15.257033 |
| 8 | E_25_26_1 | 13.779864 | 10.013738 | 14.955847 | 10.869841 |
| 9 | E_16_19_1 | 12.302170 | 8.410679 | 10.397884 | 6.288517 |
| 10 | E_1_2_1 | 11.791206 | 3.724368 | 6.987994 | 4.374317 |

All top-10 rows are `ratio-above-one observation` rows under the current
audited rating basis and formula. This does not prove thermal overload.

## E_16_19_1 special note

`E_16_19_1` exists in the current trial project as a genuine network TLine
between `N16` and `N19`. It has a qualified apparent-power rating basis from
`E_16_19_1.tli`:

- `Total MVA Rating = 100.0`
- `S_limit_pu = 1.0`

Its offline loading results are:

| window | value |
| --- | ---: |
| pre-fault loading mean | 5.204261 |
| pre-fault loading max | 5.216121 |
| fault-on loading max | 6.134021 |
| post-clear early loading mean | 6.288517 |
| post-clear early loading max | 10.397884 |
| post-clear late loading mean | 8.410679 |
| post-clear late loading max | 12.302170 |
| ranking | 9 |

The thesis discussion of `E_16_19_1` is relevant as a paper-alignment pointer,
but it cannot preselect or prove the current PSCAD candidate by itself. The
current model is an adaptation with its own generated TLine rating basis and
Run outputs, so candidate selection must follow the current audited data.

## Runtime non-TLine channel mapping gap

The stage-four runtime mapping had 439/448 existing XML channels mapped in the
`.inf` file. The nine missing channels are non-TLine channels:

- `Wang_30`
- `Wpu_30`
- `Ef_30`
- `If_30`
- `TE_30`
- `TM_30`
- `Vm_30`
- `P_30`
- `Q_30`

They are registered in
`data/validation/runtime_non_tline_channel_mapping_gap_registry.csv`.

They do not affect this loading audit because all 186 TLine P/Q/I channels are
mapped and parsed. They should not be ignored for future generator-30
quantitative analysis.

## Future model-action decision

The recommended future shadow-overload candidate is `E_28_29_1`, because it has
the highest post-clear-late loading maximum under the current audited rating
basis. The decision record is
`data/reference/future_shadow_overload_candidate_decision.json`.

The next model task should be one combined task:

`monitor-only shadow overload criterion -> Build -> one controlled Run -> automatic parsing -> audit/docs/Git/PR`

It should not be split again into separate user-return loops for build/run/parse
unless the user explicitly changes the workflow.

## Claim boundary

This stage supports:

- full-network exact TLine rating-basis registration;
- offline apparent-power loading-ratio reconstruction for qualified lines;
- post-clear candidate ranking;
- future shadow-overload candidate selection.

This stage does not support:

- confirmed overload;
- thermal overload proof;
- relay trip condition met;
- line protection action;
- line outage reproduced;
- branch trip;
- natural cascade propagation;
- physical causality direction;
- system stability;
- protection coordination;
- voltage-support performance;
- MATLAB coupling;
- strict paper reproduction.
