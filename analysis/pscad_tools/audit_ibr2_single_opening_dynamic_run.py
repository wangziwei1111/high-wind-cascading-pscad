#!/usr/bin/env python3
"""Final audit for the IBR2 trial single-opening dynamic validation.

This audit is intentionally split into two evidence sources:

1. The already-parsed dynamic run artifacts in data/validation.
2. The restored PSCAD trial project currently on disk.

The PSCAD build step may clean the transient .gf46 output directory after the
run is parsed, so this audit does not require raw .out files to still exist.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sys
import xml.etree.ElementTree as ET


PSCAD_ROOT = Path(r"C:\pscad_work\pnnl_39_3ibr_pscad46_strip5\PSCAD")
MAIN_PROJECT = PSCAD_ROOT / "3IBR.pscx"
TRIAL_PROJECT = PSCAD_ROOT / "3IBR_DFIG1_TRIAL.pscx"

RUN_SUMMARY = Path("data/validation/ibr2_trial_single_opening_run_summary.json")
RUN_COMPARISON = Path("data/validation/ibr2_enabled_vs_default_disabled_run_comparison.json")
PRE_RUN_MANIFEST = Path("data/validation/ibr2_single_opening_pre_run_manifest.json")
FINAL_AUDIT = Path("data/validation/ibr2_trial_single_opening_final_audit.json")

EXPECTED_MAIN_SHA256 = "CBA120BB167CB7FA6C4A1AE4471268850AB61761EC1877EB7B87015627FE9DAB"
EXPECTED_OUTPUT_CHANNEL_COUNT = 253


def sha256(path: Path) -> str | None:
    if not path.exists():
        return None
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest().upper()


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


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
        "audit_id": "IBR2_TRIAL_SINGLE_OPENING_FINAL_AUDIT",
        "claim_boundary": (
            "This audit supports only the approved IBR2_TRIAL source-B trial-only "
            "local-opening validation in the fixed trial model. It does not validate "
            "natural DFIG-to-IBR2 cascade propagation, physical causality direction, "
            "system stability, protection coordination, MATLAB coupling, or general applicability."
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
        "unsupported_claims": {
            "natural_dfig_to_ibr2_cascade_validation": "not_claimed",
            "physical_causality_direction": "not_claimed",
            "system_stability": "not_claimed",
            "protection_coordination": "not_claimed",
            "matlab_coupling": "not_claimed",
            "general_applicability": "not_claimed",
        },
    }
    checks: dict[str, str] = report["checks"]  # type: ignore[assignment]
    details: dict[str, object] = report["details"]  # type: ignore[assignment]

    main_sha = sha256(MAIN_PROJECT)
    trial_sha = sha256(TRIAL_PROJECT)
    details["main_sha_final"] = main_sha
    details["trial_sha_final_restored_build"] = trial_sha
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
    checks["output_channel_count_restored_status"] = status(len(pgb_names) == EXPECTED_OUTPUT_CHANNEL_COUNT)

    ibr2_enable = find_labeled_constant(root, "IBR2_TEST_ENABLE")
    ibr3_enable = find_labeled_constant(root, "IBR3_TEST_ENABLE")
    details["ibr2_test_enable_final"] = params(ibr2_enable).get("Value")
    details["ibr3_test_enable_final"] = params(ibr3_enable).get("Value")
    checks["test_enable_restored_default_status"] = status(
        params(ibr2_enable).get("Value") == "0" and params(ibr3_enable).get("Value") == "0"
    )

    ibr2_stim = find_user(root, "Name", "MODTEST_ONE_SHOT_STIMULUS")
    ibr2_packet = find_user(root, "Name", "MODTEST_OBJECT_EVENT_PACKET")
    ibr3_stim = find_user(root, "Name", "IBR3_TRIAL__OPEN_STIMULUS")
    ibr3_packet = find_user(root, "Name", "IBR3_TRIAL__EVENT_PACKET")
    details["ibr2_open_time_s_final"] = params(ibr2_stim).get("OPEN_TIME_S")
    details["ibr2_cause_code_final"] = params(ibr2_packet).get("CAUSE_CODE_VALUE")
    details["ibr3_open_time_s_final"] = params(ibr3_stim).get("OPEN_TIME_S")
    details["ibr3_cause_code_final"] = params(ibr3_packet).get("CAUSE_CODE_VALUE")
    checks["trial_configuration_restored_status"] = status(
        params(ibr2_stim).get("OPEN_TIME_S") == "4.0"
        and params(ibr2_packet).get("CAUSE_CODE_VALUE") == "4"
        and params(ibr3_stim).get("OPEN_TIME_S") == "5.0"
        and params(ibr3_packet).get("CAUSE_CODE_VALUE") == "5"
    )

    xml_text = TRIAL_PROJECT.read_text(encoding="utf-8", errors="ignore")
    forbidden_tokens = ["AUTORECLOSE", "AUTO_RECLOSE", "MATLAB", "FOURTH_SOURCE", "VIRTUAL_SOURCE"]
    details["forbidden_token_hits"] = [token for token in forbidden_tokens if token in xml_text.upper()]
    checks["no_disallowed_scope_expansion_status"] = status(not details["forbidden_token_hits"])

    run_summary = read_json(RUN_SUMMARY)
    run_comparison = read_json(RUN_COMPARISON)
    details["run_id"] = run_summary.get("run_id")
    details["run_dynamic_status"] = run_summary.get("dynamic_run_status")
    details["run_checks"] = run_summary.get("checks")
    details["comparison_status"] = run_comparison.get("ibr2_enabled_vs_default_disabled_status")

    run_checks = run_summary.get("checks", {})
    event_times = run_summary.get("event_times_s", {})
    selected = run_summary.get("selected_channel_summary", {})
    checks["dynamic_run_summary_status"] = status(run_summary.get("dynamic_run_status") == "pass")
    checks["ibr2_source_b_chain_dynamic_status"] = status(
        run_checks.get("ibr2_test_enable_dynamic_status") == "PASS"
        and run_checks.get("ibr2_stimulus_request_status") == "PASS"
        and run_checks.get("ibr2_breaker_command_status") == "PASS"
        and run_checks.get("ibr2_actual_open_status") == "PASS"
        and run_checks.get("ibr2_state_adapter_dynamic_status") == "PASS"
        and run_checks.get("source_b_event_packet_dynamic_status") == "PASS"
        and approx(event_times.get("ibr2_open_request_first_ge_0p5"), 4.0)
        and approx(event_times.get("source_b_first_event_time_last"), 4.000005)
        and selected.get("IBR2_TRIAL_CASCADE_EVENT_CAUSE_CODE", {}).get("last") == 4.0
    )
    checks["ibr3_default_disabled_isolation_status"] = status(
        run_checks.get("ibr3_default_disabled_isolation_status") == "PASS"
        and selected.get("IBR3_TRIAL_TEST_ENABLE", {}).get("max") == 0.0
        and selected.get("IBR3_TRIAL_TEST_OPEN_REQUEST", {}).get("max") == 0.0
        and selected.get("IBR3_TRIAL_CASCADE_EVENT_VALID", {}).get("max") == 0.0
    )
    checks["collector_and_chronology_dynamic_status"] = status(
        run_checks.get("three_source_collector_dynamic_status") == "PASS"
        and run_checks.get("three_event_chronology_dynamic_status") == "PASS"
        and approx(event_times.get("cascade3_first_event_time_last"), 2.01603)
        and approx(event_times.get("cascade3_second_event_time_last"), 4.000005)
        and event_times.get("cascade3_third_event_time_last") == -1.0
        and selected.get("CASCADE3_MONITOR_CAUSE_CODE_IBR2_TRIAL", {}).get("last") == 4.0
    )
    checks["baseline_contrast_status"] = status(
        run_comparison.get("ibr2_enabled_vs_default_disabled_status") == "pass"
    )

    checks["final_audit_status"] = status(all(value == "pass" for value in checks.values()))

    FINAL_AUDIT.parent.mkdir(parents=True, exist_ok=True)
    FINAL_AUDIT.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2, ensure_ascii=False))
    return 0 if checks["final_audit_status"] == "pass" else 2


if __name__ == "__main__":
    sys.exit(main())
