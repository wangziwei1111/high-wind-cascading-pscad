#!/usr/bin/env python3
"""Read-only preflight for the IBR2 single-opening trial run."""

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
BASELINE_SUMMARY = Path("data/validation/ibr3_default_disabled_baseline_run_summary.json")
BASELINE_AUDIT = Path("data/validation/ibr3_default_disabled_baseline_final_audit.json")

EXPECTED_MAIN_SHA256 = "CBA120BB167CB7FA6C4A1AE4471268850AB61761EC1877EB7B87015627FE9DAB"
EXPECTED_TRIAL_SHA256 = "C03DAA211B591923F533554C9951503096677BCF52547D13A10C4B431E69A349"
EXPECTED_OUTPUT_CHANNEL_COUNT = 253

IBR2_CHANNELS = [
    "IBR2_TRIAL_TEST_ENABLE",
    "IBR2_TRIAL_TEST_OPEN_TIME_S",
    "IBR2_TRIAL_TEST_OPEN_REQUEST",
    "IBR2_TRIAL_BRK_CMD",
    "IBR2_TRIAL_BRK_STATE",
    "IBR2_TRIAL_BRK_OPEN_BOOL",
    "IBR2_TRIAL_SOURCE_AVAILABLE",
    "IBR2_TRIAL_CASCADE_EVENT_VALID",
    "IBR2_TRIAL_CASCADE_EVENT_CAUSE_CODE",
    "IBR2_TRIAL_CASCADE_EVENT_BRK_OPEN",
    "IBR2_TRIAL_CASCADE_SOURCE_AVAILABLE",
    "IBR2_TRIAL_CASCADE_FIRST_EVENT_TIME_S",
]

IBR3_CHANNELS = [
    "IBR3_TRIAL_TEST_ENABLE",
    "IBR3_TRIAL_TEST_OPEN_REQUEST",
    "IBR3_TRIAL_BRK_CMD",
    "IBR3_TRIAL_BRK_STATE",
    "IBR3_TRIAL_BRK_OPEN_BOOL",
    "IBR3_TRIAL_SOURCE_AVAILABLE",
    "IBR3_TRIAL_CASCADE_EVENT_VALID",
    "IBR3_TRIAL_CASCADE_EVENT_CAUSE_CODE",
]

