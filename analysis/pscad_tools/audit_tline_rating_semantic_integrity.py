#!/usr/bin/env python3
"""Finalize stage-five-B semantic integrity audit and correction artifacts."""

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
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest().upper()


def git_status() -> list[str]:
    return subprocess.check_output(["git", "status", "--short"], cwd=REPO, text=True).splitlines()


def update_stage5_files(semantic: dict[str, object], sanity: dict[str, object], normalized: dict[str, object]) -> None:
    basis_path = REPO / "data/reference/full_network_tline_rating_basis.json"
    basis = read_json(basis_path)
    basis["rating_coverage_status"] = "semantic_reclassified_not_protection_grade"
    basis["qualified_line_count"] = 0
    basis["apparent_power_rating_qualified_count"] = 0
    basis["stage5b_semantic_correction"] = {
        "semantic_classification": semantic["semantic_classification"],
        "loading_ratio_semantic_status": semantic["loading_ratio_semantic_status"],
        "corrected_safe_term": "100-MVA-normalized apparent-power response index",
        "reason": semantic["blocking_reason"],
    }
    for row in basis.get("rows", []):
        row["qualification_status"] = "model_total_mva_field_not_protection_grade"
        row["rating_continuous_or_short_term_status"] = "not_verified_continuous_thermal_or_protection_grade"
        row["rejection_reason"] = "Stage-five-B semantic audit found no independent continuous thermal/protection-grade evidence for the uniform 100 MVA field."
    write_json(basis_path, basis)

    audit_path = REPO / "data/validation/tline_rating_loading_final_audit.json"
    audit = read_json(audit_path)
    audit["tline_rating_semantic_stage5b_status"] = "corrected_not_protection_grade"
    audit["line_loading_ratio_status"] = "reclassified_as_100mva_normalized_apparent_power_response_index"
    audit["line_overload_status"] = "not_validated"
    audit["shadow_relay_modeling_readiness"] = "blocked"
    audit["semantic_correction_audit"] = "data/validation/tline_rating_semantic_final_audit.json"
    audit["claim_boundary"] = "Numeric S/model-Total-MVA response remains available; no protection-grade loading ratio, overload, relay, line trip, or natural cascade is validated."
    write_json(audit_path, audit)

    decision = {
        "shadow_relay_modeling_readiness": "blocked",
        "recommended_candidate_line": None,
        "blocking_reason": "Total MVA Rating lacks verified continuous thermal / protection-grade semantics",
        "required_next_task": "Find or import auditable per-line continuous thermal limits, or build a reproducible mapping between paper line ratings and current PSCAD TLine instances before any shadow overload relay modeling.",
        "highest_normalized_apparent_power_response_line": normalized.get("highest_normalized_apparent_power_response_line"),
        "current_safe_term_for_E_28_29_1": "highest normalized apparent-power response line",
        "prohibited_terms": ["shadow-relay candidate", "overload indication", "protection-grade loading ratio"],
        "semantic_audit": "data/reference/tline_total_mva_rating_semantic_audit.json",
    }
    write_json(REPO / "data/reference/future_shadow_overload_candidate_decision.json", decision)


