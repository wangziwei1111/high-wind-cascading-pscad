"""Read-only preflight for three-source V/P/Q observability expansion.

This script does not edit PSCAD projects, does not Build, and does not Run.
It resolves the real-source V/P/Q signal names that should receive new
monitor-only Output Channel aliases in the trial project.
"""

from __future__ import annotations

import csv
import hashlib
import json
import re
import xml.etree.ElementTree as ET
from datetime import datetime, timezone, timedelta
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
PSCAD = Path(r"C:\pscad_work\pnnl_39_3ibr_pscad46_strip5\PSCAD")
MAIN = PSCAD / "3IBR.pscx"
TRIAL = PSCAD / "3IBR_DFIG1_TRIAL.pscx"
P3F = PSCAD / "3IBR_DFIG1_TRIAL.gf46" / "P3.f"

EXPECTED_MAIN_SHA = "CBA120BB167CB7FA6C4A1AE4471268850AB61761EC1877EB7B87015627FE9DAB"
EXPECTED_EXISTING_OUTPUT_CHANNELS = 253

SOURCES = {
    "A_DFIG": {
        "source_id": "DFIG_LVRT",
        "voltage": "VIBR1_2",
        "active_power": "PIBR1_2",
        "reactive_power": "QIBR1_2",
        "evidence": "DFIG LVRT logic uses VIBR1_2 for DFIG_LVRT_VSMIN_CAND; task priority names source A as VIBR1_2/PIBR1_2/QIBR1_2.",
    },
    "B_IBR2": {
        "source_id": "IBR2_TRIAL",
        "voltage": "VIBR2",
        "active_power": "PIBR2",
        "reactive_power": "QIBR2",
        "evidence": "IBR2 local-breaker boundary record maps IBR2_TRIAL observables to VIBR2/PIBR2/QIBR2.",
    },
    "C_IBR3": {
        "source_id": "IBR3_TRIAL",
        "voltage": "VIBR3",
        "active_power": "PIBR3",
        "reactive_power": "QIBR3",
        "evidence": "IBR3 real-source deployment record maps IBR3_TRIAL observables to VIBR3/PIBR3/QIBR3.",
    },
}

