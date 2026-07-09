#!/usr/bin/env python3
"""Finalize thermal-limit recovery audit, docs, and shadow-relay decision."""

from __future__ import annotations

import csv
import hashlib
import json
import subprocess
from datetime import datetime
from pathlib import Path


REPO = Path(__file__).resolve().parents[2]
MAIN = Path(r"C:\pscad_work\pnnl_39_3ibr_pscad46_strip5\PSCAD\3IBR.pscx")
TRIAL = Path(r"C:\pscad_work\pnnl_39_3ibr_pscad46_strip5\PSCAD\3IBR_DFIG1_TRIAL.pscx")
EXPECTED_MAIN = "CBA120BB167CB7FA6C4A1AE4471268850AB61761EC1877EB7B87015627FE9DAB"
EXPECTED_TRIAL = "F81959EA62211FF9C1536C8481B67675AFE4DDCC3C56E804D048731A4B88A300"


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest().upper()


def read_json(path: Path) -> object:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fields: list[str] = []
    for row in rows:
        for key in row:
            if key not in fields:
                fields.append(key)
    with path.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows(rows)


def status_lines() -> list[str]:
    return subprocess.check_output(["git", "status", "--short"], cwd=REPO, text=True).splitlines()


def update_docs_and_refs(registry: dict[str, object], mapping: dict[str, object]) -> None:
    coverage = mapping["full_network_protection_rating_coverage_status"]
    doc = f"""# TLine continuous thermal limit recovery and mapping

Generated: {datetime.now().isoformat(timespec="seconds")}

## Result

- Current-model branch identity mapping: 31 exact mappings to the PNNL 3IBR PSS/E RAW branch table.
- Protection-grade continuous thermal rating coverage: `{coverage}`
- Protection-grade loading ratio: not generated.
- Shadow relay modeling readiness: blocked.

The important distinction is that branch identity mapping succeeded, but rating
recovery failed.  The current 31 PSCAD TLines match the open/local PNNL 3IBR RAW
network branches by from/to/circuit identity and exact R/X/B values.  However,
all mapped current-network branches have `RATE1..RATE12 = 0.0`, so Rate-A or
normal continuous thermal rating remains unspecified.

## Source summary

- Sources registered: {registry["source_count"]}
- Reproducible public/context sources: {registry["reproducible_public_source_count"]}
- Adopted for branch identity mapping: {registry["adopted_source_count"]}
- Adopted for protection-grade thermal rating: 0

## E_16_19_1

`E_16_19_1` is a real current PSCAD TLine and the thesis-relevant named branch.
It maps exactly to the PNNL 3IBR RAW branch `16-19-1`, including R/X/B.  Its
RAW `RATE1` is `0.0`, so no continuous thermal limit is recovered and it cannot
enter a shadow-relay interface study.

## E_28_29_1

`E_28_29_1` is the previous highest 100-MVA-normalized apparent-power response
line.  It maps exactly to the PNNL 3IBR RAW branch `28-29-1`, including R/X/B.
Its RAW `RATE1` is also `0.0`, so it remains only a response-index observation,
not an overload or shadow-relay candidate.

## Boundary

`100-MVA-normalized apparent-power response index` remains available for
describing dynamic response.  `protection-grade loading ratio` requires an
auditable per-line continuous thermal/normal rating, which was not recovered.
No PSCAD model file was modified, and no Build or Run was performed.
"""
    (REPO / "docs/TLINE_CONTINUOUS_THERMAL_LIMIT_RECOVERY_AND_MAPPING.md").write_text(doc, encoding="utf-8")
    addendum = """

## Stage-six thermal-limit recovery result

Stage six recovered exact branch identity mapping from the current PSCAD TLines
to the PNNL 3IBR RAW network branch table, but did not recover usable continuous
thermal limits: all mapped current-network branch RATE fields are zero.  The
safe quantity remains the `100-MVA-normalized apparent-power response index`;
`protection-grade loading ratio` remains unavailable, and shadow relay modeling
remains blocked.
"""
    for rel in [
        "docs/TLINE_TOTAL_MVA_RATING_SEMANTIC_AUDIT.md",
        "docs/FULL_NETWORK_TLINE_RATING_AND_LOADING_AUDIT.md",
        "docs/PAPER_ALIGNED_20S_DYNAMIC_RUN_AND_TLINE_RESPONSE.md",
        "docs/PAPER_REPRODUCTION_ALIGNMENT_AND_MINIMUM_CASCADE_PLAN.md",
        "docs/PAPER_REPRODUCTION_GAP_REGISTER.md",
    ]:
        path = REPO / rel
        text = path.read_text(encoding="utf-8") if path.exists() else ""
        marker = "## Stage-six thermal-limit recovery result"
        if marker in text:
            text = text[: text.index(marker)].rstrip() + "\n"
        path.write_text(text.rstrip() + addendum.rstrip() + "\n", encoding="utf-8")

    decision = {
        "shadow_relay_modeling_readiness": "blocked",
        "recommended_candidate_line": None,
        "blocking_reason": "No auditable per-line continuous thermal limits were recovered; current PSCAD TLines map to open PNNL 3IBR RAW branches, but mapped branch RATE fields are zero/unspecified.",
        "next_task": "Continue searching for current PNNL/PSCAD original branch-rating data or obtain thesis-model line continuous limits that can be mapped to current TLines; do not enter relay modeling before that evidence exists.",
        "highest_normalized_apparent_power_response_line": "E_28_29_1",
        "thesis_relevant_line": "E_16_19_1",
        "coverage_status": coverage,
        "mapping_audit": "data/reference/current_tline_external_rating_mapping.json",
    }
    write_json(REPO / "data/reference/future_shadow_overload_candidate_decision.json", decision)

    cap_path = REPO / "data/reference/current_pscad_model_capability_inventory.json"
    cap = read_json(cap_path)
    cap["tline_thermal_limit_recovery_status"] = "exact_branch_mapping_recovered_but_no_protection_grade_ratings"
    cap["line_loading_ratio_status"] = "unavailable_no_recovered_continuous_thermal_rating"
    cap["future_shadow_overload_candidate"] = None
    for item in cap["capabilities"]:
        if item.get("capability_id") == "CAP03":
            item["current_status"] = "dynamic_raw_response_and_exact_open_raw_branch_mapping_available_no_thermal_rating"
            item["claim_boundary"] = "Raw P/Q/I and exact PNNL 3IBR RAW branch mapping are available; RATE fields are zero, so protection-grade loading ratio and overload remain unavailable."
    write_json(cap_path, cap)

    cap_csv = REPO / "data/reference/current_pscad_model_capability_inventory.csv"
    rows = read_csv(cap_csv)
    for row in rows:
        if row.get("capability_id") == "CAP03":
            row["current_status"] = "dynamic_raw_response_and_exact_open_raw_branch_mapping_available_no_thermal_rating"
            row["claim_boundary"] = "Raw P/Q/I and exact PNNL 3IBR RAW branch mapping are available; RATE fields are zero, so protection-grade loading ratio remains unavailable."
    write_csv(cap_csv, rows)

    fidelity_path = REPO / "data/reference/paper_reproduction_fidelity_assessment.json"
    fidelity = read_json(fidelity_path)
    fidelity["tline_thermal_limit_recovery_status"] = "fallback_no_protection_grade_rating_coverage"
    fidelity["line_loading_ratio_status"] = "unavailable_no_recovered_continuous_thermal_rating"
    fidelity["future_shadow_overload_candidate"] = None
    write_json(fidelity_path, fidelity)

    design_path = REPO / "data/reference/paper_reproduction_minimum_cascade_design.json"
    design = read_json(design_path)
    design["design_status"] = "blocked_before_shadow_relay_due_to_zero_unspecified_raw_rate_fields"
    design["next_stage"] = "rating-source acquisition only; no shadow relay until per-line continuous thermal limits are recovered"
    design["tline_thermal_limit_recovery"] = {"coverage_status": coverage, "shadow_relay_modeling_readiness": "blocked"}
    write_json(design_path, design)

    matrix_path = REPO / "data/reference/paper_reproduction_alignment_matrix.csv"
    rows = read_csv(matrix_path)
    for row in rows:
        if row.get("paper_step_id") == "P08":
            row["reasoning"] = "All 31 current PSCAD TLines have raw P/Q/I dynamic responses and exact mapping to PNNL 3IBR RAW branch identities, but the mapped RAW RATE fields are zero/unspecified. Only normalized apparent-power response remains available."
            row["safe_current_claim"] = "raw TLine P/Q/I response and exact PNNL 3IBR RAW branch identity mapping are available"
            row["prohibited_claim"] = "protection-grade loading ratio, overload, relay action, line trip, natural cascade or strict paper reproduction validated"
        if row.get("paper_step_id") == "P09":
            row["alignment_status"] = "gap"
            row["reasoning"] = "No current TLine has a recovered continuous thermal/normal rating; mapped PNNL 3IBR RAW RATE fields are zero."
            row["safe_current_claim"] = "line-overload rule remains documented only; no protection-grade rating basis recovered"
    write_csv(matrix_path, rows)


