#!/usr/bin/env python3
"""Audit Stage-12 runtime paper-order result."""

from __future__ import annotations

import json
import sys

from stage12_common import REPO


def main() -> int:
    manifest = json.loads((REPO / "data/reference/stage12_run_manifest.json").read_text(encoding="utf-8"))
    checks = {
        "runtime_detected": manifest["execution_status"] == "stage12_runtime_outputs_detected",
        "time_axis_20s": manifest["time_start_s"] == 0.0 and manifest["time_end_s"] == 20.0 and manifest["sample_count"] == 2001,
        "final_class_allowed": manifest["stage12_result_class"] in {
            "stage12_two_line_paper_order_pass",
            "stage12_second_line_trip_not_observed",
            "stage12_second_line_pickup_not_sustained",
            "stage12_second_line_pre_first_trip_pickup",
            "stage12_second_line_trip_before_first_line",
            "stage12_dfig_or_first_line_order_not_preserved",
            "stage12_pre_run_gate_blocked",
            "stage12_runtime_output_parser_fallback",
        },
    }
    failed = [name for name, ok in checks.items() if not ok]
    print(json.dumps({"checks": checks, "failed": failed, "stage12_result_class": manifest["stage12_result_class"]}, indent=2))
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
