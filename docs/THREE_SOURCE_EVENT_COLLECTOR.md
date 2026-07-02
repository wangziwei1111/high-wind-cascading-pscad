# Three-Source Event Collector

`THREE_SOURCE_EVENT_COLLECTOR` is a project-neutral PSCAD 4.6 page module for
monitor-only aggregation of three real event packets. It does not generate
protection, breaker commands, fault logic, automatic reclosing, or a global
cause code.

Each of A, B, and C supplies event-valid, breaker-open, source-available,
first-event time, and cause code inputs. Outputs are any-event, any-open,
available count, evented count, first valid time, first-source code, and three
independent cause codes.

```text
ANY_EVENT_VALID = LIMIT(0,1,A.valid+B.valid+C.valid)
ANY_BREAKER_OPEN = LIMIT(0,1,A.open+B.open+C.open)
AVAILABLE_SOURCE_COUNT = A.available+B.available+C.available
EVENTED_SOURCE_COUNT = A.valid+B.valid+C.valid
```

Only a source with `EVENT_VALID=1` and `FIRST_EVENT_TIME_S>=0` participates.
The first time is the minimum participating time, or -1 when none exists.
First-source codes are 0 none, 1 A, 2 B, 3 C, and 4 tie or indistinguishable
within the 1e-9 s static comparison interface. Cause codes pass through
independently and are never summed.

The isolated harness instance is `MODTEST_THREE_SOURCE_EVENT_COLLECTOR`.
Default inputs per source are `0,0,1,-1,0`; expected outputs are
`0,0,3,0,-1,0,0,0,0`.

The production instance maps only A=`TYPE3_DFIG_1`, B=`IBR2_TRIAL`, and
C=`IBR3_TRIAL`. This count does not represent every generator in the system.
No fake or fourth source is present. These are static interface expectations
only. No PSCAD Run was performed, and no causal cascade propagation was
validated.

## Chronology monitor addendum

The separate `CASCADE3_TRIAL__CHRONOLOGY_MONITOR` instance reads only the
existing three-source event-valid and first-event-time interfaces. It does
not modify `CASCADE3_TRIAL__EVENT_COLLECTOR`, does not consume cause codes or
breaker commands, and does not feed any protection or breaker path. Its
outputs are `CASCADE3_CHR_*` monitor-only labels.

## Dynamic validation addendum: 2026-07-02

One later approved Run temporarily enabled only the IBR3 trial local-opening
stimulus. The three-source collector monitor outputs were parsed from PSCAD
Output Channels: IBR3 cause code propagated as 5, evented source count reached
2 because an existing DFIG event was also present, and IBR2 test enable stayed
0. The result is documented in
`docs/IBR3_TRIAL_SINGLE_OPENING_DYNAMIC_VALIDATION.md`.

This addendum validates the collector's monitored dynamic equivalence for that
single fixed run only. It is not a claim of cascade propagation, physical
causality direction, system stability, or MATLAB coupling.

## Default-disabled baseline addendum: 2026-07-02

In the paired default-disabled baseline Run, IBR3 remained non-evented:
`CASCADE3_MONITOR_CAUSE_CODE_IBR3_TRIAL` held at 0 and the CASCADE3 evented
source count remained at the existing DFIG-only value of 1. See
`docs/IBR3_TRIAL_DEFAULT_DISABLED_BASELINE_VALIDATION.md`.
