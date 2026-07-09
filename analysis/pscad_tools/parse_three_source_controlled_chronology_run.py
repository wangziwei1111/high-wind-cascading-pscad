#!/usr/bin/env python3
"""Parse the controlled DFIG + IBR2_TRIAL + IBR3_TRIAL chronology PSCAD run."""

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

DATA_DIR = Path("data/validation")
BASELINE_SUMMARY = DATA_DIR / "ibr3_default_disabled_baseline_run_summary.json"
IBR2_SUMMARY = DATA_DIR / "ibr2_trial_single_opening_run_summary.json"
IBR3_SUMMARY = DATA_DIR / "ibr3_trial_single_opening_run_summary.json"

SUMMARY_JSON = DATA_DIR / "three_source_controlled_chronology_run_summary.json"
CHANNELS_CSV = DATA_DIR / "three_source_controlled_chronology_run_channels.csv"
METRICS_CSV = DATA_DIR / "three_source_controlled_chronology_run_metrics.csv"
COMPARISON_JSON = DATA_DIR / "three_source_controlled_chronology_comparison.json"
COMPARISON_CSV = DATA_DIR / "three_source_controlled_chronology_comparison.csv"

SIGNALS = [
    "DFIG_LVRT_CASCADE_EVENT_VALID",
    "DFIG_LVRT_CASCADE_EVENT_CAUSE_CODE",
    "DFIG_LVRT_CASCADE_EVENT_BRK_OPEN",
    "DFIG_LVRT_CASCADE_SOURCE_AVAILABLE",
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
    "IBR2_TRIAL_CASCADE_EVENT_BRK_OPEN",
    "IBR2_TRIAL_CASCADE_SOURCE_AVAILABLE",
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
    "IBR3_TRIAL_CASCADE_EVENT_BRK_OPEN",
    "IBR3_TRIAL_CASCADE_SOURCE_AVAILABLE",
    "IBR3_TRIAL_CASCADE_FIRST_EVENT_TIME_S",
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


def near(value: float | None, target: float, tol: float) -> bool:
    return value is not None and math.isfinite(value) and abs(value - target) <= tol


def all_close(value: float | None, target: float, tol: float = 1e-9) -> bool:
    return value is not None and abs(value - target) <= tol


def after_or_equal(t: float | None, ref: float | None, tol: float) -> bool:
    return t is not None and ref is not None and t + tol >= ref


def rounded(value: object, default: int = -999) -> int:
    try:
        return round(float(value))  # type: ignore[arg-type]
    except Exception:
        return default


def write_outputs(report: dict, comparison: dict) -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    SUMMARY_JSON.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    COMPARISON_JSON.write_text(json.dumps(comparison, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    with CHANNELS_CSV.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.writer(fh)
        writer.writerow(["signal", "pgb", "points", "first", "last", "min", "max", "first_ge_0p5_s", "first_change_s"])
        for sig, stats in report["selected_channel_summary"].items():
            writer.writerow([
                sig,
                stats.get("pgb", ""),
                stats.get("points", ""),
                stats.get("first", ""),
                stats.get("last", ""),
                stats.get("min", ""),
                stats.get("max", ""),
                stats.get("first_ge_0p5_s", ""),
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
        writer.writerow(["controlled_three_event_order_status", report["controlled_three_event_order_status"]])

    with COMPARISON_CSV.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.writer(fh)
        writer.writerow(["metric", "default_disabled", "ibr2_only", "ibr3_only", "three_source_controlled"])
        for row in comparison["comparison_rows"]:
            writer.writerow([row["metric"], row["default_disabled"], row["ibr2_only"], row["ibr3_only"], row["three_source_controlled"]])


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

    a_event_t = summary["DFIG_LVRT_CASCADE_EVENT_VALID"]["first_ge_0p5_s"]
    a_time = summary["DFIG_LVRT_CASCADE_FIRST_EVENT_TIME_S"]["last"]
    b_req_t = summary["IBR2_TRIAL_TEST_OPEN_REQUEST"]["first_ge_0p5_s"]
    b_cmd_t = summary["IBR2_TRIAL_BRK_CMD"]["first_ge_0p5_s"]
    b_state_t = summary["IBR2_TRIAL_BRK_STATE"]["first_ge_0p5_s"]
    b_open_t = summary["IBR2_TRIAL_BRK_OPEN_BOOL"]["first_ge_0p5_s"]
    b_event_t = summary["IBR2_TRIAL_CASCADE_EVENT_VALID"]["first_ge_0p5_s"]
    b_time = summary["IBR2_TRIAL_CASCADE_FIRST_EVENT_TIME_S"]["last"]
    c_req_t = summary["IBR3_TRIAL_TEST_OPEN_REQUEST"]["first_ge_0p5_s"]
    c_cmd_t = summary["IBR3_TRIAL_BRK_CMD"]["first_ge_0p5_s"]
    c_state_t = summary["IBR3_TRIAL_BRK_STATE"]["first_ge_0p5_s"]
    c_open_t = summary["IBR3_TRIAL_BRK_OPEN_BOOL"]["first_ge_0p5_s"]
    c_event_t = summary["IBR3_TRIAL_CASCADE_EVENT_VALID"]["first_ge_0p5_s"]
    c_time = summary["IBR3_TRIAL_CASCADE_FIRST_EVENT_TIME_S"]["last"]

    first_time = summary["CASCADE3_MONITOR_FIRST_EVENT_TIME_S"]["last"]
    second_time = summary["CASCADE3_MONITOR_SECOND_EVENT_TIME_S"]["last"]
    third_time = summary["CASCADE3_MONITOR_THIRD_EVENT_TIME_S"]["last"]
    gap12 = summary["CASCADE3_MONITOR_FIRST_TO_SECOND_GAP_S"]["last"]
    gap23 = summary["CASCADE3_MONITOR_SECOND_TO_THIRD_GAP_S"]["last"]

    checks = {
        "parser_mapping_status": "PASS" if not missing else "FAIL",
        "source_a_dynamic_status": "PASS" if rounded(summary["DFIG_LVRT_CASCADE_EVENT_VALID"]["last"]) == 1 and rounded(summary["DFIG_LVRT_CASCADE_EVENT_CAUSE_CODE"]["last"]) == 2 and a_time is not None and a_time >= 0 else "FAIL",
        "default_dfig_signature_status": "PASS" if near(a_time, 2.01603, time_tolerance_s) and rounded(summary["DFIG_LVRT_CASCADE_EVENT_CAUSE_CODE"]["last"]) == 2 else "INCONCLUSIVE_OR_CHANGED",
        "source_b_dynamic_status": "PASS" if summary["IBR2_TRIAL_TEST_ENABLE"]["min"] >= 0.5 and near(b_req_t, 4.0, time_tolerance_s) and after_or_equal(b_cmd_t, b_req_t, time_tolerance_s) and after_or_equal(b_state_t, b_cmd_t, time_tolerance_s) and after_or_equal(b_open_t, b_cmd_t, time_tolerance_s) and summary["IBR2_TRIAL_SOURCE_AVAILABLE"]["last"] == 0.0 and rounded(summary["IBR2_TRIAL_CASCADE_EVENT_VALID"]["last"]) == 1 and rounded(summary["IBR2_TRIAL_CASCADE_EVENT_CAUSE_CODE"]["last"]) == 4 and b_time is not None and b_time >= 0 and b_time + time_tolerance_s >= b_open_t else "FAIL",
        "source_c_dynamic_status": "PASS" if summary["IBR3_TRIAL_TEST_ENABLE"]["min"] >= 0.5 and near(c_req_t, 5.0, time_tolerance_s) and after_or_equal(c_cmd_t, c_req_t, time_tolerance_s) and after_or_equal(c_state_t, c_cmd_t, time_tolerance_s) and after_or_equal(c_open_t, c_cmd_t, time_tolerance_s) and summary["IBR3_TRIAL_SOURCE_AVAILABLE"]["last"] == 0.0 and rounded(summary["IBR3_TRIAL_CASCADE_EVENT_VALID"]["last"]) == 1 and rounded(summary["IBR3_TRIAL_CASCADE_EVENT_CAUSE_CODE"]["last"]) == 5 and c_time is not None and c_time >= 0 and c_time + time_tolerance_s >= c_open_t else "FAIL",
        "three_source_collector_dynamic_status": "PASS" if rounded(summary["CASCADE3_MONITOR_EVENTED_SOURCE_COUNT"]["last"]) == 3 and rounded(summary["CASCADE3_MONITOR_TIMED_EVENT_SOURCE_COUNT"]["last"]) == 3 and rounded(summary["CASCADE3_MONITOR_CAUSE_CODE_DFIG1"]["last"]) == 2 and rounded(summary["CASCADE3_MONITOR_CAUSE_CODE_IBR2_TRIAL"]["last"]) == 4 and rounded(summary["CASCADE3_MONITOR_CAUSE_CODE_IBR3_TRIAL"]["last"]) == 5 else "FAIL",
        "three_event_chronology_dynamic_status": "PASS" if near(first_time, a_time, time_tolerance_s) and near(second_time, b_time, time_tolerance_s) and near(third_time, c_time, time_tolerance_s) and first_time < second_time < third_time and near(gap12, second_time - first_time, time_tolerance_s) and near(gap23, third_time - second_time, time_tolerance_s) and gap12 >= 0 and gap23 >= 0 and rounded(summary["CASCADE3_MONITOR_FIRST_EVENT_SOURCE_CODE"]["last"]) == 1 and rounded(summary["CASCADE3_MONITOR_CHRONOLOGY_FIRST_SOURCE_CODE"]["last"]) == 1 and rounded(summary["CASCADE3_MONITOR_EVENT_ORDER_CLASS_CODE"]["last"]) == 4 and rounded(summary["CASCADE3_MONITOR_CHRONOLOGY_CONSISTENT"]["last"]) == 1 else "FAIL",
    }
    controlled_status = "pass" if (
        checks["parser_mapping_status"] == "PASS"
        and checks["source_a_dynamic_status"] == "PASS"
        and checks["source_b_dynamic_status"] == "PASS"
        and checks["source_c_dynamic_status"] == "PASS"
        and checks["three_source_collector_dynamic_status"] == "PASS"
        and checks["three_event_chronology_dynamic_status"] == "PASS"
        and checks["default_dfig_signature_status"] == "PASS"
    ) else "fail"

    run_timestamp = None
    out_files = sorted(RESULT_DIR.glob(f"{OUT_PREFIX}_*.out"))
    if out_files:
        run_timestamp = max(path.stat().st_mtime for path in out_files)

    report = {
        "run_id": "THREE_SOURCE_CONTROLLED_CHRONOLOGY_RUN_20260702_172923",
        "scenario_name": "THREE_SOURCE_CONTROLLED_CHRONOLOGY_DEFAULT_SCENARIO",
        "run_timestamp": "2026-07-02T17:29:23+08:00",
        "main_sha_during_run": sha256(MAIN_PROJECT),
        "trial_sha_during_run": sha256(TRIAL_PROJECT),
        "build_error_count": 0,
        "build_error_count_basis": "user reported Build and one Run completed; PSCAD output artifacts were generated",
        "simulation_timestep_s": 0.000005,
        "channel_plot_step_s": plot_step,
        "time_tolerance_s": time_tolerance_s,
        "sample_count": len(first_series),
        "missing_channel_list": missing,
        "parser_status": "parsed" if not missing else "missing_channels",
        "claim_boundary": "This run validates only one controlled timing-interface scenario: existing default DFIG event plus independently scheduled IBR2_TRIAL and IBR3_TRIAL local-opening stimuli. It does not validate natural cascade propagation, physical causality direction, system stability, protection coordination, MATLAB coupling, or general applicability.",
        "checks": checks,
        "dynamic_run_status": "pass" if all(v == "PASS" for k, v in checks.items() if k != "default_dfig_signature_status") else "fail",
        "controlled_three_event_order_status": controlled_status,
        "event_times_s": {
            "source_a_event_valid_first_ge_0p5": a_event_t,
            "source_a_first_event_time_last": a_time,
            "ibr2_open_request_first_ge_0p5": b_req_t,
            "ibr2_breaker_command_first_ge_0p5": b_cmd_t,
            "ibr2_breaker_state_first_ge_0p5": b_state_t,
            "ibr2_breaker_open_bool_first_ge_0p5": b_open_t,
            "source_b_event_valid_first_ge_0p5": b_event_t,
            "source_b_first_event_time_last": b_time,
            "ibr3_open_request_first_ge_0p5": c_req_t,
            "ibr3_breaker_command_first_ge_0p5": c_cmd_t,
            "ibr3_breaker_state_first_ge_0p5": c_state_t,
            "ibr3_breaker_open_bool_first_ge_0p5": c_open_t,
            "source_c_event_valid_first_ge_0p5": c_event_t,
            "source_c_first_event_time_last": c_time,
            "cascade3_first_event_time_last": first_time,
            "cascade3_second_event_time_last": second_time,
            "cascade3_third_event_time_last": third_time,
            "cascade3_first_to_second_gap_last": gap12,
            "cascade3_second_to_third_gap_last": gap23,
        },
        "selected_channel_summary": summary,
        "result_directory": str(RESULT_DIR),
        "inf": str(INF),
    }

    baseline = json.loads(BASELINE_SUMMARY.read_text(encoding="utf-8"))
    ibr2 = json.loads(IBR2_SUMMARY.read_text(encoding="utf-8"))
    ibr3 = json.loads(IBR3_SUMMARY.read_text(encoding="utf-8"))
    comparison_rows = [
        {
            "metric": "evented source count",
            "default_disabled": baseline["event_signature"].get("evented_source_count"),
            "ibr2_only": ibr2["selected_channel_summary"]["CASCADE3_MONITOR_EVENTED_SOURCE_COUNT"]["last"],
            "ibr3_only": ibr3["selected_channel_summary"]["CASCADE3_MONITOR_EVENTED_SOURCE_COUNT"]["last"],
            "three_source_controlled": summary["CASCADE3_MONITOR_EVENTED_SOURCE_COUNT"]["last"],
        },
        {
            "metric": "timed event source count",
            "default_disabled": baseline["event_signature"].get("timed_event_source_count"),
            "ibr2_only": ibr2["selected_channel_summary"]["CASCADE3_MONITOR_TIMED_EVENT_SOURCE_COUNT"]["last"],
            "ibr3_only": ibr3["selected_channel_summary"]["CASCADE3_MONITOR_TIMED_EVENT_SOURCE_COUNT"]["last"],
            "three_source_controlled": summary["CASCADE3_MONITOR_TIMED_EVENT_SOURCE_COUNT"]["last"],
        },
        {
            "metric": "second event time",
            "default_disabled": baseline["event_signature"].get("second_event_time_s"),
            "ibr2_only": ibr2["event_times_s"]["cascade3_second_event_time_last"],
            "ibr3_only": ibr3["event_times_s"]["cascade3_second_event_time_last"],
            "three_source_controlled": second_time,
        },
        {
            "metric": "third event time",
            "default_disabled": baseline["event_signature"].get("third_event_time_s"),
            "ibr2_only": ibr2["event_times_s"]["cascade3_third_event_time_last"],
            "ibr3_only": ibr3["event_times_s"]["cascade3_third_event_time_last"],
            "three_source_controlled": third_time,
        },
        {
            "metric": "order class code",
            "default_disabled": baseline["selected_channel_summary"]["CASCADE3_MONITOR_EVENT_ORDER_CLASS_CODE"]["last"],
            "ibr2_only": ibr2["selected_channel_summary"]["CASCADE3_MONITOR_EVENT_ORDER_CLASS_CODE"]["last"],
            "ibr3_only": ibr3["selected_channel_summary"]["CASCADE3_MONITOR_EVENT_ORDER_CLASS_CODE"]["last"],
            "three_source_controlled": summary["CASCADE3_MONITOR_EVENT_ORDER_CLASS_CODE"]["last"],
        },
    ]
    comparison = {
        "three_source_controlled_chronology_comparison_status": "pass" if controlled_status == "pass" else "fail",
        "baseline_run_id": baseline.get("run_id"),
        "ibr2_only_run_id": ibr2.get("run_id"),
        "ibr3_only_run_id": ibr3.get("run_id"),
        "three_source_run_id": report["run_id"],
        "comparison_rows": comparison_rows,
        "claim_boundary": report["claim_boundary"],
    }

    write_outputs(report, comparison)
    print(json.dumps(report, indent=2, ensure_ascii=False))
    return 0 if controlled_status == "pass" else 2


if __name__ == "__main__":
    sys.exit(main())
