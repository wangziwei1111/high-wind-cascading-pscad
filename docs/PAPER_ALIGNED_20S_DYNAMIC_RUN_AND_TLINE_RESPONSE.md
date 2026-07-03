# Paper-aligned 20 s N29 fault dynamic run and full-network TLine response audit

## Scope

This stage records one user-executed PSCAD GUI Run of the already configured
paper-aligned 20 s baseline disturbance in `3IBR_DFIG1_TRIAL`.

The stage did not modify PSCAD models, did not Build, did not add devices, did
not run MATLAB, and did not add relay/protection/line-trip logic.

## Run and model integrity

| item | result |
| --- | --- |
| Run status | one user GUI Run completed |
| Parsed time axis | 0.0 s to 20.0 s |
| Sample count | 2001 |
| Median output step | about 0.01 s |
| Main project SHA after Run | `CBA120BB167CB7FA6C4A1AE4471268850AB61761EC1877EB7B87015627FE9DAB` |
| Trial project SHA after Run | `F81959EA62211FF9C1536C8481B67675AFE4DDCC3C56E804D048731A4B88A300` |
| XML Output Channel count | 448 |
| Parsed `.inf` PGB entries | 624 |
| Full-network TLine raw signals parsed | 186 = 31 lines x 2 terminals x P/Q/I |

The XML channel count remaining at 448 is the static preservation check. The
runtime `.inf` mapping contains 439 of those 448 named XML channels; the nine
unmapped channels are non-TLine generator-30 channels and are not used for the
full-network TLine P/Q/I response audit.

## Event observations

| source | event valid | breaker open | source available | first time |
| --- | ---: | ---: | ---: | ---: |
| DFIG | 1.0 | 1.0 | 0.0 | transition near 2.43 s |
| IBR2 | 0.0 | 0.0 | 1.0 | not observed |
| IBR3 | 0.0 | 0.0 | 1.0 | not observed |
| CASCADE3 monitor | 1.0 | 1.0 | n/a | 2.42521 s |

This supports only a raw event-observation claim for the configured scenario.
It does not prove natural cascade causality.

## Top 10 raw current response scores

The current score is the absolute change between the pre-fault window and the
early post-clear window for the terminal with the larger raw response.

| rank | branch | terminal | I response score | baseline I | early post-clear I |
| ---: | --- | --- | ---: | ---: | ---: |
| 1 | E_17_27_1 | B | 2.187008 | 0.039575 | 2.226583 |
| 2 | E_26_28_1 | A | 1.961636 | 0.236410 | 2.198045 |
| 3 | E_25_26_1 | B | 1.931412 | 0.104312 | 2.035724 |
| 4 | E_26_27_1 | B | 1.914725 | 0.429833 | 2.344559 |
| 5 | E_26_29_1 | A | 1.905910 | 0.315115 | 2.221025 |
| 6 | E_28_29_1 | A | 1.733928 | 0.564630 | 2.298559 |
| 7 | E_16_17_1 | B | 1.431985 | 0.400562 | 1.832547 |
| 8 | E_2_25_1 | A | 0.747286 | 0.455750 | 1.203036 |
| 9 | E_1_2_1 | A | 0.600134 | 0.171906 | 0.772040 |
| 10 | E_1_39_1 | A | 0.600134 | 0.171906 | 0.772040 |

## Top 10 raw active-power response scores

| rank | branch | terminal | P response score | baseline P | early post-clear P |
| ---: | --- | --- | ---: | ---: | ---: |
| 1 | E_28_29_1 | B | 3.505874 | -3.540781 | -7.046655 |
| 2 | E_26_29_1 | B | 2.677804 | -1.966924 | -4.644728 |
| 3 | E_26_28_1 | B | 2.455224 | -1.462074 | -3.917298 |
| 4 | E_25_26_1 | A | 2.098720 | -0.593933 | 1.504786 |
| 5 | E_17_27_1 | B | 1.697256 | 0.229217 | -1.468039 |
| 6 | E_26_27_1 | B | 1.491528 | -2.598521 | -4.090050 |
| 7 | E_2_25_1 | B | 1.354615 | -2.837494 | -4.192109 |
| 8 | E_1_2_1 | B | 1.334737 | -1.072764 | -2.407501 |
| 9 | E_8_9_1 | A | 1.282564 | -0.241926 | 1.040638 |
| 10 | E_9_39_1 | A | 1.273604 | -0.244089 | 1.029515 |

