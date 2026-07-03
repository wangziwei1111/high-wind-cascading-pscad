#!/usr/bin/env python3
"""Recover candidate open/local sources for TLine continuous thermal limits.

Read-only for PSCAD and runtime files.  Writes only registry/manifest artifacts.
"""

from __future__ import annotations

import csv
import hashlib
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path


REPO = Path(__file__).resolve().parents[2]
MAIN = Path(r"C:\pscad_work\pnnl_39_3ibr_pscad46_strip5\PSCAD\3IBR.pscx")
TRIAL = Path(r"C:\pscad_work\pnnl_39_3ibr_pscad46_strip5\PSCAD\3IBR_DFIG1_TRIAL.pscx")
GF46 = Path(r"C:\pscad_work\pnnl_39_3ibr_pscad46_strip5\PSCAD\3IBR_DFIG1_TRIAL.gf46")
RAW_3IBR = REPO / "external/pnnl-enhanced-ieee39/Enhanced IEEE 39-Bus System_3IBRs/PSSE/IEEE39_PV_30_BV_Pmax_Pmin_equals_Pgen.raw"
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


def git_head() -> str:
    return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=REPO, text=True).strip()


def create_manifest() -> dict[str, object]:
    path = REPO / "data/validation/tline_thermal_limit_recovery_baseline_manifest.json"
    if path.exists():
        return read_json(path)  # type: ignore[return-value]
    dyn = read_json(REPO / "data/validation/paper_aligned_20s_dynamic_run_final_audit.json")
    inv = read_json(REPO / "data/reference/full_network_tline_inventory.json")
    manifest = {
        "artifact": "tline_thermal_limit_recovery_baseline_manifest",
        "generated_at_local": datetime.now().isoformat(timespec="seconds"),
        "git_head_start": git_head(),
        "main_sha_start": sha256(MAIN),
        "trial_sha_start": sha256(TRIAL),
        "stage4_dynamic_run_commit": "44283ac40e51a032446dcf67c3d4208d17f3eb69",
        "stage5_loading_audit_commit": "8336584a99269ff8a158a7f3f49e3c7198ce99ef",
        "stage5b_semantic_audit_commit": "e48e7d496ed610496baf98ba67c717bace0597e9",
        "tline_inventory_path": "data/reference/full_network_tline_inventory.json",
        "tline_count": inv["inventory_count"],
        "tline_raw_signal_count": dyn["tline_raw_signal_count"],
        "xml_output_channel_count": dyn["xml_output_channel_count"],
        "existing_dynamic_output_paths": sorted(str(p) for p in GF46.glob("3IBR_DFIG1_TRIAL_*.out")),
        "existing_raw_run_manifest_path": "data/derived/paper_aligned_20s_run_manifest.json",
        "existing_normalized_response_paths": [
            "data/derived/full_network_tline_normalized_apparent_power_response.csv",
            "data/derived/full_network_tline_normalized_apparent_power_response.json",
        ],
        "existing_rating_semantic_audit_path": "data/validation/tline_rating_semantic_final_audit.json",
        "local_model_source_roots": [str(REPO / "external/pnnl-enhanced-ieee39"), str(GF46)],
        "local_pscad_library_roots": [r"C:\pscad_work\pnnl_39_3ibr_pscad46_strip5\PSCAD"],
        "local_paper_pdf_path": str(REPO / "external/pnnl-enhanced-ieee39/Inverter-Based Power System Model for Benchmarking in Multi-Time-Scale Platforms.pdf"),
        "local_raw_case_candidates": [str(RAW_3IBR)],
        "local_tli_paths": sorted(str(p) for p in GF46.glob("E_*.tli")),
        "online_research_allowed": True,
    }
    write_json(path, manifest)
    return manifest


