# PSCAD Module Instance Rules

## Definition and instance names

Reusable definition names are project-neutral, uppercase, and
Fortran-compatible. Do not embed `IBR2`, `DFIG`, breaker names, line numbers,
or project-specific signal prefixes inside a reusable definition.

Production instances use:

```text
<OBJECT_ID>__<MODULE_TYPE>
```

Examples:

```text
LINE_12__MONITORED_OBJECT_EVENT_PACKET
IBR_TRIAL_3__ONE_SHOT_BREAKER_OPEN_STIMULUS
SOURCE_A_SOURCE_B__TWO_EVENT_CHRONOLOGY_MONITOR
```

The isolated library harness reserves these fixed names:

```text
MODTEST_OBJECT_EVENT_PACKET
MODTEST_ONE_SHOT_STIMULUS
MODTEST_TWO_EVENT_CHRONOLOGY
```

## Signal scope

- External signals connect only through declared module ports.
- Instance parameters remain in the module parameter form.
- Intermediate Data Labels are definition-local and use generic semantic
  names such as `TIME_MEM`, `TIME_CAPTURE`, or `BOTH_SOURCE_CODE`.
- Do not use `IBR2_CAS_*`, `DFIG_LVRT_*`, `CAS_CHR_*`, `LINE_*`, or specific
  breaker names internally.
- Never create multiple instances by copying and renaming internal labels.
  All instances must reference the same definition.

When an instance exports a signal to a parent page, use:

```text
<OBJECT_ID>_<PUBLIC_INTERFACE_NAME>
```

## Safe instantiation sequence

1. Create or copy an instance from the project `Definitions` branch.
2. Assign the instance name and instance parameter values.
3. Connect every input physically at the parent page boundary.
4. Keep test instances isolated from existing protection and breaker logic.
5. Build, but do not Run unless dynamic validation is separately approved.
6. Run the static module-library audit before promoting the instance.

No reusable stimulus may be connected to a real breaker command without a
separate, explicit trial authorization.

## Phase 2 naming and collector rules

The harness also reserves `MODTEST_BREAKER_STATE_ADAPTER` and
`MODTEST_THREE_SOURCE_EVENT_COLLECTOR`.

PSCAD 4.6 internal Data Label names must be no longer than 31 characters.
Use short aliases such as `IBR3_CAS_EVT_VALID`; keep long public descriptions
in Output Channel titles or documentation.

Multi-source cause codes remain per source. Do not add global cause codes,
cause sums, virtual sources, or a fourth source to a three-source instance.

## Phase 3 chronology instance rules

`THREE_EVENT_CHRONOLOGY_MONITOR` instances are monitor-only. Production
instances must live on the same PSCAD page as the source Data Labels they
read; in the CASCADE3 trial deployment this is P3, not the parent `Main`
page. Ordinary PSCAD 4.6 Data Labels are not assumed to bridge page scope.

Keep internal labels short and generic. Do not place project-specific labels
such as `DFIG`, `IBR2`, `IBR3`, `CASCADE3`, `CAS_CHR`, `LINE_`, or `BRK_`
inside the reusable module definition.
