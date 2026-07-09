# TLine continuous thermal limit recovery and mapping

Generated: 2026-07-03T13:35:37

## Result

- Current-model branch identity mapping: 31 exact mappings to the PNNL 3IBR PSS/E RAW branch table.
- Protection-grade continuous thermal rating coverage: `fallback_no_protection_grade_rating_coverage`
- Protection-grade loading ratio: not generated.
- Shadow relay modeling readiness: blocked.

The important distinction is that branch identity mapping succeeded, but rating
recovery failed.  The current 31 PSCAD TLines match the open/local PNNL 3IBR RAW
network branches by from/to/circuit identity and exact R/X/B values.  However,
all mapped current-network branches have `RATE1..RATE12 = 0.0`, so Rate-A or
normal continuous thermal rating remains unspecified.

## Source summary

- Sources registered: 4
- Reproducible public/context sources: 3
- Adopted for branch identity mapping: 1
- Adopted for protection-grade thermal rating: 0

## E_16_19_1

`E_16_19_1` is a real current PSCAD TLine and the thesis-relevant named branch.
It maps exactly to the PNNL 3IBR RAW branch `16-19-1`, including R/X/B.  Its
RAW `RATE1` is `0.0`, so no continuous thermal limit is recovered and it cannot
enter a shadow-relay interface study.

## E_28_29_1

`E_28_29_1` is the previous highest 100-MVA-normalized apparent-power response
line.  It maps exactly to the PNNL 3IBR RAW branch `28-29-1`, including R/X/B.
Its RAW `RATE1` is also `0.0`, so it remains only a response-index observation,
not an overload or shadow-relay candidate.

## Boundary

`100-MVA-normalized apparent-power response index` remains available for
describing dynamic response.  `protection-grade loading ratio` requires an
auditable per-line continuous thermal/normal rating, which was not recovered.
No PSCAD model file was modified, and no Build or Run was performed.
