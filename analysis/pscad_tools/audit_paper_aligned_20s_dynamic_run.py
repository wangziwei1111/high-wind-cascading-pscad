#!/usr/bin/env python3
"""Final audit for the paper-aligned 20 s dynamic Run analysis."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
from datetime import datetime
from pathlib import Path
import xml.etree.ElementTree as ET


REPO = Path(__file__).resolve().parents[2]
DEFAULT_MAIN = Path(r"C:\pscad_work\pnnl_39_3ibr_pscad46_strip5\PSCAD\3IBR.pscx")
DEFAULT_TRIAL = Path(r"C:\pscad_work\pnnl_39_3ibr_pscad46_strip5\PSCAD\3IBR_DFIG1_TRIAL.pscx")
EXPECTED_MAIN_SHA = "CBA120BB167CB7FA6C4A1AE4471268850AB61761EC1877EB7B87015627FE9DAB"
EXPECTED_TRIAL_SHA = "F81959EA62211FF9C1536C8481B67675AFE4DDCC3C56E804D048731A4B88A300"


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest().upper()


def read_json(path: Path) -> object:
    return json.loads(path.read_text(encoding="utf-8"))


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames: list[str] = []
    for row in rows:
        for key in row:
            if key not in fieldnames:
                fieldnames.append(key)
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def pscx_static_counts(trial: Path) -> dict[str, object]:
    root = ET.fromstring(trial.read_text(encoding="utf-8", errors="replace"))
    fault_count = sum(1 for u in root.iter("User") if "tfault" in u.attrib.get("defn", "").lower())
    pgb_count = sum(1 for u in root.iter("User") if u.attrib.get("defn") == "master:pgb")
    settings = {p.attrib.get("name", ""): p.attrib.get("value", "") for p in root.findall("./paramlist/param")}
    return {"fault_component_count": fault_count, "xml_output_channel_count": pgb_count, "settings": settings}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--main-pscx", type=Path, default=DEFAULT_MAIN)
    ap.add_argument("--trial-pscx", type=Path, default=DEFAULT_TRIAL)
    args = ap.parse_args()

    preflight = read_json(REPO / "data/validation/paper_aligned_20s_dynamic_run_preflight.json")
    manifest = read_json(REPO / "data/derived/paper_aligned_20s_run_manifest.json")
    analysis = read_json(REPO / "data/derived/paper_aligned_20s_run_analysis_summary.json")
    event_rows = read_csv(REPO / "data/derived/paper_aligned_20s_event_timeline.csv")
    metrics = read_csv(REPO / "data/derived/full_network_tline_window_metrics.csv")
    coverage = read_csv(REPO / "data/derived/paper_aligned_20s_run_channel_coverage.csv")
    current_rank = read_csv(REPO / "data/derived/full_network_tline_current_response_ranking.csv")
    power_rank = read_csv(REPO / "data/derived/full_network_tline_power_response_ranking.csv")

    main_sha_after = sha256(args.main_pscx)
    trial_sha_after = sha256(args.trial_pscx)
    static_counts = pscx_static_counts(args.trial_pscx)

    tline_metric_count = len(metrics)
    tline_quality_pass = all(r.get("window_coverage_status") == "pass" for r in metrics)
    channel_coverage_pass = all(r.get("mapping_status") == "pass" and r.get("time_axis_status") == "pass" for r in coverage)
    channel_runtime_mapped_count = sum(1 for r in coverage if r.get("mapping_status") == "pass")
    channel_runtime_total_count = len(coverage)
    time_axis = manifest["time_axis"]

    model_trace = [
        {
            "check": "main_project_sha",
            "before": preflight["main_sha_before_run"],
            "after": main_sha_after,
            "status": "pass" if main_sha_after == EXPECTED_MAIN_SHA == preflight["main_sha_before_run"] else "fail",
        },
        {
            "check": "trial_project_sha",
            "before": preflight["trial_sha_before_run"],
            "after": trial_sha_after,
            "status": "pass" if trial_sha_after == EXPECTED_TRIAL_SHA == preflight["trial_sha_before_run"] else "fail",
        },
        {
            "check": "fault_component_count",
            "before": 1,
            "after": static_counts["fault_component_count"],
            "status": "pass" if static_counts["fault_component_count"] == 1 else "fail",
        },
        {
            "check": "xml_output_channel_count",
            "before": 448,
            "after": static_counts["xml_output_channel_count"],
            "status": "pass" if static_counts["xml_output_channel_count"] == 448 else "fail",
        },
        {
            "check": "duration_of_run_s",
            "before": 20,
            "after": static_counts["settings"].get("time_duration"),
            "status": "pass" if static_counts["settings"].get("time_duration") in {"20", "20.0", "20.00"} else "fail",
        },
    ]

    tline_trace = []
    for branch in sorted({r["network_branch_id"] for r in metrics}):
        rows = [r for r in metrics if r["network_branch_id"] == branch]
        tline_trace.append(
            {
                "network_branch_id": branch,
                "expected_signal_count": 6,
                "observed_signal_count": len(rows),
                "all_windows_pass": all(r.get("window_coverage_status") == "pass" for r in rows),
                "status": "pass" if len(rows) == 6 and all(r.get("window_coverage_status") == "pass" for r in rows) else "fail",
            }
        )

    channel_trace = [
        {
            "channel_name": r.get("channel_name"),
            "inf_pgb": r.get("inf_pgb"),
            "out_file": r.get("out_file"),
            "sample_count": r.get("sample_count"),
            "last_time_s": r.get("last_time_s"),
            "mapping_status": r.get("mapping_status"),
            "time_axis_status": r.get("time_axis_status"),
            "status": "pass" if r.get("mapping_status") == "pass" and r.get("time_axis_status") == "pass" else "fail",
        }
        for r in coverage
    ]

    statuses = {
        "run_status": "single_user_gui_run_completed",
        "run_completion_status": "pass" if time_axis.get("last_time_s", 0) >= 19.99 else "fail",
        "output_parse_status": analysis["output_parse_status"],
        "time_axis_status": analysis["time_axis_status"],
        "full_network_tline_data_coverage_status": analysis["full_network_tline_data_coverage_status"],
        "fault_execution_status": "observed_from_configured_run_outputs",
        "dfig_lvrt_event_observation_status": analysis["dfig_lvrt_event_observation_status"],
        "ibr2_unexpected_event_status": analysis["ibr2_unexpected_event_status"],
        "ibr3_unexpected_event_status": analysis["ibr3_unexpected_event_status"],
        "collector_observation_status": analysis["collector_observation_status"],
        "chronology_observation_status": analysis["chronology_observation_status"],
        "network_wide_tline_dynamic_response_status": analysis["network_wide_tline_dynamic_response_status"],
        "line_loading_ratio_status": "unavailable_no_audited_line_rating_basis",
        "line_overload_status": "unavailable",
        "line_protection_status": "unavailable",
        "branch_trip_status": "unavailable",
        "natural_cascade_propagation_status": "unavailable",
        "physical_causality_direction_status": "unavailable",
        "system_stability_status": "unavailable",
        "protection_coordination_status": "unavailable",
        "voltage_support_performance_status": "unavailable",
        "matlab_status": "not_added",
        "main_project_integrity_status": "pass" if main_sha_after == EXPECTED_MAIN_SHA else "fail",
        "trial_project_integrity_status": "pass" if trial_sha_after == EXPECTED_TRIAL_SHA else "fail",
        "existing_channel_preservation_status": "pass" if static_counts["xml_output_channel_count"] == 448 else "fail",
        "runtime_existing_channel_mapping_status": "pass" if channel_coverage_pass else "partial_non_tline_channels_missing_in_inf",
        "tline_measurement_preservation_status": "pass" if len(tline_trace) == 31 and all(r["status"] == "pass" for r in tline_trace) else "fail",
    }
    hard_pass = (
        preflight.get("execution_status") == "pass"
        and analysis.get("execution_status") == "pass"
        and statuses["run_completion_status"] == "pass"
        and statuses["output_parse_status"] == "pass"
        and statuses["time_axis_status"] == "pass"
        and statuses["full_network_tline_data_coverage_status"] == "pass"
        and statuses["ibr2_unexpected_event_status"] == "pass"
        and statuses["ibr3_unexpected_event_status"] == "pass"
        and statuses["main_project_integrity_status"] == "pass"
        and statuses["trial_project_integrity_status"] == "pass"
        and statuses["tline_measurement_preservation_status"] == "pass"
        and tline_metric_count == 186
    )

    audit = {
        "audit_name": "paper_aligned_20s_dynamic_run_final_audit",
        "generated_at_local": datetime.now().isoformat(timespec="seconds"),
        "execution_status": "pass" if hard_pass else "paper_aligned_20s_dynamic_run_parser_fallback",
        **statuses,
        "main_sha_before_run": preflight["main_sha_before_run"],
        "main_sha_after_run": main_sha_after,
        "trial_sha_before_run": preflight["trial_sha_before_run"],
        "trial_sha_after_run": trial_sha_after,
        "time_axis": time_axis,
        "xml_output_channel_count": static_counts["xml_output_channel_count"],
        "inf_pgb_count": manifest["parsed_inf_pgb_count"],
        "runtime_existing_channel_mapping_count": channel_runtime_mapped_count,
        "runtime_existing_channel_total_count": channel_runtime_total_count,
        "tline_count": len(tline_trace),
        "tline_raw_signal_count": tline_metric_count,
        "event_timeline": event_rows,
        "top10_current_response": current_rank[:10],
        "top10_power_response_combined_table": power_rank[:10],
        "claim_boundary": "observed raw network-wide TLine P/Q/I dynamic response only; no overload, relay, branch trip, causal direction, stability, or strict paper-reproduction claim",
    }

    write_json(REPO / "data/validation/paper_aligned_20s_dynamic_run_final_audit.json", audit)
    write_csv(REPO / "data/validation/paper_aligned_20s_dynamic_run_channel_trace.csv", channel_trace)
    write_csv(REPO / "data/validation/paper_aligned_20s_dynamic_run_tline_trace.csv", tline_trace)
    write_csv(REPO / "data/validation/paper_aligned_20s_dynamic_run_model_integrity_trace.csv", model_trace)
    print(json.dumps(audit, ensure_ascii=False, indent=2))
    return 0 if audit["execution_status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
