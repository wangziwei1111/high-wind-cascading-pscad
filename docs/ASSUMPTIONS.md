# Assumptions

These assumptions are used only for the independent reproduction framework and MATLAB unit tests. They are not claimed to reproduce PSCAD results.

- LVRT curve points are parameterized in `config/protection_settings.yaml`; exact curve extraction from the thesis figures remains pending.
- UFLS frequency thresholds are configurable because the extracted text clearly reports three stages, 0.2 s delay, and 25/40/55 percent shedding, but the exact frequency thresholds were not available from text extraction.
- Overload inverse-time equation is implemented as a simple parameterized inverse curve anchored at 1.1 p.u. -> 5 s; the exact paper equation must be checked against the PDF formula before PSCAD coupling.
- PNNL three IBR buses and ports are not asserted by Codex; they must be identified in PSCAD GUI.
- Wind farm transformer, collector network, converter controller, and detailed DFIG parameters are pending manual Type-3 WTG import and thesis/PDF confirmation.

