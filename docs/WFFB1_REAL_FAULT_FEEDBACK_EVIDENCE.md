# WFFB1 Real-Fault Feedback Evidence

This document pins the first verified offline feedback replay milestone.

## Local PSCAD Milestone

```text
C:\pscad_work\trip_shell_stage16\PSCAD\WFFB1_real_fault_matlab_feedback_wf38_trip_verified.pscx
```

The PSCAD project file itself is not committed to this repository.

## Physical Disturbance

- Disturbance: WF38-side three-phase fault.
- Fault window: `2.0 s` to `2.15 s`.
- Fault resistance: `0.01 ohm`.
- Run A mode: no MATLAB trip schedule applied.

## MATLAB Decision

MATLAB reads the PSCAD-exported WF33/WF35/WF38 voltage trace after startup and
applies the paper VRT criterion.

Result:

```text
WF38_TRIP_TIME = 2.02 s
WF35_TRIP_TIME = 99 s
WF33_TRIP_TIME = 99 s
```

`99 s` means no trip is requested inside the replay horizon.

## Feedback Replay Observation

In the PSCAD feedback run:

```text
WF38_TRIP_CMD transition = 2.02 s
WF38_BRK_STATE transition = 2.02 s
WF35_TRIP_CMD = no transition
WF35_BRK_STATE = no transition
WF33_TRIP_CMD = no transition
WF33_BRK_STATE = no transition
WF38_PCC_P after trip ~= 0 MW
```

This verifies a real PSCAD fault waveform to MATLAB decision to PSCAD breaker
feedback loop.

## Claim Boundary

This is an offline feedback replay validation, not live runtime PSCAD-MATLAB
coupling.

No `.pscx`, `.psmx`, `.gf46`, `.out`, `.inf`, `.dta`, or `.map` artifacts are
committed as evidence. Only lightweight text summaries, scripts, tests, and CSV
schedule files belong in Git.
