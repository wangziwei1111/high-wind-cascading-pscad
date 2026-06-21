# Next Stage Handoff

Do not begin automatic PSCAD model construction.

Next stage should start only after the user manually completes:

1. PNNL three-IBR project opens in PSCAD GUI and required E-TRAN libraries load.
2. Official PSCAD Type-3 WTG example is legally obtained and opens independently.
3. One IBR is manually replaced or bypassed with one Type-3 DFIG aggregate candidate, with wiring and ports documented.

After that, build and test a PSCAD-MATLAB closed-loop interface using the neutral command names in `docs/MATLAB_INTERFACE_SPEC.md`.

