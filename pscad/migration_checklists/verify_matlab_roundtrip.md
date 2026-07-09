# Verify MATLAB Roundtrip

- [ ] PSCAD sends one complete `obs` bundle per interface period.
- [ ] MATLAB calls `pscad_cascade_step(t, dt, obs, state, settings)`.
- [ ] MATLAB returns command arrays with expected lengths.
- [ ] PSCAD distributes commands according to `mapping/command_map.csv`.
- [ ] PSCAD returns breaker status in the next observation.
- [ ] `obs_trace.csv`, `cmd_trace.csv`, and `breaker_action_trace.csv` are exported.
- [ ] `event_chain.csv` includes command, action, and confirmation times when available.

