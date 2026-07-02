# Three-source electrical observability static Build audit

## Result

Static Build audit status: `pass`.

Nine monitor-only Output Channels were added in the trial project for existing
three-source V/P/Q observables. No PSCAD Run was performed, and no dynamic
electrical response is claimed.

## Signal map

| New Output Channel | Existing signal |
| --- | --- |
| `CASCADE3_ELEC_DFIG_V` | `VIBR1_2` |
| `CASCADE3_ELEC_DFIG_P` | `PIBR1_2` |
| `CASCADE3_ELEC_DFIG_Q` | `QIBR1_2` |
| `CASCADE3_ELEC_IBR2_V` | `VIBR2` |
| `CASCADE3_ELEC_IBR2_P` | `PIBR2` |
| `CASCADE3_ELEC_IBR2_Q` | `QIBR2` |
| `CASCADE3_ELEC_IBR3_V` | `VIBR3` |
| `CASCADE3_ELEC_IBR3_P` | `PIBR3` |
| `CASCADE3_ELEC_IBR3_Q` | `QIBR3` |

## Build evidence

- Output Channel count: 262 / expected 262
- Generated Fortran NPGB values: [115, 115]
- Main project SHA-256: `CBA120BB167CB7FA6C4A1AE4471268850AB61761EC1877EB7B87015627FE9DAB`
- Trial project SHA-256: `05B4D817B615B2FCAA38587B47E5885CF589022DE8ADB51C2014AA8032034B34`

## Boundary

This change adds observability only. It does not add sources, breakers,
event modules, time-ordering logic, protection logic, control feedback,
MATLAB coupling, or runtime validation.
