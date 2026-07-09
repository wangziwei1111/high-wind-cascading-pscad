# CASCADE3 Trial Event Chronology Deployment

This trial-only deployment adds one production monitor instance:

```text
CASCADE3_TRIAL__CHRONOLOGY_MONITOR
```

The instance type is:

```text
THREE_EVENT_CHRONOLOGY_MONITOR
```

It is placed on the P3 control page near the existing three-source collector.
The existing `CASCADE3_TRIAL__EVENT_COLLECTOR` was not modified.

## Source mapping

- A = `TYPE3_DFIG_1`
  - event valid: `DFIG_LVRT_CASCADE_EVENT_VALID`
  - first event time: `DFIG_LVRT_CAS_FIRST_TIME_S`
- B = `IBR2_TRIAL`
  - event valid: `IBR2_CAS_EVT_VALID`
  - first event time: `IBR2_CAS_FIRST_S`
- C = `IBR3_TRIAL`
  - event valid: `IBR3_CAS_EVT_VALID`
  - first event time: `IBR3_CAS_FIRST_S`

## Monitor-only outputs

The deployment creates trial-local chronology labels:

- `CASCADE3_CHR_EVENTED_COUNT`
- `CASCADE3_CHR_TIMED_COUNT`
- `CASCADE3_CHR_FIRST_TIME_S`
- `CASCADE3_CHR_SECOND_TIME_S`
- `CASCADE3_CHR_THIRD_TIME_S`
- `CASCADE3_CHR_GAP_12_S`
- `CASCADE3_CHR_GAP_23_S`
- `CASCADE3_CHR_FIRST_SRC_CODE`
- `CASCADE3_CHR_ORDER_CLASS`
- `CASCADE3_CHR_CONSISTENT`

Eight new Output Channels expose the monitor-only chronology values. The final
Output Channel count is 253.

## Future validation matrix

These are future validation plans only. No PSCAD Run was performed in this
task. No dynamic event ordering or cascade propagation was validated.

| Case | Static expectation |
| --- | --- |
| No source records an event | evented=0, timed=0, first/second/third=-1, gaps=-1, first source=0, order class=0, consistent=1 |
| Only IBR3 records an event | evented=1, timed=1, first>=0, second/third=-1, first source=3, order class=1, consistent=1 |
| DFIG and IBR2 record strict different times | evented=2, timed=2, first<second, third=-1, gap12>0, order class=2, consistent=1 |
| All three record strict ordered times | evented=3, timed=3, first<second<third, gaps>0, order class=4, consistent=1 |
| At least two first-event times tie | first source code=4, order class=3 or 5, consistent=1 |

## Static status

Static audit script:

```text
analysis/pscad_tools/audit_three_event_chronology_module_deployment.py
```

The audit reports `three_event_chronology_static_pass`. PSCAD Build was
user-confirmed with zero errors. No PSCAD Run was performed.
