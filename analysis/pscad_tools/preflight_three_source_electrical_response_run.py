"""Read-only preflight for the single three-source electrical response Run.

No PSCAD GUI automation, Build, Run, or .pscx mutation is performed here.
The script checks that the trial project is ready for one manual controlled
Run and writes a pre-run manifest used by the parser/auditor.
"""

from __future__ import annotations

import hashlib
import json
import re
import shutil
import xml.etree.ElementTree as ET
from datetime import datetime, timezone, timedelta
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
PSCAD = Path(r"C:\pscad_work\pnnl_39_3ibr_pscad46_strip5\PSCAD")
MAIN = PSCAD / "3IBR.pscx"
TRIAL = PSCAD / "3IBR_DFIG1_TRIAL.pscx"
GF46 = PSCAD / "3IBR_DFIG1_TRIAL.gf46"
P3F = GF46 / "P3.f"

EXPECTED_MAIN_SHA = "CBA120BB167CB7FA6C4A1AE4471268850AB61761EC1877EB7B87015627FE9DAB"
EXPECTED_OUTPUT_CHANNEL_COUNT = 262
EXPECTED_NPGB = 115

ELECTRICAL_CHANNELS = {
    "CASCADE3_ELEC_DFIG_V": "VIBR1_2",
    "CASCADE3_ELEC_DFIG_P": "PIBR1_2",
    "CASCADE3_ELEC_DFIG_Q": "QIBR1_2",
    "CASCADE3_ELEC_IBR2_V": "VIBR2",
    "CASCADE3_ELEC_IBR2_P": "PIBR2",
    "CASCADE3_ELEC_IBR2_Q": "QIBR2",
    "CASCADE3_ELEC_IBR3_V": "VIBR3",
    "CASCADE3_ELEC_IBR3_P": "PIBR3",
    "CASCADE3_ELEC_IBR3_Q": "QIBR3",
}

EVENT_CHANNELS = [
    "DFIG_LVRT_CASCADE_EVENT_VALID",
    "DFIG_LVRT_CASCADE_EVENT_CAUSE_CODE",
    "DFIG_LVRT_CASCADE_FIRST_EVENT_TIME_S",
    "IBR2_TRIAL_TEST_ENABLE",
    "IBR2_TRIAL_TEST_OPEN_TIME_S",
    "IBR2_TRIAL_TEST_OPEN_REQUEST",
    "IBR2_TRIAL_BRK_CMD",
    "IBR2_TRIAL_BRK_STATE",
    "IBR2_TRIAL_BRK_OPEN_BOOL",
    "IBR2_TRIAL_SOURCE_AVAILABLE",
    "IBR2_TRIAL_CASCADE_EVENT_VALID",
    "IBR2_TRIAL_CASCADE_EVENT_CAUSE_CODE",
    "IBR2_TRIAL_CASCADE_FIRST_EVENT_TIME_S",
    "IBR3_TRIAL_TEST_ENABLE",
    "IBR3_TRIAL_TEST_OPEN_TIME_S",
    "IBR3_TRIAL_TEST_OPEN_REQUEST",
    "IBR3_TRIAL_BRK_CMD",
    "IBR3_TRIAL_BRK_STATE",
    "IBR3_TRIAL_BRK_OPEN_BOOL",
    "IBR3_TRIAL_SOURCE_AVAILABLE",
    "IBR3_TRIAL_CASCADE_EVENT_VALID",
    "IBR3_TRIAL_CASCADE_EVENT_CAUSE_CODE",
    "IBR3_TRIAL_CASCADE_FIRST_EVENT_TIME_S",
]

