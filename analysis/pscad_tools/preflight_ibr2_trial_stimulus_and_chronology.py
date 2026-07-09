"""Read-only preflight for the IBR2 trial stimulus/chronology build.

This script parses existing PSCAD/XML and generated-text evidence only.  It
does not start PSCAD, build, run, or modify either project.
"""

from __future__ import annotations

import hashlib
import json
import re
import xml.etree.ElementTree as ET
from collections import Counter
from pathlib import Path

from audit_main_project_sha_delta import compare_xml


ROOT = Path(__file__).resolve().parents[2]
PSCAD = Path(r"C:\pscad_work\pnnl_39_3ibr_pscad46_strip5\PSCAD")
MAIN = PSCAD / "3IBR.pscx"
TRIAL = PSCAD / "3IBR_DFIG1_TRIAL.pscx"
P3F = PSCAD / "3IBR_DFIG1_TRIAL.gf46" / "P3.f"
P3DTA = P3F.with_suffix(".dta")
MAIN_BASELINE = Path(
    r"C:\pscad_work\backups\ibr2_trial_event_packet_dual_collector_20260630_120911\3IBR.pscx"
)
EXPECTED_TRIAL_SHA = "541091C47BE05729B60F0585657AE308277CB031CBBA07A6583F3D3A04FD1A36"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def parameters(element: ET.Element | None) -> dict[str, str]:
    if element is None:
        return {}
    return {
        item.get("name", ""): item.get("value", "")
        for item in element.findall(".//param")
    }


def users(root: ET.Element) -> list[ET.Element]:
    return list(root.iter("User"))


def by_id(items: list[ET.Element], component_id: str) -> ET.Element | None:
    return next((item for item in items if item.get("id") == component_id), None)


def label_hits(items: list[ET.Element], signal: str) -> list[ET.Element]:
    return [
        item
        for item in items
        if item.get("defn") == "master:datalabel"
        and parameters(item).get("Name") == signal
    ]


def locations(items: list[ET.Element], signal: str) -> list[dict[str, str | None]]:
    return [
        {
            "page": "P3",
            "component_id": item.get("id"),
            "x": item.get("x"),
            "y": item.get("y"),
        }
        for item in label_hits(items, signal)
    ]


