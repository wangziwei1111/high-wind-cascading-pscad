# Type-3 WTG PSCAD GUI Trial Guide

This guide is only for independently opening and running the official Type-3 WTG V46 example in PSCAD v4.6.2. Do not connect it to the current 3IBR project in this stage.

## A. Before Opening

1. Close the current 3IBR project, or start a separate PSCAD session.
2. Do not load the PNNL 3IBR project at the same time.
3. Confirm PSCAD is v4.6.2 Professional.
4. Confirm the Fortran compiler can build PSCAD v4.6 projects.
5. Download the official Type-3 example only from `https://www.pscad.com/knowledge-base/article/496`.
6. Extract the original package to `external/type3-wtg-v46/ORIGINAL_DOWNLOAD_DO_NOT_EDIT/`.
7. Copy the complete extracted folder to `external/type3-wtg-v46/WORKING_COPY/`.
8. Open only the working copy in PSCAD.
9. If PSCAD asks to convert the project, convert only the working copy and do not overwrite the original download.

## B. First-Open Inspection

After opening the working copy, confirm the project tree shows:

- A main project or workspace entry.
- Average Type-3 model.
- Detailed Type-3 model.
- Wind turbine mechanical component.
- DFIG / wound-rotor induction machine electrical component.
- Rotor-side converter and controller.
- Grid-side converter and controller.
- DC-link.
- Chopper.
- Crowbar protection.
- Step-up transformer.
- Grid breaker or interconnection breaker.
- Wind speed input.
- Measurement outputs.
- Aggregation or scaling component.

Do not edit these modules during first-open inspection.

## C. Independent Run Target

The first trial goal is only:

```text
Project opens
-> 0 blocking errors
-> Build succeeds
-> Initialization succeeds
-> No-fault base case completes Run
```

Do not:

- Connect the model to IEEE-39.
- Change rated capacity.
- Apply faults.
- Implement LVRT changes.
- Connect MATLAB.
- Replace any 3IBR component.

## D. If an Error Appears

Capture screenshots showing:

- PSCAD title bar with version.
- First red error in Build Messages or Runtime Messages.
- Project tree.
- Missing library or missing file name.
- Full compiler or linker error text.

Also record whether the error happened during open, clean, build, initialization, or run.
