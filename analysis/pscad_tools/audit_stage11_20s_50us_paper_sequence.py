#!/usr/bin/env python3
"""Fail-fast audit wrapper for the Stage-11 runtime-derived artifacts."""

from __future__ import annotations

import json
import sys
from pathlib import Path


REPO = Path(__file__).resolve().parents[2]


def main() -> int:
    manifest = json.loads((REPO / "data/derived/stage11_20s_50us_runtime_manifest.json").read_text(encoding="utf-8"))
    audit = json.loads((REPO / "data/validation/stage11_20s_50us_final_audit.json").read_text(encoding="utf-8"))
    checks = {
        "runtime_outputs_detected": manifest["execution_status"] == "stage11_20s_50us_runtime_outputs_detected",
        "duration_reaches_20s": abs(manifest["time_end_s"] - 20.0) < 1e-9,
        "plot_step_is_0p01s": abs(manifest["plot_step_s_observed"] - 0.01) < 1e-12,
        "pre_fault_healthy": manifest["pre_fault_health"]["status"] == "healthy",
        "paper_order_pass": manifest["stage11_result_class"] == "stage11_20s_50us_paper_order_first_trip_pass",
        "timer_delay_5s": abs(manifest["paper_delay_observed_s"] - 5.0) <= 0.011,
        "audit_pass": audit["execution_status"] == "pass",
    }
    failed = [name for name, ok in checks.items() if not ok]
    print(json.dumps({"checks": checks, "failed": failed, "stage11_result_class": manifest["stage11_result_class"]}, indent=2))
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
