#!/usr/bin/env python3
"""Audit the zero-Run, zero-model-change paper alignment deliverables."""

from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path
import sys
import xml.etree.ElementTree as ET


ROOT = Path(__file__).resolve().parents[2]
DATA_REF = ROOT / "data" / "reference"
DATA_VAL = ROOT / "data" / "validation"
DOCS = ROOT / "docs"
PSCAD = Path(r"C:\pscad_work\pnnl_39_3ibr_pscad46_strip5\PSCAD")
MAIN = PSCAD / "3IBR.pscx"
TRIAL = PSCAD / "3IBR_DFIG1_TRIAL.pscx"
GF46 = PSCAD / "3IBR_DFIG1_TRIAL.gf46"
EXPECTED_MAIN_SHA = "CBA120BB167CB7FA6C4A1AE4471268850AB61761EC1877EB7B87015627FE9DAB"
ALLOWED_CAPABILITY_STATUS = {
    "implemented_and_audited", "implemented_static_only", "implemented_but_unverified",
    "partially_available", "not_implemented", "not_found", "unknown",
}
ALLOWED_ALIGNMENT = {
    "strictly_reproduced", "structurally_aligned_adaptation", "partially_aligned",
    "missing", "contradicted", "unknown_due_to_source_gap",
}
REQUIRED_CATEGORIES = {
    "system topology and source replacement", "wind-farm / DFIG model", "initial fault type",
    "initial fault location", "fault clearing rule", "simulation duration", "line overload protection",
    "wind LVRT / trip protection", "conventional-generator protection",
    "under-frequency load shedding", "under-voltage load shedding",
    "temporary-overvoltage protection", "SVC", "STATCOM",
    "scenario comparison dimensions", "evaluation outputs",
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def params(element: ET.Element) -> dict[str, str]:
    return {p.get("name", ""): p.get("value", "") for p in element.findall("./paramlist/param")}


def artifact_fingerprint() -> list[dict[str, object]]:
    rows = []
    for pattern in ("*.f", "*.dta", "*.inf", "*.out", "*.exe"):
        for path in sorted(GF46.glob(pattern)):
            stat = path.stat()
            rows.append({"name": path.name, "size": stat.st_size, "mtime_ns": stat.st_mtime_ns, "sha256": sha256(path)})
    return rows


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def main() -> int:
    manifest = json.loads((DATA_REF / "paper_reproduction_source_manifest.json").read_text(encoding="utf-8"))
    evidence = read_csv(DATA_REF / "paper_reproduction_evidence_registry.csv")
    inventory = read_csv(DATA_REF / "current_pscad_model_capability_inventory.csv")
    alignment = read_csv(DATA_REF / "paper_reproduction_alignment_matrix.csv")
    design = json.loads((DATA_REF / "paper_reproduction_minimum_cascade_design.json").read_text(encoding="utf-8"))
    options = read_csv(DATA_REF / "paper_reproduction_next_stage_options.csv")
    fidelity = json.loads((DATA_REF / "paper_reproduction_fidelity_assessment.json").read_text(encoding="utf-8"))
    start = manifest["task_start_integrity"]

    root = ET.parse(TRIAL).getroot()
    channels = [params(user) for user in root.iter("User") if user.get("defn") == "master:pgb"]
    channel_fingerprint = hashlib.sha256("\n".join(sorted(json.dumps(row, sort_keys=True) for row in channels)).encode()).hexdigest().upper()
    definitions = {definition.get("name", "") for definition in root.iter("Definition")}
    definition_fingerprint = hashlib.sha256("\n".join(sorted(definitions)).encode()).hexdigest().upper()

    evidence_ids = {row["evidence_id"] for row in evidence}
    evidence_categories = {row["modeling_category"] for row in evidence}
    matrix_refs_ok = True
    for row in alignment:
        refs = [item for item in row["paper_evidence_id"].split(";") if item]
        matrix_refs_ok &= bool(refs) and all(item in evidence_ids for item in refs)
        matrix_refs_ok &= row["alignment_class"] in ALLOWED_ALIGNMENT
        matrix_refs_ok &= bool(row["safe_current_claim"]) and bool(row["prohibited_claim"])

    inventory_ok = all(
        row["current_status"] in ALLOWED_CAPABILITY_STATUS
        and bool(row["xml_or_fortran_evidence"])
        and bool(row["claim_boundary"])
        for row in inventory
    )
    selected = [row for row in options if row["selected"] == "yes"]
    next_stage_ok = (
        len(selected) == 1
        and selected[0]["next_stage"] == "branch observability only"
        and all(selected[0][key] for key in ("primary_paper_evidence", "current_model_evidence", "prerequisites", "explicit_claim_boundary"))
        and design["next_stage"] == "branch observability only"
        and design["primary_paper_evidence_supporting_order"] == ["E003", "E010", "E012"]
    )

    plan_text = (DOCS / "PAPER_REPRODUCTION_ALIGNMENT_AND_MINIMUM_CASCADE_PLAN.md").read_text(encoding="utf-8")
    gap_text = (DOCS / "PAPER_REPRODUCTION_GAP_REGISTER.md").read_text(encoding="utf-8")
    required_disclaimers = [
        "不构成论文的自然连锁故障复现",
        "controlled interface-validation sequence",
        "branch observability only",
        "没有修改 PSCAD、没有 Build、没有 Run",
    ]
    claim_boundary_ok = all(text in plan_text for text in required_disclaimers) and "not-yet-permitted claim" in gap_text

    main_ok = sha256(MAIN) == start["main_sha256"] == EXPECTED_MAIN_SHA
    trial_ok = sha256(TRIAL) == start["trial_sha256"]
    output_ok = len(channels) == start["output_channel_count"] == 262 and channel_fingerprint == start["output_channel_fingerprint"]
    definition_ok = len(definitions) == start["definition_count"] and definition_fingerprint == start["definition_name_fingerprint"]
    artifacts_unchanged = artifact_fingerprint() == start["generated_artifact_fingerprint"]

    statuses = {
        "paper_evidence_traceability_status": "pass" if REQUIRED_CATEGORIES <= evidence_categories and matrix_refs_ok else "fail",
        "current_model_inventory_status": "pass" if inventory_ok and len(inventory) >= 27 else "fail",
        "alignment_matrix_status": "pass" if matrix_refs_ok and len(alignment) >= 16 else "fail",
        "minimum_cascade_design_status": "pass" if design.get("design_status") == "minimum_chain_designed_not_implemented" else "fail",
        "next_stage_recommendation_status": "pass" if next_stage_ok else "fail",
        "main_project_integrity_status": "pass" if main_ok else "fail",
        "trial_project_integrity_status": "pass" if trial_ok else "fail",
        "no_pscad_model_change_status": "pass" if main_ok and trial_ok and output_ok and definition_ok else "fail",
        "no_build_status": "pass" if artifacts_unchanged else "fail",
        "no_run_status": "pass" if artifacts_unchanged else "fail",
        "strict_reproduction_status": "not_achieved" if fidelity["strict_reproduction_status"] == "not_achieved" else "fail",
        "structural_alignment_status": "partial" if fidelity["structural_alignment_status"] == "partial" else "fail",
        "claim_boundary_status": "pass" if claim_boundary_ok else "fail",
    }
    pass_values = {"pass", "not_achieved", "partial"}
    final_pass = all(value in pass_values for value in statuses.values())
    result = {
        "execution_status": "paper_reproduction_alignment_completed" if final_pass else "paper_reproduction_alignment_audit_failed",
        "paper_source_status": manifest["paper_source_status"],
        **statuses,
        "final_audit_status": "pass" if final_pass else "fail",
        "natural_cascade_propagation_status": "unavailable",
        "physical_causality_direction_status": "unavailable",
        "system_stability_status": "unavailable",
        "protection_coordination_status": "unavailable",
        "voltage_support_performance_status": "unavailable",
        "matlab_status": "not_added",
        "main_sha_start": start["main_sha256"], "main_sha_end": sha256(MAIN),
        "trial_sha_start": start["trial_sha256"], "trial_sha_end": sha256(TRIAL),
        "output_channel_count_start": start["output_channel_count"], "output_channel_count_end": len(channels),
        "generated_artifact_fingerprint_unchanged": artifacts_unchanged,
        "current_safe_name": fidelity["current_safe_name"],
        "selected_next_stage": design["next_stage"],
        "claim_boundary": "This audit aligns evidence and designs a future minimum chain only. It creates no PSCAD model change and validates no natural cascade, causality, stability, protection coordination, voltage support, or MATLAB coupling.",
    }
    DATA_VAL.mkdir(parents=True, exist_ok=True)
    (DATA_VAL / "paper_reproduction_alignment_final_audit.json").write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0 if final_pass else 2


if __name__ == "__main__":
    sys.exit(main())
