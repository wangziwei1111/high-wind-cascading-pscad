# Paper Parameter Extraction

Source: Xu Youxin, 2024, `高比例风电系统连锁故障分析与抑制措施研究`.

Confirmed extracted values are captured in `config/paper_extracted_parameters.yaml`.

Key direct parameters:

- Base system: IEEE 39-bus, 220 kV, 10 generators, 39 buses, 46 lines.
- Wind replacement buses: 33, 35, 38.
- Wind model: WECC second-generation Type-3 DFIG generic model.
- Wind penetration case: 30 percent.
- Simulation duration: 20 s.
- Overload protection anchor: 1.1 p.u. loading -> 5 s delay, with shorter delay as loading increases.
- Conventional generator protection: 47.5 Hz under-frequency, 51.5 Hz over-frequency, 10 s delay; 0.8 p.u. under-voltage, 1.3 p.u. over-voltage, 2 s delay.
- Load shedding: three-stage UFLS with 0.2 s delay and 25/40/55 percent shedding; UVLS at 0.8 p.u., 1.0 s delay, 25 percent shedding.
- Transient overvoltage: 1.3 p.u., no intentional delay.
- Baseline example: three-phase short circuit near bus 29, fault duration 2.0 s.
- Reactive compensation comparison: SVC and STATCOM, 300 MVar at bus 28, compared for a three-phase fault near bus 4.

All PSCAD model execution details remain pending user validation in PSCAD GUI.

