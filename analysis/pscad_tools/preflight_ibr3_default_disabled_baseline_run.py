#!/usr/bin/env python3
"""Read-only preflight for the IBR3 default-disabled baseline run."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sys
import xml.etree.ElementTree as ET


ROOT = Path(r"C:\pscad_work\pnnl_39_3ibr_pscad46_strip5\PSCAD")
MAIN_PROJECT = ROOT / "3IBR.pscx"
TRIAL_PROJECT = ROOT / "3IBR_DFIG1_TRIAL.pscx"
RESULT_DIR = ROOT / "3IBR_DFIG1_TRIAL.gf46"
PREVIOUS_ENABLED_SUMMARY = Path("data/validation/ibr3_trial_single_opening_run_summary.json")
PREVIOUS_ENABLED_AUDIT = Path("data/validation/ibr3_trial_single_opening_final_audit.json")

EXPECTED_MAIN_SHA256 = "CBA120BB167CB7FA6C4A1AE4471268850AB61761EC1877EB7B87015627FE9DAB"
EXPECTED_RESTORED_TRIAL_SHA256 = "C03DAA211B591923F533554C9951503096677BCF52547D13A10C4B431E69A349"
EXPECTED_OUTPUT_CHANNEL_COUNT = 253


REQUIRED_CHANNELS = [
    "IBR2_TRIAL_TEST_ENABLE",
    "IBR3_TRIAL_TEST_ENABLE",
    "IBR3_TRIAL_TEST_OPEN_TIME_S",
    "IBR3_TRIAL_TEST_OPEN_REQUEST",
    "IBR3_TRIAL_BRK_CMD",
    "IBR3_TRIAL_BRK_STATE",
    "IBR3_TRIAL_BRK_OPEN_BOOL",
    "IBR3_TRIAL_SOURCE_AVAILABLE",
    "IBR3_TRIAL_CASCADE_EVENT_VALID",
    "IBR3_TRIAL_CASCADE_EVENT_CAUSE_CODE",
    "IBR3_TRIAL_CASCADE_EVENT_BRK_OPEN",
    "IBR3_TRIAL_CASCADE_SOURCE_AVAILABLE",
    "IBR3_TRIAL_CASCADE_FIRST_EVENT_TIME_S",
    "CASCADE3_MONITOR_ANY_TRIP",
    "CASCADE3_MONITOR_ANY_BRK_OPEN",
    "CASCADE3_MONITOR_AVAILABLE_SOURCE_COUNT",
    "CASCADE3_MONITOR_EVENTED_SOURCE_COUNT",
    "CASCADE3_MONITOR_FIRST_EVENT_TIME_S",
    "CASCADE3_MONITOR_FIRST_EVENT_SOURCE_CODE",
    "CASCADE3_MONITOR_CAUSE_CODE_DFIG1",
    "CASCADE3_MONITOR_CAUSE_CODE_IBR2_TRIAL",
    "CASCADE3_MONITOR_CAUSE_CODE_IBR3_TRIAL",
    "CASCADE3_MONITOR_TIMED_EVENT_SOURCE_COUNT",
    "CASCADE3_MONITOR_SECOND_EVENT_TIME_S",
    "CASCADE3_MONITOR_THIRD_EVENT_TIME_S",
    "CASCADE3_MONITOR_FIRST_TO_SECOND_GAP_S",
    "CASCADE3_MONITOR_SECOND_TO_THIRD_GAP_S",
    "CASCADE3_MONITOR_CHRONOLOGY_FIRST_SOURCE_CODE",
    "CASCADE3_MONITOR_EVENT_ORDER_CLASS_CODE",
    "CASCADE3_MONITOR_CHRONOLOGY_CONSISTENT",
]


def sha256(path: Path) -> str | None:
    if not path.exists():
        return None
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest().upper()


def params(elem: ET.Element | None) -> dict[str, str]:
    if elem is None:
        return {}
    return {p.get("name", ""): p.get("value", "") for p in elem.findall("./paramlist/param")}


def name_param(elem: ET.Element) -> str:
    p = params(elem)
    return p.get("Name") or p.get("NAME") or ""


def number(text: str | None) -> float | None:
    try:
        return float(text) if text is not None else None
    except ValueError:
        return None


def find_users(root: ET.Element, key: str, value: str) -> list[ET.Element]:
    return [
        elem
        for elem in root.iter()
        if elem.tag == "User" and params(elem).get(key) == value
    ]


def find_user(root: ET.Element, key: str, value: str) -> ET.Element | None:
    hits = find_users(root, key, value)
    return hits[0] if hits else None


def locate_near_constant(root: ET.Element, x: float, y: float, expected_value: str) -> ET.Element | None:
    best: tuple[float, ET.Element] | None = None
    for elem in root.iter():
        if elem.tag != "User" or elem.get("defn") != "master:const":
            continue
        p = params(elem)
        if p.get("Value") != expected_value:
            continue
        ex = number(elem.get("x"))
        ey = number(elem.get("y"))
        if ex is None or ey is None:
            continue
        if abs(ex - x) <= 160 and abs(ey - y) <= 36:
            dist = abs(ex - x) + abs(ey - y)
            if best is None or dist < best[0]:
                best = (dist, elem)
    return best[1] if best else None


def collect_pgb_names(root: ET.Element) -> list[str]:
    return [
        name_param(elem)
        for elem in root.iter()
        if elem.tag == "User" and elem.get("defn") == "master:pgb" and name_param(elem)
    ]


def status(ok: bool) -> str:
    return "pass" if ok else "fail"


def describe(elem: ET.Element | None) -> dict[str, object] | None:
    if elem is None:
        return None
    p = params(elem)
    return {
        "id": elem.get("id"),
        "defn": elem.get("defn") or elem.get("name"),
        "x": number(elem.get("x")),
        "y": number(elem.get("y")),
        "name": p.get("Name") or p.get("NAME") or "",
        "value": p.get("Value"),
        "open_time_s": p.get("OPEN_TIME_S"),
        "cause_code_value": p.get("CAUSE_CODE_VALUE"),
    }


def main() -> int:
    report: dict[str, object] = {
        "main_project": str(MAIN_PROJECT),
        "trial_project": str(TRIAL_PROJECT),
        "result_directory": str(RESULT_DIR),
        "checks": {},
        "details": {},
    }
    checks: dict[str, str] = report["checks"]  # type: ignore[assignment]
    details: dict[str, object] = report["details"]  # type: ignore[assignment]

    main_sha = sha256(MAIN_PROJECT)
    trial_sha = sha256(TRIAL_PROJECT)
    details["main_sha_before"] = main_sha
    details["trial_sha_before"] = trial_sha

    try:
        root = ET.parse(TRIAL_PROJECT).getroot()
        details["trial_xml_parse_status"] = "pass"
    except Exception as exc:
        details["trial_xml_parse_status"] = "fail"
        details["trial_xml_parse_error"] = str(exc)
        print(json.dumps(report, indent=2, ensure_ascii=False))
        return 2

    pgb_names = collect_pgb_names(root)
    missing_channels = [name for name in REQUIRED_CHANNELS if name not in set(pgb_names)]
    checks["output_channel_preflight_status"] = status(
        len(pgb_names) == EXPECTED_OUTPUT_CHANNEL_COUNT and not missing_channels
    )
    details["output_channel_count"] = len(pgb_names)
    details["missing_required_channels"] = missing_channels

    ibr3_stim = find_user(root, "Name", "IBR3_TRIAL__OPEN_STIMULUS")
    ibr3_stim_params = params(ibr3_stim)
    ibr3_x = number(ibr3_stim.get("x")) if ibr3_stim is not None else None
    ibr3_y = number(ibr3_stim.get("y")) if ibr3_stim is not None else None
    ibr3_enable = (
        locate_near_constant(root, ibr3_x - 90, ibr3_y - 18, "0")
        if ibr3_x is not None and ibr3_y is not None
        else None
    )

    ibr2_enable = None
    for label in find_users(root, "Name", "IBR2_TEST_ENABLE"):
        lx = number(label.get("x"))
        ly = number(label.get("y"))
        if lx is None or ly is None:
            continue
        hit = locate_near_constant(root, lx - 108, ly, "0")
        if hit is not None:
            ibr2_enable = hit
            break

    ibr3_packet = find_user(root, "Name", "IBR3_TRIAL__EVENT_PACKET")
    ibr3_packet_params = params(ibr3_packet)

    details["ibr2_enable_static_value"] = params(ibr2_enable).get("Value")
    details["ibr3_enable_static_value"] = params(ibr3_enable).get("Value")
    details["ibr3_open_time_static_value"] = ibr3_stim_params.get("OPEN_TIME_S")
    details["ibr3_cause_code_static_value"] = ibr3_packet_params.get("CAUSE_CODE_VALUE")
    details["ibr2_enable_component_location"] = describe(ibr2_enable)
    details["ibr3_enable_component_location"] = describe(ibr3_enable)
    details["ibr3_open_time_component_location"] = describe(ibr3_stim)
    details["ibr3_event_packet_location"] = describe(ibr3_packet)

    checks["main_project_integrity_status"] = status(main_sha == EXPECTED_MAIN_SHA256)
    checks["trial_default_disabled_integrity_status"] = status(
        trial_sha == EXPECTED_RESTORED_TRIAL_SHA256
        and ibr3_enable is not None
        and params(ibr3_enable).get("Value") == "0"
    )
    checks["ibr2_test_disabled_status"] = status(
        ibr2_enable is not None and params(ibr2_enable).get("Value") == "0"
    )
    checks["ibr3_test_disabled_status"] = status(
        ibr3_enable is not None
        and params(ibr3_enable).get("Value") == "0"
        and ibr3_stim_params.get("OPEN_TIME_S") == "5.0"
        and ibr3_packet_params.get("CAUSE_CODE_VALUE") == "5"
    )

    settings_params = list(root.findall("./param")) + list(root.findall("./paramlist[@name='Settings']/param"))
    raw_step = next((p for p in settings_params if p.get("name") == "time_step"), None)
    raw_sample = next((p for p in settings_params if p.get("name") == "sample_step"), None)
    time_step_us = number(raw_step.get("value")) if raw_step is not None else None
    sample_step_us = number(raw_sample.get("value")) if raw_sample is not None else None
    details["simulation_timestep_s"] = time_step_us * 1e-6 if time_step_us is not None else None
    details["channel_plot_step_s"] = sample_step_us * 1e-6 if sample_step_us is not None else None

    previous_status = "fail"
    previous_details: dict[str, object] = {}
    if PREVIOUS_ENABLED_SUMMARY.exists() and PREVIOUS_ENABLED_AUDIT.exists():
        enabled = json.loads(PREVIOUS_ENABLED_SUMMARY.read_text(encoding="utf-8"))
        audit = json.loads(PREVIOUS_ENABLED_AUDIT.read_text(encoding="utf-8"))
        previous_details = {
            "previous_enabled_run_id": enabled.get("run_id"),
            "enabled_dynamic_run_status": enabled.get("dynamic_run_status"),
            "enabled_audit_execution_status": audit.get("execution_status"),
            "enabled_ibr3_test_enable_min": enabled["selected_channel_summary"]["IBR3_TRIAL_TEST_ENABLE"]["min"],
            "enabled_ibr3_open_request_time": enabled["event_times_s"]["ibr3_test_open_request_first_ge_0p5"],
            "enabled_ibr3_actual_open_time": enabled["event_times_s"]["ibr3_breaker_open_bool_first_ge_0p5"],
            "enabled_ibr3_event_valid_time": enabled["event_times_s"]["ibr3_event_valid_first_ge_0p5"],
            "enabled_cascade3_first_event_time": enabled["event_times_s"]["cascade3_first_event_time_last"],
            "enabled_cascade3_second_event_time": enabled["event_times_s"]["cascade3_second_event_time_last"],
        }
        previous_status = status(
            enabled.get("dynamic_run_status") == "pass"
            and enabled["selected_channel_summary"]["IBR3_TRIAL_TEST_ENABLE"]["min"] == 1.0
            and enabled["event_times_s"]["ibr3_test_open_request_first_ge_0p5"] == 5.0
            and enabled["event_times_s"]["ibr3_breaker_open_bool_first_ge_0p5"] == 5.0
            and enabled["event_times_s"]["ibr3_event_valid_first_ge_0p5"] == 5.0
            and enabled["event_times_s"]["cascade3_first_event_time_last"] == 2.01603
            and enabled["event_times_s"]["cascade3_second_event_time_last"] == 5.0
        )
    details["previous_enabled_run_evidence"] = previous_details
    checks["previous_enabled_run_evidence_status"] = previous_status

    text = TRIAL_PROJECT.read_text(encoding="utf-8", errors="ignore").lower()
    forbidden_terms = ["matlab", "autoreclose", "fourth source", "virtual source"]
    details["forbidden_term_hits"] = {term: text.count(term) for term in forbidden_terms}
    checks["no_out_of_scope_feature_status"] = status(all(text.count(term) == 0 for term in forbidden_terms))

    details["baseline_result_parser_strategy"] = {
        "directory": str(RESULT_DIR),
        "strategy": "After the manual default-disabled Run, parse 3IBR_DFIG1_TRIAL.inf plus 3IBR_DFIG1_TRIAL_NN.out files; PSCAD writes 10 PGB channels per .out file with column 0 as time.",
    }
    checks["run_artifact_parser_readiness_status"] = status(RESULT_DIR.exists())

    gate_keys = [
        "main_project_integrity_status",
        "trial_default_disabled_integrity_status",
        "ibr2_test_disabled_status",
        "ibr3_test_disabled_status",
        "previous_enabled_run_evidence_status",
        "output_channel_preflight_status",
        "run_artifact_parser_readiness_status",
    ]
    report["required_gate_statuses"] = {key: checks[key] for key in gate_keys}
    report["overall_preflight_status"] = status(all(checks[key] == "pass" for key in gate_keys))

    print(json.dumps(report, indent=2, ensure_ascii=False))
    return 0 if report["overall_preflight_status"] == "pass" else 1


if __name__ == "__main__":
    sys.exit(main())