def main() -> int:
    required_paths = [MAIN, TRIAL, P3F, P3DTA, MAIN_BASELINE]
    missing = [str(path) for path in required_paths if not path.exists()]
    if missing:
        print(json.dumps({
            "execution_status": "ibr2_trial_stimulus_and_chronology_preflight_failed",
            "missing_paths": missing,
        }, indent=2))
        return 2

    try:
        main_now = ET.parse(MAIN).getroot()
        main_base = ET.parse(MAIN_BASELINE).getroot()
        trial_root = ET.parse(TRIAL).getroot()
    except ET.ParseError as exc:
        print(json.dumps({
            "execution_status": "ibr2_trial_stimulus_and_chronology_preflight_failed",
            "xml_parse_error": str(exc),
        }, indent=2))
        return 2

    items = users(trial_root)
    p3f = P3F.read_text(encoding="utf-8", errors="replace")
    p3dta = P3DTA.read_text(encoding="utf-8", errors="replace")
    trial_xml = TRIAL.read_text(encoding="utf-8", errors="replace")

    main_diffs = compare_xml(main_base, main_now)
    main_classes = Counter(diff["classification"] for diff in main_diffs)
    main_ok = set(main_classes) <= {"nonfunctional_metadata_or_display_change"}

    breaker = next(
        (
            item for item in items
            if item.get("defn") == "master:breaker3"
            and parameters(item).get("NAME") == "BRK_IBR2_TRIAL"
        ),
        None,
    )
    breaker_params = parameters(breaker)
    expected_breaker = {
        "Ctrl": "0",
        "OPCUR": "1",
        "ENAB": "0",
        "ROFF": "1.0e6 [ohm]",
        "RON": "1.0e-3 [ohm]",
        "TDA": "0.0 [s]",
        "TDB": "0.0 [s]",
        "TDC": "0.0 [s]",
        "TDRA": "0.05 [s]",
        "TDRB": "0.05 [s]",
        "TDRC": "0.05 [s]",
        "SBRA": "IBR2_TRIAL_BRK_STATE",
    }
    breaker_edges = re.findall(r"// 9\s+(NT_8\([123]\))\s+(NT_16\([123]\))", p3dta)
    boundary_ok = (
        breaker is not None
        and all(breaker_params.get(key) == value for key, value in expected_breaker.items())
        and len(breaker_edges) == 3
        and by_id(items, "1220231535") is not None
    )

    boundary_signals = {
        signal: bool(label_hits(items, signal)) and signal in p3f
        for signal in (
            "IBR2_TRIAL_BRK_STATE",
            "IBR2_TRIAL_BRK_OPEN_BOOL",
            "IBR2_TRIAL_SOURCE_AVAILABLE",
        )
    }

    source1_checks = {
        "event_valid": "DFIG_LVRT_CASCADE_EVENT_VALID" in p3f,
        "cause_code": "DFIG_LVRT_CAS_CAUSE_CODE" in p3f,
        "breaker_open": "DFIG_LVRT_CASCADE_EVENT_BRK_OPEN" in p3f,
        "source_available": "DFIG_LVRT_CAS_SRC_AVAIL" in p3f,
        "first_event_time": "DFIG_LVRT_CAS_FIRST_TIME_S" in p3f,
    }
    source2_checks = {
        "breaker_open": "IBR2_CAS_BRK_OPEN = 1.0 * REAL(IBR2_TRIAL_BRK_OPEN_BOOL)" in p3f,
        "source_available": "IBR2_CAS_AVAIL = 1.0 * REAL(IBR2_TRIAL_SOURCE_AVAILABLE)" in p3f,
        "armed_observation": "IBR2_CAS_EVT_OBS = IBR2_CAS_BRK_OPEN * REAL(DFIG_LVRT_ARMED)" in p3f,
        "event_valid": "IBR2_CAS_EVT_VALID" in p3f,
        "cause_code": "IBR2_CAS_CAUSE = 4.0 * IBR2_CAS_EVT_VALID" in p3f,
        "first_event_time": "IBR2_CAS_FIRST_S = 1.0 * IBR2_CAS_TIME_MEM" in p3f,
    }
    compact_p3f = p3f.replace("\n     &", "")
    collector_checks = {
        "any_trip": "CASCADE_MONITOR_ANY_TRIP = LIMIT(0.0, 1.0, RT_31)" in p3f,
        "any_breaker_open": "CASCADE_MONITOR_ANY_BRK_OPEN = LIMIT(0.0, 1.0, RT_32)" in p3f,
        "available_count": "CASCADE_MONITOR_AVAIL_SRC_COUNT" in p3f,
        "evented_count": bool(re.search(
            r"CAS_COL_EVENTED_COUNT = \+ DFIG_LVRT_CASCADE_EVENT_VALID \+ IBR2_CAS\s*&?_?EVT_VALID",
            compact_p3f,
        )),
        "first_time": "CASCADE_MONITOR_FIRST_TIME_S" in p3f,
        "first_source": "CAS_COL_FIRST_SRC_CODE" in p3f,
        "per_source_causes": (
            "CAS_COL_CAUSE_IBR2 = 1.0 * IBR2_CAS_CAUSE" in p3f
            and "CASCADE_MONITOR_CAUSE_CODE_DFIG1 = 1.0 * DFIG_LVRT_CAS_CAUSE_CODE" in p3f
        ),
    }

    new_tokens = (
        "IBR2_TEST_ENABLE",
        "IBR2_TEST_OPEN_TIME_S",
        "IBR2_TEST_TIME_REACHED",
        "IBR2_TEST_ARMED",
        "IBR2_TEST_OPEN_REQ",
        "IBR2_TEST_CMD_LIMITED",
        "CAS_CHR_",
    )
    new_signals_absent = {token: token not in trial_xml for token in new_tokens}

    fixed_constant = by_id(items, "1466514077")
    command_label = by_id(items, "1340977026")
    command_gain = by_id(items, "1534597820")
    fixed_command_ok = (
        fixed_constant is not None
        and fixed_constant.get("defn") == "master:const"
        and parameters(fixed_constant).get("Value") == "0"
        and command_label is not None
        and parameters(command_label).get("Name") == "IBR2_TRIAL_BRK_CMD"
        and command_gain is not None
        and command_gain.get("defn") == "master:gain"
        and parameters(command_gain).get("G") == "1"
        and "IBR2_TRIAL_BRK_CMD = 0.0" in p3f
        and "BRK_IBR2_TRIAL = 1.0 * IBR2_TRIAL_BRK_CMD" in p3f
    )

    time_source = by_id(items, "1468401530")
    time_source_ok = (
        time_source is not None
        and time_source.get("defn") == "master:time-sig"
        and time_source.get("x") == "1962"
        and time_source.get("y") == "1476"
    )
    armed_locations = locations(items, "DFIG_LVRT_ARMED")
    chronology_inputs = {
        signal: locations(items, signal)
        for signal in (
            "DFIG_LVRT_CASCADE_EVENT_VALID",
            "DFIG_LVRT_CAS_FIRST_TIME_S",
            "IBR2_CAS_EVT_VALID",
            "IBR2_CAS_FIRST_S",
            "CAS_COL_EVENTED_COUNT",
            "CAS_COL_FIRST_SRC_CODE",
            "CASCADE_MONITOR_FIRST_TIME_S",
        )
    }
    inputs_locatable = all(chronology_inputs.values())

    forbidden_patterns = {
        "automatic_reclose": bool(re.search(r"AUTO[_ -]?RECLOSE|AUTORECLOSE", trial_xml, re.I)),
        "matlab_component": any("matlab" in (item.get("defn") or "").lower() for item in items),
        "third_cascade_source": bool(re.search(r"CAS_(?:COL_)?(?:S3|SOURCE_?3)|IBR3_CAS", trial_xml, re.I)),
        "virtual_cascade_source": bool(re.search(r"VIRTUAL_(?:CAS|SOURCE)|CAS_VIRTUAL", trial_xml, re.I)),
    }

    statuses = {
        "project_paths_distinct_status": "pass" if MAIN.resolve() != TRIAL.resolve() else "fail",
        "main_project_integrity_status": "pass" if main_ok else "fail",
        "trial_xml_parse_status": "pass",
        "generated_static_evidence_status": "pass",
        "ibr2_local_breaker_boundary_status": "pass" if boundary_ok else "fail",
        "ibr2_breaker_state_interface_status": "pass" if all(boundary_signals.values()) else "fail",
        "source1_event_packet_status": "pass" if all(source1_checks.values()) else "fail",
        "source2_event_packet_status": "pass" if all(source2_checks.values()) else "fail",
        "dual_source_collector_status": "pass" if all(collector_checks.values()) else "fail",
        "new_module_signals_absent_status": "pass" if all(new_signals_absent.values()) else "fail",
        "fixed_closed_command_source_status": "pass" if fixed_command_ok else "fail",
        "time_and_armed_location_status": "pass" if time_source_ok and armed_locations else "fail",
        "chronology_input_location_status": "pass" if inputs_locatable else "fail",
        "forbidden_structure_absence_status": "pass" if not any(forbidden_patterns.values()) else "fail",
        "trial_start_sha_status": "pass" if sha256(TRIAL) == EXPECTED_TRIAL_SHA else "fail",
    }
    passed = all(value == "pass" for value in statuses.values())
    result = {
        "execution_status": (
            "ibr2_trial_stimulus_and_chronology_preflight_passed"
            if passed
            else "ibr2_trial_stimulus_and_chronology_preflight_failed"
        ),
        "read_only": True,
        "projects": {
            "main": {"path": str(MAIN), "sha256": sha256(MAIN)},
            "trial": {"path": str(TRIAL), "sha256": sha256(TRIAL)},
            "main_baseline": {"path": str(MAIN_BASELINE), "sha256": sha256(MAIN_BASELINE)},
        },
        "main_difference_summary": {
            "count": len(main_diffs),
            "classes": dict(main_classes),
        },
        "actual_gui_mapping": {
            "page": "P3",
            "command_region": {
                "fixed_constant": {"id": "1466514077", "x": "756", "y": "1386", "value": "0"},
                "command_label": {"id": "1340977026", "x": "846", "y": "1386"},
                "breaker_gain": {"id": "1534597820", "x": "918", "y": "1386", "gain": "1"},
                "breaker": {"id": breaker.get("id") if breaker is not None else None, "x": breaker.get("x") if breaker is not None else None, "y": breaker.get("y") if breaker is not None else None},
            },
            "time_source": {"id": "1468401530", "x": "1962", "y": "1476", "defn": "master:time-sig"},
            "armed_labels": armed_locations,
            "chronology_inputs": chronology_inputs,
            "collector_public_to_internal": {
                "CASCADE_MONITOR_EVENTED_SOURCE_COUNT": "CAS_COL_EVENTED_COUNT",
                "CASCADE_MONITOR_FIRST_EVENT_SOURCE_CODE": "CAS_COL_FIRST_SRC_CODE",
                "CASCADE_MONITOR_FIRST_EVENT_TIME_S": "CASCADE_MONITOR_FIRST_TIME_S",
            },
        },
        "checks": {
            "breaker_state_signals": boundary_signals,
            "source1": source1_checks,
            "source2": source2_checks,
            "collector": collector_checks,
            "new_signals_absent": new_signals_absent,
            "forbidden_structures": forbidden_patterns,
        },
        "statuses": statuses,
    }
    print(json.dumps(result, indent=2))
    return 0 if passed else 2


if __name__ == "__main__":
    raise SystemExit(main())
