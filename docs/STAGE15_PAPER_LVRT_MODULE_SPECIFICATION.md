# Stage 15 paper LVRT module specification

Reusable module: `PAPER_WF_LVRT_TRIP`.

Instances: `WF33_LVRT_TRIP`, `WF35_LVRT_TRIP`, `WF38_LVRT_TRIP`.

Each instance must read only its own PCC voltage and drive only its own breaker.

Frozen rule comes from E004 / Fig. 2-3 / Eq. 2-8 and prior audit `type3_dfig_lvrt_trip_criterion_audit.json`.

- `Vs <= 0.20`: immediate trip.
- `0.20 < Vs < 0.90`: `t_allow = 0.625 + ((Vs - 0.20)/(0.90 - 0.20))*(2.0 - 0.625)`.
- `Vs >= 0.90` and below high-voltage bands: reset healthy state before latch.
- high-voltage bands use a non-overlap implementation convention: 1.10<=Vs<1.20 -> 10 s, 1.20<=Vs<1.25 -> 1 s, 1.25<=Vs<1.30 -> 0.5 s, Vs>=1.30 -> immediate.
