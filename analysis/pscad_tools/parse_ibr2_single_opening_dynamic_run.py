#!/usr/bin/env python3
"""Parse the IBR2 single-opening PSCAD run and compare to the disabled baseline."""

from __future__ import annotations

import csv
import hashlib
import json
import math
from pathlib import Path
import re
import statistics
import sys


RESULT_DIR = Path(r"C:\pscad_work\pnnl_39_3ibr_pscad46_strip5\PSCAD\3IBR_DFIG1_TRIAL.gf46")
INF = RESULT_DIR / "3IBR_DFIG1_TRIAL.inf"
OUT_PREFIX = "3IBR_DFIG1_TRIAL"
MAIN_PROJECT = Path(r"C:\pscad_work\pnnl_39_3ibr_pscad46_strip5\PSCAD\3IBR.pscx")
TRIAL_PROJECT = Path(r"C:\pscad_work\pnnl_39_3ibr_pscad46_strip5\PSCAD\3IBR_DFIG1_TRIAL.pscx")
BASELINE_SUMMARY = Path("data/validation/ibr3_default_disabled_baseline_run_summary.json")

SUMMARY_JSON = Path("data/validation/ibr2_trial_single_opening_run_summary.json")
CHANNELS_CSV = Path("data/validation/ibr2_trial_single_opening_run_channels.csv")
METRICS_CSV = Path("data/validation/ibr2_trial_single_opening_run_metrics.csv")
COMPARISON_JSON = Path("data/validation/ibr2_enabled_vs_default_disabled_run_comparison.json")
COMPARISON_CSV = Path("data/validation/ibr2_enabled_vs_default_disabled_run_comparison.csv")