CASCADE3_CHANNELS = [
    "CASCADE3_MONITOR_EVENTED_SOURCE_COUNT",
    "CASCADE3_MONITOR_TIMED_EVENT_SOURCE_COUNT",
    "CASCADE3_MONITOR_FIRST_EVENT_TIME_S",
    "CASCADE3_MONITOR_SECOND_EVENT_TIME_S",
    "CASCADE3_MONITOR_THIRD_EVENT_TIME_S",
    "CASCADE3_MONITOR_FIRST_TO_SECOND_GAP_S",
    "CASCADE3_MONITOR_SECOND_TO_THIRD_GAP_S",
    "CASCADE3_MONITOR_FIRST_EVENT_SOURCE_CODE",
    "CASCADE3_MONITOR_CAUSE_CODE_DFIG1",
    "CASCADE3_MONITOR_CAUSE_CODE_IBR2_TRIAL",
    "CASCADE3_MONITOR_CAUSE_CODE_IBR3_TRIAL",
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


def number(value: str | None) -> float | None:
    try:
        return float(value) if value is not None else None
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


def locate_near_constant(root: ET.Element, x: float, y: float, value: str) -> ET.Element | None:
    best: tuple[float, ET.Element] | None = None
    for elem in root.iter():
        if elem.tag != "User" or elem.get("defn") != "master:const":
            continue
        if params(elem).get("Value") != value:
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


def status(ok: bool) -> str:
    return "pass" if ok else "fail"


def mapping(names: list[str], required: list[str]) -> dict[str, int | None]:
    return {name: (names.index(name) + 1 if name in names else None) for name in required}


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
    checks["main_project_integrity_status"] = status(
        MAIN_PROJECT.exists()
        and TRIAL_PROJECT.exists()
        and MAIN_PROJECT.resolve() != TRIAL_PROJECT.resolve()
        and main_sha == EXPECTED_MAIN_SHA256
    )
    checks["trial_project_pre_run_status"] = status(trial_sha == EXPECTED_TRIAL_SHA256)

    try:
        root = ET.parse(TRIAL_PROJECT).getroot()
        details["trial_xml_parse_status"] = "pass"
    except Exception as exc:
        details["trial_xml_parse_status"] = "fail"
        details["trial_xml_parse_error"] = str(exc)
        print(json.dumps(report, indent=2, ensure_ascii=False))
        return 2

    pgb_names = collect_pgb_names(root)
    required_channels = IBR2_CHANNELS + IBR3_CHANNELS + CASCADE3_CHANNELS
    missing_channels = [name for name in required_channels if name not in set(pgb_names)]
    details["output_channel_count"] = len(pgb_names)
    details["missing_required_channels"] = missing_channels
    details["ibr2_output_channel_mapping"] = mapping(pgb_names, IBR2_CHANNELS)
    details["ibr3_output_channel_mapping"] = mapping(pgb_names, IBR3_CHANNELS)
    details["cascade3_output_channel_mapping"] = mapping(pgb_names, CASCADE3_CHANNELS)
    checks["output_channel_preflight_status"] = status(
        len(pgb_names) == EXPECTED_OUTPUT_CHANNEL_COUNT and not missing_channels
    )

    # IBR2 stimulus still uses the earlier module-test instance name.
    ibr2_stim = find_user(root, "Name", "MODTEST_ONE_SHOT_STIMULUS")
    ibr2_packet = find_user(root, "Name", "MODTEST_OBJECT_EVENT_PACKET")
    ibr3_stim = find_user(root, "Name", "IBR3_TRIAL__OPEN_STIMULUS")
    ibr3_packet = find_user(root, "Name", "IBR3_TRIAL__EVENT_PACKET")

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

    ibr3_enable = None
    ibr3_x = number(ibr3_stim.get("x")) if ibr3_stim is not None else None
    ibr3_y = number(ibr3_stim.get("y")) if ibr3_stim is not None else None
    if ibr3_x is not None and ibr3_y is not None:
        ibr3_enable = locate_near_constant(root, ibr3_x - 90, ibr3_y - 18, "0")

    details["ibr2_test_enable_component_location"] = describe(ibr2_enable)
    details["ibr3_test_enable_component_location"] = describe(ibr3_enable)
    details["ibr2_open_time_parameter_location"] = describe(ibr2_stim)
    details["ibr2_cause_code_parameter_location"] = describe(ibr2_packet)
    details["ibr3_open_time_parameter_location"] = describe(ibr3_stim)
    details["ibr3_cause_code_parameter_location"] = describe(ibr3_packet)

    checks["ibr2_single_run_interface_status"] = status(
        ibr2_enable is not None
        and params(ibr2_enable).get("Value") == "0"
        and params(ibr2_stim).get("OPEN_TIME_S") == "4.0"
        and params(ibr2_packet).get("CAUSE_CODE_VALUE") == "4"
    )
    checks["ibr3_default_disabled_isolation_status"] = status(
        ibr3_enable is not None
        and params(ibr3_enable).get("Value") == "0"
        and params(ibr3_stim).get("OPEN_TIME_S") == "5.0"
        and params(ibr3_packet).get("CAUSE_CODE_VALUE") == "5"
    )

    baseline_ok = "fail"
    baseline_details: dict[str, object] = {}
    if BASELINE_SUMMARY.exists() and BASELINE_AUDIT.exists():
        baseline = json.loads(BASELINE_SUMMARY.read_text(encoding="utf-8"))
        audit = json.loads(BASELINE_AUDIT.read_text(encoding="utf-8"))
        baseline_details = {
            "baseline_run_id": baseline.get("run_id"),
            "baseline_dynamic_status": baseline.get("dynamic_baseline_status"),
            "baseline_audit_status": audit.get("execution_status"),
            "dfig_first_event_time_s": baseline["event_signature"]["dfig_first_event_time_s"],
            "dfig_cause_code": baseline["event_signature"]["dfig_cause_code"],
            "ibr2_cause_code": baseline["event_signature"]["ibr2_cause_code"],
            "ibr3_cause_code": baseline["event_signature"]["ibr3_cause_code"],
            "evented_source_count": baseline["event_signature"]["evented_source_count"],
            "second_event_time_s": baseline["event_signature"]["second_event_time_s"],
        }
        baseline_ok = status(
            baseline.get("dynamic_baseline_status") == "pass"
            and audit.get("execution_status") == "completed_pass"
            and baseline["event_signature"]["dfig_first_event_time_s"] == 2.01603
            and round(baseline["event_signature"]["dfig_cause_code"]) == 2
            and round(baseline["event_signature"]["ibr2_cause_code"]) == 0
            and round(baseline["event_signature"]["ibr3_cause_code"]) == 0
            and round(baseline["event_signature"]["evented_source_count"]) == 1
            and baseline["event_signature"]["second_event_time_s"] == -1.0
        )
    details["baseline_evidence"] = baseline_details
    checks["baseline_evidence_status"] = baseline_ok

    settings_params = list(root.findall("./param")) + list(root.findall("./paramlist[@name='Settings']/param"))
    raw_step = next((p for p in settings_params if p.get("name") == "time_step"), None)
    raw_sample = next((p for p in settings_params if p.get("name") == "sample_step"), None)
    time_step_us = number(raw_step.get("value")) if raw_step is not None else None
    sample_step_us = number(raw_sample.get("value")) if raw_sample is not None else None
    details["simulation_timestep_s"] = time_step_us * 1e-6 if time_step_us is not None else None
    details["channel_plot_step_s"] = sample_step_us * 1e-6 if sample_step_us is not None else None

    text = TRIAL_PROJECT.read_text(encoding="utf-8", errors="ignore").lower()
    forbidden_terms = ["autoreclose", "matlab", "fourth source", "virtual source"]
    details["forbidden_term_hits"] = {term: text.count(term) for term in forbidden_terms}
    checks["no_out_of_scope_feature_status"] = status(all(text.count(term) == 0 for term in forbidden_terms))

    details["run_result_directory_strategy"] = {
        "directory": str(RESULT_DIR),
        "directory_exists": RESULT_DIR.exists(),
        "strategy": "After the manual IBR2 enabled Run, parse 3IBR_DFIG1_TRIAL.inf plus 3IBR_DFIG1_TRIAL_NN.out files; PSCAD writes 10 PGB channels per .out file with column 0 as time.",
    }
    details["available_output_parser_strategy"] = {
        "primary": "Map Output Channel names from .inf PGB(n) entries to NN.out files using file=ceil(n/10), data_column=((n-1)%10)+1.",
        "fallback": "If named PGB output files are absent, report inconclusive rather than inferring from EMTDC branch files.",
    }
    checks["run_artifact_parser_readiness_status"] = status(RESULT_DIR.exists())

    gate_keys = [
        "main_project_integrity_status",
        "trial_project_pre_run_status",
        "ibr2_single_run_interface_status",
        "ibr3_default_disabled_isolation_status",
        "baseline_evidence_status",
        "output_channel_preflight_status",
        "run_artifact_parser_readiness_status",
    ]
    report["required_gate_statuses"] = {key: checks[key] for key in gate_keys}
    report["overall_preflight_status"] = status(all(checks[key] == "pass" for key in gate_keys))
    print(json.dumps(report, indent=2, ensure_ascii=False))
    return 0 if report["overall_preflight_status"] == "pass" else 1


if __name__ == "__main__":
    sys.exit(main())
