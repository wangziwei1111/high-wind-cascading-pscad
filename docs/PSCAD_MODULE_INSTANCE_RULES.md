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