def main() -> int:
    manifest = create_manifest()
    now = datetime.now(timezone.utc).isoformat(timespec="seconds")
    raw_sha = sha256(RAW_3IBR) if RAW_3IBR.exists() else ""
    rows = [
        {
            "source_id": "SRC_PNNL_GITHUB_3IBR_RAW",
            "source_title": "Enhanced IEEE 39-Bus System with three IBRs PSS/E RAW",
            "source_owner_or_publisher": "pnnltestsystem / Pacific Northwest National Laboratory test-system publication",
            "source_type": "open_machine_readable_raw_case",
            "source_url": "https://github.com/pnnltestsystem/Enhanced-IEEE-39-Bus-System-with-Inverter-based-Resources-on-Multi-Time-Scale-Platforms/tree/main/Enhanced%20IEEE%2039-Bus%20System_3IBRs/PSSE",
            "retrieval_timestamp_utc": now,
            "version_or_commit_or_release_tag": "public GitHub repository; local workspace copy dated 2026-06-21",
            "license_status": "repository_public; explicit license not found in local copy, so raw file is referenced and hashed rather than newly redistributed",
            "machine_readable_status": "pass",
            "local_cache_path_or_not_cached_reason": str(RAW_3IBR),
            "sha256_if_downloaded": raw_sha,
            "network_case_identity": "Enhanced IEEE 39-Bus System_3IBRs",
            "system_base_mva": "100",
            "rating_field_name": "RATE1..RATE12 in PSS/E branch records",
            "rating_field_semantic_claim": "PSS/E RATE1 is normally Rate A/normal branch rating, but all current-network branches are zero/unspecified in this file",
            "rate_a_or_normal_rating_status": "present_as_field_but_zero_unspecified_for_31_current_tlines",
            "rate_b_or_emergency_rating_status": "present_as_field_but_zero_unspecified_for_31_current_tlines",
            "rate_c_or_emergency_rating_status": "present_as_field_but_zero_unspecified_for_31_current_tlines",
            "current_model_genealogy_evidence": "Current PSCAD TLine identities and R/X/B values match this PNNL 3IBR RAW network branch table.",
            "source_quality_class": "priority_2_current_project_open_origin_source",
            "accepted_for_mapping_status": "accepted_for_branch_identity_mapping_not_for_thermal_rating",
            "rejection_reason": "RATE fields for the 31 current transmission-network branches are all zero, therefore no continuous thermal limit is recovered.",
        },
        {
            "source_id": "SRC_CURRENT_PSCAD_TLI_TOTAL_MVA",
            "source_title": "Current generated PSCAD E_*.tli Total MVA Rating fields",
            "source_owner_or_publisher": "local PSCAD/E-TRAN generated files",
            "source_type": "local_generated_model_file",
            "source_url": "",
            "retrieval_timestamp_utc": now,
            "version_or_commit_or_release_tag": "current protected trial project",
            "license_status": "local generated files; not external rating evidence",
            "machine_readable_status": "pass",
            "local_cache_path_or_not_cached_reason": str(GF46),
            "sha256_if_downloaded": "",
            "network_case_identity": "current PSCAD trial TLine generated data",
            "system_base_mva": "100",
            "rating_field_name": "Total MVA Rating",
            "rating_field_semantic_claim": "uniform model field, not verified continuous thermal rating",
            "rate_a_or_normal_rating_status": "not_rate_a",
            "rate_b_or_emergency_rating_status": "not_rate_b",
            "rate_c_or_emergency_rating_status": "not_rate_c",
            "current_model_genealogy_evidence": "Stage-five-B semantic audit traced XML MVA=100.0 to generated .tli Total MVA Rating=100.0.",
            "source_quality_class": "local_generated_non_thermal_semantic_evidence",
            "accepted_for_mapping_status": "rejected_for_protection_rating",
            "rejection_reason": "Uniform 100 MVA field has no verified thermal/protection-grade semantics and no runtime protection usage.",
        },
        {
            "source_id": "SRC_PNNL_PROJECT_REPORT_PAGE",
            "source_title": "Generic EMT Modeling for IBR / PNNL-35064 publication page",
            "source_owner_or_publisher": "Pacific Northwest National Laboratory",
            "source_type": "official_report_page",
            "source_url": "https://www.pnnl.gov/publications/generic-emt-modeling-ibr",
            "retrieval_timestamp_utc": now,
            "version_or_commit_or_release_tag": "published 2023-10-09",
            "license_status": "public report page",
            "machine_readable_status": "partial_text_pdf",
            "local_cache_path_or_not_cached_reason": "not cached; used as project genealogy/context only",
            "sha256_if_downloaded": "",
            "network_case_identity": "generic EMT modeling context, not branch-rating dataset",
            "system_base_mva": "",
            "rating_field_name": "",
            "rating_field_semantic_claim": "no per-line thermal rating table located",
            "rate_a_or_normal_rating_status": "not_available",
            "rate_b_or_emergency_rating_status": "not_available",
            "rate_c_or_emergency_rating_status": "not_available",
            "current_model_genealogy_evidence": "Official PNNL report page points to IBR EMT modeling context and OpenEI posting.",
            "source_quality_class": "priority_2_context_not_rating_data",
            "accepted_for_mapping_status": "rejected_no_branch_rating_data",
            "rejection_reason": "No machine-readable current-model branch continuous thermal limits found on the report page.",
        },
        {
            "source_id": "SRC_GENERIC_IEEE39_MATPOWER_CASE39",
            "source_title": "Generic MATPOWER case39 / New England 39-bus variants",
            "source_owner_or_publisher": "MATPOWER or public forks",
            "source_type": "generic_public_ieee39_case_family",
            "source_url": "https://matpower.org/docs/ref/matpower5.0/case39.html",
            "retrieval_timestamp_utc": now,
            "version_or_commit_or_release_tag": "not used",
            "license_status": "public documentation/source family",
            "machine_readable_status": "available_but_not_current_model_genealogy",
            "local_cache_path_or_not_cached_reason": "not cached; not needed because current PNNL 3IBR RAW is available locally",
            "sha256_if_downloaded": "",
            "network_case_identity": "generic IEEE 39-bus, not the current PNNL 3IBR adaptation",
            "system_base_mva": "100 in many variants",
            "rating_field_name": "rateA/rateB/rateC if present",
            "rating_field_semantic_claim": "not accepted for current PSCAD without genealogy and electrical-parameter mapping",
            "rate_a_or_normal_rating_status": "not_evaluated_for_use",
            "rate_b_or_emergency_rating_status": "not_evaluated_for_use",
            "rate_c_or_emergency_rating_status": "not_evaluated_for_use",
            "current_model_genealogy_evidence": "insufficient",
            "source_quality_class": "priority_4_generic_case_rejected",
            "accepted_for_mapping_status": "rejected_no_current_model_genealogy",
            "rejection_reason": "Generic IEEE39 ratings cannot be grafted onto the current PNNL/PSCAD model without exact branch identity and parameter correspondence.",
        },
    ]
    adopted = [r for r in rows if r["accepted_for_mapping_status"].startswith("accepted")]
    registry = {
        "artifact": "tline_thermal_limit_source_registry",
        "generated_at_local": datetime.now().isoformat(timespec="seconds"),
        "baseline_manifest": "data/validation/tline_thermal_limit_recovery_baseline_manifest.json",
        "source_count": len(rows),
        "reproducible_public_source_count": 3,
        "adopted_source_count": len(adopted),
        "rejected_source_count": len(rows) - len(adopted),
        "adopted_source_ids": [r["source_id"] for r in adopted],
        "main_sha_current": sha256(MAIN),
        "trial_sha_current": sha256(TRIAL),
        "main_project_integrity_status": "pass" if sha256(MAIN) == EXPECTED_MAIN else "fail",
        "trial_project_integrity_status": "pass" if sha256(TRIAL) == EXPECTED_TRIAL else "fail",
        "rows": rows,
    }
    write_csv(REPO / "data/reference/tline_thermal_limit_source_registry.csv", rows)
    write_json(REPO / "data/reference/tline_thermal_limit_source_registry.json", registry)
    print(json.dumps({"source_count": len(rows), "adopted_source_count": len(adopted), "raw_sha": raw_sha}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
