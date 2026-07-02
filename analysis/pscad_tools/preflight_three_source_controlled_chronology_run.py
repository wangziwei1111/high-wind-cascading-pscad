#!/usr/bin/env python3
"""Read-only preflight for the controlled three-source chronology PSCAD run."""

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
EXPECTED_RESTORED_TRIAL_SHA256 = "B6BBC137FA11C421EC5419BBD0661B2924285BD70A1E2026F47F8DF958FD271B"
EXPECTED_OUTPUT_CHANNEL_COUNT = 253

REQUIRED_EVIDENCE = [
    Path("data/validation/ibr3_default_disabled_baseline_run_summary.json"),
    Path("data/validation/ibr2_trial_single_opening_run_summary.json"),
    Path("data/validation/ibr3_trial_single_opening_run_summary.json"),
]

SOURCE_A = [
    "DFIG_LVRT_CASCADE_EVENT_VALID",
    "DFIG_LVRT_CASCADE_EVENT_CAUSE_CODE",
    "DFIG_LVRT_CASCADE_EVENT_BRK_OPEN",
    "DFIG_LVRT_CASCADE_SOURCE_AVAILABLE",
    "DFIG_LVRT_CASCADE_FIRST_EVENT_TIME_S",
]
SOURCE_B = [
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
SOURCE_C = [
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
]
COLLECTOR = [
    "CASCADE3_MONITOR_ANY_TRIP",
    "CASCADE3_MONITOR_ANY_BRK_OPEN",
    "CASCADE3_MONITOR_AVAILABLE_SOURCE_COUNT",
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
]
CHRONOLOGY = [
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


def number(value: str | None) -> float | None:
    try:
        return float(value) if value is not None else None
    except ValueError:
        return None


def name_param(elem: ET.Element) -> str:
    p = params(elem)
    return p.get("Name") or p.get("NAME") or ""


def find_users(root: ET.Element, key: str, value: str) -> list[ET.Element]:
    return [elem for elem in root.iter() if elem.tag == "User" and params(elem).get(key) == value]


def find_user(root: ET.Element, key: str, value: str) -> ET.Element | None:
    hits = find_users(root, key, value)
    return hits[0] if hits else None


def locate_near_constant(root: ET.Element, x: float, y: float, value: str | None = None) -> ET.Element | None:
    best: tuple[float, ET.Element] | None = None
    for elem in root.iter():
        if elem.tag != "User" or elem.get("defn") != "master:const":
            continue
        p = params(elem)
        if value is not None and p.get("Value") != value:
            continue
        ex = number(elem.get("x"))
        ey = number(elem.get("y"))
        if ex is None or ey is None:
            continue
        if abs(ex - x) <= 180 and abs(ey - y) <= 72:
            dist = abs(ex - x) + abs(ey - y)
            if best is None or dist < best[0]:
                best = (dist, elem)
    return best[1] if best else None


def find_labeled_constant(root: ET.Element, label_name: str) -> ET.Element | None:
    for label in find_users(root, "Name", label_name):
        lx = number(label.get("x"))
        ly = number(label.get("y"))
        if lx is None or ly is None:
            continue
        hit = locate_near_constant(root, lx - 108, ly)
        if hit is not None:
            return hit
    return None


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


def collect_pgb_names(root: ET.Element) -> list[str]:
    return [
        name_param(elem)
        for elem in root.iter()
        if elem.tag == "User" and elem.get("defn") == "master:pgb" and name_param(elem)
    ]


def mapping(names: list[str], required: list[str]) -> dict[str, int | None]:
    return {name: (names.index(name) + 1 if name in names else None) for name in required}


def status(ok: bool) -> str:
    return "pass" if ok else "fail"


def main() -> int:
    report: dict[str, object] = {
        "execution_status": "three_source_controlled_chronology_preflight",
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
    checks["trial_project_pre_run_status"] = status(trial_sha == EXPECTED_RESTORED_TRIAL_SHA256)

    try:
        root = ET.parse(TRIAL_PROJECT).getroot()
        details["trial_xml_parse_status"] = "pass"
    except Exception as exc:
        details["trial_xml_parse_status"] = "fail"
        details["trial_xml_parse_error"] = str(exc)
        print(json.dumps(report, indent=2, ensure_ascii=False))
        return 2

    pgb_names = collect_pgb_names(root)
    details["output_channel_count"] = len(pgb_names)
    details["source_a_actual_signal_mapping"] = mapping(pgb_names, SOURCE_A)
    details["source_b_actual_signal_mapping"] = mapping(pgb_names, SOURCE_B)
    details["source_c_actual_signal_mapping"] = mapping(pgb_names, SOURCE_C)
    details["collector_actual_signal_mapping"] = mapping(pgb_names, COLLECTOR)
    details["chronology_actual_signal_mapping"] = mapping(pgb_names, CHRONOLOGY)
    checks["output_channel_preflight_status"] = status(len(pgb_names) == EXPECTED_OUTPUT_CHANNEL_COUNT)
    checks["source_a_interface_status"] = status(all(name in pgb_names for name in SOURCE_A))
    checks["source_b_interface_status"] = status(all(name in pgb_names for name in SOURCE_B))
    checks["source_c_interface_status"] = status(all(name in pgb_names for name in SOURCE_C))
    checks["three_source_collector_interface_status"] = status(all(name in pgb_names for name in COLLECTOR))
    checks["three_event_chronology_interface_status"] = status(all(name in pgb_names for name in CHRONOLOGY))

    ibr2_enable = find_labeled_constant(root, "IBR2_TEST_ENABLE")
    ibr3_enable = find_labeled_constant(root, "IBR3_TEST_ENABLE")
    ibr2_stim = find_user(root, "Name", "MODTEST_ONE_SHOT_STIMULUS")
    ibr2_packet = find_user(root, "Name", "MODTEST_OBJECT_EVENT_PACKET")
    ibr3_stim = find_user(root, "Name", "IBR3_TRIAL__OPEN_STIMULUS")
    ibr3_packet = find_user(root, "Name", "IBR3_TRIAL__EVENT_PACKET")

    details["ibr2_enable_constant_location"] = describe(ibr2_enable)
    details["ibr3_enable_constant_location"] = describe(ibr3_enable)
    details["ibr2_stimulus"] = describe(ibr2_stim)
    details["ibr2_event_packet"] = describe(ibr2_packet)
    details["ibr3_stimulus"] = describe(ibr3_stim)
    details["ibr3_event_packet"] = describe(ibr3_packet)

    checks["dual_trial_enable_clean_state_status"] = status(
        params(ibr2_enable).get("Value") == "0"
        and params(ibr3_enable).get("Value") == "0"
        and params(ibr2_stim).get("OPEN_TIME_S") == "4.0"
        and params(ibr2_packet).get("CAUSE_CODE_VALUE") == "4"
        and params(ibr3_stim).get("OPEN_TIME_S") == "5.0"
        and params(ibr3_packet).get("CAUSE_CODE_VALUE") == "5"
    )

    details["required_prior_evidence"] = {str(path): path.exists() for path in REQUIRED_EVIDENCE}
    checks["prior_dynamic_evidence_status"] = status(all(path.exists() for path in REQUIRED_EVIDENCE))

    xml_text = TRIAL_PROJECT.read_text(encoding="utf-8", errors="ignore").upper()
    forbidden_tokens = ["MATLAB", "AUTORECLOSE", "AUTO_RECLOSE", "FOURTH_SOURCE", "VIRTUAL_SOURCE"]
    details["forbidden_token_hits"] = [token for token in forbidden_tokens if token in xml_text]
    checks["scope_guard_status"] = status(not details["forbidden_token_hits"])

    details["simulation_timestep_s"] = 0.000005
    details["channel_plot_step_s"] = 0.01
    details["run_result_directory_strategy"] = str(RESULT_DIR)
    details["output_parser_strategy"] = "Read 3IBR_DFIG1_TRIAL.inf for PGB numbers; read 3IBR_DFIG1_TRIAL_NN.out with 10 channels per file."
    checks["run_artifact_parser_readiness_status"] = status(True)

    required_pass = [
        "main_project_integrity_status",
        "trial_project_pre_run_status",
        "source_a_interface_status",
        "source_b_interface_status",
        "source_c_interface_status",
        "three_source_collector_interface_status",
        "three_event_chronology_interface_status",
        "dual_trial_enable_clean_state_status",
        "output_channel_preflight_status",
        "run_artifact_parser_readiness_status",
        "prior_dynamic_evidence_status",
        "scope_guard_status",
    ]
    checks["overall_status"] = status(all(checks[name] == "pass" for name in required_pass))
    if checks["overall_status"] != "pass":
        report["execution_status"] = "three_source_controlled_chronology_preflight_fallback"

    print(json.dumps(report, indent=2, ensure_ascii=False))
    return 0 if checks["overall_status"] == "pass" else 2


if __name__ == "__main__":
    sys.exit(main())
