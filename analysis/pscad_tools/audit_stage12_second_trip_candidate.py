#!/usr/bin/env python3
"""Audit Stage-12 second-trip candidate selection artifacts."""

from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

from stage12_common import DEFINITE_DELAY_S, REPO, STAGE11_FIRST_LINE_OPEN_S


def main() -> int:
    audit = json.loads((REPO / "data/validation/stage12_second_trip_candidate_final_audit.json").read_text(encoding="utf-8"))
    freeze_path = REPO / "data/reference/stage12_second_trip_parameter_freeze.json"
    ranking = list(csv.DictReader((REPO / "data/reference/stage12_second_trip_candidate_ranking.csv").open(encoding="utf-8")))
    checks = {
        "candidate_status_pass": audit["stage12_candidate_status"] == "pass",
        "top_three_screened_lines_present": len(audit["top_three_screened_lines"]) >= 3,
        "ranking_has_rejections_and_eligible_rows": len(ranking) >= 30 and any(r["candidate_status"] == "eligible" for r in ranking),
        "freeze_exists": freeze_path.exists(),
    }
    if freeze_path.exists():
        freeze = json.loads(freeze_path.read_text(encoding="utf-8"))
        checks.update({
            "selected_matches_audit": freeze["selected_tline_id"] == audit["selected_tline_id"],
            "pre_window_ends_at_first_trip": abs(freeze["pre_first_trip_window"][1] - STAGE11_FIRST_LINE_OPEN_S) < 1e-12,
            "post_window_is_at_least_5s": freeze["post_first_trip_5s_window"][1] - freeze["post_first_trip_5s_window"][0] >= DEFINITE_DELAY_S - 1e-12,
            "threshold_between_pre_and_floor": freeze["pre_first_trip_max_S"] < freeze["threshold_T"] < freeze["post_first_trip_5s_floor_S"],
            "expected_open_before_15s": freeze["expected_second_open_time_s"] <= 15.0,
        })
    failed = [name for name, ok in checks.items() if not ok]
    print(json.dumps({"checks": checks, "failed": failed, "selected_tline_id": audit.get("selected_tline_id")}, indent=2))
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
