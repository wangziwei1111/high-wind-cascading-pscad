# Interface Shell

The interface shell is responsible for:

- Measurement collection.
- Fixed-order observation packing.
- One MATLAB call per interface step.
- Command unpacking and breaker fan-out.
- Actual breaker status feedback.
- Raw trace export.

It is not responsible for protection judgement, timers, event ordering, or cascade reasoning.

