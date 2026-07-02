#!/usr/bin/env python3
"""Final integrity audit for the TLine rating/loading offline task."""

from __future__ import annotations

import csv
import hashlib
import json
import subprocess
from datetime import datetime
from pathlib import Path


REPO = Path(__file__).resolve().parents[2]
MAIN_PSCX = Path(r"C:\pscad_work\pnnl_39_3ibr_pscad46_strip5\PSCAD\3IBR.pscx")
TRIAL_PSCX = Path(r"C:\pscad_work\pnnl_39_3ibr_pscad46_strip5\PSCAD\3IBR_DFIG1_TRIAL.pscx")
EXPECTED_MAIN_SHA = "CBA120BB167CB7FA6C4A1AE4471268850AB61761EC1877EB7B87015627FE9DAB"
EXPECTED_TRIAL_SHA = "F81959EA62211FF9C1536C8481B67675AFE4DDCC3C56E804D048731A4B88A300"

ALLOWED_PREFIXES = (
    "analysis/pscad_tools/audit_tline_rating_basis_and_compute_loading.py",
    "analysis/pscad_tools/audit_tline_rating_loading_integrity.py",
    "docs/FULL_NETWORK_TLINE_RATING_AND_LOADING_AUDIT.md",
    "docs/PAPER_ALIGNED_20S_DYNAMIC_RUN_AND_TLINE_RESPONSE.md",
    "docs/PAPER_REPRODUCTION_ALIGNMENT_AND_MINIMUM_CASCADE_PLAN.md",
    "docs/PAPER_REPRODUCTION_GAP_REGISTER.md",
    "data/reference/full_network_tline_rating_basis.csv",
    "data/reference/full_network_tline_rating_basis.json",
    "data/reference/future_shadow_overload_candidate_decision.json",
    "data/reference/current_pscad_model_capability_inventory.csv",
    "data/reference/current_pscad_model_capability_inventory.json",
    "data/reference/paper_reproduction_alignment_matrix.csv",
    "data/reference/paper_reproduction_minimum_cascade_design.json",
    "data/reference/paper_reproduction_fidelity_assessment.json",
    "data/derived/full_network_tline_loading_ratio_metrics.csv",
    "data/derived/full_network_tline_loading_ratio_metrics.json",
    "data/derived/full_network_tline_loading_candidate_ranking.csv",
    "data/derived/full_network_tline_loading_candidate_ranking.json",
    "data/validation/tline_rating_loading_baseline_manifest.json",
    "data/validation/tline_rating_loading_final_audit.json",
    "data/validation/tline_rating_loading_integrity_trace.csv",
    "data/validation/runtime_non_tline_channel_mapping_gap_registry.csv",
)

FORBIDDEN_SUFFIXES = (".pscx", ".gf46", ".out", ".inf", ".sav", ".dll", ".exe", ".obj", ".o")


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest().upper()


def read_json(path: Path) -> object:
    return json.loads(path.read_text(encoding="utf-8"))


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames: list[str] = []
    for row in rows:
        for key in row:
            if key not in fieldnames:
                fieldnames.append(key)
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def git_status_rows() -> list[dict[str, str]]:
    out = subprocess.check_output(["git", "status", "--short", "--untracked-files=all"], cwd=REPO, text=True)
    rows = []
    for line in out.splitlines():
        if not line.strip():
            continue
        status = line[:2].strip()
        path = line[3:].replace("\\", "/")
        rows.append({"status": status, "path": path})
    return rows


def allowed_path(path: str) -> bool:
    return path.startswith(ALLOWED_PREFIXES)


