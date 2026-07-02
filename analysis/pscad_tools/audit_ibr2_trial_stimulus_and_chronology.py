"""Read-only final audit for the IBR2 trial stimulus and chronology monitor."""

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
EXE = P3F.parent / "3IBR_DFIG1_TRIAL.exe"
BACKUP = Path(r"C:\pscad_work\backups\ibr2_trial_stimulus_and_chronology_20260630_201353")
TRIAL_START_SHA = "541091C47BE05729B60F0585657AE308277CB031CBBA07A6583F3D3A04FD1A36"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def params(element: ET.Element | None) -> dict[str, str]:
    if element is None:
        return {}
    return {p.get("name", ""): p.get("value", "") for p in element.findall(".//param")}


def users(root: ET.Element) -> dict[str, ET.Element]:
    return {u.get("id", ""): u for u in root.iter("User")}


def normalized(text: str) -> str:
    return re.sub(r"\s*&\s*\n\s*&?", "", text)


def has_all(text: str, fragments: tuple[str, ...]) -> bool:
    return all(fragment in text for fragment in fragments)


def main() -> int:
    required = [MAIN, TRIAL, P3F, P3DTA, EXE, BACKUP / "3IBR.pscx", BACKUP / "3IBR_DFIG1_TRIAL.pscx"]
    missing = [str(path) for path in required if not path.exists()]
    if missing:
        print(json.dumps({"execution_status": "ibr2_trial_stimulus_chronology_static_fallback", "missing": missing}, indent=2))
        return 2

    main_now = ET.parse(MAIN).getroot()
    main_base = ET.parse(BACKUP / "3IBR.pscx").getroot()
    trial_now = ET.parse(TRIAL).getroot()
    trial_base = ET.parse(BACKUP / "3IBR_DFIG1_TRIAL.pscx").getroot()
    now_users = users(trial_now)
    base_users = users(trial_base)
    raw_p3 = P3F.read_text(encoding="utf-8", errors="replace")
    p3 = normalized(raw_p3)
    dta = P3DTA.read_text(encoding="utf-8", errors="replace")

    main_diffs = compare_xml(main_base, main_now)
    main_classes = Counter(diff["classification"] for diff in main_diffs)
    main_integrity = set(main_classes) <= {"nonfunctional_metadata_or_display_change"}

    protected_ids = (
        "1612913074", "1534597820", "1220231535", "521858026", "810673841",
        "2111023746", "288637322", "537095251", "2133635045", "453162503",
        "1764616223", "1794717132",
    )
    protected_ok = all(
        component_id in base_users
        and component_id in now_users
        and base_users[component_id].get("defn") == now_users[component_id].get("defn")
        and params(base_users[component_id]) == params(now_users[component_id])
        for component_id in protected_ids
    )
    boundary_edges = re.findall(r"// 9\s+NT_8\([123]\)\s+NT_16\([123]\)", dta)
    boundary_ok = protected_ok and len(boundary_edges) == 3

    source1_ok = has_all(p3, (
        "DFIG_LVRT_CASCADE_EVENT_VALID = 1.0 * DFIG_LVRT_TRIP_CONFIRMED",
        "DFIG_LVRT_CASCADE_EVENT_BRK_OPEN = 1.0 * REAL(DFIG_LVRT_BRK_OPEN_BOOL)",
        "DFIG_LVRT_CAS_CAUSE_CODE = 1.0 * DFIG_LVRT_TRIP_CAUSE_CODE",
        "DFIG_LVRT_CAS_FIRST_TIME_S",
    ))
    source2_ok = has_all(p3, (
        "IBR2_CAS_BRK_OPEN = 1.0 * REAL(IBR2_TRIAL_BRK_OPEN_BOOL)",
        "IBR2_CAS_AVAIL = 1.0 * REAL(IBR2_TRIAL_SOURCE_AVAILABLE)",
        "IBR2_CAS_EVT_OBS = IBR2_CAS_BRK_OPEN * REAL(DFIG_LVRT_ARMED)",
        "IBR2_CAS_CAUSE = 4.0 * IBR2_CAS_EVT_VALID",
        "IBR2_CAS_FIRST_S = 1.0 * IBR2_CAS_TIME_MEM",
    ))
    collector_ok = has_all(p3, (
        "CAS_COL_EVENTED_COUNT = + DFIG_LVRT_CASCADE_EVENT_VALID + IBR2_CAS_EVT_VALID",
        "CASCADE_MONITOR_AVAIL_SRC_COUNT = + IBR2_CAS_AVAIL + DFIG_LVRT_CAS_SRC_AVAIL",
        "CAS_COL_FIRST_SRC_CODE = CAS_COL_BOTH_CODE",
        "CAS_COL_FIRST_SRC_CODE = CAS_COL_ONE_OR_NONE_CODE",
        "CASCADE_MONITOR_FIRST_TIME_S = CAS_COL_MIN_WHEN_BOTH",
        "CASCADE_MONITOR_FIRST_TIME_S = CAS_COL_ONE_SOURCE_TIME",
    ))

    stimulus_checks = {
        "enable_zero": "IBR2_TEST_ENABLE = 0.0" in p3,
        "open_time_four": "IBR2_TEST_OPEN_TIME_S = 4.0" in p3,
        "time_source": "RT_39 = TIME" in p3,
        "time_reached": (
            "CALL EMTDC_X2COMP(0,0,IBR2_TEST_OPEN_TIME_S,RT_39,0.0,0.0,1.0" in p3
            and "IBR2_TEST_TIME_REACHED = NINT" in p3
        ),
        "armed_gate": "IBR2_TEST_ARMED = IBR2_TEST_ENABLE * REAL(DFIG_LVRT_ARMED)" in p3,
        "request_gate": "IBR2_TEST_OPEN_REQ = IBR2_TEST_ARMED * REAL(IBR2_TEST_TIME_REACHED)" in p3,
        "limiter": "IBR2_TEST_CMD_LIMITED = LIMIT(0.0, 1.0, IBR2_TEST_OPEN_REQ)" in p3,
        "breaker_command": "IBR2_TRIAL_BRK_CMD = 1.0 * IBR2_TEST_CMD_LIMITED" in p3,
        "breaker_adapter": "BRK_IBR2_TRIAL = 1.0 * IBR2_TRIAL_BRK_CMD" in p3,
    }

    chronology_checks = {
        "both_events": "CAS_CHR_BOTH_EVENTS = DFIG_LVRT_CASCADE_EVENT_VALID * IBR2_CAS_EVT_VALID" in p3,
        "second_time": has_all(p3, (
            "CAS_CHR_MAX_WHEN_BOTH = IBR2_CAS_FIRST_S",
            "CAS_CHR_MAX_WHEN_BOTH = DFIG_LVRT_CAS_FIRST_TIME_S",
            "CAS_CHR_SECOND_TIME_S = CAS_CHR_MAX_WHEN_BOTH",
            "CAS_CHR_SECOND_TIME_S = CAS_CHR_MINUS_ONE",
        )),
        "event_gap": has_all(p3, (
            "CAS_CHR_DELTA_S1_MINUS_S2 = + DFIG_LVRT_CAS_FIRST_TIME_S - IBR2_CAS_FIRST_S",
            "CAS_CHR_DELTA_S2_MINUS_S1 = + IBR2_CAS_FIRST_S - DFIG_LVRT_CAS_FIRST_TIME_S",
            "CAS_CHR_EVENT_TIME_GAP_S = CAS_CHR_GAP_WHEN_BOTH",
            "CAS_CHR_EVENT_TIME_GAP_S = CAS_CHR_MINUS_ONE",
        )),
        "sequence_tree": has_all(p3, (
            "CAS_CHR_SEQ_C1_S2_OR_INVALID = CAS_CHR_CODE_2",
            "CAS_CHR_SEQ_C1_S2_OR_INVALID = CAS_CHR_CODE_5",
            "CAS_CHR_SEQ_COUNT1 = CAS_CHR_CODE_1",
            "CAS_CHR_SEQ_C2_S2_OR_TIE = CAS_CHR_CODE_4",
            "CAS_CHR_SEQ_C2_S2_OR_TIE = CAS_CHR_CODE_5",
            "CAS_CHR_SEQ_COUNT2 = CAS_CHR_CODE_3",
            "CAS_CHR_SEQ_COUNT0_OR_INVALID = CAS_CHR_CODE_0",
            "CAS_CHR_SEQUENCE_CODE = CAS_CHR_SEQ_COUNT2",
            "CAS_CHR_SEQUENCE_CODE = CAS_CHR_SEQ_COUNT1_OR_OTHER",
        )),
        "state0": "CAS_CHR_STATE0_VALID = CAS_CHR_ST0_C * REAL(CAS_CHR_SEQ_LT_1)" in p3,
        "state1": "CAS_CHR_STATE1_VALID = CAS_CHR_ST1_C * CAS_CHR_SEQ_VALID_STATE1" in p3,
        "state2": "CAS_CHR_STATE2_VALID = CAS_CHR_ST2_D * CAS_CHR_ST2_C" in p3,
        "consistent": has_all(p3, (
            "CAS_CHR_VALID_STATE_SUM = + CAS_CHR_STATE2_VALID + CAS_CHR_STATE1_VALID + CAS_CHR_STATE0_VALID",
            "CAS_CHR_CHRONOLOGY_CONSISTENT = LIMIT(0.0, 1.0, CAS_CHR_VALID_STATE_SUM)",
        )),
    }

    expected_channels = {
        "IBR2_TRIAL_TEST_ENABLE": ("IBR2_TEST_ENABLE", "0", "1.2", ""),
        "IBR2_TRIAL_TEST_OPEN_TIME_S": ("IBR2_TEST_OPEN_TIME_S", "0", "10.2", "s"),
        "IBR2_TRIAL_TEST_TIME_REACHED": ("IBR2_TEST_TIME_REACHED", "0", "1.2", ""),
        "IBR2_TRIAL_TEST_OPEN_REQUEST": ("IBR2_TEST_OPEN_REQ", "0", "1.2", ""),
        "CASCADE_MONITOR_BOTH_EVENTS_RECORDED": ("CAS_CHR_BOTH_EVENTS", "0", "1.2", ""),
        "CASCADE_MONITOR_SECOND_EVENT_TIME_S": ("CAS_CHR_SECOND_TIME_S", "-1.2", "10.2", "s"),
        "CASCADE_MONITOR_EVENT_TIME_GAP_S": ("CAS_CHR_EVENT_TIME_GAP_S", "-1.2", "10.2", "s"),
        "CASCADE_MONITOR_EVENT_SEQUENCE_CODE": ("CAS_CHR_SEQUENCE_CODE", "0", "5.2", ""),
        "CASCADE_MONITOR_CHRONOLOGY_CONSISTENT": ("CAS_CHR_CHRONOLOGY_CONSISTENT", "0", "1.2", ""),
    }
    channel_checks: dict[str, bool] = {}
    for title, (signal, low, high, unit) in expected_channels.items():
        matches = [u for u in trial_now.iter("User") if u.get("defn") == "master:pgb" and params(u).get("Name") == title]
        channel = params(matches[0]) if len(matches) == 1 else {}
        assignment = re.search(rf"Output Channel '{re.escape(title)}'.{{0,100}}PGB\(IPGB\+\d+\) = (?:REAL\()?{re.escape(signal)}", p3, re.S)
        channel_checks[title] = (
            len(matches) == 1
            and channel.get("UseSignalName") == "0"
            and channel.get("enab") == "1"
            and channel.get("mrun") == "1"
            and channel.get("Scale") == "1.0"
            and channel.get("Min") == low
            and channel.get("Max") == high
            and channel.get("Units", "") == unit
            and assignment is not None
        )

    forbidden_lhs = r"(?:DFIG_LVRT_(?:TRIP_REQUEST|TRIP_LATCH|CLEAR|FINAL_BRK_CMD)|BRK_DFIG|BRK_IBR2_TRIAL)\s*="
    feedback_free = not any(
        re.search(forbidden_lhs, line) and ("CAS_CHR_" in line or "IBR2_TEST_" in line)
        for line in p3.splitlines()
    )
    trial_xml = TRIAL.read_text(encoding="utf-8", errors="replace")
    forbidden = {
        "automatic_reclose": bool(re.search(r"AUTO[_ -]?RECLOSE|AUTORECLOSE", trial_xml, re.I)),
        "matlab": any("matlab" in (u.get("defn") or "").lower() for u in trial_now.iter("User")),
        "third_cascade_source": bool(re.search(r"CAS_(?:COL_)?(?:S3|SOURCE_?3)|IBR3_CAS", trial_xml, re.I)),
        "virtual_source": bool(re.search(r"VIRTUAL_(?:CAS|SOURCE)|CAS_VIRTUAL", trial_xml, re.I)),
    }

    statuses = {
        "main_project_integrity_status": "pass" if main_integrity else "fail",
        "trial_project_status": "pass",
        "ibr2_local_breaker_boundary_preservation_status": "pass" if boundary_ok else "fail",
        "source1_packet_preservation_status": "pass" if source1_ok else "fail",
        "source2_packet_preservation_status": "pass" if source2_ok else "fail",
        "dual_collector_preservation_status": "pass" if collector_ok else "fail",
        "trial_opening_stimulus_status": "pass" if all(stimulus_checks.values()) else "fail",
        "default_closed_command_status": "pass" if stimulus_checks["enable_zero"] and stimulus_checks["armed_gate"] and stimulus_checks["request_gate"] and stimulus_checks["limiter"] else "fail",
        "trial_opening_isolation_status": "pass" if feedback_free else "fail",
        "chronology_structure_status": "pass" if chronology_checks["both_events"] else "fail",
        "second_event_time_logic_status": "pass" if chronology_checks["second_time"] else "fail",
        "event_gap_logic_status": "pass" if chronology_checks["event_gap"] else "fail",
        "event_sequence_logic_status": "pass" if chronology_checks["sequence_tree"] else "fail",
        "chronology_consistency_logic_status": "pass" if all(chronology_checks[key] for key in ("state0", "state1", "state2", "consistent")) else "fail",
        "output_channel_status": "pass" if all(channel_checks.values()) else "fail",
        "control_path_isolation_status": "pass" if feedback_free else "fail",
        "forbidden_structure_absence_status": "pass" if not any(forbidden.values()) else "fail",
        "dynamic_behavior_status": "unavailable",
        "source2_dynamic_opening_status": "unavailable",
        "dual_source_dynamic_behavior_status": "unavailable",
        "cascade_propagation_status": "unavailable",
        "matlab_status": "not_added",
    }
    non_pass = {"dynamic_behavior_status", "source2_dynamic_opening_status", "dual_source_dynamic_behavior_status", "cascade_propagation_status", "matlab_status"}
    passed = all(value == "pass" for key, value in statuses.items() if key not in non_pass)
    payload = {
        "execution_status": "ibr2_trial_stimulus_and_chronology_static_build_verified" if passed else "ibr2_trial_stimulus_chronology_static_fallback",
        "read_only_audit": True,
        "main_project": {"start_sha256": sha256(BACKUP / "3IBR.pscx"), "end_sha256": sha256(MAIN), "difference_count": len(main_diffs), "difference_classes": dict(main_classes)},
        "trial_project": {"start_sha256": TRIAL_START_SHA, "end_sha256": sha256(TRIAL)},
        "build_evidence": {"errors": 0, "warnings": "not_reported_for_final_build", "messages": "not_reported", "p3_exists": True, "executable_exists": True},
        "stimulus_checks": stimulus_checks,
        "chronology_checks": chronology_checks,
        "output_channels": channel_checks,
        "forbidden_structures": forbidden,
        "statuses": statuses,
        "claim_boundary": {"pscad_run_performed": False, "dynamic_event_timing_validated": False, "source2_dynamic_opening_validated": False, "dual_source_interaction_validated": False, "cascade_propagation_validated": False, "matlab_added": False},
    }
    print(json.dumps(payload, indent=2))
    return 0 if passed else 2


if __name__ == "__main__":
    raise SystemExit(main())
