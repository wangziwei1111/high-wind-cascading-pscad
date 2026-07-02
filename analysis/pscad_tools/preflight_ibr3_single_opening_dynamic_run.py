#!/usr/bin/env python3
"""Read-only preflight for the IBR3 single controlled opening dynamic run.

This script intentionally does not edit, build, or run PSCAD projects.  It
checks that the trial project is exactly at the expected static baseline and
that the one-run dynamic validation can be performed and parsed afterward.
"""

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

EXPECTED_MAIN_SHA256 = "CBA120BB167CB7FA6C4A1AE4471268850AB61761EC1877EB7B87015627FE9DAB"
EXPECTED_TRIAL_PRE_RUN_SHA256 = "469103EF282C97CF7735D0E4BB8665A6D57FA453A6AA7F5BA86B5770951CDE92"
EXPECTED_OUTPUT_CHANNEL_COUNT = 253

REQUIRED_IBR3_CHANNELS = [
    "IBR3_TRIAL_BRK_CMD",
    "IBR3_TRIAL_BRK_STATE",
    "IBR3_TRIAL_BRK_OPEN_BOOL",
    "IBR3_TRIAL_SOURCE_AVAILABLE",
    "IBR3_TRIAL_TEST_ENABLE",
    "IBR3_TRIAL_TEST_OPEN_TIME_S",
    "IBR3_TRIAL_TEST_OPEN_REQUEST",
    "IBR3_TRIAL_CASCADE_EVENT_VALID",
    "IBR3_TRIAL_CASCADE_EVENT_CAUSE_CODE",
    "IBR3_TRIAL_CASCADE_EVENT_BRK_OPEN",
    "IBR3_TRIAL_CASCADE_SOURCE_AVAILABLE",
    "IBR3_TRIAL_CASCADE_FIRST_EVENT_TIME_S",
]