CHRONOLOGY_CHANNELS = [
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


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def params(element: ET.Element) -> dict[str, str]:
    return {p.get("name", ""): p.get("value", "") for p in element.findall("./paramlist/param")}


def output_channels(root: ET.Element) -> list[dict[str, str]]:
    rows = []
    for user in root.iter("User"):
        if user.get("defn") != "master:pgb":
            continue
        p = params(user)
        rows.append(
            {
                "name": p.get("Name", ""),
                "id": user.get("id", ""),
                "x": user.get("x", ""),
                "y": user.get("y", ""),
                "scale": p.get("Scale", ""),
                "units": p.get("Units", ""),
                "min": p.get("Min", ""),
                "max": p.get("Max", ""),
                "transfer_data": p.get("enab", ""),
                "multiple_run_save": p.get("mrun", ""),
                "use_signal_name": p.get("UseSignalName", ""),
            }
        )
    return rows


def parse_pgb_assignments(p3f: str) -> dict[str, str]:
    mapping = {}
    current = None
    for line in p3f.splitlines():
        m = re.search(r"Output Channel '([^']+)'", line)
        if m:
            current = m.group(1)
            continue
        m = re.search(r"PGB\(IPGB\+\d+\)\s*=\s*(.+)", line)
        if m and current:
            mapping[current] = m.group(1).strip()
            current = None
    return mapping


def p3_definition(root: ET.Element) -> ET.Element:
    for definition in root.iter("Definition"):
        if definition.get("name") == "P3":
            return definition
    raise RuntimeError("P3 definition not found")


def find_users_by_param(definition: ET.Element, param_name: str, param_value: str) -> list[dict[str, object]]:
    rows = []
    for user in definition.findall("./schematic/User"):
        p = params(user)
        if p.get(param_name) == param_value:
            rows.append({"id": user.get("id"), "defn": user.get("defn"), "x": user.get("x"), "y": user.get("y"), "params": p})
    return rows


def find_constant(definition: ET.Element, component_id: str) -> dict[str, object] | None:
    for user in definition.findall("./schematic/User"):
        if user.get("id") == component_id:
            return {"id": user.get("id"), "defn": user.get("defn"), "x": user.get("x"), "y": user.get("y"), "params": params(user)}
    return None


def main() -> int:
    out_dir = ROOT / "data" / "validation"
    out_dir.mkdir(parents=True, exist_ok=True)
    now = datetime.now(timezone(timedelta(hours=8)))
    run_id_seed = f"three_source_electrical_response_{now.strftime('%Y%m%d_%H%M%S')}"

    missing = [str(path) for path in (MAIN, TRIAL, P3F) if not path.exists()]
    result: dict[str, object] = {
        "schema_version": 1,
        "execution_status": "three_source_electrical_response_preflight_started",
        "run_id_seed": run_id_seed,
        "preflight_timestamp": now.isoformat(timespec="seconds"),
        "read_only": True,
        "missing_paths": missing,
    }
    if missing:
        result["execution_status"] = "three_source_electrical_response_preflight_fallback"
        (out_dir / "three_source_electrical_response_pre_run_manifest.json").write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
        return 2

    root = ET.parse(TRIAL).getroot()
    p3 = p3_definition(root)
    p3f = P3F.read_text(encoding="utf-8", errors="replace")
    pgb_map = parse_pgb_assignments(p3f)
    channels = output_channels(root)
    by_name = {row["name"]: row for row in channels}
    main_sha = sha256(MAIN)
    trial_sha = sha256(TRIAL)

    simulation_end_time_s = float(next(p.get("value") for p in root.findall("./paramlist/param") if p.get("name") == "time_duration"))
    sample_step_us = float(next(p.get("value") for p in root.findall("./paramlist/param") if p.get("name") == "sample_step"))
    channel_plot_step_s = sample_step_us * 1e-6

    electrical_ok = all(
        name in by_name
        and pgb_map.get(name) == signal
        and by_name[name]["scale"] == "1.0"
        and by_name[name]["transfer_data"] == "1"
        for name, signal in ELECTRICAL_CHANNELS.items()
    )
    event_missing = [name for name in EVENT_CHANNELS if name not in by_name]
    chronology_missing = [name for name in CHRONOLOGY_CHANNELS if name not in by_name]

    ibr2_enable_const = find_constant(p3, "1778759091")
    ibr2_open_time_const = find_constant(p3, "939314032")
    ibr3_enable_const = find_constant(p3, "444774384")
    ibr3_time_const = find_constant(p3, "674606924")
    ibr3_stimulus = find_users_by_param(p3, "Name", "IBR3_TRIAL__OPEN_STIMULUS")

    ibr2_enable_value = float(ibr2_enable_const["params"]["Value"]) if ibr2_enable_const else None
    ibr2_time_value = float(ibr2_open_time_const["params"]["Value"]) if ibr2_open_time_const else None
    ibr3_enable_value = float(ibr3_enable_const["params"]["Value"]) if ibr3_enable_const else None
    ibr3_time_value = float(ibr3_stimulus[0]["params"]["OPEN_TIME_S"]) if len(ibr3_stimulus) == 1 else None
    ibr3_time_constant_value = float(ibr3_time_const["params"]["Value"]) if ibr3_time_const else None

    event_packets = find_users_by_param(p3, "Name", "IBR3_TRIAL__EVENT_PACKET")
    ibr3_cause_value = float(event_packets[0]["params"]["CAUSE_CODE_VALUE"]) if len(event_packets) == 1 else None

    p3f_checks = {
        "ibr2_enable_default_fortran": bool(re.search(r"\bIBR2_TEST_ENABLE\s*=\s*0\.0\b", p3f)),
        "ibr3_enable_default_fortran": bool(re.search(r"\bIBR3_TEST_ENABLE\s*=\s*0\.0\b", p3f)),
        "ibr2_open_time_fortran": bool(re.search(r"\bIBR2_TEST_OPEN_TIME_S\s*=\s*4\.0\b", p3f)),
        "ibr3_open_time_fortran": bool(re.search(r"\bIBR3_TEST_OPEN_TIME_S\s*=\s*5\.0\b", p3f)),
        "ibr2_cause_fortran": bool(re.search(r"\bIBR2_CAS_CAUSE\s*=\s*4\.0\s*\*\s*IBR2_CAS_EVT_VALID\b", p3f)),
        "ibr3_cause_module_parameter": ibr3_cause_value == 5.0,
    }

    forbidden = {
        "matlab": "matlab" in TRIAL.read_text(encoding="utf-8-sig", errors="replace").lower(),
        "automatic_reclose": bool(re.search(r"AUTO[_ -]?RECLOSE|AUTORECLOSE", TRIAL.read_text(encoding="utf-8-sig", errors="replace"), re.I)),
        "fourth_source": bool(re.search(r"SOURCE[_ -]?4|SRC[_ -]?4|IBR4|CASCADE4", TRIAL.read_text(encoding="utf-8-sig", errors="replace"), re.I)),
        "virtual_source": bool(re.search(r"VIRTUAL_(?:SOURCE|CAS)|CAS_VIRTUAL", TRIAL.read_text(encoding="utf-8-sig", errors="replace"), re.I)),
    }

    statuses = {
        "main_project_integrity_status": "pass" if main_sha == EXPECTED_MAIN_SHA else "fail",
        "trial_project_pre_run_status": "pass" if root.get("version") == "4.6.2" and P3F.exists() else "fail",
        "electrical_observability_static_status": "pass" if len(channels) == EXPECTED_OUTPUT_CHANNEL_COUNT and electrical_ok else "fail",
        "existing_output_channel_preservation_status": "pass" if len(channels) == EXPECTED_OUTPUT_CHANNEL_COUNT else "fail",
        "event_interface_status": "pass" if not event_missing and not chronology_missing else "fail",
        "dual_trial_enable_clean_state_status": "pass" if ibr2_enable_value == 0.0 and ibr3_enable_value == 0.0 and p3f_checks["ibr2_enable_default_fortran"] and p3f_checks["ibr3_enable_default_fortran"] else "fail",
        "ibr3_open_time_default_status": "pass" if ibr3_time_value == 5.0 and ibr3_time_constant_value == 5.0 and p3f_checks["ibr3_open_time_fortran"] else "fail",
        "run_artifact_parser_readiness_status": "pass" if GF46.exists() and simulation_end_time_s >= 5.0 and channel_plot_step_s > 0 else "fail",
        "source_cause_preflight_status": "pass" if p3f_checks["ibr2_cause_fortran"] and p3f_checks["ibr3_cause_module_parameter"] else "fail",
        "forbidden_feature_absence_status": "pass" if not any(forbidden.values()) else "fail",
    }
    overall = all(value == "pass" for value in statuses.values())

    backup_dir = None
    if overall:
        backup_dir = Path(r"C:\pscad_work\backups") / f"three_source_electrical_response_run_{now.strftime('%Y%m%d_%H%M%S')}"
        backup_dir.mkdir(parents=True, exist_ok=True)
        shutil.copy2(MAIN, backup_dir / "3IBR.pscx")
        shutil.copy2(TRIAL, backup_dir / "3IBR_DFIG1_TRIAL.pscx")
        (backup_dir / "manifest.json").write_text(
            json.dumps({"created_at": now.isoformat(timespec="seconds"), "main_sha_before": main_sha, "trial_sha_before": trial_sha}, indent=2),
            encoding="utf-8",
        )

    result.update(
        {
            "execution_status": "three_source_electrical_response_preflight_pass" if overall else "three_source_electrical_response_preflight_fallback",
            "main_sha_before": main_sha,
            "trial_sha_before": trial_sha,
            "main_project": str(MAIN),
            "trial_project": str(TRIAL),
            "output_channel_count_before": len(channels),
            "expected_output_channel_count": EXPECTED_OUTPUT_CHANNEL_COUNT,
            "simulation_end_time_s": simulation_end_time_s,
            "simulation_timestep_s": None,
            "channel_plot_step_s": channel_plot_step_s,
            "planned_IBR3_trial_open_time_s": 4.5,
            "planned_post_event_observation_horizon_s": 0.45,
            "ibr2_enable_component_location": ibr2_enable_const,
            "ibr2_open_time_component_location": ibr2_open_time_const,
            "ibr3_enable_component_location": ibr3_enable_const,
            "ibr3_open_time_constant_location": ibr3_time_const,
            "ibr3_open_time_parameter_location": ibr3_stimulus[0] if len(ibr3_stimulus) == 1 else ibr3_stimulus,
            "ibr3_event_packet_location": event_packets[0] if len(event_packets) == 1 else event_packets,
            "IBR2_TEST_ENABLE": ibr2_enable_value,
            "IBR2_TEST_OPEN_TIME_S": ibr2_time_value,
            "IBR3_TEST_ENABLE": ibr3_enable_value,
            "IBR3_OPEN_TIME_S": ibr3_time_value,
            "electrical_channel_mapping": ELECTRICAL_CHANNELS,
            "event_channel_mapping": {name: pgb_map.get(name) for name in EVENT_CHANNELS},
            "chronology_channel_mapping": {name: pgb_map.get(name) for name in CHRONOLOGY_CHANNELS},
            "missing_event_channels": event_missing,
            "missing_chronology_channels": chronology_missing,
            "generated_fortran_npgb_values": [int(m.group(1)) for m in re.finditer(r"NPGB\s*=\s*NPGB\s*\+\s*(\d+)", p3f)],
            "output_parser_strategy": {
                "result_dir": str(GF46),
                "inf_file": str(GF46 / "3IBR_DFIG1_TRIAL.inf"),
                "out_file_pattern": "3IBR_DFIG1_TRIAL_*.out",
                "mapping_rule": "Parse PGB(n) entries from .inf; PSCAD writes 10 PGB channels per .out file, column 1 is time and data columns start at 2.",
                "artifact_selection": "Use files newer than this pre-run manifest timestamp for the single approved Run.",
            },
            "pre_run_artifact_timestamp": now.timestamp(),
            "backup_dir": str(backup_dir) if backup_dir else None,
            "statuses": statuses,
            "forbidden_feature_scan": forbidden,
            "claim_boundary": {
                "preflight_only": True,
                "pscad_run_performed": False,
                "dynamic_response_validated": False,
            },
        }
    )
    path = out_dir / "three_source_electrical_response_pre_run_manifest.json"
    path.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps({"execution_status": result["execution_status"], "manifest": str(path), "backup_dir": result["backup_dir"], "statuses": statuses}, indent=2))
    return 0 if overall else 2


if __name__ == "__main__":
    raise SystemExit(main())