def update_reference_status_files() -> None:
    cap_path = REPO / "data/reference/current_pscad_model_capability_inventory.json"
    cap = read_json(cap_path)
    for item in cap["capabilities"]:
        if item.get("capability_id") == "CAP03":
            item["existing_dynamic_evidence"] = "data/validation/tline_rating_semantic_final_audit.json; data/derived/full_network_tline_normalized_apparent_power_response.csv"
            item["current_status"] = "dynamic_raw_response_and_100mva_normalized_apparent_power_response_observed_no_protection_grade_loading"
            item["claim_boundary"] = "Full-network raw branch P/Q/I response and a 100-MVA-normalized apparent-power response index are available; verified thermal loading ratio, overload, relay, branch trip, causality and natural cascade remain unavailable."
    cap["tline_rating_loading_audit_status"] = "semantic_reclassified_not_protection_grade"
    cap["line_loading_ratio_status"] = "unavailable_no_verified_continuous_thermal_rating"
    cap["normalized_apparent_power_response_status"] = "available"
    cap["future_shadow_overload_candidate"] = None
    write_json(cap_path, cap)

    cap_csv = REPO / "data/reference/current_pscad_model_capability_inventory.csv"
    if cap_csv.exists():
        rows = read_csv(cap_csv)
        for row in rows:
            if row.get("capability_id") == "CAP03":
                row["existing_dynamic_evidence"] = "data/validation/tline_rating_semantic_final_audit.json; data/derived/full_network_tline_normalized_apparent_power_response.csv"
                row["current_status"] = "dynamic_raw_response_and_100mva_normalized_apparent_power_response_observed_no_protection_grade_loading"
                row["claim_boundary"] = "Raw P/Q/I and normalized S/model-MVA response are available; protection-grade loading ratio and overload remain unavailable."
        write_csv(cap_csv, rows)

    fidelity_path = REPO / "data/reference/paper_reproduction_fidelity_assessment.json"
    fidelity = read_json(fidelity_path)
    fidelity["power_flow_redistribution_status"] = "raw_branch_pqi_and_100mva_normalized_apparent_power_response_observed_not_causal"
    fidelity["line_loading_ratio_status"] = "unavailable_no_verified_continuous_thermal_rating"
    fidelity["tline_rating_loading_audit_status"] = "semantic_reclassified_not_protection_grade"
    fidelity["future_shadow_overload_candidate"] = None
    fidelity["highest_normalized_apparent_power_response_line"] = "E_28_29_1"
    write_json(fidelity_path, fidelity)

    design_path = REPO / "data/reference/paper_reproduction_minimum_cascade_design.json"
    design = read_json(design_path)
    design["design_status"] = "minimum_chain_blocked_before_shadow_relay_due_to_unverified_line_thermal_ratings"
    design["next_stage"] = "rating-source acquisition or paper-to-current-model rating mapping; no shadow relay until continuous thermal/protection-grade semantics are verified"
    design["tline_rating_semantic_stage5b"] = {
        "semantic_classification": "uniform_model_value_or_default_parameter",
        "shadow_relay_modeling_readiness": "blocked",
        "highest_normalized_apparent_power_response_line": "E_28_29_1",
    }
    for cand in design.get("candidates", []):
        cand["network_propagation_link"] = cand["network_propagation_link"].replace("loading redistribution", "100-MVA-normalized apparent-power response redistribution")
        cand["claim_boundary"] = "Raw branch P/Q/I and normalized S/model-MVA response are available; verified thermal loading, overload relay, line trip, or natural cascade behavior has not been validated."
        cand["missing_components"] = list(dict.fromkeys(cand.get("missing_components", []) + ["verified per-line continuous thermal ratings"]))
    write_json(design_path, design)

    matrix_path = REPO / "data/reference/paper_reproduction_alignment_matrix.csv"
    if matrix_path.exists():
        rows = read_csv(matrix_path)
        for row in rows:
            if row.get("paper_step_id") == "P08":
                row["current_project_component"] = "full-network TLine P/Q/I measurement plus 100-MVA-normalized apparent-power response index"
                row["current_project_evidence"] = "CAP03; data/validation/tline_rating_semantic_final_audit.json; data/derived/full_network_tline_normalized_apparent_power_response.csv"
                row["reasoning"] = "All 31 genuine current-model TLines have raw P/Q/I dynamic responses. Stage-five-B reclassified uniform .tli Total MVA Rating as a model/default field, so only a normalized S/model-MVA response index is available; no verified thermal loading ratio exists."
                row["minimum_adaptation_needed"] = "future dynamic Run and offline redistribution analysis using audited raw P/Q/I plus independently verified per-line thermal rating evidence"
                row["prerequisite_dependency"] = "full-network raw TLine observability is available; verified line thermal limits and dynamic scenario matrix remain future dependencies"
                row["safe_current_claim"] = "full-network raw TLine P/Q/I dynamic response and 100-MVA-normalized apparent-power response index were observed"
                row["prohibited_claim"] = "confirmed overload, protection-grade loading ratio, relay action, line trip, natural cascade, causality or strict paper reproduction validated"
            if row.get("paper_step_id") == "P09":
                row["reasoning"] = "A normalized S/model-MVA response index exists, but no verified continuous thermal rating, inverse-time overload relay, thermal memory, or trip criterion has been implemented or validated."
                row["minimum_adaptation_needed"] = "obtain auditable per-line continuous thermal limits before any shadow relay; then implement monitor-only criterion"
                row["safe_current_claim"] = "paper overload rule remains documented only; current model has normalized apparent-power response observations"
                row["prohibited_claim"] = "line overload protection implemented, thermal overload detected, or relay trip validated"
        write_csv(matrix_path, rows)


