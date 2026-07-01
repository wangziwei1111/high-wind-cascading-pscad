# IBR3 Trial Real-Source Module Deployment

## Static result

`IBR3_TRIAL` is a trial-local third source based on the real
`IBR_AVM_2_1_1_2` branch (component ID `202861579`). Its existing observables
are `VIBR3`, `PIBR3`, and `QIBR3`. A physical three-phase breaker named
`BRK_IBR3_TRIAL` was inserted in the unique local series path between the
0.6 kV side of transformer `E_2_30_1` and the low-voltage multimeter feeding
the IBR component. Static XML and generated-network checks found no parallel
bypass around the new breaker.

```text
main SHA-256  = CBA120BB167CB7FA6C4A1AE4471268850AB61761EC1877EB7B87015627FE9DAB
trial start   = D56430173617DCCD16C9C9DDF3787EF7D9ADDD606EB4C9F5B8419BC290476314
trial final   = CDFBBAA3A987B67E3B3BC3294E9993AB06AA3F77BED90AF111B6B35A55B0C99E
Build Errors  = 0 (final user-confirmed Build)
PSCAD Run     = not performed
```

## Breaker and modules

`BRK_IBR3_TRIAL` uses the proven trial breaker semantics: command 0 is closed,
command 1 is open, and `SBRA` exports `IBR3_TRIAL_BRK_STATE`. The reusable
`BREAKER_STATE_ADAPTER` maps state values greater than or equal to 0.5 to
`IBR3_TRIAL_BRK_OPEN_BOOL=1` and exports the inverse as
`IBR3_TRIAL_SOURCE_AVAILABLE`.

Production instances are `IBR3_TRIAL__OPEN_STIMULUS` (`OPEN_TIME_S=5.0`),
`IBR3_TRIAL__BREAKER_STATE_ADAPTER` (`OPEN_THRESHOLD=0.5`),
`IBR3_TRIAL__EVENT_PACKET` (cause 5, latch initial 0, first-time initial -1),
and `CASCADE3_TRIAL__EVENT_COLLECTOR`.

```text
IBR3_TRIAL_BRK_CMD = LIMIT(0, 1,
  IBR3_TEST_ENABLE * DFIG_LVRT_ARMED * (TIME >= 5.0 s))
IBR3_TEST_ENABLE = 0
```

No actual dynamic opening occurred. Cause code 5 means that the local breaker
was observed open while armed and the root cause remains unclassified. It is
not a claim about protection responsibility or propagation.

PSCAD 4.6 internal Data Labels were kept short (`IBR3_CAS_EVT_VALID`,
`IBR3_CAS_CAUSE`, `IBR3_CAS_BRK_OPEN`, `IBR3_CAS_AVAIL`, and
`IBR3_CAS_FIRST_S`). Long descriptive names are Output Channel titles only.
Twenty-one channels were added, bringing the total from 224 to 245; the prior
224 channel parameter sets are unchanged.

## Future dynamic validation matrix

| Case | Future stimulus | Static interface expectation |
| --- | --- | --- |
| A | All three sources remain available | available=3, evented=0, first time=-1, source code=0 |
| B | Enable only IBR3 after separate approval | IBR3 valid=1, cause=5, available=2, evented=1, source code=3 |
| C | Approved DFIG/IBR2/IBR3 events | evented=1/2/3, minimum valid time, source code=1/2/3/4, per-source causes |

These are static interface expectations only. No PSCAD Run was performed in
this task. No causal cascade propagation was validated. Physical isolation,
dynamic timing, and three-source interaction remain unavailable.
