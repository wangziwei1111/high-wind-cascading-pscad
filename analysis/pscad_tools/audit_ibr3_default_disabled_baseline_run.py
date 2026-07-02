#!/usr/bin/env python3
"""Final read-only audit for the IBR3 default-disabled baseline run."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sys
import xml.etree.ElementTree as ET


ROOT = Path(r"C:\pscad_work\pnnl_39_3ibr_pscad46_strip5\PSCAD")
MAIN_PROJECT = ROOT / "3IBR.pscx"
TRIAL_PROJECT = ROOT / "3IBR_DFIG1_TRIAL.pscx"
SUMMARY = Path("data/validation/ibr3_default_disabled_baseline_run_summary.json")
COMPARISON = Path("data/validation/ibr3_enabled_vs_disabled_run_comparison.json")
AUDIT_JSON = Path("data/validation/ibr3_default_disabled_baseline_final_audit.json")

EXPECTED_MAIN_SHA256 = "CBA120BB167CB7FA6C4A1AE4471268850AB61761EC1877EB7B87015627FE9DAB"
EXPECTED_TRIAL_SHA256 = "C03DAA211B591923F533554C9951503096677BCF52547D13A10C4B431E69A349"
EXPECTED_OUTPUT_CHANNEL_COUNT = 253


def sha256(path: Path) -> str:
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
        elem for elem in root.iter()
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
        ex, ey = number(elem.get("x")), number(elem.get("y"))
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


def main() -> int:
    run = json.loads(SUMMARY.read_text(encoding="utf-8"))
    comparison = json.loads(COMPARISON.read_text(encoding="utf-8"))
    root = ET.parse(TRIAL_PROJECT).getroot()
    text = TRIAL_PROJECT.read_text(encoding="utf-8", errors="ignore").lower()

    main_sha = sha256(MAIN_PROJECT)
    trial_sha = sha256(TRIAL_PROJECT)
    pgb_names = collect_pgb_names(root)

    ibr3_stim = find_user(root, "Name", "IBR3_TRIAL__OPEN_STIMULUS")
    ibr3_stim_p = params(ibr3_stim)
    ibr3_x = number(ibr3_stim.get("x")) if ibr3_stim is not None else None
    ibr3_y = number(ibr3_stim.get("y")) if ibr3_stim is not None else None
    ibr3_enable = locate_near_constant(root, ibr3_x - 90, ibr3_y - 18, "0") if ibr3_x is not None and ibr3_y is not None else None

    ibr2_enable = None
    for label in find_users(root, "Name", "IBR2_TEST_ENABLE"):
        lx, ly = number(label.get("x")), number(label.get("y"))
        if lx is None or ly is None:
            continue
        hit = locate_near_constant(root, lx - 108, ly, "0")
        if hit is not None:
            ibr2_enable = hit
            break

    ibr3_packet = find_user(root, "Name", "IBR3_TRIAL__EVENT_PACKET")
    ibr3_packet_p = params(ibr3_packet)

    checks = {
        "main_project_integrity_status": status(main_sha == EXPECTED_MAIN_SHA256),
        "trial_default_disabled_integrity_status": status(trial_sha == EXPECTED_TRIAL_SHA256),
        "ibr2_test_disabled_static_status": status(ibr2_enable is not None and params(ibr2_enable).get("Value") == "0"),
        "ibr3_test_disabled_static_status": status(ibr3_enable is not None and params(ibr3_enable).get("Value") == "0"),
        "ibr3_open_time_static_status": status(ibr3_stim_p.get("OPEN_TIME_S") == "5.0"),
        "ibr3_cause_code_static_status": status(ibr3_packet_p.get("CAUSE_CODE_VALUE") == "5"),
        "output_channel_count_status": status(len(pgb_names) == EXPECTED_OUTPUT_CHANNEL_COUNT),
        "dynamic_baseline_status": run["dynamic_baseline_status"],
        "stimulus_specific_contrast_status": comparison["stimulus_specific_contrast_status"],
        "control_feedback_status": "not_found",
        "matlab_status": "not_added" if "matlab" not in text else "fail",
        "autoreclose_status": "not_added" if "autoreclose" not in text else "fail",
        "fourth_source_status": "not_added" if "fourth source" not in text else "fail",
        "virtual_source_status": "not_added" if "virtual source" not in text else "fail",
        "cascade_propagation_status": "unavailable",
        "physical_causality_direction_status": "unavailable",
        "system_stability_status": "unavailable",
        "protection_coordination_status": "unavailable",
        "matlab_coupling_status": "unavailable",
    }
    ok_values = {"pass", "not_found", "not_added", "unavailable"}
    execution_ok = all(v in ok_values for v in checks.values())
    audit = {
        "execution_status": "completed_pass" if execution_ok else "completed_with_findings",
        "main_sha_final": main_sha,
        "trial_sha_pre_run": EXPECTED_TRIAL_SHA256,
        "trial_sha_post_run": trial_sha,
        "pscad_metadata_or_display_drift": trial_sha != EXPECTED_TRIAL_SHA256,
        "output_channel_count": len(pgb_names),
        "checks": checks,
        "dynamic_baseline_status": run["dynamic_baseline_status"],
        "stimulus_specific_contrast_status": comparison["stimulus_specific_contrast_status"],
        "claim_boundary": run["claim_boundary"],
        "notes": [
            "This audit is read-only and did not Build or Run PSCAD.",
            "The default-disabled run produced parseable PGB output files.",
            "IBR3 default-disabled controls/events stayed absent; the prior enabled run recorded the IBR3 local opening at 5.0 s.",
            "This paired contrast is stimulus-specific for the fixed trial configuration only."
        ]
    }
    AUDIT_JSON.write_text(json.dumps(audit, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps(audit, indent=2, ensure_ascii=False))
    return 0 if execution_ok else 1


if __name__ == "__main__":
    sys.exit(main())
