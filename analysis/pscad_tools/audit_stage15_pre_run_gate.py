#!/usr/bin/env python3
"""Stage 15 pre-run gate after the user completes GUI refactor and Build."""

from __future__ import annotations

import json
from datetime import datetime

from stage15_common import (
    EXPECTED_MAIN_SHA,
    LEGACY_TRIAL,
    LEGACY_TRIAL_SHA,
    MAIN,
    NEW_GF46,
    NEW_TRIAL,
    OUTPUT_CHANNELS,
    REPO,
    sha256,
    write_json,
)


def main() -> int:
    now = datetime.now().astimezone().isoformat(timespec="seconds")
    checks: dict[str, bool] = {
        "main_sha_unchanged": MAIN.exists() and sha256(MAIN) == EXPECTED_MAIN_SHA,
        "legacy_trial_unchanged": LEGACY_TRIAL.exists() and sha256(LEGACY_TRIAL) == LEGACY_TRIAL_SHA,
        "new_trial_exists": NEW_TRIAL.exists(),
        "new_gf46_exists": NEW_GF46.exists(),
        "new_inf_exists": (NEW_GF46 / "3IBR_PAPER_WF33_35_38_TRIAL.inf").exists(),
        "new_p3_dta_exists": (NEW_GF46 / "P3.dta").exists(),
        "new_p3_map_exists": (NEW_GF46 / "3IBR_PAPER_WF33_35_38_TRIAL.map").exists() or (NEW_GF46 / "3IBR.map").exists(),
        "freeze_files_exist": all((REPO / p).exists() for p in [
            "data/reference/stage15_clean_baseline_selection.json",
            "data/reference/stage15_lvrt_module_parameter_freeze.json",
            "data/reference/stage15_output_minimum_manifest.json",
            "data/reference/stage15_gui_change_manifest.json",
        ]),
    }
    status = "PASS" if all(checks.values()) else "BLOCKED"
    audit = {
        "audit_name": "stage15_pre_run_gate",
        "generated_at_local": now,
        "gate_status": status,
        "checks": checks,
        "required_new_output_channels": OUTPUT_CHANNELS,
        "manual_gate_items_after_build": [
            "Verify exactly WF33/WF35/WF38 at bus33/35/38.",
            "Verify bus30 is G_30_0_1_DYR and no bus30 DFIG/IBR remains.",
            "Verify each LVRT reads only its own PCC voltage.",
            "Verify no OVL1/OVL2 or fixed-time path drives windfarm breakers.",
        ],
        "claim_boundary": "This gate is automatic file/build-integrity gate plus explicit checklist. It does not run PSCAD.",
    }
    write_json(REPO / "data/validation/stage15_pre_run_gate.json", audit)
    print(f"STAGE15 PRE-RUN GATE: {status}")
    print(json.dumps(audit, ensure_ascii=False, indent=2))
    return 0 if status == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
