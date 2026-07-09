# Live Coupling Limitation And Substitute

The paper used PSCAD 4.6.2 and MATLAB 2016b for runtime interaction with MATLAB
`.m` files. That exact route is not the current project target.

## Limitation

The required software combination is old and not reliably available in the
current local environment. PSCAD can run the physical model, and MATLAB R2025a
can run the protection logic offline, but stable live PSCAD-MATLAB runtime
coupling has not been verified.

Therefore this repository must not describe the current workflow as live
runtime coupling.

## Substitute

The accepted substitute route is:

```text
offline MATLAB protection iteration + PSCAD feedback replay
```

or:

```text
offline quasi-dynamic protection loop
```

This route preserves the core physical meaning:

- PSCAD owns the electromagnetic transient physics.
- MATLAB owns the protection judgement.
- PSCAD executes real breaker feedback in a replay run.
- MATLAB audits the event chain.

## Claim Boundary

Allowed:

- "Offline feedback replay validation."
- "MATLAB protection decision computed from PSCAD-exported observations."
- "PSCAD replay executed scheduled breaker feedback."

Not allowed:

- "Live PSCAD-MATLAB runtime coupling is complete."
- "The original paper real-time interface has been reproduced."
- "The full bus-29 paper cascade has been reproduced."

The claim boundary can change only after a future PSCAD 4.6.2 + MATLAB 2016b
environment runs the live interface and produces recorded evidence.
