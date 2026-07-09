#!/usr/bin/env python3
"""Audit that Stage-13 reads the unique Stage-12 20 s runtime input."""

from __future__ import annotations

import json
from datetime import datetime

from stage13_common import GF46, INF, MAIN, PREFIX, REPO, STAGE12_TRIAL_SHA, TRIAL, sha256, write_json


def main() -> None:
    manifest = json.loads((REPO / "data/reference/stage12_run_manifest.json").read_text(encoding="utf-8"))
    outs = sorted(GF46.glob(f"{PREFIX}_*.out"))
    gates = {
        "stage12_manifest_result_pass": manifest["stage12_result_class"] == "stage12_two_line_paper_order_pass",
        "runtime_time_axis_20s": manifest["time_start_s"] == 0.0 and manifest["time_end_s"] == 20.0,
        "sample_count_2001": manifest["sample_count"] == 2001,
        "plot_step_0p01": abs(manifest["plot_step_s"] - 0.01) < 1e-12,
        "trial_sha_matches_stage12": manifest["trial_sha256"] == STAGE12_TRIAL_SHA == sha256(TRIAL),
        "inf_sha_matches_manifest": INF.exists() and sha256(INF) == manifest["inf_sha256"],
        "runtime_files_present": len(outs) >= 65,
    }
    status = "pass" if all(gates.values()) else "blocked_stage12_runtime_not_recoverable"
    audit = {
        "audit_name": "stage13_runtime_input_audit",
        "generated_at_local": datetime.now().astimezone().isoformat(timespec="seconds"),
        "stage13_runtime_input_status": status,
        "runtime_output_authoritative": True,
        "project_duration_field_non_authoritative": True,
        "main_sha256": sha256(MAIN),
        "trial_sha256": sha256(TRIAL),
        "stage12_manifest": manifest,
        "runtime_file_count": len(outs),
        "runtime_newest_mtime": datetime.fromtimestamp(max(p.stat().st_mtime for p in outs)).astimezone().isoformat(timespec="seconds") if outs else None,
        "gates": gates,
    }
    write_json(REPO / "data/validation/stage13_runtime_input_audit.json", audit)
    print(json.dumps({"stage13_runtime_input_status": status, "failed": [k for k, v in gates.items() if not v]}, indent=2))


if __name__ == "__main__":
    main()
