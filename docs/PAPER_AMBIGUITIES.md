# Paper Ambiguities

- The extracted text reports bus 29 near-area three-phase fault and 2.0 s duration, but the start time for that specific baseline table is not available in the extracted text.
- The baseline event text contains a possible mismatch: one line reports bus 38 wind farm LVRT failure and 850 MW loss, while the later paragraph says bus 35 first failed after node 38 voltage drop and 830 MW loss. This must be checked visually in the PDF table/paragraph.
- Exact LVRT/HVRT curve coordinates are figure-based and not reliably available from OCR text.
- Exact overload inverse-time formula appears near the thesis equation text but was not fully recoverable from OCR; MATLAB currently uses a parameterized anchored curve.
- Exact UFLS frequency thresholds were not recovered from the available text, only stage count, delay, and shedding percentages.
- Synchronous machine, exciter, governor, transformer, collector-line, and wind controller parameters are not fully public in the extracted text.

