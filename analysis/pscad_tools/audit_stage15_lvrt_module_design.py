#!/usr/bin/env python3
"""Audit Stage 15 reusable LVRT module design freeze."""

from __future__ import annotations

import json

from stage15_common import REPO


def main() -> int:
    freeze = json.loads((REPO / "data/reference/stage15_lvrt_module_parameter_freeze.json").read_text(encoding="utf-8"))
    ok = freeze["module_name"] == "PAPER_WF_LVRT_TRIP" and freeze["state_independence_required"] and len(freeze["instances"]) == 3
    audit = {
        "audit_name": "stage15_lvrt_module_design_audit",
        "status": "pass" if ok else "blocked_paper_lvrt_curve_not_resolved",
        "module_name": freeze.get("module_name"),
        "instances": freeze.get("instances"),
        "state_independence_required": freeze.get("state_independence_required"),
    }
    (REPO / "data/validation/stage15_lvrt_module_design_audit.json").write_text(json.dumps(audit, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(audit, indent=2))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
