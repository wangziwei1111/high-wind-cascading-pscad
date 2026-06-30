# IBR2_TRIAL Dual-Source Cascade Collector

```text
source 1 = TYPE3_DFIG_1
source 2 = IBR2_TRIAL

ANY_TRIP = LIMIT(0, 1, S1_EVENT_VALID + S2_EVENT_VALID)
ANY_BRK_OPEN = LIMIT(0, 1, S1_BRK_OPEN + S2_BRK_OPEN)
AVAILABLE_SOURCE_COUNT = S1_AVAILABLE + S2_AVAILABLE
EVENTED_SOURCE_COUNT = S1_EVENT_VALID + S2_EVENT_VALID
FIRST_EVENT_TIME_S = minimum non-negative source time; -1 if neither is set
```

`FIRST_EVENT_SOURCE_CODE` is 0 when neither time is set, 1 for an earlier
TYPE3_DFIG_1 event, 2 for an earlier IBR2_TRIAL event, and 3 for equal or
indistinguishable times. It does not express causality, propagation direction,
or protection responsibility.

Cause codes remain per-source because DFIG codes 0/1/2/3 and IBR2 code 4 have
different semantics. They are never added into a global cause code.

| Public field | Type | Initial | Meaning | Dynamic status |
| --- | ---: | ---: | --- | --- |
| `IBR2_TRIAL_CASCADE_EVENT_VALID` | bool | 0 | armed observation of actual IBR2 opening | Not run |
| `IBR2_TRIAL_CASCADE_EVENT_CAUSE_CODE` | code | 0 | 0 or 4; root cause unclassified | Not run |
| `IBR2_TRIAL_CASCADE_EVENT_BRK_OPEN` | bool | 0 | actual local breaker open | Not run |
| `IBR2_TRIAL_CASCADE_SOURCE_AVAILABLE` | bool | 1 | current IBR2 trial availability | Not run |
| `IBR2_TRIAL_CASCADE_FIRST_EVENT_TIME_S` | real | -1 | first IBR2 event-valid time | Not run |
| `CASCADE_MONITOR_EVENTED_SOURCE_COUNT` | count | 0 | sources that recorded event-valid | Not run |
| `CASCADE_MONITOR_FIRST_EVENT_SOURCE_CODE` | code | 0 | earliest-source interface code | Not run |
| `CASCADE_MONITOR_CAUSE_CODE_IBR2_TRIAL` | code | 0 | IBR2 per-source cause | Not run |

## Deferred dynamic matrix

| Case | ANY_TRIP | ANY_BRK_OPEN | AVAILABLE | EVENTED | FIRST SOURCE | DFIG cause | IBR2 cause |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Both remain available | 0 | 0 | 2 | 0 | 0 | 0 | 0 |
| Only source 1 opens | 1 | 1 | 1 | 1 | 1 | 1/2/3 | 0 |
| Only IBR2 opens after armed | 1 | 1 | 1 | 1 | 2 | 0 | 4 |
| Both record events | 1 | interface-dependent | interface-dependent | 2 | 1/2/3 | per-source | 4 |

These are static interface expectations only. No dynamic PSCAD Run was
performed. No causal cascade propagation was validated.
