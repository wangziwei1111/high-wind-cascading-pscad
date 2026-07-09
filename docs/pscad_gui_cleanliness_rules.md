# PSCAD GUI Cleanliness Rules

## Allowed In The Clean Plant

- IEEE39 buses and 220 kV network representation.
- 46 line branches.
- Generator, wind-farm, transformer, load, and fault components.
- Real line-end breakers, wind outlet breakers, generator outlet breakers, and staged load-shedding switches.
- Voltage, current, power, frequency, min/max/RMS measurement points.
- Minimal PSCAD-MATLAB input/output ports.
- Minimal command latch, pulse hold, breaker driver, and status feedback logic.

## Not Allowed In The Clean Plant

- Protection threshold decisions.
- Protection timers.
- Cascade event ordering.
- Fault-chain reason judgement.
- Candidate follow-up fault screening.
- Plot generation and offline statistics.
- Temporary relay networks.
- Debug comparators and delay blocks that duplicate MATLAB logic.

## Interface Shell Boundary

The shell may pack measurements, call MATLAB once per interface step, distribute commands, latch breaker pulses, and export raw traces. It must not decide why a device should trip.

