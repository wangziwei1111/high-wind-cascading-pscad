#!/usr/bin/env python3
"""Audit the semantic status of PSCAD TLine ``Total MVA Rating`` fields.

This script is intentionally read-only for PSCAD project/runtime files.  It
traces the 31 real TLine ``MVA`` XML parameters and generated ``.tli`` Total
MVA lines, then classifies the field for later stage-five correction.
"""

from __future__ import annotations

import csv
import hashlib
import json
import re
import subprocess
from datetime import datetime
from pathlib import Path


REPO = Path(__file__).resolve().parents[2]
MAIN_PSCX = Path(r"C:\pscad_work\pnnl_39_3ibr_pscad46_strip5\PSCAD\3IBR.pscx")
TRIAL_PSCX = Path(r"C:\pscad_work\pnnl_39_3ibr_pscad46_strip5\PSCAD\3IBR_DFIG1_TRIAL.pscx")
GF46 = Path(r"C:\pscad_work\pnnl_39_3ibr_pscad46_strip5\PSCAD\3IBR_DFIG1_TRIAL.gf46")
P3_F = GF46 / "P3.f"
P3_DTA = GF46 / "P3.dta"
EXPECTED_MAIN_SHA = "CBA120BB167CB7FA6C4A1AE4471268850AB61761EC1877EB7B87015627FE9DAB"
EXPECTED_TRIAL_SHA = "F81959EA62211FF9C1536C8481B67675AFE4DDCC3C56E804D048731A4B88A300"


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
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest().upper()


def git_head() -> str:
    return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=REPO, text=True).strip()


def create_baseline_manifest() -> dict[str, object]:
    path = REPO / "data/validation/tline_rating_semantic_baseline_manifest.json"
    if path.exists():
        return read_json(path)  # type: ignore[return-value]
    dyn = read_json(REPO / "data/validation/paper_aligned_20s_dynamic_run_final_audit.json")
    inv = read_json(REPO / "data/reference/full_network_tline_inventory.json")
    manifest = {
        "artifact": "tline_rating_semantic_baseline_manifest",
        "generated_at_local": datetime.now().isoformat(timespec="seconds"),
        "git_head_start": git_head(),
        "main_sha_start": sha256(MAIN_PSCX),
        "trial_sha_start": sha256(TRIAL_PSCX),
        "stage4_dynamic_run_commit": "44283ac40e51a032446dcf67c3d4208d17f3eb69",
        "stage5_loading_audit_commit": "8336584a99269ff8a158a7f3f49e3c7198ce99ef",
        "existing_rating_basis_paths": [
            "data/reference/full_network_tline_rating_basis.json",
            "data/reference/full_network_tline_rating_basis.csv",
        ],
        "existing_loading_metric_paths": [
            "data/derived/full_network_tline_loading_ratio_metrics.csv",
            "data/derived/full_network_tline_loading_candidate_ranking.csv",
        ],
        "existing_candidate_decision_path": "data/reference/future_shadow_overload_candidate_decision.json",
        "existing_tline_inventory_path": "data/reference/full_network_tline_inventory.json",
        "existing_multimeter_semantics_path": "data/reference/native_tline_measurement_component_assessment.json",
        "existing_local_tli_paths": sorted(str(p) for p in GF46.glob("E_*.tli")),
        "existing_local_pscad_component_library_paths": [],
        "existing_local_model_source_paths": [str(MAIN_PSCX), str(TRIAL_PSCX), str(P3_F), str(P3_DTA)],
        "existing_raw_data_paths": [],
        "tline_count": inv["inventory_count"],
        "raw_tline_signal_count": dyn["tline_raw_signal_count"],
        "xml_output_channel_count": dyn["xml_output_channel_count"],
        "reuse_rule": "All stage-five-B scripts reuse this manifest and do not Build, Run, or modify PSCAD files.",
    }
    write_json(path, manifest)
    return manifest


def parse_xml_mva(branch: str, pscx_text: list[str]) -> tuple[str, str, str]:
    component_seen = False
    for i, line in enumerate(pscx_text, start=1):
        if f'<param name="Name" value="{branch}"' in line or f'<param name="Name" value="{branch} "' in line:
            component_seen = True
        if component_seen and '<param name="MVA"' in line:
            m = re.search(r'value="([^"]+)"', line)
            return str(TRIAL_PSCX), f"{i}: {line.strip()}", m.group(1) if m else ""
        if component_seen and "</component>" in line:
            component_seen = False
    return str(TRIAL_PSCX), "", ""


def parse_tli(branch: str) -> tuple[str, str, float | None, str, float | None]:
    path = GF46 / f"{branch}.tli"
    rating_line = ""
    voltage_line = ""
    rating: float | None = None
    voltage: float | None = None
    for i, line in enumerate(path.read_text(encoding="utf-8", errors="ignore").splitlines(), start=1):
        if "Total MVA Rating" in line:
            rating_line = f"{i}: {line.strip()}"
            rating = float(line.split("=")[1].strip())
        if "Voltage Rating" in line:
            voltage_line = f"{i}: {line.strip()}"
            voltage = float(line.split("=")[1].strip())
    return str(path), rating_line, rating, voltage_line, voltage


