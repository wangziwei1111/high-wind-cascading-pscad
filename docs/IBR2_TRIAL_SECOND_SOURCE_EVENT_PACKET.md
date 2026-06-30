# IBR2_TRIAL Second-Source Event Packet

## Static result

```text
source_id = IBR2_TRIAL
source_component = IBR_AVM_2_1_1_1
source2_packet_structure_status = pass
control_path_isolation_status = pass
dynamic_behavior_status = unavailable
```

The packet is monitor-only. `EVENT_VALID` means that the local IBR2 breaker
was observed actually open after `DFIG_LVRT_ARMED`; it is not a protection
request. Cause code 4 means observed local breaker opening with root cause
unclassified. It is not an LVRT cause, cascade cause, or protection
attribution.

| Public Output Channel | Internal signal | Initial | Static formula |
| --- | --- | ---: | --- |
| `IBR2_TRIAL_CASCADE_EVENT_VALID` | `IBR2_CAS_EVT_VALID` | 0 | sticky latch of `IBR2_CAS_BRK_OPEN AND DFIG_LVRT_ARMED` |
| `IBR2_TRIAL_CASCADE_EVENT_CAUSE_CODE` | `IBR2_CAS_CAUSE` | 0 | `4 × IBR2_CAS_EVT_VALID` |
| `IBR2_TRIAL_CASCADE_EVENT_BRK_OPEN` | `IBR2_CAS_BRK_OPEN` | 0 | `1 × IBR2_TRIAL_BRK_OPEN_BOOL` |
| `IBR2_TRIAL_CASCADE_SOURCE_AVAILABLE` | `IBR2_CAS_AVAIL` | 1 | `1 × IBR2_TRIAL_SOURCE_AVAILABLE` |
| `IBR2_TRIAL_CASCADE_FIRST_EVENT_TIME_S` | `IBR2_CAS_FIRST_S` | -1 | first valid event time memory |

The event latch starts at 0.0. The time memory starts at -1.0 s and captures
the existing armed TIME source only while the memory is unset. It does not
continuously output TIME.

No PSCAD Run was performed. Dynamic IBR2 disconnection, event time, physical
source isolation, and root-cause attribution remain unvalidated.

## Trial-stimulus linkage addendum

The packet now has a default-disabled trial-only opening stimulus upstream of
the already-preserved local breaker. The packet logic itself is unchanged.
Static chronology fields consume its existing event-valid and first-time
signals without feedback. No dynamic source-2 opening or event capture was
validated.