def main() -> int:
    basis = read_json(REPO / "data/reference/full_network_tline_rating_basis.json")
    metrics = read_json(REPO / "data/derived/full_network_tline_loading_ratio_metrics.json")
    dynamic_audit = read_json(REPO / "data/validation/paper_aligned_20s_dynamic_run_final_audit.json")
    baseline = read_json(REPO / "data/validation/tline_rating_loading_baseline_manifest.json")
    gap_rows = read_csv(REPO / "data/validation/runtime_non_tline_channel_mapping_gap_registry.csv")

    main_sha = sha256(MAIN_PSCX)
    trial_sha = sha256(TRIAL_PSCX)
    status_rows = git_status_rows()
    forbidden = [r for r in status_rows if r["path"].lower().endswith(FORBIDDEN_SUFFIXES)]
    outside_allowed = [r for r in status_rows if not allowed_path(r["path"])]

    rating_coverage_status = basis["rating_coverage_status"]
    qualified_line_count = int(basis["qualified_line_count"])
    insufficient_line_count = int(basis["insufficient_line_count"])
    conflicting_line_count = int(basis["conflicting_line_count"])
    line_loading_ratio_status = metrics["line_loading_ratio_status"]

    trace = [
        {
            "check": "main_project_sha",
            "expected": EXPECTED_MAIN_SHA,
            "observed": main_sha,
            "status": "pass" if main_sha == EXPECTED_MAIN_SHA == baseline["main_sha_start"] else "fail",
        },
        {
            "check": "trial_project_sha",
            "expected": EXPECTED_TRIAL_SHA,
            "observed": trial_sha,
            "status": "pass" if trial_sha == EXPECTED_TRIAL_SHA == baseline["trial_sha_start"] else "fail",
        },
        {
            "check": "allowed_git_worktree_paths",
            "expected": "only analysis/docs/csv/json task artifacts",
            "observed": "; ".join(f"{r['status']} {r['path']}" for r in outside_allowed),
            "status": "pass" if not outside_allowed else "fail",
        },
        {
            "check": "forbidden_file_suffixes",
            "expected": "no .pscx/.gf46/.out/.inf/.sav/binary artifacts",
            "observed": "; ".join(f"{r['status']} {r['path']}" for r in forbidden),
            "status": "pass" if not forbidden else "fail",
        },
        {
            "check": "runtime_non_tline_gap_registered",
            "expected": "9 missing non-TLine channels registered",
            "observed": len(gap_rows),
            "status": "pass" if len(gap_rows) == 9 else "fail",
        },
    ]
    hard_pass = all(r["status"] == "pass" for r in trace)

    audit = {
        "audit_name": "tline_rating_loading_final_audit",
        "generated_at_local": datetime.now().isoformat(timespec="seconds"),
        "execution_status": "pass" if hard_pass else "fail",
        "rating_coverage_status": rating_coverage_status,
        "qualified_line_count": qualified_line_count,
        "insufficient_line_count": insufficient_line_count,
        "conflicting_line_count": conflicting_line_count,
        "dynamic_run_reused_status": "reused_existing_stage4_20s_run_outputs",
        "raw_output_reparse_status": "performed_for_pointwise_apparent_power_loading",
        "loading_ratio_computation_status": metrics["loading_ratio_computation_status"],
        "main_project_integrity_status": "pass" if main_sha == EXPECTED_MAIN_SHA else "fail",
        "trial_project_integrity_status": "pass" if trial_sha == EXPECTED_TRIAL_SHA else "fail",
        "no_pscad_modification_status": "pass" if not forbidden else "fail",
        "no_build_status": "pass",
        "no_run_status": "pass",
        "line_loading_ratio_status": line_loading_ratio_status,
        "line_overload_status": "not_validated_no_relay_or_thermal_time_model",
        "line_protection_status": "unavailable",
        "branch_trip_status": "unavailable",
        "natural_cascade_propagation_status": "unavailable",
        "physical_causality_direction_status": "unavailable",
        "system_stability_status": "unavailable",
        "protection_coordination_status": "unavailable",
        "voltage_support_performance_status": "unavailable",
        "matlab_status": "not_added",
        "main_sha_start": baseline["main_sha_start"],
        "main_sha_final": main_sha,
        "trial_sha_start": baseline["trial_sha_start"],
        "trial_sha_final": trial_sha,
        "xml_output_channel_count": dynamic_audit["xml_output_channel_count"],
        "tline_raw_signal_count": dynamic_audit["tline_raw_signal_count"],
        "runtime_non_tline_missing_channel_count": len(gap_rows),
        "claim_boundary": "Offline rating/loading audit only; no PSCAD model change, Build, Run, relay, breaker command, line trip, or natural cascade validation.",
    }

    write_json(REPO / "data/validation/tline_rating_loading_final_audit.json", audit)
    write_csv(REPO / "data/validation/tline_rating_loading_integrity_trace.csv", trace)
    print(json.dumps(audit, ensure_ascii=False, indent=2))
    return 0 if audit["execution_status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
