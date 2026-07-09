# Stage 9 short-run relay initialization root cause

Generated: 2026-07-03T17:22:49

## Unique root cause

Timer component 2132554116 has both VOn (top, component 2118574082) and VOff (bottom, component 522397627) connected to 1.0. PSCAD defines O=TIMER3(TS,TD,F,FSet,VOff,VOn); therefore O is 1 before completion as well as after completion. O drives latch S, so latch Q, TRIP_REQUEST and BRK_CMD assert at t=0 even while ABOVE_THRESHOLD is 0.

The installed PSCAD master definition has Timer ports `F`, `VOn` (top), `VOff`
(bottom), and one output `O`. Its generated equation is
`O = TIMER3(TS, TD, F, FSet, VOff, VOn)`. The official component semantics make
the timer active when `F < FSet`; otherwise it returns `VOff`.

The Timer has no separate enable or reset port. `F` is the active-low trigger:
`F < 0.5` starts/continues the delay, while `F > 0.5` returns `O` to `VOff` and
resets the timing condition. The right-side `O` is the single delayed-completion
output and is already connected to latch `S`; no output-port swap is required.

The relay uses `F = 1 - ABOVE_THRESHOLD`, `FSet = 0.5`, `TS = 5.0 s`, and
`TD = 100 s`. Thus `ABOVE_THRESHOLD=0` correctly gives `F=1` (inactive), but the
current `VOff=1.0` incorrectly makes the inactive output high. Stage-8 runtime
data directly confirms `ABOVE_THRESHOLD=0` and `TIMER_STATE=1` at `t=0`.

## Minimal repair

Change only Constant component `522397627`, connected directly to Timer
`VOff`/bottom, from `1.0` to `0.0`. Keep the upper `VOn=1.0` constant and every
wire unchanged. The existing Simple RS latch already has `QInit=Low [0]`,
Timer `O -> S`, constant `0 -> R`, and `Q -> TRIP_REQ`; those are correct once
the Timer inactive value is zero.

Separately set trial `Duration of Run` from `20.0 s` to `9.0 s`. Keep the EMTDC
time step at `5 us` and Channel Plot Step at `10000 us` (`0.01 s`). This does
not alter the fault, relay calculations, breaker boundary, PGB configuration,
or any of the 13 Stage-8 runtime channel mappings.
