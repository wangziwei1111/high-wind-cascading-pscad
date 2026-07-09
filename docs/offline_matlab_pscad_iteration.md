# Offline MATLAB Protection Iteration With PSCAD

This workflow is used because the local PSCAD 4.6 environment is configured with GFortran 4.2.1, while the available MATLAB is R2025a. Direct PSCAD-MATLAB runtime coupling is therefore not the next stable step.

The verified PSCAD plant milestone is:

```text
C:\pscad_work\trip_shell_stage16\PSCAD\WFMR1.pscx
```

`WFMR1` contains three PSCAD Variable components:

```text
WF38_TRIP_TIME
WF35_TRIP_TIME
WF33_TRIP_TIME
```

The trip command comparators use those variables. The baseline case has already been verified in PSCAD:

```text
WF38_TRIP_TIME = 0.57 s
WF35_TRIP_TIME = 0.67 s
WF33_TRIP_TIME = 0.77 s
```

## One-Case Loop

From the repository root, generate a short-name PSCAD working project:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\apply_offline_trip_case.ps1 `
  -CaseId baseline_manual_verified `
  -OutputProject C:\pscad_work\trip_shell_stage16\PSCAD\WFCASE.pscx `
  -OutputNamespace WFCASE
```

Then open this file in PSCAD:

```text
C:\pscad_work\trip_shell_stage16\PSCAD\WFCASE.pscx
```

Build and Run it in the PSCAD GUI. After the run finishes, check the trip timing:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\check_pscad_trip_outputs.ps1 `
  -RunDir C:\pscad_work\trip_shell_stage16\PSCAD\WFCASE.gf46 `
  -Namespace WFCASE `
  -CaseId baseline_manual_verified
```

## MATLAB Protection Role

MATLAB should compute or update the three trip times, then export them into a small CSV with the same columns as:

```text
config/offline_trip_cases.csv
```

PSCAD remains the EMT simulation engine. MATLAB owns the protection decision and timing logic. The repository does not claim live PSCAD-MATLAB co-simulation for this stage.

## Verified Real-Fault Feedback Loop

The first real PSCAD electrical-disturbance feedback loop has been verified locally:

1. `WFFLT1.pscx` keeps all offline trip commands at `99 s` and adds a WF38-side three-phase fault.
2. PSCAD Run produces a real voltage sag at WF38 during the `2.0-2.15 s` fault window.
3. The WF38 voltage trace is exported to `results/wfflt1_pscad_voltage_trace_after_startup.csv`.
4. MATLAB reads the PSCAD voltage trace and exports `config/offline_trip_cases_from_wfflt1.csv`.
5. The resulting trip decision is:

```text
WF38_TRIP_TIME = 2.02 s
WF35_TRIP_TIME = 99 s
WF33_TRIP_TIME = 99 s
```

6. `WFFB1.pscx` applies those trip times back into PSCAD while preserving the physical fault.

Validation evidence from the local PSCAD output:

```text
WF38_TRIP_CMD transition = 2.02 s
WF38_BRK_STATE transition = 2.02 s
WF35_TRIP_CMD/BRK_STATE = no transition
WF33_TRIP_CMD/BRK_STATE = no transition
WF38_PCC_P after trip = approximately 0 MW
```

Local milestone copy:

```text
C:\pscad_work\trip_shell_stage16\PSCAD\WFFB1_real_fault_matlab_feedback_wf38_trip_verified.pscx
```
