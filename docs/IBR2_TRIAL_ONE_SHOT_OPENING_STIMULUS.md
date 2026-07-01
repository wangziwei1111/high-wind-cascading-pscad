# IBR2_TRIAL One-Shot Opening Stimulus

## Static result

```text
trial_opening_stimulus_status = pass
default_closed_command_status = pass
trial_opening_isolation_status = pass
dynamic_behavior_status = unavailable
```

This is a trial-only test controller. It is not part of the original IBR2
controller, the DFIG LVRT protection, or an automatic reclosing function. It
only supplies the command of `BRK_IBR2_TRIAL` in the independent trial
project.

The default is deliberately disabled:

```text
IBR2_TEST_ENABLE = 0.0
IBR2_TEST_OPEN_TIME_S = 4.0 s
IBR2_TEST_TIME_REACHED = TIME >= IBR2_TEST_OPEN_TIME_S
IBR2_TEST_ARMED = IBR2_TEST_ENABLE AND DFIG_LVRT_ARMED
IBR2_TEST_OPEN_REQ = IBR2_TEST_ARMED AND IBR2_TEST_TIME_REACHED
IBR2_TEST_CMD_LIMITED = LIMIT(0, 1, IBR2_TEST_OPEN_REQ)
IBR2_TRIAL_BRK_CMD = 1.0 * IBR2_TEST_CMD_LIMITED
```

Consequently, the static default satisfies `TEST_ENABLE=0`,
`TEST_OPEN_REQ=0`, and `IBR2_TRIAL_BRK_CMD=0` (closed command). The existing
unity adapter remains the only connection from that command to
`BRK_IBR2_TRIAL`.

| Signal | Type | Initial value | Meaning | Dynamic status |
| --- | ---: | ---: | --- | --- |
| `IBR2_TRIAL_TEST_ENABLE` | bool | 0 | Trial opening stimulus enable | Not run |
| `IBR2_TRIAL_TEST_OPEN_TIME_S` | real | 4.0 | Opening template time | Not run |
| `IBR2_TRIAL_TEST_TIME_REACHED` | bool | 0 | TIME has reached the template time | Not run |
| `IBR2_TRIAL_TEST_OPEN_REQUEST` | bool | 0 | Sustained trial-local opening request | Not run |

## Deferred validation

- Future test A keeps `TEST_ENABLE=0` and checks that the default closed
  command is not changed.
- Future test B, only after explicit approval, sets `TEST_ENABLE=1` and an
  approved opening time, then observes the local breaker and source-2 packet.

These are future validation plans only. No PSCAD Run was performed in this
task. No dynamic opening, physical isolation, event timing, or causal cascade
propagation was validated.

## Reusable module-library addendum

`ONE_SHOT_BREAKER_OPEN_STIMULUS` is now available as an independent native
page-module definition with `OPEN_TIME_S=4`. Its isolated harness instance is
default-disabled. The existing IBR2 trial stimulus and breaker command path
were preserved and were not migrated to the reusable module. Static Build and
audit passed; dynamic behavior remains unavailable.
