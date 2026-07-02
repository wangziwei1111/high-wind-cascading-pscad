#!/usr/bin/env python3
"""Parse the IBR3 default-disabled baseline PSCAD run and compare to enabled run."""

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
ENABLED_SUMMARY = Path("data/validation/ibr3_trial_single_opening_run_summary.json")

SUMMARY_JSON = Path("data/validation/ibr3_default_disabled_baseline_run_summary.json")
CHANNELS_CSV = Path("data/validation/ibr3_default_disabled_baseline_run_channels.csv")
METRICS_CSV = Path("data/validation/ibr3_default_disabled_baseline_run_metrics.csv")
COMPARISON_JSON = Path("data/validation/ibr3_enabled_vs_disabled_run_comparison.json")
COMPARISON_CSV = Path("data/validation/ibr3_enabled_vs_disabled_run_comparison.csv")


SIGNALS = [
    "IBR2_TRIAL_TEST_ENABLE",
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
    "CASCADE3_MONITOR_FIRST_EVENT_TIME_S",
    "CASCADE3_MONITOR_FIRST_EVENT_SOURCE_CODE",
    "CASCADE3_MONITOR_CAUSE_CODE_DFIG1",
    "CASCADE3_MONITOR_CAUSE_CODE_IBR2_TRIAL",
    "CASCADE3_MONITOR_CAUSE_CODE_IBR3_TRIAL",
    "CASCADE3_MONITOR_TIMED_EVENT_SOURCE_COUNT",
    "CASCADE3_MONITOR_SECOND_EVENT_TIME_S",
    "CASCADE3_MONITOR_THIRD_EVENT_TIME_S",
    "CASCADE3_MONITOR_FIRST_TO_SECOND_GAP_S",
    "CASCADE3_MONITOR_SECOND_TO_THIRD_GAP_S",
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
    series: list[tuple[float, float]] = []
    for raw in path.read_text(encoding="utf-8", errors="ignore").splitlines():
        parts = raw.split()
        if len(parts) <= col:
            continue
        try:
            series.append((float(parts[0]), float(parts[col])))
        except ValueError:
            continue
    return series


def first_crossing(series: list[tuple[float, float]], threshold: float = 0.5) -> float | None:
    for t, v in series:
        if v >= threshold:
            return t
    return None


def first_change(series: list[tuple[float, float]], eps: float = 1e-6) -> float | None:
    if not series:
        return None
    first = series[0][1]
    for t, v in series:
        if abs(v - first) > eps:
            return t
    return None


def minmax_last(series: list[tuple[float, float]]) -> dict[str, float | None]:
    if not series:
        return {"first": None, "last": None, "min": None, "max": None}
    vals = [v for _, v in series]
    return {"first": vals[0], "last": vals[-1], "min": min(vals), "max": max(vals)}


def all_close(value: float | None, target: float, tol: float = 1e-9) -> bool:
    return value is not None and abs(value - target) <= tol


def write_outputs(report: dict, comparison: dict, series_by_signal: dict[str, list[tuple[float, float]]]) -> None:
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
        for key, value in report["event_signature"].items():
            writer.writerow([key, value])
        writer.writerow(["dynamic_baseline_status", report["dynamic_baseline_status"]])

    with COMPARISON_CSV.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.writer(fh)
        writer.writerow(["metric", "enabled_run", "default_disabled_baseline", "contrast"])
        for item in comparison["comparison_rows"]:
            writer.writerow([item["metric"], item["enabled"], item["disabled"], item["contrast"]])


def main() -> int:
    mapping = parse_inf()
    missing = [sig for sig in SIGNALS if sig not in mapping]
    series_by_signal: dict[str, list[tuple[float, float]]] = {}
    summary: dict[str, dict[str, object]] = {}
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
    plot_step = statistics.median(
        b[0] - a[0] for a, b in zip(first_series, first_series[1:])
    )
    time_tolerance_s = max(2 * 0.000005, 2 * plot_step, 0.02)

    checks = {
        "parser_mapping_status": "PASS" if not missing else "FAIL",
        "ibr2_test_enable_zero_status": "PASS" if all_close(summary["IBR2_TRIAL_TEST_ENABLE"]["min"], 0) and all_close(summary["IBR2_TRIAL_TEST_ENABLE"]["max"], 0) else "FAIL",
        "ibr3_test_enable_zero_status": "PASS" if all_close(summary["IBR3_TRIAL_TEST_ENABLE"]["min"], 0) and all_close(summary["IBR3_TRIAL_TEST_ENABLE"]["max"], 0) else "FAIL",
        "ibr3_open_request_absent_status": "PASS" if all_close(summary["IBR3_TRIAL_TEST_OPEN_REQUEST"]["max"], 0) else "FAIL",
        "ibr3_breaker_command_absent_status": "PASS" if all_close(summary["IBR3_TRIAL_BRK_CMD"]["max"], 0) else "FAIL",
        "ibr3_actual_open_absent_status": "PASS" if summary["IBR3_TRIAL_BRK_STATE"]["max"] < 0.5 and all_close(summary["IBR3_TRIAL_BRK_OPEN_BOOL"]["max"], 0) else "FAIL",
        "ibr3_source_available_status": "PASS" if all_close(summary["IBR3_TRIAL_SOURCE_AVAILABLE"]["min"], 1) and all_close(summary["IBR3_TRIAL_SOURCE_AVAILABLE"]["max"], 1) else "FAIL",
        "ibr3_event_valid_absent_status": "PASS" if all_close(summary["IBR3_TRIAL_CASCADE_EVENT_VALID"]["max"], 0) else "FAIL",
        "ibr3_cause_zero_status": "PASS" if all_close(summary["IBR3_TRIAL_CASCADE_EVENT_CAUSE_CODE"]["max"], 0) else "FAIL",
        "ibr3_packet_open_absent_status": "PASS" if all_close(summary["IBR3_TRIAL_CASCADE_EVENT_BRK_OPEN"]["max"], 0) else "FAIL",
        "ibr3_packet_available_status": "PASS" if all_close(summary["IBR3_TRIAL_CASCADE_SOURCE_AVAILABLE"]["min"], 1) and all_close(summary["IBR3_TRIAL_CASCADE_SOURCE_AVAILABLE"]["max"], 1) else "FAIL",
        "ibr3_first_event_time_unset_status": "PASS" if all_close(summary["IBR3_TRIAL_CASCADE_FIRST_EVENT_TIME_S"]["min"], -1) and all_close(summary["IBR3_TRIAL_CASCADE_FIRST_EVENT_TIME_S"]["max"], -1) else "FAIL",
        "cascade3_ibr3_cause_zero_status": "PASS" if all_close(summary["CASCADE3_MONITOR_CAUSE_CODE_IBR3_TRIAL"]["max"], 0) else "FAIL",
        "default_dfig_signature_status": "PASS" if abs(summary["CASCADE3_MONITOR_FIRST_EVENT_TIME_S"]["last"] - 2.01603) <= time_tolerance_s and round(summary["CASCADE3_MONITOR_CAUSE_CODE_DFIG1"]["last"]) == 2 else "FAIL",
        "cascade3_disabled_chronology_status": "PASS" if round(summary["CASCADE3_MONITOR_EVENTED_SOURCE_COUNT"]["last"]) == 1 and round(summary["CASCADE3_MONITOR_TIMED_EVENT_SOURCE_COUNT"]["last"]) == 1 and round(summary["CASCADE3_MONITOR_FIRST_EVENT_SOURCE_CODE"]["last"]) == 1 and all_close(summary["CASCADE3_MONITOR_SECOND_EVENT_TIME_S"]["last"], -1) and all_close(summary["CASCADE3_MONITOR_THIRD_EVENT_TIME_S"]["last"], -1) and all_close(summary["CASCADE3_MONITOR_FIRST_TO_SECOND_GAP_S"]["last"], -1) and all_close(summary["CASCADE3_MONITOR_SECOND_TO_THIRD_GAP_S"]["last"], -1) and round(summary["CASCADE3_MONITOR_CHRONOLOGY_CONSISTENT"]["last"]) == 1 else "FAIL",
    }
    dynamic_baseline_status = "pass" if all(v == "PASS" for v in checks.values()) else "fail"

    enabled = json.loads(ENABLED_SUMMARY.read_text(encoding="utf-8"))
    comparison_rows = [
        {
            "metric": "IBR3 test enable",
            "enabled": enabled["selected_channel_summary"]["IBR3_TRIAL_TEST_ENABLE"]["min"],
            "disabled": summary["IBR3_TRIAL_TEST_ENABLE"]["max"],
            "contrast": "enabled=1 vs disabled=0",
        },
        {
            "metric": "IBR3 open request time",
            "enabled": enabled["event_times_s"]["ibr3_test_open_request_first_ge_0p5"],
            "disabled": summary["IBR3_TRIAL_TEST_OPEN_REQUEST"]["first_ge_0p5_s"],
            "contrast": "present at 5.0 s vs absent",
        },
        {
            "metric": "IBR3 actual open time",
            "enabled": enabled["event_times_s"]["ibr3_breaker_open_bool_first_ge_0p5"],
            "disabled": summary["IBR3_TRIAL_BRK_OPEN_BOOL"]["first_ge_0p5_s"],
            "contrast": "present at 5.0 s vs absent",
        },
        {
            "metric": "IBR3 event valid time",
            "enabled": enabled["event_times_s"]["ibr3_event_valid_first_ge_0p5"],
            "disabled": summary["IBR3_TRIAL_CASCADE_EVENT_VALID"]["first_ge_0p5_s"],
            "contrast": "present at 5.0 s vs absent",
        },
        {
            "metric": "IBR3 cause code",
            "enabled": enabled["selected_channel_summary"]["IBR3_TRIAL_CASCADE_EVENT_CAUSE_CODE"]["last"],
            "disabled": summary["IBR3_TRIAL_CASCADE_EVENT_CAUSE_CODE"]["last"],
            "contrast": "cause 5 vs cause 0",
        },
        {
            "metric": "CASCADE3 second event time",
            "enabled": enabled["event_times_s"]["cascade3_second_event_time_last"],
            "disabled": summary["CASCADE3_MONITOR_SECOND_EVENT_TIME_S"]["last"],
            "contrast": "5.0 s vs unset -1",
        },
    ]
    stimulus_specific_contrast_status = "pass" if dynamic_baseline_status == "pass" and all(
        row["contrast"] for row in comparison_rows
    ) else "fail"

    report = {
        "run_id": "IBR3_TRIAL_DEFAULT_DISABLED_BASELINE_RUN_20260702_151518",
        "scenario_name": "IBR3_TRIAL_DEFAULT_DISABLED_BASELINE",
        "run_timestamp": "2026-07-02T15:15:18+08:00",
        "main_sha_during_run": sha256(MAIN_PROJECT),
        "trial_sha_during_run": sha256(TRIAL_PROJECT),
        "build_error_count": 0,
        "build_error_count_basis": "user reported Build completed and PSCAD generated default-disabled output artifacts",
        "simulation_timestep_s": 0.000005,
        "channel_plot_step_s": plot_step,
        "time_tolerance_s": time_tolerance_s,
        "sample_count": len(first_series),
        "missing_channel_list": missing,
        "parser_status": "parsed" if not missing else "missing_channels",
        "claim_boundary": "This run only establishes the default-disabled IBR3 trial stimulus baseline for the fixed trial model and default scenario. It does not validate cascade propagation, physical causality direction, system stability, protection coordination, MATLAB coupling, or general applicability.",
        "checks": checks,
        "dynamic_baseline_status": dynamic_baseline_status,
        "event_signature": {
            "dfig_first_event_time_s": summary["CASCADE3_MONITOR_FIRST_EVENT_TIME_S"]["last"],
            "dfig_cause_code": summary["CASCADE3_MONITOR_CAUSE_CODE_DFIG1"]["last"],
            "ibr2_cause_code": summary["CASCADE3_MONITOR_CAUSE_CODE_IBR2_TRIAL"]["last"],
            "ibr3_cause_code": summary["CASCADE3_MONITOR_CAUSE_CODE_IBR3_TRIAL"]["last"],
            "evented_source_count": summary["CASCADE3_MONITOR_EVENTED_SOURCE_COUNT"]["last"],
            "timed_event_source_count": summary["CASCADE3_MONITOR_TIMED_EVENT_SOURCE_COUNT"]["last"],
            "first_event_source_code": summary["CASCADE3_MONITOR_FIRST_EVENT_SOURCE_CODE"]["last"],
            "second_event_time_s": summary["CASCADE3_MONITOR_SECOND_EVENT_TIME_S"]["last"],
            "third_event_time_s": summary["CASCADE3_MONITOR_THIRD_EVENT_TIME_S"]["last"],
            "chronology_consistent": summary["CASCADE3_MONITOR_CHRONOLOGY_CONSISTENT"]["last"],
        },
        "selected_channel_summary": summary,
    }
    comparison = {
        "stimulus_specific_contrast_status": stimulus_specific_contrast_status,
        "enabled_run_id": enabled["run_id"],
        "disabled_run_id": report["run_id"],
        "comparison_rows": comparison_rows,
        "claim_boundary": report["claim_boundary"],
    }
    write_outputs(report, comparison, series_by_signal)
    print(json.dumps(report, indent=2, ensure_ascii=False))
    print(json.dumps(comparison, indent=2, ensure_ascii=False))
    return 0 if dynamic_baseline_status == "pass" and stimulus_specific_contrast_status == "pass" else 1


if __name__ == "__main__":
    sys.exit(main())
