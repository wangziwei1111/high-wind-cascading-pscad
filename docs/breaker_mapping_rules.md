# Breaker Mapping Rules

All PSCAD breaker names must be stable and auditable.

## Lines

Line `k` has two physical breakers:

- `BR_LINE_k_FROM`
- `BR_LINE_k_TO`

`cmd.line_trip_cmd(k)` opens both breakers. The next `obs.line_online(k)` confirms whether the line is actually offline.

## Wind Farms

- Bus 33 wind farm: `BR_WIND_33`
- Bus 35 wind farm: `BR_WIND_35`
- Bus 38 wind farm: `BR_WIND_38`

## Generators

Use `BR_GEN_30` through `BR_GEN_39`.

## Loads

Use staged switches:

- `BR_LOAD_<bus>_STAGE1`
- `BR_LOAD_<bus>_STAGE2`
- `BR_LOAD_<bus>_STAGE3`

UFLS cumulative targets are 25%, 40%, and 55%. UVLS uses 25% unless a scenario-specific setting overrides it.

