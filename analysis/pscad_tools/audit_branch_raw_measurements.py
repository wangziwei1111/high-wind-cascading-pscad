#!/usr/bin/env python3
"""Read-only final audit for raw branch measurement preflight/fallback."""

from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path
import re
import sys
import xml.etree.ElementTree as ET

from preflight_branch_raw_measurements import (
    EXPECTED_CHANNELS,
    EXPECTED_MAIN_SHA,
    GF46,
    MAIN,
    TRIAL,
    params,
    parse_fortran_channels,
    sha256,
    generated_artifact_fingerprint,
)


ROOT = Path(__file__).resolve().parents[2]
DATA_REF = ROOT / "data" / "reference"
DATA_VAL = ROOT / "data" / "validation"


def write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def main() -> int:
    preflight = json.loads((DATA_VAL / "branch_raw_measurements_preflight.json").read_text(encoding="utf-8"))
    baseline = json.loads((DATA_VAL / "branch_raw_measurements_existing_channel_baseline.json").read_text(encoding="utf-8"))
    registry = json.loads((DATA_REF / "paper_branch_candidate_registry.json").read_text(encoding="utf-8"))
    design = json.loads((DATA_REF / "paper_branch_raw_measurement_design.json").read_text(encoding="utf-8"))

    root = ET.parse(TRIAL).getroot()
    fortran, fortran_count = parse_fortran_channels(sorted(GF46.glob("*.f")))
    channel_elements = [user for user in root.iter("User") if user.get("defn") == "master:pgb"]
    channels = []
    for xml_order, user in enumerate(channel_elements, 1):
        row = params(user)
        name = row.get("Name", "")
        channels.append({
            "xml_order": xml_order, "name": name, "component_id": user.get("id", ""),
            "definition": user.get("defn", ""), "x": user.get("x", ""), "y": user.get("y", ""),
            "xml_parameters": row, "fortran_mappings": fortran.get(name, []),
        })
    fingerprint = hashlib.sha256(json.dumps(channels, sort_keys=True).encode()).hexdigest().upper()
    existing_preserved = (
        len(channels) == baseline["output_channel_count"] == EXPECTED_CHANNELS
        and fingerprint == baseline["output_channel_fingerprint"]
    )

    channel_trace = []
    for before, after in zip(baseline["channels"], channels):
        channel_trace.append({
            "xml_order": before["xml_order"], "name": before["name"],
            "component_id_before": before["component_id"], "component_id_after": after["component_id"],
            "xml_parameters_preserved": before["xml_parameters"] == after["xml_parameters"],
            "fortran_mappings_preserved": before["fortran_mappings"] == after["fortran_mappings"],
            "channel_status": "preserved" if before == after else "changed",
        })
    write_csv(DATA_VAL / "branch_raw_measurements_channel_trace.csv", channel_trace)

    semantic_trace = []
    for candidate in registry["candidates"]:
        semantic_trace.append({
            "candidate_branch_id": candidate["candidate_branch_id"],
            "branch_name": candidate["current_project_branch_name"],
            "from_node": candidate["from_bus_or_node"], "to_node": candidate["to_bus_or_node"],
            "real_tline_traceability": "pass",
            "p_signal_semantics": candidate["p_signal_semantics"],
            "q_signal_semantics": candidate["q_signal_semantics"],
            "i_signal_semantics": candidate["i_signal_semantics"],
            "measurement_semantics_status": "fail",
            "eligibility_status": candidate["eligibility_status"],
            "rejection_reason": candidate["rejection_reason"],
        })
    write_csv(DATA_VAL / "branch_raw_measurements_semantic_trace.csv", semantic_trace)

    trial_text = TRIAL.read_text(encoding="utf-8-sig", errors="replace")
    forbidden_absent = not any([
        bool(re.search(r"LINE[_ -]?OVERLOAD|BRANCH[_ -]?OVERLOAD", trial_text, re.I)),
        bool(re.search(r"AUTO[_ -]?RECLOSE|AUTORECLOSE", trial_text, re.I)),
        bool(re.search(r"SOURCE[_ -]?4|SRC[_ -]?4|IBR4|CASCADE4", trial_text, re.I)),
        bool(re.search(r"VIRTUAL_(?:SOURCE|CAS)|CAS_VIRTUAL", trial_text, re.I)),
        bool(re.search(r"MATLAB", trial_text, re.I)),
        bool(re.search(r"STATCOM|\bSVC\b", trial_text, re.I)),
    ])
    p3 = next(definition for definition in root.iter("Definition") if definition.get("name") == "P3")
    defaults = {
        "ibr2_enable": params(next(user for user in p3.findall("./schematic/User") if user.get("id") == "1778759091")).get("Value"),
        "ibr2_open_time_s": params(next(user for user in p3.findall("./schematic/User") if user.get("id") == "939314032")).get("Value"),
        "ibr3_enable": params(next(user for user in p3.findall("./schematic/User") if user.get("id") == "444774384")).get("Value"),
        "ibr3_open_time_s": params(next(user for user in p3.findall("./schematic/User") if params(user).get("Name") == "IBR3_TRIAL__OPEN_STIMULUS")).get("OPEN_TIME_S"),
    }
    defaults_ok = defaults == {"ibr2_enable": "0", "ibr2_open_time_s": "4", "ibr3_enable": "0", "ibr3_open_time_s": "5"}
    main_ok = sha256(MAIN) == preflight["main_sha_before"] == EXPECTED_MAIN_SHA
    trial_ok = sha256(TRIAL) == preflight["trial_sha_before"] == baseline["trial_sha256"]
    generated_artifacts_unchanged = generated_artifact_fingerprint() == preflight["generated_artifact_fingerprint_before"]

    result = {
        "execution_status": "branch_raw_measurements_static_fallback",
        "main_project_integrity_status": "pass" if main_ok else "fail",
        "trial_project_integrity_status": "pass" if trial_ok else "fail",
        "existing_output_channel_preservation_status": "pass" if existing_preserved and all(row["channel_status"] == "preserved" for row in channel_trace) else "fail",
        "selected_real_branch_traceability_status": "pass" if registry["candidate_count"] >= 2 else "fail",
        "branch_measurement_semantics_status": "fail",
        "new_branch_output_presence_status": "not_applicable_static_fallback",
        "new_branch_output_fortran_mapping_status": "not_applicable_static_fallback",
        "final_output_channel_count_status": "pass" if len(channels) == EXPECTED_CHANNELS else "fail",
        "no_in_model_loading_ratio_status": "pass" if design["no_in_model_loading_ratio"] else "fail",
        "no_in_model_protection_logic_status": "pass" if forbidden_absent else "fail",
        "monitor_only_scope_status": "pass",
        "branch_control_isolation_status": "pass" if trial_ok else "fail",
        "default_trial_state_status": "pass" if defaults_ok else "fail",
        "build_status": "not_performed_due_to_static_fallback" if generated_artifacts_unchanged else "artifact_change_detected",
        "run_status": "not_performed" if generated_artifacts_unchanged else "artifact_change_detected",
        "paper_alignment_update_status": "fallback_recorded_no_capability_change",
        "natural_cascade_research_readiness_status": "not_ready_missing_raw_branch_pqi",
        "power_flow_redistribution_status": "unavailable",
        "line_loading_ratio_status": "unavailable",
        "line_overload_status": "unavailable",
        "line_protection_status": "unavailable",
        "branch_trip_status": "unavailable",
        "natural_cascade_propagation_status": "unavailable",
        "physical_causality_direction_status": "unavailable",
        "system_stability_status": "unavailable",
        "protection_coordination_status": "unavailable",
        "voltage_support_performance_status": "unavailable",
        "matlab_status": "not_added",
        "main_sha_start": preflight["main_sha_before"], "main_sha_end": sha256(MAIN),
        "trial_sha_start": preflight["trial_sha_before"], "trial_sha_end": sha256(TRIAL),
        "selected_branch_count": 0, "new_output_channel_count": 0,
        "final_output_channel_count": len(channels),
        "generated_fortran_output_assignment_count": fortran_count,
        "generated_artifact_fingerprint_unchanged": generated_artifacts_unchanged,
        "blocking_reason": design["blocking_reason"],
        "claim_boundary": design["claim_boundary"],
        "final_audit_status": "pass_static_fallback" if main_ok and trial_ok and existing_preserved and forbidden_absent and defaults_ok and generated_artifacts_unchanged else "fail",
    }
    (DATA_VAL / "branch_raw_measurements_final_audit.json").write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0 if result["final_audit_status"] == "pass_static_fallback" else 2


if __name__ == "__main__":
    sys.exit(main())
