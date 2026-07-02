"""Read-only audit for the Type-3 DFIG LVRT cascade-event bus scaffold."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any


SOURCE_PACKET_SIGNALS = {
    "DFIG_LVRT_CASCADE_EVENT_VALID": "DFIG_LVRT_TRIP_CONFIRMED",
    "DFIG_LVRT_CAS_CAUSE_CODE": "DFIG_LVRT_TRIP_CAUSE_CODE",
    "DFIG_LVRT_CASCADE_EVENT_BRK_OPEN": "DFIG_LVRT_BRK_OPEN_BOOL",
    "DFIG_LVRT_CAS_SRC_AVAIL": "DFIG_LVRT_CASCADE_AVAILABLE",
    "DFIG_LVRT_CAS_FIRST_TIME_S": "DFIG_LVRT_CAS_TIME_MEM",
}

COLLECTOR_SIGNALS = {
    "CASCADE_MONITOR_ANY_TRIP": "DFIG_LVRT_CASCADE_EVENT_VALID",
    "CASCADE_MONITOR_ANY_BRK_OPEN": "DFIG_LVRT_CASCADE_EVENT_BRK_OPEN",
    "CASCADE_MONITOR_AVAIL_SRC_COUNT": "DFIG_LVRT_CAS_SRC_AVAIL",
    "CASCADE_MONITOR_FIRST_TIME_S": "DFIG_LVRT_CAS_FIRST_TIME_S",
    "CASCADE_MONITOR_CAUSE_CODE_DFIG1": "DFIG_LVRT_CAS_CAUSE_CODE",
}

OUTPUT_CHANNELS = {
    "DFIG_LVRT_CASCADE_EVENT_VALID": {"min": "0", "max": "1.2", "units": {""}},
    "DFIG_LVRT_CASCADE_EVENT_CAUSE_CODE": {"min": "0", "max": "3.2", "units": {"", "code"}},
    "DFIG_LVRT_CASCADE_EVENT_BRK_OPEN": {"min": "0", "max": "1.2", "units": {""}},
    "DFIG_LVRT_CASCADE_SOURCE_AVAILABLE": {"min": "0", "max": "1.2", "units": {""}},
    "DFIG_LVRT_CASCADE_FIRST_EVENT_TIME_S": {"min": "-1.2", "max": "10.2", "units": {"s"}},
    "CASCADE_MONITOR_ANY_TRIP": {"min": "0", "max": "1.2", "units": {""}},
    "CASCADE_MONITOR_ANY_BRK_OPEN": {"min": "0", "max": "1.2", "units": {""}},
    "CASCADE_MONITOR_AVAILABLE_SOURCE_COUNT": {"min": "0", "max": "1.2", "units": {"", "count"}},
    "CASCADE_MONITOR_FIRST_EVENT_TIME_S": {"min": "-1.2", "max": "10.2", "units": {"s"}},
    "CASCADE_MONITOR_CAUSE_CODE_DFIG1": {"min": "0", "max": "3.2", "units": {"", "code"}},
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
    return {
        item.attrib["id"]: item
        for item in root.findall(".//User")
        if "id" in item.attrib
    }


def normalize_fortran(text: str) -> str:
    return re.sub(r"\s*&\s*\n\s*&?", "", text.replace("\r\n", "\n"))


def check(name: str, passed: bool, evidence: str) -> dict[str, str]:
    return {"check": name, "status": "pass" if passed else "fail", "evidence": evidence}


def find_channels(root: ET.Element) -> dict[str, Any]:
    channels: dict[str, Any] = {}
    for item in root.findall(".//User[@defn='master:pgb']"):
        item_params = params(item)
        title = item_params.get("Name", "")
        if title in OUTPUT_CHANNELS:
            channels[title] = {"id": item.attrib.get("id"), **item_params}
    return channels


def protected_component_differences(active: ET.Element, baseline: ET.Element) -> list[dict[str, Any]]:
    active_users = users_by_id(active)
    differences: list[dict[str, Any]] = []
    for component_id, old in users_by_id(baseline).items():
        old_params = params(old)
        if not (PROTECTED_SIGNALS & set(old_params.values())):
            continue
        new = active_users.get(component_id)
        if new is None or old.attrib.get("defn") != new.attrib.get("defn") or old_params != params(new):
            differences.append(
                {
                    "id": component_id,
                    "definition_before": old.attrib.get("defn"),
                    "definition_after": new.attrib.get("defn") if new is not None else None,
                    "params_before": old_params,
                    "params_after": params(new) if new is not None else None,
                }
            )
    return differences


def audit(active: Path, baseline: Path, fortran: Path) -> dict[str, Any]:
    active_root = ET.parse(active).getroot()
    baseline_root = ET.parse(baseline).getroot()
    generated = normalize_fortran(fortran.read_text(encoding="utf-8", errors="replace"))

    checks: list[dict[str, str]] = []

    formula_patterns: dict[str, str] = {
        "event_valid_maps_trip_confirmed": (
            r"DFIG_LVRT_CASCADE_EVENT_VALID\s*=\s*1\.0\s*\*\s*DFIG_LVRT_TRIP_CONFIRMED"
        ),
        "event_cause_maps_cause_code": (
            r"DFIG_LVRT_CAS_CAUSE_CODE\s*=\s*1\.0\s*\*\s*DFIG_LVRT_TRIP_CAUSE_CODE"
        ),
        "event_brk_open_maps_brk_open_bool": (
            r"DFIG_LVRT_CASCADE_EVENT_BRK_OPEN\s*=\s*1\.0\s*\*\s*REAL\(DFIG_LVRT_BRK_OPEN_BOOL\)"
        ),
        "source_available_maps_cascade_available": (
            r"DFIG_LVRT_CAS_SRC_AVAIL\s*=\s*1\.0\s*\*\s*REAL\(DFIG_LVRT_CASCADE_AVAILABLE\)"
        ),
        "first_event_time_maps_time_mem": (
            r"DFIG_LVRT_CAS_FIRST_TIME_S\s*=\s*1\.0\s*\*\s*DFIG_LVRT_CAS_TIME_MEM"
        ),
        "time_unset_comparator_uses_mem_less_than_zero": (
            r"EMTDC_X2COMP\(0,0,0\.0,DFIG_LVRT_CAS_TIME_MEM,1\.0,0\.0,0\.0,RVD2_1\)"
        ),
        "time_capture_enable_formula": (
            r"DFIG_LVRT_CAS_TIME_CAP\s*=\s*DFIG_LVRT_CASCADE_EVENT_VALID\s*\*\s*REAL\(DFIG_LVRT_CAS_TIME_UNSET\)"
        ),
        "time_selector_captures_time": (
            r"IF \(NINT\(DFIG_LVRT_CAS_TIME_CAP\) \.EQ\. RTCI\(NRTCI\)\) THEN\s*"
            r"DFIG_LVRT_CAS_TIME_NEXT\s*=\s*RT_29\s*ELSE\s*"
            r"DFIG_LVRT_CAS_TIME_NEXT\s*=\s*DFIG_LVRT_CAS_TIME_MEM"
        ),
        "time_mem_initial_minus_one": r"IF \(TIMEZERO\) DFIG_LVRT_CAS_TIME_MEM = -1\.0",
        "collector_any_trip_maps_event_valid": (
            r"CASCADE_MONITOR_ANY_TRIP\s*=\s*1\.0\s*\*\s*DFIG_LVRT_CASCADE_EVENT_VALID"
        ),
        "collector_any_brk_open_maps_event_brk_open": (
            r"CASCADE_MONITOR_ANY_BRK_OPEN\s*=\s*1\.0\s*\*\s*DFIG_LVRT_CASCADE_EVENT_BRK_OPEN"
        ),
        "collector_available_count_maps_source_available": (
            r"CASCADE_MONITOR_AVAIL_SRC_COUNT\s*=\s*1\.0\s*\*\s*DFIG_LVRT_CAS_SRC_AVAIL"
        ),
        "collector_first_time_maps_source_first_time": (
            r"CASCADE_MONITOR_FIRST_TIME_S\s*=\s*1\.0\s*\*\s*DFIG_LVRT_CAS_FIRST_TIME_S"
        ),
        "collector_cause_code_maps_source_cause_code": (
            r"CASCADE_MONITOR_CAUSE_CODE_DFIG1\s*=\s*1\.0\s*\*\s*DFIG_LVRT_CAS_CAUSE_CODE"
        ),
        "final_command_composition_preserved": (
            r"RT_23\s*=\s*\+\s*DFIG_LVRT_EXISTING_BRK_CMD_BOOL\s*\+\s*DFIG_LVRT_TRIP_LATCH_BOOL"
        ),
        "final_command_limiter_preserved": (
            r"DFIG_LVRT_FINAL_BRK_CMD\s*=\s*LIMIT\(0\.0,\s*1\.0,\s*RT_23\)"
        ),
        "breaker_sole_command_preserved": (
            r"BRK_DFIG\s*=\s*1\.0\s*\*\s*DFIG_LVRT_FINAL_BRK_CMD"
        ),
    }
    for name, pattern in formula_patterns.items():
        checks.append(check(name, bool(re.search(pattern, generated)), pattern))

    channels = find_channels(active_root)
    for title, expected in OUTPUT_CHANNELS.items():
        channel = channels.get(title)
        valid = bool(channel) and all(
            (
                channel.get("UseSignalName") == "0",
                channel.get("enab") == "1",
                channel.get("Display") == "1",
                channel.get("Scale") == "1.0",
                channel.get("mrun") == "1",
                channel.get("Min") == expected["min"],
                channel.get("Max") == expected["max"],
                channel.get("Units", "") in expected["units"],
            )
        )
        checks.append(check(f"output_channel:{title}", valid, json.dumps(channel, sort_keys=True)))

    differences = protected_component_differences(active_root, baseline_root)
    checks.append(
        check(
            "preexisting_protected_component_parameters_unchanged",
            not differences,
            json.dumps(differences, sort_keys=True),
        )
    )

    direct_time_output = bool(
        re.search(r"DFIG_LVRT_CAS_FIRST_TIME_S\s*=\s*1\.0\s*\*\s*RT_29", generated)
    )
    checks.append(
        check(
            "first_event_time_not_continuous_time",
            not direct_time_output,
            "DFIG_LVRT_CAS_FIRST_TIME_S must map to DFIG_LVRT_CAS_TIME_MEM, not RT_29/TIME",
        )
    )

    failed = [item for item in checks if item["status"] != "pass"]
    channel_failed = [
        item for item in checks
        if item["check"].startswith("output_channel:") and item["status"] != "pass"
    ]

    return {
        "execution_status": "cascade_event_bus_static_audit_complete",
        "structure_status": "pass" if not failed else "fail",
        "control_path_isolation_status": "pass" if not differences else "fail",
        "output_channel_status": "pass" if not channel_failed and len(channels) == len(OUTPUT_CHANNELS) else "fail",
        "dynamic_behavior_status": "unavailable",
        "multi_source_behavior_status": "unavailable",
        "dynamic_behavior_note": "No PSCAD Run or EMTDC execution was performed for this static cascade-event bus task.",
        "multi_source_behavior_note": "Only the real current Type-3 DFIG source was connected; no second source or synthetic source was constructed.",
        "active_project": {"path": str(active), "sha256": sha256(active)},
        "task_start_baseline": {"path": str(baseline), "sha256": sha256(baseline)},
        "generated_fortran": {"path": str(fortran), "sha256": sha256(fortran)},
        "build": {
            "stage_a": {"errors": 0, "warnings": None, "messages": None},
            "stage_b": {"errors": 0, "warnings": None, "messages": None},
            "stage_c": {"errors": 0, "warnings": None, "messages": None},
            "source": "user-confirmed Builds; exact final warning/message counts not supplied",
        },
        "source_id": "TYPE3_DFIG_1",
        "source_packet_internal_signals": SOURCE_PACKET_SIGNALS,
        "collector_internal_signals": COLLECTOR_SIGNALS,
        "output_channels": channels,
        "checks": checks,
        "failed_checks": failed,
        "protected_component_differences": differences,
        "claim_boundary": {
            "static_structure_verified": not failed,
            "dynamic_behavior_validated_in_this_task": False,
            "multi_machine_cascade_validated": False,
            "matlab_coupling_added": False,
            "physical_field_breaker_validated": False,
            "synthetic_multi_source_created": False,
        },
        "future_dynamic_expectations": {
            "R5_immediate_trip": {
                "EVENT_VALID": 1,
                "EVENT_CAUSE_CODE": 2,
                "EVENT_BRK_OPEN": 1,
                "SOURCE_AVAILABLE": 0,
                "FIRST_EVENT_TIME_S": "approximately 2.02",
                "ANY_TRIP": 1,
                "ANY_BRK_OPEN": 1,
                "AVAILABLE_SOURCE_COUNT": 0,
                "COLLECTOR_FIRST_EVENT_TIME_S": "approximately 2.02",
                "CAUSE_CODE_DFIG1": 2,
            },
            "C3_duration_trip": {
                "EVENT_VALID": 1,
                "EVENT_CAUSE_CODE": 1,
                "EVENT_BRK_OPEN": 1,
                "SOURCE_AVAILABLE": 0,
                "FIRST_EVENT_TIME_S": "approximately 3.04",
                "ANY_TRIP": 1,
                "ANY_BRK_OPEN": 1,
                "AVAILABLE_SOURCE_COUNT": 0,
                "COLLECTOR_FIRST_EVENT_TIME_S": "approximately 3.04",
                "CAUSE_CODE_DFIG1": 1,
            },
            "C2_ride_through": {
                "EVENT_VALID": 0,
                "EVENT_CAUSE_CODE": 0,
                "EVENT_BRK_OPEN": 0,
                "SOURCE_AVAILABLE": 1,
                "FIRST_EVENT_TIME_S": -1,
                "ANY_TRIP": 0,
                "ANY_BRK_OPEN": 0,
                "AVAILABLE_SOURCE_COUNT": 1,
                "COLLECTOR_FIRST_EVENT_TIME_S": -1,
                "CAUSE_CODE_DFIG1": 0,
            },
            "C1_no_fault": {
                "EVENT_VALID": 0,
                "EVENT_CAUSE_CODE": 0,
                "EVENT_BRK_OPEN": 0,
                "SOURCE_AVAILABLE": 1,
                "FIRST_EVENT_TIME_S": -1,
                "ANY_TRIP": 0,
                "ANY_BRK_OPEN": 0,
                "AVAILABLE_SOURCE_COUNT": 1,
                "COLLECTOR_FIRST_EVENT_TIME_S": -1,
                "CAUSE_CODE_DFIG1": 0,
            },
        },
    }


def write_summary(result: dict[str, Any], path: Path) -> None:
    rows = [
        {"item": "structure_status", "status": result["structure_status"], "detail": "single-source event packet and collector formulas"},
        {"item": "control_path_isolation_status", "status": result["control_path_isolation_status"], "detail": "protected LVRT and BRK_DFIG path unchanged"},
        {"item": "output_channel_status", "status": result["output_channel_status"], "detail": "ten required cascade channels"},
        {"item": "dynamic_behavior_status", "status": result["dynamic_behavior_status"], "detail": "no new PSCAD Run"},
        {"item": "multi_source_behavior_status", "status": result["multi_source_behavior_status"], "detail": "no second or synthetic source constructed"},
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

    keys = (
        "structure_status",
        "control_path_isolation_status",
        "output_channel_status",
        "dynamic_behavior_status",
        "multi_source_behavior_status",
    )
    print(json.dumps({key: result[key] for key in keys}, indent=2))
    if result["structure_status"] == "fail":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
