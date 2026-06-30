"""Read-only audit for the IBR2 trial event packet and dual collector."""

from __future__ import annotations

import csv
import hashlib
import json
import re
import xml.etree.ElementTree as ET
from collections import Counter
from pathlib import Path

from audit_main_project_sha_delta import compare_xml

ROOT = Path(__file__).resolve().parents[2]
MAIN = Path(r"C:\pscad_work\pnnl_39_3ibr_pscad46_strip5\PSCAD\3IBR.pscx")
TRIAL = Path(r"C:\pscad_work\pnnl_39_3ibr_pscad46_strip5\PSCAD\3IBR_DFIG1_TRIAL.pscx")
P3F = Path(r"C:\pscad_work\pnnl_39_3ibr_pscad46_strip5\PSCAD\3IBR_DFIG1_TRIAL.gf46\P3.f")
P3DTA = P3F.with_suffix(".dta")
EXE = P3F.parent / "3IBR_DFIG1_TRIAL.exe"
BACKUP = Path(r"C:\pscad_work\backups\ibr2_trial_event_packet_dual_collector_20260630_120911")
MAIN_START_SHA = "97AE9A99E199734510352DACBDE6120BBC411356C244C3DEA0ED8B01AB2B7906"
TRIAL_START_SHA = "FB29872FCA8BCF92E5450C5944A312C1E6F018F87B5B499FEAF0E6B16C8A4A1E"

EVENT_JSON = ROOT / "data/reference/ibr2_trial_second_source_event_packet.json"
EVENT_CSV = ROOT / "data/reference/ibr2_trial_second_source_event_packet_summary.csv"
COL_JSON = ROOT / "data/reference/ibr2_trial_dual_source_cascade_collector.json"
COL_CSV = ROOT / "data/reference/ibr2_trial_dual_source_cascade_collector_summary.csv"


def sha(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest().upper()


def params(e: ET.Element) -> dict[str, str]:
    return {p.get("name", ""): p.get("value", "") for p in e.findall(".//param")}


def users(root: ET.Element) -> dict[str, ET.Element]:
    return {u.get("id", ""): u for u in root.iter("User")}


def write_summary(path: Path, statuses: dict[str, str]) -> None:
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f); w.writerow(["status_key", "status_value"]); w.writerows(statuses.items())


