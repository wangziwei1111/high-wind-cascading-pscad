# Stage 10B fault-to-DFIG interface alignment

## Static result

Decision: `no_defensible_electrical_difference_found`.

The XML layout changed around E_28_29_1 when `PAPER_OVL1_BRK_CMD` was inserted. A coordinate-only inspection appears to show a 36 px gap between graphical objects. That appearance is not an electrical disconnection.

The authoritative generated `P3.dta` node map shows the Stage-9 breaker internal nodes `NT_84(1..3)` connected to `N29(1..3)`. The three-phase fault branches also reference `N29(1..3)`, as in Stage 4. Fault parameters, timing, TLine parameters, DFIG breaker identity, and scoped interfaces remain unchanged. The breaker contributes its intentional closed resistance `RON=1e-3 ohm`; no evidence establishes that as an erroneous parameter or as the cause of the observed voltage difference.

## Decision and stop condition

No GUI correction is defensible. Adding a wire based on graphical coordinates could create an unintended parallel path or breaker bypass. Changing breaker RON, fault strength, LVRT threshold/delay, or network topology would also exceed the evidence and the permitted scope.

Therefore Stage 10B is statically blocked before GUI, Build, and Run. Required next evidence is a compiled Stage-4/Stage-9 nodal or admittance comparison around N29 and the DFIG PCC, plus an initial-condition/power-flow comparison that identifies one specific non-intended external-interface difference.

The trial remains at its Stage-9 SHA and Run Duration. No model or project setting was changed.
