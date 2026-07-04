#!/usr/bin/env python3
"""Audit Stage 15 generator-to-windfarm replacement mapping."""

from __future__ import annotations

import csv
import json
from pathlib import Path

from stage15_common import REPO


def main() -> int:
    path = REPO / "data/reference/stage15_wf33_35_38_replacement_map.csv"
    rows = list(csv.DictReader(path.open(encoding="utf-8"))) if path.exists() else []
    status = "pass" if len(rows) == 3 and {r["paper_wind_farm_id"] for r in rows} == {"WF33", "WF35", "WF38"} else "blocked_windfarm_replacement_interface_unresolved"
    out = {
        "audit_name": "stage15_generator_bus_mapping_audit",
        "status": status,
        "row_count": len(rows),
        "required_windfarms": ["WF33", "WF35", "WF38"],
        "mapping_file": str(path),
    }
    (REPO / "data/validation").mkdir(parents=True, exist_ok=True)
    (REPO / "data/validation/stage15_generator_bus_mapping_audit.json").write_text(json.dumps(out, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(out, indent=2))
    return 0 if status == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
