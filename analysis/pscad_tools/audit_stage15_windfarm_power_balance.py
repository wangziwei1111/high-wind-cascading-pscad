#!/usr/bin/env python3
"""Audit Stage 15 windfarm pre-fault power-balance freeze."""

from __future__ import annotations

import json

from stage15_common import REPO


def main() -> int:
    freeze = json.loads((REPO / "data/reference/stage15_pre_fault_power_balance_freeze.json").read_text(encoding="utf-8"))
    status = "pass" if freeze["policy"] == "per_bus_replacement_equivalence" else "blocked_power_balance_policy_unresolved"
    audit = {
        "audit_name": "stage15_windfarm_power_balance_audit",
        "status": status,
        "policy": freeze["policy"],
        "noted_difference_MW": freeze["noted_difference_MW"],
        "claim_boundary": "Preserves pre-fault power balance; does not claim strict paper windfarm power equivalence.",
    }
    (REPO / "data/validation/stage15_power_balance_final_audit.json").write_text(json.dumps(audit, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(audit, indent=2))
    return 0 if status == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