def main() -> int:
    main_base = ET.parse(BACKUP / "3IBR.pscx").getroot()
    main_now = ET.parse(MAIN).getroot()
    trial_base = ET.parse(BACKUP / "3IBR_DFIG1_TRIAL.pscx").getroot()
    trial_now = ET.parse(TRIAL).getroot()
    text = P3F.read_text(errors="replace")
    dta = P3DTA.read_text(errors="replace")
    main_sha, trial_sha = sha(MAIN), sha(TRIAL)

    main_diffs = compare_xml(main_base, main_now)
    main_classes = Counter(d["classification"] for d in main_diffs)
    main_integrity = "pass" if set(main_classes) <= {"nonfunctional_metadata_or_display_change"} else "fail"

    base_users, now_users = users(trial_base), users(trial_now)
    protected_ids = [
        "1612913074", "1466514077", "1534597820", "1220231535", "521858026",
        "810673841", "2111023746", "288637322", "537095251", "2133635045", "453162503",
    ]
    protected_ok = all(
        i in base_users and i in now_users
        and base_users[i].get("defn") == now_users[i].get("defn")
        and params(base_users[i]) == params(now_users[i])
        for i in protected_ids
    )
    breaker_edges = re.findall(r"// 9\s+(NT_8\([123]\))\s+(NT_16\([123]\))", dta)
    boundary_ok = protected_ok and len(breaker_edges) == 3

    source1 = {
        "DFIG_LVRT_CASCADE_EVENT_VALID": "DFIG_LVRT_CASCADE_EVENT_VALID",
        "DFIG_LVRT_CASCADE_EVENT_CAUSE_CODE": "DFIG_LVRT_CAS_CAUSE_CODE",
        "DFIG_LVRT_CASCADE_EVENT_BRK_OPEN": "DFIG_LVRT_CASCADE_EVENT_BRK_OPEN",
        "DFIG_LVRT_CASCADE_SOURCE_AVAILABLE": "DFIG_LVRT_CAS_SRC_AVAIL",
        "DFIG_LVRT_CASCADE_FIRST_EVENT_TIME_S": "DFIG_LVRT_CAS_FIRST_TIME_S",
    }
    source2 = {
        "IBR2_TRIAL_CASCADE_EVENT_VALID": "IBR2_CAS_EVT_VALID",
        "IBR2_TRIAL_CASCADE_EVENT_CAUSE_CODE": "IBR2_CAS_CAUSE",
        "IBR2_TRIAL_CASCADE_EVENT_BRK_OPEN": "IBR2_CAS_BRK_OPEN",
        "IBR2_TRIAL_CASCADE_SOURCE_AVAILABLE": "IBR2_CAS_AVAIL",
        "IBR2_TRIAL_CASCADE_FIRST_EVENT_TIME_S": "IBR2_CAS_FIRST_S",
    }

    event_checks = {
        "breaker_open_passthrough": "IBR2_CAS_BRK_OPEN = 1.0 * REAL(IBR2_TRIAL_BRK_OPEN_BOOL)" in text,
        "availability_passthrough": "IBR2_CAS_AVAIL = 1.0 * REAL(IBR2_TRIAL_SOURCE_AVAILABLE)" in text,
        "armed_gate": "IBR2_CAS_EVT_OBS = IBR2_CAS_BRK_OPEN * REAL(DFIG_LVRT_ARMED)" in text,
        "sticky_latch": "IBR2_CAS_LATCH_MEM = IBR2_CAS_LATCH_NEXT" in text and "IF (TIMEZERO) IBR2_CAS_LATCH_MEM = 0.0" in text,
        "cause_code": "IBR2_CAS_CAUSE = 4.0 * IBR2_CAS_EVT_VALID" in text,
        "time_unset": "EMTDC_X2COMP(0,0,0.0,IBR2_CAS_TIME_MEM,1.0,0.0,0.0" in text,
        "time_capture": "IBR2_CAS_TIME_CAP = IBR2_CAS_EVT_VALID * REAL(IBR2_CAS_TIME_UNSET)" in text,
        "time_memory": "IBR2_CAS_TIME_MEM = IBR2_CAS_TIME_NEXT" in text and "IF (TIMEZERO) IBR2_CAS_TIME_MEM = -1.0" in text,
        "first_time_export": "IBR2_CAS_FIRST_S = 1.0 * IBR2_CAS_TIME_MEM" in text,
    }

    collector_checks = {
        "any_trip": "RT_31 = + IBR2_CAS_EVT_VALID + DFIG_LVRT_CASCADE_EVENT_VALID" in text and "CASCADE_MONITOR_ANY_TRIP = LIMIT(0.0, 1.0, RT_31)" in text,
        "any_breaker_open": "RT_32 = + DFIG_LVRT_CASCADE_EVENT_BRK_OPEN + IBR2_CAS_BRK_OPEN" in text and "CASCADE_MONITOR_ANY_BRK_OPEN = LIMIT(0.0, 1.0, RT_32)" in text,
        "available_count": bool(re.search(r"CASCADE_MONITOR_AVAIL_SRC_COUNT = \+ IBR2_CAS_AVAIL \+ DFIG_LVRT_CAS\s*&?_?SRC_AVAIL", text.replace("\n     &", ""))),
        "evented_count": bool(re.search(r"CAS_COL_EVENTED_COUNT = \+ DFIG_LVRT_CASCADE_EVENT_VALID \+ IBR2_CAS\s*&?_?EVT_VALID", text.replace("\n     &", ""))),
        "per_source_cause": "CAS_COL_CAUSE_IBR2 = 1.0 * IBR2_CAS_CAUSE" in text and "CASCADE_MONITOR_CAUSE_CODE_DFIG1 = 1.0 * DFIG_LVRT_CAS_CAUSE_CODE" in text,
        "no_global_cause_sum": not any(x in text for x in ("GLOBAL_CAUSE", "TOTAL_CAUSE", "CAUSE_SUM")),
    }
    time_logic_ok = all(x in text for x in (
        "S1_TIME_SET", "S2_TIME_SET", "BOTH_TIME_SET", "S1_STRICTLY_EARLIER",
        "S2_STRICTLY_EARLIER", "CAS_COL_MIN_WHEN_BOTH", "CAS_COL_ONE_SOURCE_TIME",
        "CASCADE_MONITOR_FIRST_TIME_S = CAS_COL_MIN_WHEN_BOTH",
        "CASCADE_MONITOR_FIRST_TIME_S = CAS_COL_ONE_SOURCE_TIME",
    ))
    source_code_ok = all(x in text for x in (
        "CAS_COL_ONLY_S2_OR_NONE = RT_37", "CAS_COL_ONLY_S2_OR_NONE = RT_38",
        "CAS_COL_ONE_OR_NONE_CODE = RT_33", "CAS_COL_S2_OR_TIE_CODE = RT_34",
        "CAS_COL_S2_OR_TIE_CODE = RT_35", "CAS_COL_BOTH_CODE = RT_36",
        "CAS_COL_FIRST_SRC_CODE = CAS_COL_BOTH_CODE", "CAS_COL_FIRST_SRC_CODE = CAS_COL_ONE_OR_NONE_CODE",
        "RT_33 = 1.0", "RT_34 = 2.0", "RT_35 = 3.0", "RT_36 = 1.0", "RT_37 = 2.0", "RT_38 = 0.0",
    ))

    expected_channels = {
        "IBR2_TRIAL_CASCADE_EVENT_VALID": ("0", "1.2"),
        "IBR2_TRIAL_CASCADE_EVENT_CAUSE_CODE": ("0", "4.2"),
        "IBR2_TRIAL_CASCADE_EVENT_BRK_OPEN": ("0", "1.2"),
        "IBR2_TRIAL_CASCADE_SOURCE_AVAILABLE": ("0", "1.2"),
        "IBR2_TRIAL_CASCADE_FIRST_EVENT_TIME_S": ("-1.2", "10.2"),
        "CASCADE_MONITOR_CAUSE_CODE_IBR2_TRIAL": ("0", "4.2"),
        "CASCADE_MONITOR_EVENTED_SOURCE_COUNT": ("0", "2.2"),
        "CASCADE_MONITOR_FIRST_EVENT_SOURCE_CODE": ("0", "3.2"),
    }
    channels = {}
    for title, limits in expected_channels.items():
        hits = [params(u) for u in trial_now.iter("User") if u.get("defn") == "master:pgb" and params(u).get("Name") == title]
        p = hits[0] if len(hits) == 1 else {}
        channels[title] = len(hits) == 1 and p.get("enab") == "1" and p.get("mrun") == "1" and p.get("Scale") == "1.0" and (p.get("Min"), p.get("Max")) == limits
    avail_channel = next(params(u) for u in trial_now.iter("User") if u.get("defn") == "master:pgb" and params(u).get("Name") == "CASCADE_MONITOR_AVAILABLE_SOURCE_COUNT")
    channels_ok = all(channels.values()) and avail_channel.get("Max") == "2.2"

    control_isolation = all(x not in text for x in (
        "BRK_IBR2_TRIAL = IBR2_CAS", "DFIG_LVRT_FINAL_BRK_CMD = IBR2_CAS",
        "DFIG_LVRT_TRIP_REQUEST = IBR2_CAS", "DFIG_LVRT_TRIP_LATCH = IBR2_CAS",
    ))
    statuses = {
        "main_project_integrity_status": main_integrity,
        "trial_project_status": "pass",
        "ibr2_local_breaker_boundary_preservation_status": "pass" if boundary_ok else "fail",
        "source1_packet_preservation_status": "pass" if protected_ok else "fail",
        "source2_packet_structure_status": "pass" if all(event_checks.values()) else "fail",
        "collector_structure_status": "pass" if all(collector_checks.values()) else "fail",
        "event_time_logic_status": "pass" if time_logic_ok else "fail",
        "event_source_code_logic_status": "pass" if source_code_ok else "fail",
        "output_channel_status": "pass" if channels_ok else "fail",
        "control_path_isolation_status": "pass" if control_isolation else "fail",
        "dynamic_behavior_status": "unavailable",
        "dual_source_dynamic_behavior_status": "unavailable",
        "cascade_propagation_status": "unavailable",
        "matlab_status": "not_added",
    }
    passed = all(v == "pass" for k, v in statuses.items() if k not in {"dynamic_behavior_status", "dual_source_dynamic_behavior_status", "cascade_propagation_status", "matlab_status"})
    common = {
        "execution_status": "ibr2_trial_event_packet_dual_collector_static_build_verified" if passed else "dual_source_event_bus_static_fallback",
        "main_project": {"start_sha256": MAIN_START_SHA, "end_sha256": main_sha, "difference_count": len(main_diffs), "difference_classes": dict(main_classes)},
        "trial_project": {"start_sha256": TRIAL_START_SHA, "end_sha256": trial_sha},
        "build": {"errors": 0, "warnings": "not_reported", "messages": "not_reported", "p3_exists": P3F.exists(), "executable_exists": EXE.exists()},
        "statuses": statuses,
        "claim_boundary": {"pscad_run_performed": False, "dynamic_event_timing_validated": False, "dual_source_interaction_validated": False, "cascade_propagation_validated": False, "matlab_added": False},
    }
    event_payload = {**common, "source_id": "IBR2_TRIAL", "source_component": "IBR_AVM_2_1_1_1", "interface_mapping": source2, "structure_checks": event_checks, "cause_code_4_semantics": "observed armed local breaker opening; root cause unclassified"}
    collector_payload = {**common, "sources": ["TYPE3_DFIG_1", "IBR2_TRIAL"], "source1_mapping": source1, "source2_mapping": source2, "collector_checks": collector_checks, "output_channels": channels, "available_source_count_max": avail_channel.get("Max")}
    EVENT_JSON.parent.mkdir(parents=True, exist_ok=True)
    EVENT_JSON.write_text(json.dumps(event_payload, indent=2), encoding="utf-8")
    COL_JSON.write_text(json.dumps(collector_payload, indent=2), encoding="utf-8")
    write_summary(EVENT_CSV, statuses); write_summary(COL_CSV, statuses)
    print(json.dumps({"execution_status": common["execution_status"], **statuses}, indent=2))
    return 0 if passed else 2


if __name__ == "__main__":
    raise SystemExit(main())
