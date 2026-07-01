# PSCAD Reusable Control Module Library — Phase 1

## Result

Three native PSCAD 4.6 page-module definitions were created only in
`3IBR_DFIG1_TRIAL.pscx` and passed user-confirmed static Builds with zero
errors:

- `MONITORED_OBJECT_EVENT_PACKET`
- `ONE_SHOT_BREAKER_OPEN_STIMULUS`
- `TWO_EVENT_CHRONOLOGY_MONITOR`

The project also contains the independent hierarchy pages
`CASCADE_CONTROL_MODULE_LIBRARY` and `MODULE_TEMPLATE_TEST_HARNESS`. The
three isolated harness instances are `MODTEST_OBJECT_EVENT_PACKET`,
`MODTEST_ONE_SHOT_STIMULUS`, and `MODTEST_TWO_EVENT_CHRONOLOGY`.

```text
main SHA-256  = CBA120BB167CB7FA6C4A1AE4471268850AB61761EC1877EB7B87015627FE9DAB
trial SHA-256 = D56430173617DCCD16C9C9DDF3787EF7D9ADDD606EB4C9F5B8419BC290476314
Build Errors  = 0
PSCAD Run     = not performed
```

The existing IBR2 breaker boundary, event packets, dual-source collector,
chronology monitor, test stimulus, DFIG protection, fault logic, and main
circuit were not migrated or modified. The Output Channel count remains 224.

## Module interfaces

### MONITORED_OBJECT_EVENT_PACKET

Inputs: `IN_OBJECT_OPEN_BOOL`, `IN_OBJECT_AVAILABLE`, `IN_ARMED`, `IN_TIME`.

Parameters: `CAUSE_CODE_VALUE=4`, `EVENT_LATCH_INITIAL=0`,
`FIRST_TIME_INITIAL=-1`.

Outputs: `OUT_EVENT_VALID`, `OUT_CAUSE_CODE`, `OUT_OBJECT_OPEN`,
`OUT_OBJECT_AVAILABLE`, `OUT_FIRST_EVENT_TIME_S`.

The event latch is sticky, the cause code is gated by event-valid, and the
first nonnegative event time is retained. PSCAD 4.6 Feedback Loop Selector
initial-value fields accept literals only. Therefore instance initial
parameters enter the page as REAL Import signals and are merged through local
Selectors; the two Feedback components retain literal storage seeds of 0 and
-1.

### ONE_SHOT_BREAKER_OPEN_STIMULUS

Inputs: `IN_TEST_ENABLE`, `IN_ARMED`, `IN_TIME`.

Parameter: `OPEN_TIME_S=4`.

Outputs: `OUT_TIME_REACHED`, `OUT_OPEN_REQUEST`, `OUT_BREAKER_COMMAND`.

The module computes `IN_TIME-OPEN_TIME_S`, gates the time-reached state with
test-enable and armed, and limits the command to [0,1]. It has no breaker
feedback, protection, fault, pulse recovery, repeated action, or automatic
reclosing logic.

### TWO_EVENT_CHRONOLOGY_MONITOR

Inputs: `IN_EVENT_VALID_A`, `IN_FIRST_EVENT_TIME_A_S`, `IN_EVENT_VALID_B`,
`IN_FIRST_EVENT_TIME_B_S`.

Outputs: `OUT_EVENTED_OBJECT_COUNT`, `OUT_BOTH_EVENTS_RECORDED`,
`OUT_FIRST_EVENT_TIME_S`, `OUT_SECOND_EVENT_TIME_S`,
`OUT_EVENT_TIME_GAP_S`, `OUT_FIRST_EVENT_SOURCE_CODE`,
`OUT_EVENT_SEQUENCE_CODE`, `OUT_CHRONOLOGY_CONSISTENT`.

First-source codes are 0 none, 1 A, 2 B, and 3 tie/indistinguishable.
Sequence codes are 0 none, 1 A only, 2 B only, 3 A first, 4 B first, and 5
tie/indistinguishable. Consistency is asserted when each event-valid flag
matches whether its corresponding time is nonnegative; the remaining legal
state properties follow from Min/Max and nonnegative gap construction.

## Static harness defaults

| Instance | Inputs | Expected outputs |
| --- | --- | --- |
| `MODTEST_OBJECT_EVENT_PACKET` | 0, 1, 0, 0 | 0, 0, 0, 1, -1 |
| `MODTEST_ONE_SHOT_STIMULUS` | 0, 0, 0 | 0, 0, 0 |
| `MODTEST_TWO_EVENT_CHRONOLOGY` | 0, -1, 0, -1 | 0, 0, -1, -1, -1, 0, 0, 1 |

The harness outputs are isolated and no Output Channels were added.

## Verification and claim boundary

Run the final read-only gate with:

```powershell
python analysis/pscad_tools/audit_pscad_reusable_control_module_library.py --require-complete
```

The audit verifies the frozen main SHA, protected generated formulas and
breaker edges, module definitions, ports, parameters, named test instances,
Output Channel count, and absence of automatic reclosing, MATLAB, third
source, or virtual source structures. It does not establish dynamic opening,
event timing, multi-source interaction, physical cascade propagation, or
runtime behavior.

## Phase 2 addendum — 2026-07-01

Two native definitions were added: `BREAKER_STATE_ADAPTER` and
`THREE_SOURCE_EVENT_COLLECTOR`. Their isolated harness instances are
`MODTEST_BREAKER_STATE_ADAPTER` and
`MODTEST_THREE_SOURCE_EVENT_COLLECTOR`. The adapter uses
`OPEN_THRESHOLD=0.5`; default state 0 has expected outputs open=0 and
available=1. The collector has 15 inputs and nine outputs; its default test
expects `0,0,3,0,-1,0,0,0,0`.

Phase 2 is deployed only in the trial IBR3 path. Final Output Channel count is
245. The original three definitions and prior 224 channels are statically
unchanged. PSCAD internal identifiers are kept within 31 characters; long
names are reserved for Output Channel titles and documentation. No Run was
performed.