REQUIRED_CASCADE3_CHANNELS = [
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


def params(elem: ET.Element) -> dict[str, str]:
    return {
        p.get("name", ""): p.get("value", "")
        for p in elem.findall("./paramlist/param")
    }


def name_param(elem: ET.Element) -> str:
    p = params(elem)
    return p.get("Name") or p.get("NAME") or ""


def number(value: str) -> float | None:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def describe(elem: ET.Element | None) -> dict[str, object] | None:
    if elem is None:
        return None
    p = params(elem)
    return {
        "id": elem.get("id"),
        "defn": elem.get("defn") or elem.get("name"),
        "x": number(elem.get("x", "")),
        "y": number(elem.get("y", "")),
        "name": p.get("Name") or p.get("NAME") or "",
        "value": p.get("Value"),
        "open_time_s": p.get("OPEN_TIME_S"),
        "cause_code_value": p.get("CAUSE_CODE_VALUE"),
    }


def find_user_by_param(root: ET.Element, key: str, value: str) -> ET.Element | None:
    for elem in root.iter():
        if elem.tag != "User":
            continue
        if params(elem).get(key) == value:
            return elem
    return None


def find_users_by_param(root: ET.Element, key: str, value: str) -> list[ET.Element]:
    hits: list[ET.Element] = []
    for elem in root.iter():
        if elem.tag != "User":
            continue
        if params(elem).get(key) == value:
            hits.append(elem)
    return hits


def find_users_by_defn(root: ET.Element, defn: str) -> list[ET.Element]:
    return [e for e in root.iter() if e.tag == "User" and e.get("defn") == defn]


def collect_pgb_names(root: ET.Element) -> list[str]:
    names: list[str] = []
    for elem in root.iter():
        if elem.tag == "User" and elem.get("defn") == "master:pgb":
            nm = name_param(elem)
            if nm:
                names.append(nm)
    return names


def locate_near_constant(
    root: ET.Element,
    x: float,
    y: float,
    expected_value: str,
    max_dx: float = 160.0,
    max_dy: float = 36.0,
) -> ET.Element | None:
    best: tuple[float, ET.Element] | None = None
    for elem in root.iter():
        if elem.tag != "User" or elem.get("defn") != "master:const":
            continue
        p = params(elem)
        if p.get("Value") != expected_value:
            continue
        ex = number(elem.get("x", ""))
        ey = number(elem.get("y", ""))
        if ex is None or ey is None:
            continue
        if abs(ex - x) <= max_dx and abs(ey - y) <= max_dy:
            dist = abs(ex - x) + abs(ey - y)
            if best is None or dist < best[0]:
                best = (dist, elem)
    return best[1] if best else None


def status(ok: bool) -> str:
    return "PASS" if ok else "FAIL"


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
    details["main_sha256"] = main_sha
    details["trial_sha256"] = trial_sha
    details["expected_main_sha256"] = EXPECTED_MAIN_SHA256
    details["expected_trial_pre_run_sha256"] = EXPECTED_TRIAL_PRE_RUN_SHA256
    checks["main_project_integrity_status"] = status(
        MAIN_PROJECT.exists()
        and TRIAL_PROJECT.exists()
        and MAIN_PROJECT.resolve() != TRIAL_PROJECT.resolve()
        and main_sha == EXPECTED_MAIN_SHA256
    )
    checks["trial_project_pre_run_status"] = status(
        TRIAL_PROJECT.exists() and trial_sha == EXPECTED_TRIAL_PRE_RUN_SHA256
    )

    try:
        tree = ET.parse(TRIAL_PROJECT)
        root = tree.getroot()
        details["trial_xml_parse_status"] = "PASS"
    except Exception as exc:  # pragma: no cover - diagnostic exit path
        details["trial_xml_parse_status"] = "FAIL"
        details["trial_xml_parse_error"] = str(exc)
        print(json.dumps(report, indent=2, ensure_ascii=False))
        return 2

    pgb_names = collect_pgb_names(root)
    pgb_set = set(pgb_names)
    missing_ibr3 = [n for n in REQUIRED_IBR3_CHANNELS if n not in pgb_set]
    missing_cascade3 = [n for n in REQUIRED_CASCADE3_CHANNELS if n not in pgb_set]
    details["output_channel_count"] = len(pgb_names)
    details["required_ibr3_output_channels_missing"] = missing_ibr3
    details["required_cascade3_output_channels_missing"] = missing_cascade3
    checks["output_channel_preflight_status"] = status(
        len(pgb_names) == EXPECTED_OUTPUT_CHANNEL_COUNT
        and not missing_ibr3
        and not missing_cascade3
    )

    ibr3_stim = find_user_by_param(root, "Name", "IBR3_TRIAL__OPEN_STIMULUS")
    ibr3_stim_params = params(ibr3_stim) if ibr3_stim is not None else {}
    ibr3_x = number(ibr3_stim.get("x", "")) if ibr3_stim is not None else None
    ibr3_y = number(ibr3_stim.get("y", "")) if ibr3_stim is not None else None
    ibr3_enable = (
        locate_near_constant(root, ibr3_x - 90, ibr3_y - 18, "0")
        if ibr3_x is not None and ibr3_y is not None
        else None
    )
    ibr3_open_time_param = find_user_by_param(root, "Name", "IBR3_TRIAL__OPEN_STIMULUS")
    ibr3_cause = find_user_by_param(root, "Name", "IBR3_TRIAL__EVENT_PACKET")
    ibr3_cause_params = params(ibr3_cause) if ibr3_cause is not None else {}

    # IBR2 used an older instance name in this project.  The local default
    # disable source is the zero Constant feeding the IBR2_TEST_ENABLE label.
    ibr2_enable = None
    for ibr2_test_enable_label in find_users_by_param(root, "Name", "IBR2_TEST_ENABLE"):
        ibr2_x = number(ibr2_test_enable_label.get("x", ""))
        ibr2_y = number(ibr2_test_enable_label.get("y", ""))
        if ibr2_x is None or ibr2_y is None:
            continue
        hit = locate_near_constant(root, ibr2_x - 108, ibr2_y, "0")
        if hit is not None:
            ibr2_enable = hit
            break

    brk_ibr3_trial = find_user_by_param(root, "NAME", "BRK_IBR3_TRIAL")
    if brk_ibr3_trial is None:
        brk_ibr3_trial = find_user_by_param(root, "Name", "BRK_IBR3_TRIAL")
    required_instances = {
        "BRK_IBR3_TRIAL": brk_ibr3_trial,
        "IBR3_TRIAL__EVENT_PACKET": ibr3_cause,
        "CASCADE3_TRIAL__EVENT_COLLECTOR": find_user_by_param(root, "Name", "CASCADE3_TRIAL__EVENT_COLLECTOR"),
        "CASCADE3_TRIAL__CHRONOLOGY_MONITOR": find_user_by_param(root, "Name", "CASCADE3_TRIAL__CHRONOLOGY_MONITOR"),
    }

    details["ibr3_test_enable_component_location"] = describe(ibr3_enable)
    details["ibr2_test_enable_component_location"] = describe(ibr2_enable)
    details["ibr3_open_time_parameter_location"] = describe(ibr3_open_time_param)
    details["ibr3_event_packet_location"] = describe(ibr3_cause)
    details["required_instance_locations"] = {k: describe(v) for k, v in required_instances.items()}

    checks["ibr3_single_run_interface_status"] = status(
        ibr3_stim is not None
        and ibr3_enable is not None
        and params(ibr3_enable).get("Value") == "0"
        and ibr3_stim_params.get("OPEN_TIME_S") == "5.0"
        and ibr3_cause is not None
        and ibr3_cause_params.get("CAUSE_CODE_VALUE") == "5"
        and all(v is not None for v in required_instances.values())
    )
    checks["ibr2_test_isolation_status"] = status(
        ibr2_enable is not None and params(ibr2_enable).get("Value") == "0"
    )

    settings_params = list(root.findall("./param")) + list(root.findall("./paramlist[@name='Settings']/param"))
    raw_duration = next((p for p in settings_params if p.get("name") == "time_duration"), None)
    raw_step = next((p for p in settings_params if p.get("name") == "time_step"), None)
    raw_sample = next((p for p in settings_params if p.get("name") == "sample_step"), None)
    time_step_us = number(raw_step.get("value", "")) if raw_step is not None else None
    sample_step_us = number(raw_sample.get("value", "")) if raw_sample is not None else None
    details["simulation_duration_s"] = number(raw_duration.get("value", "")) if raw_duration is not None else None
    details["simulation_timestep_s"] = time_step_us * 1e-6 if time_step_us is not None else None
    details["simulation_timestep_raw_project_value_us"] = time_step_us
    details["plot_sample_step_s"] = sample_step_us * 1e-6 if sample_step_us is not None else None
    details["plot_sample_step_raw_project_value_us"] = sample_step_us

    forbidden_terms = ["autoreclose", "fourth source", "virtual source", "matlab"]
    text = TRIAL_PROJECT.read_text(encoding="utf-8", errors="ignore").lower()
    details["forbidden_term_hits"] = {term: text.count(term) for term in forbidden_terms}
    checks["no_out_of_scope_feature_status"] = status(
        details["forbidden_term_hits"] == {term: 0 for term in forbidden_terms}
    )

    result_files = []
    if RESULT_DIR.exists():
        for path in sorted(RESULT_DIR.glob("*")):
            if path.is_file() and path.suffix.lower() in {".inf", ".out", ".tli", ".tlo", ".log"}:
                result_files.append(
                    {
                        "name": path.name,
                        "suffix": path.suffix.lower(),
                        "bytes": path.stat().st_size,
                        "mtime": path.stat().st_mtime,
                    }
                )
    details["run_result_directory_strategy"] = {
        "directory_exists": RESULT_DIR.exists(),
        "directory": str(RESULT_DIR),
        "strategy": "After the manual Run, parse files in this directory whose LastWriteTime is newer than the pre-run manifest timestamp; prefer PSCAD Output Channel mapping files if emitted.",
        "current_relevant_file_count": len(result_files),
    }
    details["available_output_parser_strategy"] = {
        "primary": "Discover new/updated PSCAD output artifacts after the single Run and map Output Channel names to numeric series.",
        "fallback": "If named Output Channel artifacts are not emitted, report INCONCLUSIVE rather than inferring from unrelated EMTDC branch .out files.",
    }
    checks["run_artifact_parser_readiness_status"] = status(RESULT_DIR.exists())

    required_statuses = [
        "main_project_integrity_status",
        "trial_project_pre_run_status",
        "ibr3_single_run_interface_status",
        "ibr2_test_isolation_status",
        "output_channel_preflight_status",
        "run_artifact_parser_readiness_status",
    ]
    report["overall_preflight_status"] = status(all(checks.get(k) == "PASS" for k in required_statuses))
    report["required_gate_statuses"] = {k: checks.get(k) for k in required_statuses}

    print(json.dumps(report, indent=2, ensure_ascii=False))
    return 0 if report["overall_preflight_status"] == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