def write_docs(semantic: dict[str, object], sanity: dict[str, object]) -> None:
    doc = f"""# TLine Total MVA Rating semantic audit

Generated: {datetime.now().isoformat(timespec="seconds")}

This audit rechecks the stage-five assumption that every real PSCAD TLine
`Total MVA Rating = 100.0 MVA` can be used as a continuous thermal or
protection-grade line rating.

## Result

- Final semantic classification: `{semantic["semantic_classification"]}`
- Safe numerical interpretation: `100-MVA-normalized apparent-power response index`
- Protection-grade loading ratio: unavailable
- Shadow relay modeling readiness: blocked
- Blocking reason: `{semantic["blocking_reason"]}`

## Exact source

The field is traced to each TLine's XML `MVA` parameter in
`3IBR_DFIG1_TRIAL.pscx`; PSCAD generation writes it into each generated
`E_*.tli` file as `Total MVA Rating = 100.0`.

No local evidence was found that this uniform value is an independently
verified per-line continuous thermal limit. No generated runtime code path was
found that uses this field for thermal timing, warning, relay comparison,
limiting, breaker command, or branch trip.

## Sanity check

- Pre-fault index > 1: {sanity["pre_fault_ratio_above_one_count"]} lines
- Pre-fault index > 2: {sanity["pre_fault_ratio_above_two_count"]} lines
- Pre-fault index > 5: {sanity["pre_fault_ratio_above_five_count"]} lines

The P/Q -> S -> 100 MVA conversion chain still stands as a normalized response
index because P/Q were already audited as per-unit signals on a 100 MVA system
base. It does not stand as a protection-grade overload ratio.

## Stage-five correction

Earlier stage-five numeric files are retained for traceability, but their
interpretation is corrected. `E_28_29_1` may currently be called the highest
normalized apparent-power response line, not a future shadow-overload candidate.
"""
    (REPO / "docs/TLINE_TOTAL_MVA_RATING_SEMANTIC_AUDIT.md").write_text(doc, encoding="utf-8")

    addendum = """

## Stage-five-B semantic correction

The later TLine Total MVA semantic audit reclassified the uniform `100.0 MVA`
field as `uniform_model_value_or_default_parameter`, not a verified continuous
thermal or protection-grade rating. Therefore previous S/100 MVA values must be
read as a `100-MVA-normalized apparent-power response index`, not an overload
ratio. `E_28_29_1` remains only the highest normalized apparent-power response
line. Shadow overload relay modeling is blocked until auditable per-line
continuous thermal limits, or a reproducible paper-to-current-model rating
mapping, are available.
"""
    for rel in [
        "docs/FULL_NETWORK_TLINE_RATING_AND_LOADING_AUDIT.md",
        "docs/PAPER_ALIGNED_20S_DYNAMIC_RUN_AND_TLINE_RESPONSE.md",
        "docs/PAPER_REPRODUCTION_ALIGNMENT_AND_MINIMUM_CASCADE_PLAN.md",
        "docs/PAPER_REPRODUCTION_GAP_REGISTER.md",
    ]:
        p = REPO / rel
        text = p.read_text(encoding="utf-8") if p.exists() else ""
        marker = "## Stage-five-B semantic correction"
        if marker in text:
            text = text[: text.index(marker)].rstrip() + "\n"
        p.write_text(text.rstrip() + addendum.rstrip() + "\n", encoding="utf-8")


