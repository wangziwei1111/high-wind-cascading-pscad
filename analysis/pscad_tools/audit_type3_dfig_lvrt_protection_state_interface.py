"""Read-only audit for the Type-3 DFIG LVRT protection-state interface."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any


OUTPUT_CHANNELS = {
    "DFIG_LVRT_TRIP_CAUSE_IMM_LATCH": {"max": "1.2", "unit": ""},
    "DFIG_LVRT_TRIP_CAUSE_DURATION_LATCH": {"max": "1.2", "unit": ""},
    "DFIG_LVRT_TRIP_CAUSE_CODE": {"max": "3.2", "unit": "code"},
    "DFIG_LVRT_ORIGINAL_CMD_OPEN_BOOL": {"max": "1.2", "unit": ""},
    "DFIG_LVRT_FINAL_CMD_BOOL": {"max": "1.2", "unit": ""},
    "DFIG_LVRT_BRK_OPEN_BOOL": {"max": "1.2", "unit": ""},
    "DFIG_LVRT_TRIP_CONFIRMED": {"max": "1.2", "unit": ""},
    "DFIG_LVRT_CASCADE_AVAILABLE": {"max": "1.2", "unit": ""},
}

PROTECTED_SIGNALS = {
    "DFIG_LVRT_TRIP_REQUEST",
    "DFIG_LVRT_TRIP_LATCH",
    "DFIG_LVRT_CLEAR",
    "DFIG_LVRT_FINAL_BRK_CMD",
    "BRK_DFIG",
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def params(element: ET.Element) -> dict[str, str]:
    return {
        item.attrib.get("name", ""): item.attrib.get("value", "")
        for item in element.findall("./paramlist/param")
    }


def users_by_id(root: ET.Element) -> dict[str, ET.Element]:
    return {item.attrib["id"]: item for item in root.findall(".//User") if "id" in item.attrib}


def check(name: str, passed: bool, evidence: str) -> dict[str, str]:
    return {"check": name, "status": "pass" if passed else "fail", "evidence": evidence}


def normalize_fortran(text: str) -> str:
    return re.sub(r"\s*&\s*\n\s*&?", "", text.replace("\r\n", "\n"))


def audit(active: Path, baseline: Path, fortran: Path) -> dict[str, Any]:
    active_root = ET.parse(active).getroot()
    baseline_root = ET.parse(baseline).getroot()
    active_users = users_by_id(active_root)
    baseline_users = users_by_id(baseline_root)
    generated = normalize_fortran(fortran.read_text(encoding="utf-8", errors="replace"))

    checks: list[dict[str, str]] = []
    channels: dict[str, Any] = {}
    for item in active_root.findall(".//User[@defn='master:pgb']"):
        item_params = params(item)
        title = item_params.get("Name", "")
        if title in OUTPUT_CHANNELS:
            channels[title] = {"id": item.attrib.get("id"), **item_params}

    for title, expected in OUTPUT_CHANNELS.items():
        channel = channels.get(title)
        valid = bool(channel) and all(
            (
                channel.get("UseSignalName") == "0",
                channel.get("enab") == "1",
                channel.get("Display") == "1",
                channel.get("Scale") == "1.0",
                channel.get("mrun") == "1",
                channel.get("Min") == "0",
                channel.get("Max") == expected["max"],
                channel.get("Units", "") == expected["unit"],
            )
        )
        checks.append(check(f"output_channel:{title}", valid, json.dumps(channel, sort_keys=True)))

    formula_patterns = {
        "imm_request_is_armed": r"DFIG_LVRT_CAUSE_IMM_REQ\s*=\s*REAL\(DFIG_LVRT_IMMTRIP_BOOL_MON\)\s*\*\s*REAL\(DFIG_LVRT_ARMED_BOOL_MON\)",
        "duration_request_is_armed": r"DFIG_LVRT_CAUSE_DUR_REQ\s*=\s*REAL\(DFIG_LVRT_ARMED_BOOL_MON\)\s*\*\s*REAL\(DFIG_LVRT_DURATION_BOOL_MON\)",
        "imm_latch_initial_zero": r"IF \(TIMEZERO\) DFIG_LVRT_CAUSE_IMM_MEM = 0\.0",
        "duration_latch_initial_zero": r"IF \(TIMEZERO\) DFIG_LVRT_CAUSE_DUR_MEM = 0\.0",
        "cause_code_formula": r"DFIG_LVRT_TRIP_CAUSE_CODE\s*=\s*\+\s*RT_27\s*\+\s*RT_28",
        "cause_code_imm_weight": r"RT_27\s*=\s*2\.0\s*\*\s*DFIG_LVRT_TRIP_CAUSE_IMM_LATCH",
        "cause_code_duration_weight": r"RT_28\s*=\s*1\.0\s*\*\s*DFIG_LVRT_CAUSE_DUR_LATCH",
        "trip_confirmed_formula": r"DFIG_LVRT_TRIP_CONFIRMED\s*=\s*RT_26\s*\*\s*REAL\(DFIG_LVRT_BRK_OPEN_BOOL\)",
        "trip_confirmed_first_stage": r"RT_26\s*=\s*REAL\(DFIG_LVRT_TRIP_LATCH_BOOL_MON\)\s*\*\s*REAL\(DFIG_LVRT_FINAL_CMD_BOOL\)",
        "cascade_available_inversion": r"EMTDC_X2COMP\(0,0,0\.5,REAL\(DFIG_LVRT_BRK_OPEN_BOOL\),1\.0,0\.0,0\.0,RVD2_1\)",
        "final_command_composition": r"RT_23\s*=\s*\+\s*DFIG_LVRT_EXISTING_BRK_CMD_BOOL\s*\+\s*DFIG_LVRT_TRIP_LATCH_BOOL",
        "final_command_limiter": r"DFIG_LVRT_FINAL_BRK_CMD\s*=\s*LIMIT\(0\.0,\s*1\.0,\s*RT_23\)",
        "breaker_sole_command": r"BRK_DFIG\s*=\s*1\.0\s*\*\s*DFIG_LVRT_FINAL_BRK_CMD",
    }
    for name, pattern in formula_patterns.items():
        matched = bool(re.search(pattern, generated))
        checks.append(check(name, matched, pattern))

    protected_component_differences: list[dict[str, Any]] = []
    for component_id, old in baseline_users.items():
        old_params = params(old)
        if not (PROTECTED_SIGNALS & set(old_params.values())):
            continue
        new = active_users.get(component_id)
        if new is None or old.attrib.get("defn") != new.attrib.get("defn") or old_params != params(new):
            protected_component_differences.append(
                {
                    "id": component_id,
                    "definition_before": old.attrib.get("defn"),
                    "definition_after": new.attrib.get("defn") if new is not None else None,
                    "params_before": old_params,
                    "params_after": params(new) if new is not None else None,
                }
            )
    checks.append(
        check(
            "preexisting_protected_component_parameters_unchanged",
            not protected_component_differences,
            json.dumps(protected_component_differences, sort_keys=True),
        )
    )

    failed = [item for item in checks if item["status"] != "pass"]
    return {
        "execution_status": "protection_state_interface_static_audit_complete",
        "structure_status": "pass" if not failed else "fail",
        "control_path_isolation_status": "pass" if not protected_component_differences else "fail",
        "output_channel_status": "pass" if len(channels) == len(OUTPUT_CHANNELS) and not any(item["check"].startswith("output_channel:") and item["status"] == "fail" for item in checks) else "fail",
        "dynamic_behavior_status": "unavailable",
        "dynamic_behavior_note": "No PSCAD Run or EMTDC execution was performed for this static interface task.",
        "active_project": {"path": str(active), "sha256": sha256(active)},
        "task_start_baseline": {"path": str(baseline), "sha256": sha256(baseline)},
        "generated_fortran": {"path": str(fortran), "sha256": sha256(fortran)},
        "build": {"errors": 0, "warnings": None, "messages": None, "source": "user-confirmed final Build; exact warning/message counts not supplied"},
        "checks": checks,
        "failed_checks": failed,
        "output_channels": channels,
        "protected_component_differences": protected_component_differences,
        "historical_status_preserved": {
            "C1_no_fault": "pass",
            "C2_ride_through": "pass",
            "R5_immediate_trip_chain": "pass",
            "C3_command_state_chain": "pass",
            "legacy_C3_full_run_VSMIN_reference": "fail",
            "overall_closed_loop_coverage": "partial",
        },
        "claim_boundary": {
            "static_structure_verified": not failed,
            "dynamic_behavior_validated_in_this_task": False,
            "multi_machine_cascade_validated": False,
            "matlab_coupling_added": False,
            "physical_field_breaker_validated": False,
        },
    }


def write_summary(result: dict[str, Any], path: Path) -> None:
    rows = [
        {"item": "structure_status", "status": result["structure_status"], "detail": "monitor-only structure and formulas"},
        {"item": "control_path_isolation_status", "status": result["control_path_isolation_status"], "detail": "pre-existing protected component parameters"},
        {"item": "output_channel_status", "status": result["output_channel_status"], "detail": "eight required channels and parameters"},
        {"item": "dynamic_behavior_status", "status": result["dynamic_behavior_status"], "detail": "no new PSCAD Run"},
    ]
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=["item", "status", "detail"])
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--active", required=True, type=Path)
    parser.add_argument("--baseline", required=True, type=Path)
    parser.add_argument("--fortran", required=True, type=Path)
    parser.add_argument("--json-out", required=True, type=Path)
    parser.add_argument("--csv-out", required=True, type=Path)
    args = parser.parse_args()
    result = audit(args.active, args.baseline, args.fortran)
    args.json_out.parent.mkdir(parents=True, exist_ok=True)
    args.csv_out.parent.mkdir(parents=True, exist_ok=True)
    args.json_out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_summary(result, args.csv_out)
    print(json.dumps({key: result[key] for key in ("structure_status", "control_path_isolation_status", "output_channel_status", "dynamic_behavior_status")}, indent=2))
    if result["structure_status"] == "fail":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
