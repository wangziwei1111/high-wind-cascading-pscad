# IBR_AVM_2_1_1 Static Map

## Location and Instances

The PNNL project contains three `3IBR:IBR_AVM_2_1_1` instances on page/definition `P3`.

| Instance id | Page | Position | Status |
|---|---|---|---|
| `475433949` | `P3` | `x=990, y=990` | verified_from_model_file |
| `1220231535` | `P3` | `x=990, y=1332` | verified_from_model_file |
| `202861579` | `P3` | `x=990, y=1656` | verified_from_model_file |

The candidate closest to the user's GBUS30/N30 description is instance `475433949`, because it is aligned with the `E_2_30_1` 345/22 kV transformer, 22/0.6 kV transformer, and local series inductor in the same `P3` branch. This is still a static inference and must be confirmed visually in PSCAD before editing.

## IBR Definition Ports

| Port | Direction/type | Meaning | Evidence |
|---|---|---|---|
| `out` | Natural, 3-phase electrical | IBR AC terminal | verified_from_model_file |
| `Inputs` | Transfer input, real dim=8 | Input bus | verified_from_model_file |
| `Flags` | Transfer input, real dim=6 | Control/status flags | verified_from_model_file |
| `fPLL` | Transfer output, real dim=1 | PLL frequency output | verified_from_model_file |

No `fGFM` port was present on the parsed `IBR_AVM_2_1_1` definition. Earlier build errors mentioning `fGFM` therefore refer to a stale/removed export expectation rather than a verified current external port.

## Candidate GBUS30/N30 Branch Evidence

| Component | Parameters | Evidence |
|---|---|---|
| Upstream transformer | `Name=E_2_30_1`, `Tmva3=100`, `V1LL=345`, `V2LL=22`, `Xl=0.0181`, `TapI=1.025` | verified_from_model_file |
| Series inductor | `L=3.50133 [uH]` between the 22 kV side and local step-down branch | verified_from_model_file |
| Local step-down transformer | `Name=E_2_30_1`, `Tmva3=110.4`, `V1LL=0.6`, `V2LL=22`, `Xl=0.06245`, `Config1=2`, `Config2=2` | verified_from_model_file |
| IBR block | `IBR_AVM_2_1_1`, instance `475433949` | verified_from_model_file |

## Input Bus Status

The definition confirms an 8-signal `Inputs` bus and a 6-signal `Flags` bus. The semantic ordering (`Sbase`, `Pini`, `Pord`, `Qord`, `Pfcmd`, `DB`, `QIBR`, `INV_Vbase`) is consistent with the user's GUI observation, but the static XML scan did not fully reconstruct the bus wiring order. Status: inferred, GUI confirmation required.

## Open Items

- Exact source components feeding `Pini`, `Pord`, `Qord`, `Sbase`, `INV_Vbase`, and `DB/DBLK` remain unresolved from static parsing alone.
- The branch-to-bus identity `GBUS30/N30` is strongly supported by component naming `E_2_30_1` and user GUI evidence, but the final replacement candidate must be confirmed by clicking the branch in PSCAD.
- Direct controllable trip/block interface for the IBR is not exposed as a simple external `Dblk`-equivalent port; use an external breaker for first DFIG trial isolation.
