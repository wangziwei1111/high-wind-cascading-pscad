#!/usr/bin/env python3
"""Extract/freeze Stage 15 paper WF layout and LVRT rule from existing audited evidence."""

from __future__ import annotations

import json
from datetime import datetime

from stage15_common import OUTPUT_CHANNELS, PAPER_WIND_POWER, REPO, write_json


def main() -> int:
    now = datetime.now().astimezone().isoformat(timespec="seconds")
    lvrt_curve = {
        "audit_name": "stage15_paper_lvrt_curve_transcription",
        "generated_at_local": now,
        "paper_evidence_id": "E004",
        "paper_section": "2.3.2 wind turbine voltage ride-through protection",
        "paper_figure_or_equation": "Fig. 2-3; Eq. 2-8",
        "source_audit": "data/reference/type3_dfig_lvrt_trip_criterion_audit.json",
        "regions": [
            {
                "paper_page": "11-12 (PDF 19-20)",
                "paper_figure_or_equation": "Eq. 2-8",
                "voltage_condition": "Vs <= 0.20",
                "delay_condition": "0 s immediate trip",
                "implementation_expression": "trip_request = 1 immediately",
                "reset_condition": "latched until run end / breaker open",
                "confidence": "project_boundary_decision_recorded",
            },
            {
                "paper_page": "11-12 (PDF 19-20)",
                "paper_figure_or_equation": "Eq. 2-8; Fig. 2-3",
                "voltage_condition": "0.20 < Vs < 0.90",
                "delay_condition": "0.625 + ((Vs - 0.20)/(0.90 - 0.20))*(2.0 - 0.625)",
                "implementation_expression": "use minimum-voltage latch inside one continuous low-voltage event, trip when elapsed >= t_allow(Vs_min)",
                "reset_condition": "if Vs >= 0.90 before latch, reset low-voltage event",
                "confidence": "high_for_interior_branch",
            },
            {
                "paper_page": "11-12 (PDF 19-20)",
                "paper_figure_or_equation": "Eq. 2-8",
                "voltage_condition": "0.90 <= Vs < 1.10",
                "delay_condition": "healthy/no low-voltage trip timing",
                "implementation_expression": "low-voltage timer reset if not already latched",
                "reset_condition": "normal state",
                "confidence": "engineering_translation",
            },
            {
                "paper_page": "11-12 (PDF 19-20)",
                "paper_figure_or_equation": "Eq. 2-8",
                "voltage_condition": "1.10 <= Vs < 1.20",
                "delay_condition": "10.0 s",
                "implementation_expression": "high-voltage delayed trip branch",
                "reset_condition": "reset if voltage returns to normal before latch",
                "confidence": "paper_formula_transcribed",
            },
            {
                "paper_page": "11-12 (PDF 19-20)",
                "paper_figure_or_equation": "Eq. 2-8",
                "voltage_condition": "1.20 <= Vs < 1.25",
                "delay_condition": "1.0 s",
                "implementation_expression": "high-voltage delayed trip branch",
                "reset_condition": "reset if voltage returns to normal before latch",
                "confidence": "paper_formula_transcribed",
            },
            {
                "paper_page": "11-12 (PDF 19-20)",
                "paper_figure_or_equation": "Eq. 2-8",
                "voltage_condition": "1.25 <= Vs < 1.30",
                "delay_condition": "0.5 s",
                "implementation_expression": "high-voltage delayed trip branch",
                "reset_condition": "reset if voltage returns to normal before latch",
                "confidence": "paper_formula_transcribed",
            },
            {
                "paper_page": "11-12 (PDF 19-20)",
                "paper_figure_or_equation": "Eq. 2-8",
                "voltage_condition": "Vs >= 1.30",
                "delay_condition": "0 s immediate trip",
                "implementation_expression": "trip_request = 1 immediately",
                "reset_condition": "latched until run end / breaker open",
                "confidence": "paper_formula_transcribed",
            },
        ],
    }
    freeze = {
        "audit_name": "stage15_lvrt_module_parameter_freeze",
        "generated_at_local": now,
        "module_name": "PAPER_WF_LVRT_TRIP",
        "instances": ["WF33_LVRT_TRIP", "WF35_LVRT_TRIP", "WF38_LVRT_TRIP"],
        "state_independence_required": True,
        "input_rule": "Each instance reads only its own PCC voltage.",
        "timer_method": "minimum-voltage latch within continuous low/high voltage event",
        "trip_latch_behavior": "once trip_request=1, latch for the run and drive only the local windfarm breaker",
        "output_channels_allowed": OUTPUT_CHANNELS,
        "paper_wind_layout": {"WF33": 33, "WF35": 35, "WF38": 38},
        "paper_reported_wind_power_MW": PAPER_WIND_POWER,
    }
    write_json(REPO / "data/reference/stage15_paper_lvrt_curve_transcription.json", lvrt_curve)
    write_json(REPO / "data/reference/stage15_lvrt_module_parameter_freeze.json", freeze)
    (REPO / "docs/STAGE15_PAPER_LVRT_MODULE_SPECIFICATION.md").write_text(
        "# Stage 15 paper LVRT module specification\n\n"
        "Reusable module: `PAPER_WF_LVRT_TRIP`.\n\n"
        "Instances: `WF33_LVRT_TRIP`, `WF35_LVRT_TRIP`, `WF38_LVRT_TRIP`.\n\n"
        "Each instance must read only its own PCC voltage and drive only its own breaker.\n\n"
        "Frozen rule comes from E004 / Fig. 2-3 / Eq. 2-8 and prior audit `type3_dfig_lvrt_trip_criterion_audit.json`.\n\n"
        "- `Vs <= 0.20`: immediate trip.\n"
        "- `0.20 < Vs < 0.90`: `t_allow = 0.625 + ((Vs - 0.20)/(0.90 - 0.20))*(2.0 - 0.625)`.\n"
        "- `Vs >= 0.90` and below high-voltage bands: reset healthy state before latch.\n"
        "- high-voltage bands use a non-overlap implementation convention: 1.10<=Vs<1.20 -> 10 s, 1.20<=Vs<1.25 -> 1 s, 1.25<=Vs<1.30 -> 0.5 s, Vs>=1.30 -> immediate.\n",
        encoding="utf-8",
    )
    print(json.dumps({"stage15_lvrt_freeze": "written", "instances": freeze["instances"]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
