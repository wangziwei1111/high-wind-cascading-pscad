# Verify Breaker Mapping

- [ ] Every line has `BR_LINE_k_FROM` and `BR_LINE_k_TO`.
- [ ] Each `cmd.line_trip_cmd(k)` opens both line breakers.
- [ ] Each wind command opens exactly one wind outlet breaker.
- [ ] Each generator command opens exactly one generator outlet breaker.
- [ ] Load commands open only staged load switches.
- [ ] PSCAD reports actual online/offline state after command execution.
- [ ] MATLAB does not infer successful opening without PSCAD feedback.

