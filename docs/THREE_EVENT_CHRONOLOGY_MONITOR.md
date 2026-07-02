# THREE_EVENT_CHRONOLOGY_MONITOR

`THREE_EVENT_CHRONOLOGY_MONITOR` is a reusable native PSCAD 4.6 page module
for monitor-only ordering of three event sources.

It does not create breaker commands, protection commands, fault commands,
automatic reclosing, or main-circuit control. Its outputs are observability
signals only.

## Interface

Inputs:

- `IN_EVENT_VALID_A`, `IN_FIRST_EVENT_TIME_A_S`
- `IN_EVENT_VALID_B`, `IN_FIRST_EVENT_TIME_B_S`
- `IN_EVENT_VALID_C`, `IN_FIRST_EVENT_TIME_C_S`

Outputs:

- `OUT_EVENTED_OBJECT_COUNT`
- `OUT_TIMED_EVENT_OBJECT_COUNT`
- `OUT_FIRST_EVENT_TIME_S`
- `OUT_SECOND_EVENT_TIME_S`
- `OUT_THIRD_EVENT_TIME_S`
- `OUT_FIRST_TO_SECOND_GAP_S`
- `OUT_SECOND_TO_THIRD_GAP_S`
- `OUT_FIRST_EVENT_SOURCE_CODE`
- `OUT_EVENT_ORDER_CLASS_CODE`
- `OUT_CHRONOLOGY_CONSISTENT`

## Static rules

`evented count` is the raw count of event-valid flags. `timed-event count`
counts only sources whose event-valid flag is asserted and whose first-event
time is nonnegative. A difference between these counts means the event
interface is incomplete or internally inconsistent.

Invalid source times are excluded from min/max ordering by local selector
candidates: invalid min candidates use `1000000.0`, and invalid max candidates
use `-1.0`. With three timed events, the middle time is computed as:

```text
A time + B time + C time - minimum time - maximum time
```

The first/second/third event times are only an ordering of the source
first-event-time interface. They do not establish physical causality,
protection responsibility, cascade propagation direction, EMTDC sub-step
ordering, or electromagnetic transient propagation delay.

`OUT_FIRST_EVENT_SOURCE_CODE` uses:

- `0`: no timed event
- `1`: A is uniquely first
- `2`: B is uniquely first
- `3`: C is uniquely first
- `4`: at least two sources tie for first

`OUT_EVENT_ORDER_CLASS_CODE` uses:

- `0`: no timed event
- `1`: one timed event
- `2`: two timed events with strict order
- `3`: two timed events with equal time
- `4`: three timed events with strict order
- `5`: three timed events with at least one adjacent tie
- `6`: event-valid count and timed-event count are inconsistent

`OUT_CHRONOLOGY_CONSISTENT` is zero when evented count and timed count differ;
otherwise it is asserted for the legal static states constructed by the module
selectors.

## Harness coverage

The isolated harness instances are:

- `MODTEST_THREE_EVENT_CHRONOLOGY_NONE`
- `MODTEST_THREE_EVENT_CHRONOLOGY_TWO_STRICT`
- `MODTEST_THREE_EVENT_CHRONOLOGY_THREE_TIE`

These are static build harnesses only. No PSCAD Run was performed.

## Dynamic validation addendum: 2026-07-02

One later approved IBR3_TRIAL single-opening Run parsed the production
`CASCADE3_TRIAL__CHRONOLOGY_MONITOR` Output Channels. In that run an existing
DFIG event was first at 2.01603 s and the IBR3 trial event was second at
5.0 s; the first-to-second gap was 2.98397 s, third time remained `-1`, and
`CASCADE3_MONITOR_CHRONOLOGY_CONSISTENT` remained 1.

The detailed result is documented in
`docs/IBR3_TRIAL_SINGLE_OPENING_DYNAMIC_VALIDATION.md`. This validates only
that single run's chronology monitor outputs and does not establish cascade
propagation, physical causality direction, system stability, or MATLAB
coupling.