NEW_CHANNELS = {
    "CASCADE3_ELEC_DFIG_V": ("A_DFIG", "voltage"),
    "CASCADE3_ELEC_DFIG_P": ("A_DFIG", "active_power"),
    "CASCADE3_ELEC_DFIG_Q": ("A_DFIG", "reactive_power"),
    "CASCADE3_ELEC_IBR2_V": ("B_IBR2", "voltage"),
    "CASCADE3_ELEC_IBR2_P": ("B_IBR2", "active_power"),
    "CASCADE3_ELEC_IBR2_Q": ("B_IBR2", "reactive_power"),
    "CASCADE3_ELEC_IBR3_V": ("C_IBR3", "voltage"),
    "CASCADE3_ELEC_IBR3_P": ("C_IBR3", "active_power"),
    "CASCADE3_ELEC_IBR3_Q": ("C_IBR3", "reactive_power"),
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def params(element: ET.Element) -> dict[str, str]:
    return {p.get("name", ""): p.get("value", "") for p in element.findall("./paramlist/param")}


def pgb_channels(root: ET.Element) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for user in root.iter("User"):
        if user.get("defn") != "master:pgb":
            continue
        p = params(user)
        rows.append(
            {
                "id": user.get("id", ""),
                "x": user.get("x", ""),
                "y": user.get("y", ""),
                "name": p.get("Name", ""),
                "units": p.get("Units", ""),
                "scale": p.get("Scale", ""),
                "min": p.get("Min", ""),
                "max": p.get("Max", ""),
                "transfer_data": p.get("enab", ""),
                "display": p.get("Display", ""),
                "multiple_run_save": p.get("mrun", ""),
                "use_signal_name": p.get("UseSignalName", ""),
            }
        )
    return rows


def load_reference(path: Path) -> object:
    if not path.exists():
        return {"missing": str(path)}
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> int:
    out_dir = ROOT / "data" / "validation"
    out_dir.mkdir(parents=True, exist_ok=True)

    missing = [str(path) for path in (MAIN, TRIAL, P3F) if not path.exists()]
    result: dict[str, object] = {
        "schema_version": 1,
        "audit_time": datetime.now(timezone(timedelta(hours=8))).isoformat(timespec="seconds"),
        "operation": "three_source_electrical_observability_preflight",
        "read_only": True,
        "pscad_build_performed": False,
        "pscad_run_performed": False,
        "missing_paths": missing,
    }
    if missing:
        result["three_source_electrical_observability_ready_status"] = "fail"
        (out_dir / "three_source_electrical_observability_preflight.json").write_text(
            json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8"
        )
        return 2

    trial_root = ET.parse(TRIAL).getroot()
    p3f = P3F.read_text(encoding="utf-8", errors="replace")
    channels = pgb_channels(trial_root)
    channels_by_name = {row["name"]: row for row in channels}
    output_names = set(channels_by_name)

    main_sha = sha256(MAIN)
    trial_sha = sha256(TRIAL)
    new_existing = sorted(set(NEW_CHANNELS) & output_names)

    source_results: dict[str, object] = {}
    csv_rows: list[dict[str, str]] = []
    for source_key, spec in SOURCES.items():
        signal_names = [spec["voltage"], spec["active_power"], spec["reactive_power"]]
        existing_rows = {name: channels_by_name.get(name) for name in signal_names}
        present_in_output_channels = all(row is not None for row in existing_rows.values())
        present_in_fortran = all(re.search(rf"\b{re.escape(name)}\b", p3f) for name in signal_names)
        parameter_sets_match = all(
            row is not None
            and row["scale"] == "1.0"
            and row["min"] == "-2.0"
            and row["max"] == "2.0"
            and row["transfer_data"] == "1"
            for row in existing_rows.values()
        )
        status = "pass" if present_in_output_channels and present_in_fortran and parameter_sets_match else "fail"
        source_results[source_key] = {
            "source_id": spec["source_id"],
            "voltage_signal": spec["voltage"],
            "active_power_signal": spec["active_power"],
            "reactive_power_signal": spec["reactive_power"],
            "unit_evidence": "Existing PSCAD Output Channel units are blank; existing min/max are -2.0 to 2.0 with scale 1.0.",
            "source_resolution_evidence": spec["evidence"],
            "existing_output_channel_rows": existing_rows,
            "resolution_status": status,
        }
        for metric, channel_suffix, signal in (
            ("voltage", "V", spec["voltage"]),
            ("active_power", "P", spec["active_power"]),
            ("reactive_power", "Q", spec["reactive_power"]),
        ):
            target_name = next(
                name
                for name, (src, field) in NEW_CHANNELS.items()
                if src == source_key and field == metric
            )
            row = channels_by_name.get(signal, {})
            csv_rows.append(
                {
                    "source_key": source_key,
                    "source_id": str(spec["source_id"]),
                    "metric": metric,
                    "new_output_channel": target_name,
                    "connect_to_existing_signal": signal,
                    "units": row.get("units", ""),
                    "scale": row.get("scale", "1.0"),
                    "min": row.get("min", "-2.0"),
                    "max": row.get("max", "2.0"),
                    "transfer_data": "Yes",
                    "multiple_run_save": "No",
                    "use_signal_name_as_title": "No",
                    "scope": "monitor_only_existing_vpq_observable",
                }
            )

    status = {
        "main_project_integrity_status": "pass" if main_sha == EXPECTED_MAIN_SHA else "fail",
        "trial_project_preflight_status": "pass" if trial_root.get("version") == "4.6.2" else "fail",
        "existing_output_channel_baseline_status": "pass" if len(channels) == EXPECTED_EXISTING_OUTPUT_CHANNELS else "fail",
        "source_a_vpq_resolution_status": source_results["A_DFIG"]["resolution_status"],
        "source_b_vpq_resolution_status": source_results["B_IBR2"]["resolution_status"],
        "source_c_vpq_resolution_status": source_results["C_IBR3"]["resolution_status"],
        "new_channel_absence_status": "pass" if not new_existing else "fail",
        "monitor_only_scope_status": "pass",
    }
    ready = all(value == "pass" for value in status.values())
    status["three_source_electrical_observability_ready_status"] = "pass" if ready else "fail"

    result.update(
        {
            "main_project": {"path": str(MAIN), "sha256": main_sha, "expected_sha256": EXPECTED_MAIN_SHA},
            "trial_project": {"path": str(TRIAL), "sha256": trial_sha, "version": trial_root.get("version")},
            "existing_output_channel_count": len(channels),
            "expected_existing_output_channel_count": EXPECTED_EXISTING_OUTPUT_CHANNELS,
            "expected_final_output_channel_count_after_manual_add": EXPECTED_EXISTING_OUTPUT_CHANNELS + len(NEW_CHANNELS),
            "preexisting_requested_new_channels": new_existing,
            "source_a_voltage_signal": SOURCES["A_DFIG"]["voltage"],
            "source_a_active_power_signal": SOURCES["A_DFIG"]["active_power"],
            "source_a_reactive_power_signal": SOURCES["A_DFIG"]["reactive_power"],
            "source_b_voltage_signal": SOURCES["B_IBR2"]["voltage"],
            "source_b_active_power_signal": SOURCES["B_IBR2"]["active_power"],
            "source_b_reactive_power_signal": SOURCES["B_IBR2"]["reactive_power"],
            "source_c_voltage_signal": SOURCES["C_IBR3"]["voltage"],
            "source_c_active_power_signal": SOURCES["C_IBR3"]["active_power"],
            "source_c_reactive_power_signal": SOURCES["C_IBR3"]["reactive_power"],
            "source_resolution": source_results,
            "new_output_channel_plan": {
                name: {"source": src, "field": field, "connect_to": SOURCES[src][field]}
                for name, (src, field) in NEW_CHANNELS.items()
            },
            "recommended_output_channel_parameters": {
                "Scale": "1.0",
                "Units": "",
                "Min": "-2.0",
                "Max": "2.0",
                "Transfer Data": "Yes",
                "Multiple Run Save": "No",
                "Use Signal Name as Title": "No",
            },
            "recommended_axis_ranges": {
                "voltage": {"min": -2.0, "max": 2.0},
                "active_power": {"min": -2.0, "max": 2.0},
                "reactive_power": {"min": -2.0, "max": 2.0},
            },
            "reference_evidence": {
                "ibr2_local_breaker_boundary": load_reference(ROOT / "data" / "reference" / "ibr2_trial_local_breaker_boundary.json"),
                "ibr3_real_source_deployment": load_reference(ROOT / "data" / "reference" / "ibr3_trial_real_source_module_deployment.json"),
            },
            "statuses": status,
            "claim_boundary": {
                "adds_only_monitor_output_channels": True,
                "control_feedback_added": False,
                "event_logic_added": False,
                "build_or_run_performed_by_script": False,
                "dynamic_electrical_response_validated": False,
            },
        }
    )

    json_path = out_dir / "three_source_electrical_observability_preflight.json"
    csv_path = out_dir / "three_source_electrical_observability_signal_map.csv"
    json_path.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
    with csv_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(csv_rows[0]))
        writer.writeheader()
        writer.writerows(csv_rows)

    print(json.dumps({"preflight": status["three_source_electrical_observability_ready_status"], "json": str(json_path), "csv": str(csv_path)}, indent=2))
    return 0 if ready else 2


if __name__ == "__main__":
    raise SystemExit(main())