SIGNALS = [
    "IBR2_TRIAL_TEST_ENABLE",
    "IBR2_TRIAL_TEST_OPEN_TIME_S",
    "IBR2_TRIAL_TEST_OPEN_REQUEST",
    "IBR2_TRIAL_BRK_CMD",
    "IBR2_TRIAL_BRK_STATE",
    "IBR2_TRIAL_BRK_OPEN_BOOL",
    "IBR2_TRIAL_SOURCE_AVAILABLE",
    "IBR2_TRIAL_CASCADE_EVENT_VALID",
    "IBR2_TRIAL_CASCADE_EVENT_CAUSE_CODE",
    "IBR2_TRIAL_CASCADE_EVENT_BRK_OPEN",
    "IBR2_TRIAL_CASCADE_SOURCE_AVAILABLE",
    "IBR2_TRIAL_CASCADE_FIRST_EVENT_TIME_S",
    "IBR3_TRIAL_TEST_ENABLE",
    "IBR3_TRIAL_TEST_OPEN_REQUEST",
    "IBR3_TRIAL_BRK_CMD",
    "IBR3_TRIAL_BRK_STATE",
    "IBR3_TRIAL_BRK_OPEN_BOOL",
    "IBR3_TRIAL_SOURCE_AVAILABLE",
    "IBR3_TRIAL_CASCADE_EVENT_VALID",
    "IBR3_TRIAL_CASCADE_EVENT_CAUSE_CODE",
    "CASCADE3_MONITOR_ANY_TRIP",
    "CASCADE3_MONITOR_ANY_BRK_OPEN",
    "CASCADE3_MONITOR_AVAILABLE_SOURCE_COUNT",
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
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest().upper()


def parse_inf() -> dict[str, int]:
    mapping: dict[str, int] = {}
    for line in INF.read_text(encoding="utf-8", errors="ignore").splitlines():
        m = re.search(r"PGB\((\d+)\).*?Desc=\"([^\"]+)\"", line)
        if m:
            mapping[m.group(2)] = int(m.group(1))
    return mapping


def file_and_col(pgb: int) -> tuple[Path, int]:
    file_index = (pgb - 1) // 10 + 1
    data_col = (pgb - 1) % 10 + 1
    return RESULT_DIR / f"{OUT_PREFIX}_{file_index:02d}.out", data_col


def read_channel(pgb: int) -> list[tuple[float, float]]:
    path, col = file_and_col(pgb)
    out: list[tuple[float, float]] = []
    for raw in path.read_text(encoding="utf-8", errors="ignore").splitlines():
        parts = raw.split()
        if len(parts) <= col:
            continue
        try:
            out.append((float(parts[0]), float(parts[col])))
        except ValueError:
            continue
    return out


def first_crossing(series: list[tuple[float, float]], threshold: float = 0.5) -> float | None:
    for t, v in series:
        if v >= threshold:
            return t
    return None


def first_change(series: list[tuple[float, float]], eps: float = 1e-6) -> float | None:
    if not series:
        return None
    base = series[0][1]
    for t, v in series:
        if abs(v - base) > eps:
            return t
    return None


def minmax_last(series: list[tuple[float, float]]) -> dict[str, float | None]:
    if not series:
        return {"first": None, "last": None, "min": None, "max": None}
    vals = [v for _, v in series]
    return {"first": vals[0], "last": vals[-1], "min": min(vals), "max": max(vals)}


def all_close(value: float | None, target: float, tol: float = 1e-9) -> bool:
    return value is not None and abs(value - target) <= tol


def near(value: float | None, target: float, tol: float) -> bool:
    return value is not None and abs(value - target) <= tol


def after_or_equal(t: float | None, ref: float | None, tol: float) -> bool:
    return t is not None and ref is not None and t + tol >= ref


def write_outputs(report: dict, comparison: dict) -> None:
    SUMMARY_JSON.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    COMPARISON_JSON.write_text(json.dumps(comparison, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    with CHANNELS_CSV.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.writer(fh)
        writer.writerow(["signal", "pgb", "points", "first", "last", "min", "max", "first_ge_0p5_s", "first_change_s"])
        for sig, stats in report["selected_channel_summary"].items():
            writer.writerow([
                sig, stats.get("pgb", ""), stats.get("points", ""),
                stats.get("first", ""), stats.get("last", ""), stats.get("min", ""),
                stats.get("max", ""), stats.get("first_ge_0p5_s", ""),
                stats.get("first_change_s", ""),
            ])

    with METRICS_CSV.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.writer(fh)
        writer.writerow(["metric", "value"])
        for key, value in report["checks"].items():
            writer.writerow([key, value])
        for key, value in report["event_times_s"].items():
            writer.writerow([key, value])
        writer.writerow(["dynamic_run_status", report["dynamic_run_status"]])

    with COMPARISON_CSV.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.writer(fh)
        writer.writerow(["metric", "baseline_default_disabled", "ibr2_enabled_run", "contrast"])
        for row in comparison["comparison_rows"]:
            writer.writerow([row["metric"], row["baseline"], row["ibr2_enabled"], row["contrast"]])


def main() -> int:
    mapping = parse_inf()
    missing = [sig for sig in SIGNALS if sig not in mapping]
    summary: dict[str, dict[str, object]] = {}
    series_by_signal: dict[str, list[tuple[float, float]]] = {}
    for sig in SIGNALS:
        if sig not in mapping:
            continue
        series = read_channel(mapping[sig])
        series_by_signal[sig] = series
        summary[sig] = {
            "pgb": mapping[sig],
            "file": str(file_and_col(mapping[sig])[0]),
            "data_column": file_and_col(mapping[sig])[1],
            "points": len(series),
            **minmax_last(series),
            "first_ge_0p5_s": first_crossing(series),
            "first_change_s": first_change(series),
        }

    first_series = next(iter(series_by_signal.values()))
    plot_step = statistics.median(b[0] - a[0] for a, b in zip(first_series, first_series[1:]))
    time_tolerance_s = max(2 * 0.000005, 2 * plot_step, 0.02)

    req_t = summary["IBR2_TRIAL_TEST_OPEN_REQUEST"]["first_ge_0p5_s"]
    cmd_t = summary["IBR2_TRIAL_BRK_CMD"]["first_ge_0p5_s"]
    state_t = summary["IBR2_TRIAL_BRK_STATE"]["first_ge_0p5_s"]
    open_t = summary["IBR2_TRIAL_BRK_OPEN_BOOL"]["first_ge_0p5_s"]
    event_t = summary["IBR2_TRIAL_CASCADE_EVENT_VALID"]["first_ge_0p5_s"]
    source_b_time = summary["IBR2_TRIAL_CASCADE_FIRST_EVENT_TIME_S"]["last"]

    checks = {
        "parser_mapping_status": "PASS" if not missing else "FAIL",
        "ibr2_test_enable_dynamic_status": "PASS" if summary["IBR2_TRIAL_TEST_ENABLE"]["min"] >= 0.5 and summary["IBR2_TRIAL_TEST_ENABLE"]["max"] >= 0.5 else "FAIL",
        "ibr2_stimulus_request_status": "PASS" if req_t is not None and req_t + time_tolerance_s >= 4.0 else "FAIL",
        "ibr2_breaker_command_status": "PASS" if after_or_equal(cmd_t, req_t, time_tolerance_s) else "FAIL",
        "ibr2_actual_open_status": "PASS" if after_or_equal(open_t, cmd_t, time_tolerance_s) else "FAIL",
        "ibr2_state_adapter_dynamic_status": "PASS" if after_or_equal(state_t, cmd_t, time_tolerance_s) else "FAIL",
        "ibr2_source_available_status": "PASS" if summary["IBR2_TRIAL_SOURCE_AVAILABLE"]["first"] == 1.0 and summary["IBR2_TRIAL_SOURCE_AVAILABLE"]["last"] == 0.0 else "FAIL",
        "source_b_event_packet_dynamic_status": "PASS" if event_t is not None and round(summary["IBR2_TRIAL_CASCADE_EVENT_CAUSE_CODE"]["last"]) == 4 and round(summary["IBR2_TRIAL_CASCADE_EVENT_BRK_OPEN"]["last"]) == 1 and round(summary["IBR2_TRIAL_CASCADE_SOURCE_AVAILABLE"]["last"]) == 0 and source_b_time is not None and source_b_time >= 0 and source_b_time + time_tolerance_s >= open_t else "FAIL",
        "ibr3_default_disabled_isolation_status": "PASS" if all_close(summary["IBR3_TRIAL_TEST_ENABLE"]["max"], 0) and all_close(summary["IBR3_TRIAL_TEST_OPEN_REQUEST"]["max"], 0) and all_close(summary["IBR3_TRIAL_BRK_CMD"]["max"], 0) and summary["IBR3_TRIAL_BRK_STATE"]["max"] < 0.5 and all_close(summary["IBR3_TRIAL_BRK_OPEN_BOOL"]["max"], 0) and all_close(summary["IBR3_TRIAL_SOURCE_AVAILABLE"]["min"], 1) and all_close(summary["IBR3_TRIAL_CASCADE_EVENT_VALID"]["max"], 0) and all_close(summary["IBR3_TRIAL_CASCADE_EVENT_CAUSE_CODE"]["max"], 0) and all_close(summary["CASCADE3_MONITOR_CAUSE_CODE_IBR3_TRIAL"]["max"], 0) else "FAIL",
        "default_dfig_signature_status": "PASS" if near(summary["CASCADE3_MONITOR_FIRST_EVENT_TIME_S"]["last"], 2.01603, time_tolerance_s) and round(summary["CASCADE3_MONITOR_CAUSE_CODE_DFIG1"]["last"]) == 2 else "FAIL",
        "three_source_collector_dynamic_status": "PASS" if round(summary["CASCADE3_MONITOR_CAUSE_CODE_IBR2_TRIAL"]["last"]) == 4 and round(summary["CASCADE3_MONITOR_CAUSE_CODE_IBR3_TRIAL"]["last"]) == 0 and round(summary["CASCADE3_MONITOR_EVENTED_SOURCE_COUNT"]["last"]) == 2 and round(summary["CASCADE3_MONITOR_TIMED_EVENT_SOURCE_COUNT"]["last"]) == 2 else "FAIL",
        "three_event_chronology_dynamic_status": "PASS" if near(summary["CASCADE3_MONITOR_FIRST_EVENT_TIME_S"]["last"], 2.01603, time_tolerance_s) and near(summary["CASCADE3_MONITOR_SECOND_EVENT_TIME_S"]["last"], 4.0, time_tolerance_s) and all_close(summary["CASCADE3_MONITOR_THIRD_EVENT_TIME_S"]["last"], -1) and near(summary["CASCADE3_MONITOR_FIRST_TO_SECOND_GAP_S"]["last"], 4.0 - 2.01603, time_tolerance_s) and all_close(summary["CASCADE3_MONITOR_SECOND_TO_THIRD_GAP_S"]["last"], -1) and round(summary["CASCADE3_MONITOR_FIRST_EVENT_SOURCE_CODE"]["last"]) == 1 and round(summary["CASCADE3_MONITOR_CHRONOLOGY_FIRST_SOURCE_CODE"]["last"]) == 1 and round(summary["CASCADE3_MONITOR_EVENT_ORDER_CLASS_CODE"]["last"]) == 2 and round(summary["CASCADE3_MONITOR_CHRONOLOGY_CONSISTENT"]["last"]) == 1 else "FAIL",
    }
    dynamic_run_status = "pass" if all(v == "PASS" for v in checks.values()) else "fail"

    baseline = json.loads(BASELINE_SUMMARY.read_text(encoding="utf-8"))
    base_channels = baseline["selected_channel_summary"]
    comparison_rows = [
        {"metric": "IBR2 test enable", "baseline": baseline["event_signature"].get("ibr2_cause_code", 0), "ibr2_enabled": summary["IBR2_TRIAL_TEST_ENABLE"]["min"], "contrast": "baseline source-B cause 0 vs enabled test enable 1"},
        {"metric": "IBR2 open request time", "baseline": base_channels.get("IBR2_TRIAL_TEST_OPEN_REQUEST", {}).get("first_ge_0p5_s", "unavailable_in_baseline_summary"), "ibr2_enabled": req_t, "contrast": "baseline detail unavailable/absent vs 4.0 s"},
        {"metric": "IBR2 actual open time", "baseline": base_channels.get("IBR2_TRIAL_BRK_OPEN_BOOL", {}).get("first_ge_0p5_s", "unavailable_in_baseline_summary"), "ibr2_enabled": open_t, "contrast": "baseline detail unavailable/absent vs 4.0 s"},
        {"metric": "IBR2 event valid time", "baseline": base_channels.get("IBR2_TRIAL_CASCADE_EVENT_VALID", {}).get("first_ge_0p5_s", "unavailable_in_baseline_summary"), "ibr2_enabled": event_t, "contrast": "baseline detail unavailable/absent vs 4.0 s"},
        {"metric": "IBR2 cause code", "baseline": baseline["event_signature"]["ibr2_cause_code"], "ibr2_enabled": summary["CASCADE3_MONITOR_CAUSE_CODE_IBR2_TRIAL"]["last"], "contrast": "0 vs 4"},
        {"metric": "CASCADE3 second event time", "baseline": baseline["event_signature"]["second_event_time_s"], "ibr2_enabled": summary["CASCADE3_MONITOR_SECOND_EVENT_TIME_S"]["last"], "contrast": "-1 vs 4.0 s"},
    ]

    report = {
        "run_id": "IBR2_TRIAL_SINGLE_OPENING_DYNAMIC_RUN_20260702_154655",
        "scenario_name": "IBR2_TRIAL_SINGLE_OPENING_DEFAULT_SCENARIO",
        "run_timestamp": "2026-07-02T15:46:55+08:00",
        "main_sha_during_run": sha256(MAIN_PROJECT),
        "trial_sha_during_run": sha256(TRIAL_PROJECT),
        "build_error_count": 0,
        "build_error_count_basis": "user reported Build completed and PSCAD generated IBR2 enabled output artifacts",
        "simulation_timestep_s": 0.000005,
        "channel_plot_step_s": plot_step,
        "time_tolerance_s": time_tolerance_s,
        "sample_count": len(first_series),
        "missing_channel_list": missing,
        "parser_status": "parsed" if not missing else "missing_channels",
        "claim_boundary": "This run only validates the IBR2_TRIAL source-B trial-only local-opening path in the fixed trial model. It is not a natural DFIG-to-IBR2 cascade validation and does not validate physical causality direction, system stability, protection coordination, MATLAB coupling, or general applicability.",
        "checks": checks,
        "dynamic_run_status": dynamic_run_status,
        "event_times_s": {
            "ibr2_open_request_first_ge_0p5": req_t,
            "ibr2_breaker_command_first_ge_0p5": cmd_t,
            "ibr2_breaker_state_first_ge_0p5": state_t,
            "ibr2_breaker_open_bool_first_ge_0p5": open_t,
            "source_b_event_valid_first_ge_0p5": event_t,
            "source_b_first_event_time_last": source_b_time,
            "cascade3_first_event_time_last": summary["CASCADE3_MONITOR_FIRST_EVENT_TIME_S"]["last"],
            "cascade3_second_event_time_last": summary["CASCADE3_MONITOR_SECOND_EVENT_TIME_S"]["last"],
            "cascade3_third_event_time_last": summary["CASCADE3_MONITOR_THIRD_EVENT_TIME_S"]["last"],
            "cascade3_first_to_second_gap_last": summary["CASCADE3_MONITOR_FIRST_TO_SECOND_GAP_S"]["last"],
            "cascade3_second_to_third_gap_last": summary["CASCADE3_MONITOR_SECOND_TO_THIRD_GAP_S"]["last"],
        },
        "selected_channel_summary": summary,
    }
    comparison = {
        "ibr2_enabled_vs_default_disabled_status": "pass" if dynamic_run_status == "pass" else "fail",
        "baseline_run_id": baseline["run_id"],
        "ibr2_enabled_run_id": report["run_id"],
        "comparison_rows": comparison_rows,
        "claim_boundary": report["claim_boundary"],
    }
    write_outputs(report, comparison)
    print(json.dumps(report, indent=2, ensure_ascii=False))
    print(json.dumps(comparison, indent=2, ensure_ascii=False))
    return 0 if dynamic_run_status == "pass" else 1


if __name__ == "__main__":
    sys.exit(main())