def main() -> int:
    semantic = read_json(REPO / "data/reference/tline_total_mva_rating_semantic_audit.json")
    sanity = read_json(REPO / "data/derived/full_network_tline_100mva_sanity_metrics.json")
    normalized = read_json(REPO / "data/derived/full_network_tline_normalized_apparent_power_response.json")
    update_stage5_files(semantic, sanity, normalized)
    update_reference_status_files()
    write_docs(semantic, sanity)

    status_lines = git_status()
    forbidden_exts = (".pscx", ".gf46", ".tli", ".out", ".inf", ".sav")
    forbidden = [s for s in status_lines if any(ext in s.lower() for ext in forbidden_exts)]
    trace = [
        {"check": "main_project_integrity_status", "status": "pass" if sha256(MAIN_PSCX) == EXPECTED_MAIN_SHA else "fail"},
        {"check": "trial_project_integrity_status", "status": "pass" if sha256(TRIAL_PSCX) == EXPECTED_TRIAL_SHA else "fail"},
        {"check": "forbidden_pscad_file_git_changes", "status": "pass" if not forbidden else "fail", "details": "; ".join(forbidden)},
        {"check": "semantic_classification", "status": semantic["semantic_classification"]},
        {"check": "shadow_relay_modeling_readiness", "status": "blocked"},
    ]
    final = {
        "artifact": "tline_rating_semantic_final_audit",
        "generated_at_local": datetime.now().isoformat(timespec="seconds"),
        "execution_status": "pass" if not forbidden else "fail",
        "main_sha_start": semantic["main_sha_start"],
        "trial_sha_start": semantic["trial_sha_start"],
        "main_sha_final": sha256(MAIN_PSCX),
        "trial_sha_final": sha256(TRIAL_PSCX),
        "main_project_integrity_status": trace[0]["status"],
        "trial_project_integrity_status": trace[1]["status"],
        "no_pscad_modification_status": "pass" if not forbidden else "fail",
        "no_build_status": "pass_no_build_invoked_by_this_audit",
        "no_run_status": "pass_no_run_invoked_by_this_audit",
        "tline_count": semantic["tline_count"],
        "raw_tline_signal_count": 186,
        "xml_output_channel_count": 448,
        "total_mva_rating_origin_status": semantic["total_mva_rating_origin_status"],
        "total_mva_rating_runtime_usage_status": semantic["total_mva_rating_runtime_usage_status"],
        "p_q_unit_chain_status": semantic["p_q_to_s_to_100mva_chain_status"],
        "baseline_sanity_status": sanity["baseline_sanity_status"],
        "pre_fault_ratio_above_one_count": sanity["pre_fault_ratio_above_one_count"],
        "pre_fault_ratio_above_two_count": sanity["pre_fault_ratio_above_two_count"],
        "pre_fault_ratio_above_five_count": sanity["pre_fault_ratio_above_five_count"],
        "semantic_classification": semantic["semantic_classification"],
        "loading_ratio_semantic_status": semantic["loading_ratio_semantic_status"],
        "shadow_relay_modeling_readiness": "blocked",
        "recommended_candidate_line": None,
        "highest_normalized_apparent_power_response_line": normalized["highest_normalized_apparent_power_response_line"],
        "line_overload_status": "not_validated",
        "line_protection_status": "unavailable",
        "branch_trip_status": "unavailable",
        "natural_cascade_propagation_status": "unavailable",
        "physical_causality_direction_status": "unavailable",
        "system_stability_status": "unavailable",
        "protection_coordination_status": "unavailable",
        "voltage_support_performance_status": "unavailable",
        "matlab_status": "not_added",
        "claim_boundary": "Stage-five-B only verifies TLine Total MVA field semantics and corrects stage-five wording; it modifies no PSCAD model, performs no Build/Run, and adds no protection or line trip.",
    }
    write_csv(REPO / "data/validation/tline_rating_semantic_integrity_trace.csv", trace)
    write_json(REPO / "data/validation/tline_rating_semantic_final_audit.json", final)
    print(json.dumps({"execution_status": final["execution_status"], "semantic_classification": final["semantic_classification"], "shadow_relay_modeling_readiness": final["shadow_relay_modeling_readiness"]}, indent=2))
    return 0 if final["execution_status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