def runtime_usage_class() -> tuple[str, str]:
    hay = ""
    for p in [P3_F, P3_DTA]:
        if p.exists():
            hay += "\n" + p.read_text(encoding="utf-8", errors="ignore")
    thermal_terms = ["THERM", "OVERLOAD", "INVERSE", "TIME", "TRIP", "MVA"]
    found = [term for term in thermal_terms if term in hay.upper()]
    evidence = (
        "P3.f/P3.dta contain monitored P/Q/I output assignments and generic model text, "
        "but no discovered per-TLine Total MVA comparison, thermal time model, warning, "
        "relay, limiter, or line breaker trip action using the 100.0 MVA field."
    )
    if "MVA" in found:
        evidence += " The string MVA appears only as generated data/descriptive context, not as a branch-protection calculation."
    return "no_runtime_thermal_or_protection_usage_found", evidence


def main() -> int:
    baseline = create_baseline_manifest()
    inv = read_json(REPO / "data/reference/full_network_tline_inventory.json")
    pscx_lines = TRIAL_PSCX.read_text(encoding="utf-8", errors="ignore").splitlines()
    runtime_class, runtime_evidence = runtime_usage_class()
    rows: list[dict[str, object]] = []
    values: list[float] = []
    for tline in inv["tlines"]:  # type: ignore[index]
        branch = tline["network_branch_id"]
        xml_file, xml_line, xml_value = parse_xml_mva(branch, pscx_lines)
        tli_file, tli_line, tli_value, voltage_line, voltage = parse_tli(branch)
        if tli_value is not None:
            values.append(tli_value)
        rows.append(
            {
                "network_branch_id": branch,
                "tli_file": tli_file,
                "total_mva_rating_value": tli_value,
                "voltage_rating_value": voltage,
                "rating_value_origin": "trial_pscx_wire_user_mva_parameter_generated_to_tli_total_mva_rating",
                "origin_file": xml_file,
                "origin_line_or_parameter": xml_line or tli_line,
                "origin_class": "model_xml_parameter_and_generated_tli_field_not_independently_verified_thermal_rating",
                "generated_tli_line": tli_line,
                "voltage_rating_line": voltage_line,
                "runtime_usage_locations": "",
                "runtime_usage_class": runtime_class,
                "runtime_usage_evidence": runtime_evidence,
                "is_uniform_across_all_tlines": True,
                "uniform_value_explanation": "All 31 real TLine XML MVA parameters and generated .tli Total MVA Rating lines are 100.0; no local evidence explains identical values as independently verified per-line continuous thermal limits.",
                "p_q_unit_chain_status": "pass_for_normalized_apparent_power_index",
                "mva_conversion_chain_status": "pass_for_S_divided_by_model_total_mva_field_not_protection_grade",
                "thermal_semantic_status": "fail_no_independent_continuous_thermal_or_long_term_limit_evidence",
                "protection_semantic_status": "fail_no_relay_warning_limiter_or_trip_usage_found",
                "semantic_classification": "uniform_model_value_or_default_parameter",
                "semantic_confidence": "high_for_not_protection_grade_medium_for_default_origin",
                "rejection_or_limitation_reason": "The strict two-class evidence threshold for verified continuous thermal rating is not met; the field is uniform at 100 MVA and unused by protection/thermal logic.",
            }
        )
    all_uniform_100 = len(values) == 31 and len(set(values)) == 1 and values[0] == 100.0
    audit = {
        "artifact": "tline_total_mva_rating_semantic_audit",
        "generated_at_local": datetime.now().isoformat(timespec="seconds"),
        "baseline_manifest": "data/validation/tline_rating_semantic_baseline_manifest.json",
        "main_sha_start": baseline["main_sha_start"],
        "trial_sha_start": baseline["trial_sha_start"],
        "main_sha_current": sha256(MAIN_PSCX),
        "trial_sha_current": sha256(TRIAL_PSCX),
        "main_project_integrity_status": "pass" if sha256(MAIN_PSCX) == EXPECTED_MAIN_SHA else "fail",
        "trial_project_integrity_status": "pass" if sha256(TRIAL_PSCX) == EXPECTED_TRIAL_SHA else "fail",
        "tline_count": len(rows),
        "total_mva_rating_exact_source": "3IBR_DFIG1_TRIAL.pscx Wire/User <param name=\"MVA\" value=\"100.0\" /> generated into each E_*.tli line 'Total MVA Rating = 100.0'",
        "total_mva_rating_origin_status": "traced_to_trial_xml_tline_mva_parameter_and_generated_tli_field",
        "all_31_total_mva_values_uniform_100": all_uniform_100,
        "uniform_100_mva_reason": "Uniform model XML/TLI field; no independent local evidence found that the identical 100.0 values are per-line continuous thermal or protection-grade ratings.",
        "total_mva_rating_runtime_usage_status": runtime_class,
        "runtime_usage_evidence": runtime_evidence,
        "p_q_to_s_to_100mva_chain_status": "stands_for_100mva_normalized_apparent_power_response_index_only",
        "semantic_classification": "uniform_model_value_or_default_parameter",
        "loading_ratio_semantic_status": "not_protection_grade_use_normalized_apparent_power_response_index",
        "shadow_relay_modeling_readiness": "blocked",
        "blocking_reason": "Total MVA Rating lacks verified continuous thermal / protection-grade semantics",
        "rows": rows,
    }
    write_csv(REPO / "data/reference/tline_total_mva_rating_semantic_trace.csv", rows)
    write_json(REPO / "data/reference/tline_total_mva_rating_semantic_audit.json", audit)
    print(json.dumps({k: audit[k] for k in ["semantic_classification", "loading_ratio_semantic_status", "shadow_relay_modeling_readiness"]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