## Top 10 raw reactive-power response scores

| rank | branch | terminal | Q response score | baseline Q | early post-clear Q |
| ---: | --- | --- | ---: | ---: | ---: |
| 1 | E_28_29_1 | B | 12.862013 | 0.318824 | -12.543189 |
| 2 | E_26_29_1 | B | 12.620788 | 0.604527 | -12.016261 |
| 3 | E_26_28_1 | B | 10.226773 | 0.495171 | -9.731603 |
| 4 | E_16_17_1 | A | 3.845525 | -0.220812 | 3.624713 |
| 5 | E_25_26_1 | B | 3.224679 | 0.268657 | -2.956022 |
| 6 | E_17_27_1 | A | 3.105309 | -0.421974 | 2.683336 |
| 7 | E_26_27_1 | B | 2.740740 | -0.681262 | -3.422003 |
| 8 | E_16_19_1 | B | 2.078639 | -0.750834 | -2.829473 |
| 9 | E_1_39_1 | B | 1.744412 | 0.814880 | -0.929533 |
| 10 | E_3_4_1 | B | 1.425745 | 1.081978 | -0.343767 |

## Produced evidence

- `data/derived/paper_aligned_20s_event_timeline.csv`
- `data/derived/full_network_tline_window_metrics.csv`
- `data/derived/full_network_tline_current_response_ranking.csv`
- `data/derived/full_network_tline_power_response_ranking.csv`
- `data/derived/paper_aligned_20s_run_channel_coverage.csv`
- `data/derived/paper_aligned_20s_run_manifest.json`
- `data/derived/paper_aligned_20s_run_analysis_summary.json`
- `data/validation/paper_aligned_20s_dynamic_run_final_audit.json`
- `data/validation/paper_aligned_20s_dynamic_run_channel_trace.csv`
- `data/validation/paper_aligned_20s_dynamic_run_tline_trace.csv`
- `data/validation/paper_aligned_20s_dynamic_run_model_integrity_trace.csv`

## Claim boundary

This stage supports:

- a single configured 20 s fault Run was parsed successfully;
- full-network raw TLine P/Q/I dynamic responses were observed offline;
- DFIG event behavior was observed in the configured run;
- IBR2 and IBR3 remained in their default disabled/non-triggered state.

This stage does not support claims of line loading ratio, overload, relay
operation, branch trip, natural cascade propagation, physical causality
direction, protection coordination, voltage-support performance, system
stability, MATLAB coupling, or strict thesis reproduction.

## Stage-five offline loading addendum

The follow-up rating/loading audit reused this same 20 s Run and did not modify
PSCAD, Build, or Run. Exact generated `.tli` records were found for all 31
network TLines, each with `Total MVA Rating = 100.0`, enabling offline
apparent-power loading-ratio reconstruction for qualified lines only.

The resulting `line_loading_ratio_status` is
`observed_for_qualified_lines_only`. `line_overload_status` remains
`not_validated_no_relay_or_thermal_time_model`, and line protection, branch
trip, natural cascade propagation, causality, stability, protection
coordination, voltage-support performance, MATLAB coupling, and strict thesis
reproduction remain unavailable/unvalidated.

Detailed evidence is in
`docs/FULL_NETWORK_TLINE_RATING_AND_LOADING_AUDIT.md` and
`data/validation/tline_rating_loading_final_audit.json`.

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
