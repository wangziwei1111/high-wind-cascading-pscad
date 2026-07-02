#!/usr/bin/env python3
"""Final audit for the controlled three-source chronology PSCAD run."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sys
import xml.etree.ElementTree as ET


PSCAD_ROOT = Path(r"C:\pscad_work\pnnl_39_3ibr_pscad46_strip5\PSCAD")
MAIN_PROJECT = PSCAD_ROOT / "3IBR.pscx"
TRIAL_PROJECT = PSCAD_ROOT / "3IBR_DFIG1_TRIAL.pscx"

RUN_SUMMARY = Path("data/validation/three_source_controlled_chronology_run_summary.json")
RUN_COMPARISON = Path("data/validation/three_source_controlled_chronology_comparison.json")
PRE_RUN_MANIFEST = Path("data/validation/three_source_controlled_chronology_pre_run_manifest.json")
FINAL_AUDIT = Path("data/validation/three_source_controlled_chronology_final_audit.json")

EXPECTED_MAIN_SHA256 = "CBA120BB167CB7FA6C4A1AE4471268850AB61761EC1877EB7B87015627FE9DAB"
EXPECTED_PRE_RUN_TRIAL_SHA256 = "B6BBC137FA11C421EC5419BBD0661B2924285BD70A1E2026F47F8DF958FD271B"
EXPECTED_OUTPUT_CHANNEL_COUNT = 253


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


def collect_pgb_names(root: ET.Element) -> list[str]:
    return [
        name_param(elem)
        for elem in root.iter()
        if elem.tag == "User" and elem.get("defn") == "master:pgb" and name_param(elem)
    ]


def status(ok: bool) -> str:
    return "pass" if ok else "fail"


def approx(value: float | None, expected: float, tol: float = 2.0e-2) -> bool:
    return value is not None and abs(value - expected) <= tol


def main() -> int:
    report: dict[str, object] = {
        "execution_status": "three_source_controlled_chronology_final_audit",
        "dynamic_claim_boundary": (
            "This audit supports only one controlled timing-interface validation: "
            "the existing default DFIG event plus independently scheduled IBR2_TRIAL "
            "and IBR3_TRIAL local-opening stimuli. It does not validate natural "
            "cascade propagation, physical causality direction, system stability, "
            "protection coordination, MATLAB coupling, or general applicability."
        ),
        "paths": {
            "main_project": str(MAIN_PROJECT),
            "trial_project": str(TRIAL_PROJECT),
            "run_summary": str(RUN_SUMMARY),
            "run_comparison": str(RUN_COMPARISON),
            "pre_run_manifest": str(PRE_RUN_MANIFEST),
        },
        "checks": {},
        "details": {},
        "fixed_unavailable_statuses": {
            "matlab_status": "not_added",
            "cascade_propagation_status": "unavailable",
            "multi_source_causality_status": "unavailable",
            "physical_causality_direction_status": "unavailable",
            "system_stability_status": "unavailable",
            "protection_coordination_status": "unavailable",
        },
    }
    checks: dict[str, str] = report["checks"]  # type: ignore[assignment]
    details: dict[str, object] = report["details"]  # type: ignore[assignment]

    main_sha = sha256(MAIN_PROJECT)
    trial_sha = sha256(TRIAL_PROJECT)
    details["main_sha_final"] = main_sha
    details["trial_sha_pre_run_expected"] = EXPECTED_PRE_RUN_TRIAL_SHA256
    details["trial_sha_post_restore_build"] = trial_sha
    details["trial_byte_sha_drift_after_restore_build"] = trial_sha != EXPECTED_PRE_RUN_TRIAL_SHA256
    checks["main_project_integrity_status"] = status(main_sha == EXPECTED_MAIN_SHA256)

    try:
        root = ET.parse(TRIAL_PROJECT).getroot()
        details["trial_xml_parse_status"] = "pass"
    except Exception as exc:
        details["trial_xml_parse_status"] = "fail"
        details["trial_xml_parse_error"] = str(exc)
        print(json.dumps(report, indent=2, ensure_ascii=False))
        return 2

    pgb_names = collect_pgb_names(root)
    details["output_channel_count_final"] = len(pgb_names)
    checks["output_channel_count_status"] = status(len(pgb_names) == EXPECTED_OUTPUT_CHANNEL_COUNT)

    ibr2_enable = find_labeled_constant(root, "IBR2_TEST_ENABLE")
    ibr3_enable = find_labeled_constant(root, "IBR3_TEST_ENABLE")
    ibr2_stim = find_user(root, "Name", "MODTEST_ONE_SHOT_STIMULUS")
    ibr2_packet = find_user(root, "Name", "MODTEST_OBJECT_EVENT_PACKET")
    ibr3_stim = find_user(root, "Name", "IBR3_TRIAL__OPEN_STIMULUS")
    ibr3_packet = find_user(root, "Name", "IBR3_TRIAL__EVENT_PACKET")
    details["ibr2_test_enable_final"] = params(ibr2_enable).get("Value")
    details["ibr3_test_enable_final"] = params(ibr3_enable).get("Value")
    details["ibr2_open_time_s_final"] = params(ibr2_stim).get("OPEN_TIME_S")
    details["ibr2_cause_code_final"] = params(ibr2_packet).get("CAUSE_CODE_VALUE")
    details["ibr3_open_time_s_final"] = params(ibr3_stim).get("OPEN_TIME_S")
    details["ibr3_cause_code_final"] = params(ibr3_packet).get("CAUSE_CODE_VALUE")
    checks["trial_post_restore_integrity_status"] = status(
        params(ibr2_enable).get("Value") == "0"
        and params(ibr3_enable).get("Value") == "0"
        and params(ibr2_stim).get("OPEN_TIME_S") == "4.0"
        and params(ibr2_packet).get("CAUSE_CODE_VALUE") == "4"
        and params(ibr3_stim).get("OPEN_TIME_S") == "5.0"
        and params(ibr3_packet).get("CAUSE_CODE_VALUE") == "5"
    )
    checks["trial_pre_run_integrity_status"] = status(PRE_RUN_MANIFEST.exists())

    xml_text = TRIAL_PROJECT.read_text(encoding="utf-8", errors="ignore").upper()
    forbidden_tokens = ["MATLAB", "AUTORECLOSE", "AUTO_RECLOSE", "FOURTH_SOURCE", "VIRTUAL_SOURCE"]
    details["forbidden_token_hits"] = [token for token in forbidden_tokens if token in xml_text]
    checks["control_path_isolation_status"] = status(not details["forbidden_token_hits"])

    run_summary = json.loads(RUN_SUMMARY.read_text(encoding="utf-8"))
    run_comparison = json.loads(RUN_COMPARISON.read_text(encoding="utf-8"))
    run_checks = run_summary.get("checks", {})
    times = run_summary.get("event_times_s", {})
    selected = run_summary.get("selected_channel_summary", {})
    details["run_id"] = run_summary.get("run_id")
    details["run_dynamic_status"] = run_summary.get("dynamic_run_status")
    details["controlled_three_event_order_status"] = run_summary.get("controlled_three_event_order_status")
    details["comparison_status"] = run_comparison.get("three_source_controlled_chronology_comparison_status")

    checks["build_before_run_status"] = status(run_summary.get("build_error_count") == 0)
    checks["run_completion_status"] = status(run_summary.get("parser_status") == "parsed")
    checks["output_parser_status"] = status(run_summary.get("missing_channel_list") == [])
    checks["source_a_dynamic_status"] = status(run_checks.get("source_a_dynamic_status") == "PASS")
    checks["source_b_dynamic_status"] = status(run_checks.get("source_b_dynamic_status") == "PASS")
    checks["source_c_dynamic_status"] = status(run_checks.get("source_c_dynamic_status") == "PASS")
    checks["three_source_collector_dynamic_status"] = status(run_checks.get("three_source_collector_dynamic_status") == "PASS")
    checks["three_event_chronology_dynamic_status"] = status(run_checks.get("three_event_chronology_dynamic_status") == "PASS")
    checks["default_dfig_signature_status"] = status(run_checks.get("default_dfig_signature_status") == "PASS")
    checks["controlled_three_event_order_status"] = status(
        run_summary.get("controlled_three_event_order_status") == "pass"
        and approx(times.get("source_a_first_event_time_last"), 2.01603)
        and approx(times.get("source_b_first_event_time_last"), 4.000005)
        and approx(times.get("source_c_first_event_time_last"), 5.0)
        and approx(times.get("cascade3_first_to_second_gap_last"), 1.983975)
        and approx(times.get("cascade3_second_to_third_gap_last"), 0.999995)
        and selected.get("CASCADE3_MONITOR_EVENTED_SOURCE_COUNT", {}).get("last") == 3.0
        and selected.get("CASCADE3_MONITOR_TIMED_EVENT_SOURCE_COUNT", {}).get("last") == 3.0
        and selected.get("CASCADE3_MONITOR_EVENT_ORDER_CLASS_CODE", {}).get("last") == 4.0
        and selected.get("CASCADE3_MONITOR_CHRONOLOGY_CONSISTENT", {}).get("last") == 1.0
    )

    checks["matlab_status"] = "pass"
    checks["final_audit_status"] = status(all(value == "pass" for value in checks.values()))

    FINAL_AUDIT.parent.mkdir(parents=True, exist_ok=True)
    FINAL_AUDIT.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2, ensure_ascii=False))
    return 0 if checks["final_audit_status"] == "pass" else 2


if __name__ == "__main__":
    sys.exit(main())
