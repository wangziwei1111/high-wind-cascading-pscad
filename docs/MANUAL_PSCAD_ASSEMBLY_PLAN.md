# Manual PSCAD Assembly Plan

Target route:

```text
PNNL Enhanced IEEE-39 three-IBR PSCAD project
  -> keep verified network, synchronous machine, line, load, breaker structure
  -> manually locate three IBR points
  -> map wind farm targets to buses 33, 35, 38
  -> manually disconnect or bypass original IBR blocks
  -> manually import PSCAD Type-3 DFIG aggregate wind farm module
  -> manually set wind farm capacities, initial outputs, transformers, breakers
  -> MATLAB protection logic outputs neutral commands
  -> manually connect LVRT, overload, UFLS/UVLS, TOV ports in PSCAD GUI
```

| Step | Action | Status owner |
| ---: | --- | --- |
| 1 | Open PNNL `Enhanced IEEE 39-Bus System_3IBRs/PSCAD/3IBR.pscx` in PSCAD | 用户需在 PSCAD GUI 中完成 |
| 2 | Check PSCAD project version, workspace migration prompts, compiler selection, and E-TRAN library loading | 用户需在 PSCAD GUI 中完成 |
| 3 | Locate the three IBR modules in the hierarchy and record page names and component IDs | 用户需在 PSCAD GUI 中完成 |
| 4 | Record each IBR interconnection bus, transformer, voltage level, measurement channels, and control ports | 用户需在 PSCAD GUI 中完成 |
| 5 | Compare observed IBR buses with target thesis buses 33, 35, 38 | 需要论文或导师进一步确认 |
| 6 | Download/import official PSCAD Type-3 WTG through legitimate PSCAD access | 用户需在 PSCAD GUI 中完成 |
| 7 | Configure Type-3 WTG as aggregate wind farm candidate | 用户需在 PSCAD GUI 中完成 |
| 8 | For one pilot IBR only, manually disconnect or bypass the original IBR after saving a copy of the source project | 用户需在 PSCAD GUI 中完成 |
| 9 | Connect the DFIG aggregate to the original IBR point or mark bus mismatch as a manual redesign item | 用户需在 PSCAD GUI 中完成 |
| 10 | Add grid-connection breaker and measurement points for voltage, frequency, P/Q, and breaker status | 用户需在 PSCAD GUI 中完成 |
| 11 | Add PSCAD external input ports for neutral commands: `trip_line`, `shed_load`, `disconnect_wind_farm`, `trip_generator`, `trip_device` | 用户需在 PSCAD GUI 中完成 |
| 12 | Map MATLAB command IDs to PSCAD breakers, load blocks, wind disconnection commands, and device trips | 用户需在 PSCAD GUI 中完成 |
| 13 | Configure the bus 29 near-area three-phase short-circuit benchmark case | 用户需在 PSCAD GUI 中完成 |
| 14 | Compile and initialize in PSCAD GUI; record warnings and errors | 用户需在 PSCAD GUI 中完成 |
| 15 | Export voltage, frequency, wind active power, line loading, and event data | 用户需在 PSCAD GUI 中完成 |

Codex prepared: source audit, parameter files, MATLAB protection modules, and checklists. No PSCAD drawing has been automatically modified.

