# IBR2_TRIAL Event Chronology Monitor

## Static result

```text
chronology_structure_status = pass
second_event_time_logic_status = pass
event_gap_logic_status = pass
event_sequence_logic_status = pass
chronology_consistency_logic_status = pass
dynamic_behavior_status = unavailable
```

The monitor consumes the two existing real-source event packets and the
existing dual-source collector. It is monitor-only and has no feedback to a
controller, breaker, protection, fault, UFLS, UVLS, or system-control path.

`SECOND_EVENT_TIME_S` is the later of the two source first-event times when
both events are recorded; otherwise it is -1. `EVENT_TIME_GAP_S` is their
non-negative absolute difference when both exist; otherwise it is -1.

`EVENT_SEQUENCE_CODE` represents only the static event interface ordering:

| Code | Meaning |
| ---: | --- |
| 0 | No event recorded |
| 1 | Only source 1 recorded |
| 2 | Only source 2 recorded |
| 3 | Both recorded; source 1 earlier |
| 4 | Both recorded; source 2 earlier |
| 5 | Both recorded with equal/indistinguishable time, or invalid fallback |

`CHRONOLOGY_CONSISTENT` is a monitor-only interface-state check. It is 1 only
for one of these combinations:

- count 0: first=-1, second=-1, first-source=0, sequence=0;
- count 1: first>=0, second=-1, first-source in {1,2}, sequence in {1,2};
- count 2: first>=0, second>=first, gap>=0, first-source in {1,2,3},
  sequence in {3,4,5}.

| Signal | Type | Initial value | Meaning | Dynamic status |
| --- | ---: | ---: | --- | --- |
| `CASCADE_MONITOR_BOTH_EVENTS_RECORDED` | bool | 0 | Both sources record event-valid | Not run |
| `CASCADE_MONITOR_SECOND_EVENT_TIME_S` | real | -1 | Later source event time | Not run |
| `CASCADE_MONITOR_EVENT_TIME_GAP_S` | real | -1 | Static non-negative event-time difference | Not run |
| `CASCADE_MONITOR_EVENT_SEQUENCE_CODE` | code | 0 | Static event-record ordering code | Not run |
| `CASCADE_MONITOR_CHRONOLOGY_CONSISTENT` | bool | 1 | Interface-state combination is self-consistent | Not run |

These fields do not establish dynamic physical causality, propagation delay,
protection-coordination delay, EMTDC sub-step ordering, or cascade propagation
direction.

Future test C, only after approval, would combine the existing source-1 LVRT
event with an approved source-2 opening time and observe event count, first
and second times, gap, first-source code, sequence code, and consistency.

These are future validation plans only. No PSCAD Run was performed in this
task. No causal cascade propagation was validated.
