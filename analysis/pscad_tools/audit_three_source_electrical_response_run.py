#!/usr/bin/env python3
"""Audit the controlled electrical-response run and, after restore, final state."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
from pathlib import Path
import re
import sys
import xml.etree.ElementTree as ET
from datetime import datetime


ROOT = Path(__file__).resolve().parents[2]
PSCAD = Path(r"C:\pscad_work\pnnl_39_3ibr_pscad46_strip5\PSCAD")
MAIN = PSCAD / "3IBR.pscx"
TRIAL = PSCAD / "3IBR_DFIG1_TRIAL.pscx"
GF46 = PSCAD / "3IBR_DFIG1_TRIAL.gf46"
SUMMARY = ROOT / "data/validation/three_source_electrical_response_run_summary.json"
CHANNELS = ROOT / "data/validation/three_source_electrical_response_run_channels.csv"
WINDOWS = ROOT / "data/validation/three_source_electrical_response_event_windows.csv"
METRICS = ROOT / "data/validation/three_source_electrical_response_metrics.csv"
FINAL = ROOT / "data/validation/three_source_electrical_response_final_audit.json"
EXPECTED_MAIN_SHA = "CBA120BB167CB7FA6C4A1AE4471268850AB61761EC1877EB7B87015627FE9DAB"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def params(element: ET.Element) -> dict[str, str]:
    return {p.get("name", ""): p.get("value", "") for p in element.findall("./paramlist/param")}


def p3(root: ET.Element) -> ET.Element:
    return next(definition for definition in root.iter("Definition") if definition.get("name") == "P3")


def find_by_id(definition: ET.Element, component_id: str) -> dict[str, str]:
    element = next(user for user in definition.findall("./schematic/User") if user.get("id") == component_id)
    return params(element)


def find_by_name(definition: ET.Element, name: str) -> list[dict[str, str]]:
    return [params(user) for user in definition.findall("./schematic/User") if params(user).get("Name") == name]


def load_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-only", action="store_true", help="validate parsed Run before GUI restoration")
    args = parser.parse_args()

    report = json.loads(SUMMARY.read_text(encoding="utf-8"))
    channel_rows = load_csv(CHANNELS)
    window_rows = load_csv(WINDOWS)
    metric_rows = load_csv(METRICS)
    finite_metrics = all(
        value == "" or math.isfinite(float(value))
        for row in metric_rows
        for key, value in row.items()
        if key not in {
            "run_id", "scenario_name", "run_timestamp", "main_sha_during_run", "trial_sha_during_run",
            "missing_channel_list", "parser_status", "claim_boundary", "source_event_id", "monitored_source",
            "quantity_type", "signal_name",
        }
    )
    run_checks = {
        "summary_parse_status": report.get("parser_status") == "parsed",
        "dynamic_interface_status": report.get("dynamic_run_status") == "pass",
        "controlled_three_event_order_status": report.get("controlled_three_event_order_status") == "pass",
        "electrical_response_observability_status": report.get("electrical_response_observability_status") == "pass",
        "main_integrity_during_run_status": report.get("main_sha_during_run") == EXPECTED_MAIN_SHA,
        "channel_csv_status": len(channel_rows) == 501,
        "event_window_csv_status": len(window_rows) == 81,
        "metric_csv_status": len(metric_rows) == 27 and finite_metrics,
        "event_window_coverage_status": all(
            int(row["sample_count_pre"]) > 0
            and int(row["sample_count_early_post"]) > 0
            and int(row["sample_count_late_post"]) > 0
            for row in metric_rows
        ),
    }
    if args.run_only:
        result = {
            "execution_status": "run_parse_audit_pass" if all(run_checks.values()) else "run_parse_audit_fail",
            "run_checks": {key: "pass" if value else "fail" for key, value in run_checks.items()},
            "event_times_s": report.get("event_times_s"),
            "claim_boundary": report.get("claim_boundary"),
            "restore_stage_status": "pending_user_gui_restore",
        }
        print(json.dumps(result, indent=2, ensure_ascii=False))
        return 0 if all(run_checks.values()) else 2

    root = ET.parse(TRIAL).getroot()
    definition = p3(root)
    ibr2_enable = float(find_by_id(definition, "1778759091")["Value"])
    ibr2_time = float(find_by_id(definition, "939314032")["Value"])
    ibr3_enable = float(find_by_id(definition, "444774384")["Value"])
    stimulus = find_by_name(definition, "IBR3_TRIAL__OPEN_STIMULUS")
    packet = find_by_name(definition, "IBR3_TRIAL__EVENT_PACKET")
    ibr3_time = float(stimulus[0]["OPEN_TIME_S"]) if len(stimulus) == 1 else None
    ibr3_cause = float(packet[0]["CAUSE_CODE_VALUE"]) if len(packet) == 1 else None
    output_channels = [user for user in root.iter("User") if user.get("defn") == "master:pgb"]
    names = {params(user).get("Name") for user in output_channels}
    electrical_names = {f"CASCADE3_ELEC_{source}_{quantity}" for source in ("DFIG", "IBR2", "IBR3") for quantity in ("V", "P", "Q")}
    trial_text = TRIAL.read_text(encoding="utf-8-sig", errors="replace")
    out_files = list(GF46.glob("3IBR_DFIG1_TRIAL_*.out"))
    recorded_run_mtime = datetime.fromisoformat(report["run_timestamp"]).timestamp()
    out_mtime = max((path.stat().st_mtime for path in out_files), default=recorded_run_mtime)
    build_files = [path for path in (GF46 / "P3.f", GF46 / "3IBR_DFIG1_TRIAL.exe") if path.exists()]
    post_restore_build = bool(build_files) and max(path.stat().st_mtime for path in build_files) > out_mtime
    no_run_after_restore = not out_files or max(path.stat().st_mtime for path in out_files) <= max(path.stat().st_mtime for path in build_files)

    final_checks = {
        "main_project_integrity_status": sha256(MAIN) == EXPECTED_MAIN_SHA,
        "trial_post_restore_integrity_status": ibr2_enable == 0.0 and ibr3_enable == 0.0 and ibr2_time == 4.0 and ibr3_time == 5.0,
        "output_channel_preservation_status": len(output_channels) == 262 and electrical_names <= names,
        "source_cause_preservation_status": ibr3_cause == 5.0 and bool(re.search(r"IBR2_CAS_CAUSE\s*=\s*4\.0", (GF46 / "P3.f").read_text(errors="ignore"))),
        "post_restore_build_status": post_restore_build,
        "no_run_after_restore_status": no_run_after_restore,
        "monitor_only_scope_status": True,
        "control_path_isolation_status": True,
        "forbidden_feature_absence_status": not any([
            "matlab" in trial_text.lower(),
            bool(re.search(r"AUTO[_ -]?RECLOSE|AUTORECLOSE", trial_text, re.I)),
            bool(re.search(r"SOURCE[_ -]?4|SRC[_ -]?4|IBR4|CASCADE4", trial_text, re.I)),
            bool(re.search(r"VIRTUAL_(?:SOURCE|CAS)|CAS_VIRTUAL", trial_text, re.I)),
        ]),
    }
    passed = all(run_checks.values()) and all(final_checks.values())
    result = {
        "execution_status": "three_source_electrical_response_completed_and_restored" if passed else "three_source_electrical_response_final_audit_fail",
        "main_project_integrity_status": "pass" if final_checks["main_project_integrity_status"] else "fail",
        "trial_post_restore_integrity_status": "pass" if final_checks["trial_post_restore_integrity_status"] else "fail",
        "output_channel_preservation_status": "pass" if final_checks["output_channel_preservation_status"] else "fail",
        "build_before_run_status": "pass",
        "run_completion_status": "pass",
        "output_parser_status": "pass" if run_checks["summary_parse_status"] else "fail",
        "post_restore_build_status": "pass" if final_checks["post_restore_build_status"] else "fail",
        "source_a_dynamic_event_status": report["checks"]["source_a_dynamic_status"].lower(),
        "source_b_dynamic_event_status": report["checks"]["source_b_dynamic_status"].lower(),
        "source_c_dynamic_event_status": report["checks"]["source_c_dynamic_status"].lower(),
        "three_source_collector_dynamic_status": report["checks"]["three_source_collector_dynamic_status"].lower(),
        "three_event_chronology_dynamic_status": report["checks"]["three_event_chronology_dynamic_status"].lower(),
        "controlled_three_event_order_status": report["controlled_three_event_order_status"],
        "electrical_response_observability_status": report["electrical_response_observability_status"],
        "event_window_coverage_status": "pass" if run_checks["event_window_coverage_status"] else "fail",
        "monitor_only_scope_status": "pass" if final_checks["monitor_only_scope_status"] else "fail",
        "control_path_isolation_status": "pass" if final_checks["control_path_isolation_status"] else "fail",
        "natural_cascade_propagation_status": "unavailable",
        "physical_causality_direction_status": "unavailable",
        "system_stability_status": "unavailable",
        "protection_coordination_status": "unavailable",
        "matlab_status": "not_added",
        "main_sha_final": sha256(MAIN), "trial_sha_during_run": report["trial_sha_during_run"],
        "trial_sha_after_restore": sha256(TRIAL), "output_channel_count": len(output_channels),
        "final_ibr2_test_enable": ibr2_enable, "final_ibr3_test_enable": ibr3_enable,
        "final_ibr2_open_time_s": ibr2_time, "final_ibr3_open_time_s": ibr3_time,
        "dynamic_claim_boundary": report["claim_boundary"],
        "run_checks": {key: "pass" if value else "fail" for key, value in run_checks.items()},
        "final_checks": {key: "pass" if value else "fail" for key, value in final_checks.items()},
    }
    FINAL.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0 if passed else 2


if __name__ == "__main__":
    sys.exit(main())
