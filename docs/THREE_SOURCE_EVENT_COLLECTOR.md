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
