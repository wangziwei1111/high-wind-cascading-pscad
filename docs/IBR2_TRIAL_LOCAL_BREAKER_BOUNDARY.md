# IBR2_TRIAL Local Breaker Boundary

## Result

```text
execution_status = trial_local_breaker_boundary_static_build_verified
main_project_start_sha256 = 97AE9A99E199734510352DACBDE6120BBC411356C244C3DEA0ED8B01AB2B7906
main_project_end_sha256   = 97AE9A99E199734510352DACBDE6120BBC411356C244C3DEA0ED8B01AB2B7906
trial_start_sha256 = 62A9202F708402A850F6810797C852A54CD7D627D77B691749C4C6512CAEEF15
trial_end_sha256   = FB29872FCA8BCF92E5450C5944A312C1E6F018F87B5B499FEAF0E6B16C8A4A1E
```

A trial-local physical breaker boundary for `IBR2_TRIAL` was manually
constructed and statically Build-verified. The generated network maps the
three IBR2 phases on `NT_8` through `BRK_IBR2_TRIAL` to `NT_16`, the 0.6 kV
side of transformer `E_2_30_1`. No second `NT_8`–`NT_16` electrical path was
found.

## Interface

| Signal | Type | Initial value | Meaning | Dynamic status |
| --- | --- | ---: | --- | --- |
| `IBR2_TRIAL_BRK_CMD` | bool/code | 0 | Trial-local breaker command; 0 closes, 1 opens | Not run |
| `IBR2_TRIAL_BRK_STATE` | state | 0 closed; 2 open | Actual phase-A breaker state | Not run |
| `IBR2_TRIAL_BRK_OPEN_BOOL` | bool | 0 | `BRK_STATE >= 0.5` | Not run |
| `IBR2_TRIAL_SOURCE_AVAILABLE` | bool | 1 | `NOT BRK_OPEN_BOOL` | Not run |

All four signals have independent Output Channels with Transfer Data enabled,
All-runs saving, and scale factor 1.0. The state channel range is 0–2.2; the
three logical channels use 0–1.2.

## Static evidence and limits

The final Build completed with zero errors. Exact warning and message counts
were not supplied. Generated Fortran confirms the constant command, unity
command adapter, breaker state output, both comparator formulas, and all four
Output Channels. No new signal feeds the original IBR2 controller, DFIG LVRT,
`FINAL_BRK_CMD`, `BRK_DFIG`, or system protection/control chains.

The main project still has no qualified monitor-only second source. No PSCAD
Run was performed. No dynamic source disconnection, second-source event
packet, cause code, first-event time, dual-source collector, automatic
reclosing, virtual source, cascade propagation, or MATLAB behavior was built
or validated.

## 2026-06-30 event-interface addendum

The preserved boundary now feeds a trial-only monitor packet and two-real-
source collector. Static audit confirms that breaker parameters, the command
chain, `NT_8`–breaker–`NT_16` topology, and the original IBR2 controller were
not changed. No Run was performed.

## 2026-06-30 default-disabled opening stimulus addendum

The fixed-zero source was replaced, only in the trial project, by a
default-disabled one-shot test controller. `TEST_ENABLE` remains 0, so the
default `IBR2_TRIAL_BRK_CMD` remains the closed command 0. The breaker
parameters, physical series boundary, state interface, and original IBR2
controller remain preserved. This was statically built but not run.