def main() -> int:
    registry = read_json(REPO / "data/reference/tline_thermal_limit_source_registry.json")
    mapping = read_json(REPO / "data/reference/current_tline_external_rating_mapping.json")
    update_docs_and_refs(registry, mapping)
    forbidden = [s for s in status_lines() if any(ext in s.lower() for ext in [".pscx", ".gf46", ".tli", ".out", ".inf", ".sav"])]
    main_sha = sha256(MAIN)
    trial_sha = sha256(TRIAL)
    trace = [
        {"check": "main_project_integrity_status", "status": "pass" if main_sha == EXPECTED_MAIN else "fail"},
        {"check": "trial_project_integrity_status", "status": "pass" if trial_sha == EXPECTED_TRIAL else "fail"},
        {"check": "forbidden_pscad_file_git_changes", "status": "pass" if not forbidden else "fail", "details": "; ".join(forbidden)},
        {"check": "full_network_protection_rating_coverage_status", "status": mapping["full_network_protection_rating_coverage_status"]},
        {"check": "shadow_relay_modeling_readiness", "status": "blocked"},
    ]
    final = {
        "artifact": "tline_thermal_limit_recovery_final_audit",
        "generated_at_local": datetime.now().isoformat(timespec="seconds"),
        "execution_status": "pass" if not forbidden and main_sha == EXPECTED_MAIN and trial_sha == EXPECTED_TRIAL else "fail",
        "main_project_integrity_status": trace[0]["status"],
        "trial_project_integrity_status": trace[1]["status"],
        "main_sha_start": registry["main_sha_current"],
        "trial_sha_start": registry["trial_sha_current"],
        "main_sha_final": main_sha,
        "trial_sha_final": trial_sha,
        "no_pscad_modification_status": "pass" if not forbidden else "fail",
        "no_build_status": "pass_no_build_invoked",
        "no_run_status": "pass_no_run_invoked",
        "tline_count": mapping["tline_count"],
        "source_registry_status": "pass",
        "mapping_coverage_status": mapping["mapping_counts"],
        "continuous_rating_semantic_status": mapping["continuous_rating_semantic_status"],
        "full_network_protection_rating_coverage_status": mapping["full_network_protection_rating_coverage_status"],
        "candidate_only_protection_rating_coverage_status": "fail_no_candidate_qualified",
        "protection_grade_loading_ratio_status": "not_generated_no_qualified_continuous_thermal_limits",
        "shadow_relay_modeling_readiness": "blocked",
        "recommended_candidate_line": None,
        "line_overload_status": "not_validated",
        "line_protection_status": "unavailable",
        "branch_trip_status": "unavailable",
        "natural_cascade_propagation_status": "unavailable",
        "physical_causality_direction_status": "unavailable",
        "system_stability_status": "unavailable",
        "protection_coordination_status": "unavailable",
        "voltage_support_performance_status": "unavailable",
        "matlab_status": "not_added",
        "e_16_19_1_status": mapping["e_16_19_1_status"],
        "e_28_29_1_status": mapping["e_28_29_1_status"],
    }
    write_csv(REPO / "data/validation/tline_thermal_limit_recovery_integrity_trace.csv", trace)
    write_json(REPO / "data/validation/tline_thermal_limit_recovery_final_audit.json", final)
    print(json.dumps({"execution_status": final["execution_status"], "coverage": final["full_network_protection_rating_coverage_status"], "shadow": final["shadow_relay_modeling_readiness"]}, indent=2))
    return 0 if final["execution_status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
