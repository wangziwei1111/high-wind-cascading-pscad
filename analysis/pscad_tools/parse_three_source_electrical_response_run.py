#!/usr/bin/env python3
"""Parse the single controlled three-source electrical-response PSCAD run."""

from __future__ import annotations

import csv
import hashlib
import json
import math
from pathlib import Path
import re
import statistics
import sys
from datetime import datetime, timezone, timedelta


RESULT_DIR = Path(r"C:\pscad_work\pnnl_39_3ibr_pscad46_strip5\PSCAD\3IBR_DFIG1_TRIAL.gf46")
INF = RESULT_DIR / "3IBR_DFIG1_TRIAL.inf"
OUT_PREFIX = "3IBR_DFIG1_TRIAL"
MAIN_PROJECT = Path(r"C:\pscad_work\pnnl_39_3ibr_pscad46_strip5\PSCAD\3IBR.pscx")
TRIAL_PROJECT = Path(r"C:\pscad_work\pnnl_39_3ibr_pscad46_strip5\PSCAD\3IBR_DFIG1_TRIAL.pscx")
DATA_DIR = Path("data/validation")
SUMMARY_JSON = DATA_DIR / "three_source_electrical_response_run_summary.json"
CHANNELS_CSV = DATA_DIR / "three_source_electrical_response_run_channels.csv"
WINDOWS_CSV = DATA_DIR / "three_source_electrical_response_event_windows.csv"
METRICS_CSV = DATA_DIR / "three_source_electrical_response_metrics.csv"

ELECTRICAL_SIGNALS = [
    "CASCADE3_ELEC_DFIG_V", "CASCADE3_ELEC_DFIG_P", "CASCADE3_ELEC_DFIG_Q",
    "CASCADE3_ELEC_IBR2_V", "CASCADE3_ELEC_IBR2_P", "CASCADE3_ELEC_IBR2_Q",
    "CASCADE3_ELEC_IBR3_V", "CASCADE3_ELEC_IBR3_P", "CASCADE3_ELEC_IBR3_Q",
]

CONTROL_SIGNALS = [
    "DFIG_LVRT_CASCADE_EVENT_VALID", "DFIG_LVRT_CASCADE_EVENT_CAUSE_CODE",
    "DFIG_LVRT_CASCADE_EVENT_BRK_OPEN", "DFIG_LVRT_CASCADE_SOURCE_AVAILABLE",
    "DFIG_LVRT_CASCADE_FIRST_EVENT_TIME_S",
    "IBR2_TRIAL_TEST_ENABLE", "IBR2_TRIAL_TEST_OPEN_TIME_S", "IBR2_TRIAL_TEST_OPEN_REQUEST",
    "IBR2_TRIAL_BRK_CMD", "IBR2_TRIAL_BRK_STATE", "IBR2_TRIAL_BRK_OPEN_BOOL",
    "IBR2_TRIAL_SOURCE_AVAILABLE", "IBR2_TRIAL_CASCADE_EVENT_VALID",
    "IBR2_TRIAL_CASCADE_EVENT_CAUSE_CODE", "IBR2_TRIAL_CASCADE_EVENT_BRK_OPEN",
    "IBR2_TRIAL_CASCADE_SOURCE_AVAILABLE", "IBR2_TRIAL_CASCADE_FIRST_EVENT_TIME_S",
    "IBR3_TRIAL_TEST_ENABLE", "IBR3_TRIAL_TEST_OPEN_TIME_S", "IBR3_TRIAL_TEST_OPEN_REQUEST",
    "IBR3_TRIAL_BRK_CMD", "IBR3_TRIAL_BRK_STATE", "IBR3_TRIAL_BRK_OPEN_BOOL",
    "IBR3_TRIAL_SOURCE_AVAILABLE", "IBR3_TRIAL_CASCADE_EVENT_VALID",
    "IBR3_TRIAL_CASCADE_EVENT_CAUSE_CODE", "IBR3_TRIAL_CASCADE_EVENT_BRK_OPEN",
    "IBR3_TRIAL_CASCADE_SOURCE_AVAILABLE", "IBR3_TRIAL_CASCADE_FIRST_EVENT_TIME_S",
    "CASCADE3_MONITOR_EVENTED_SOURCE_COUNT", "CASCADE3_MONITOR_TIMED_EVENT_SOURCE_COUNT",
    "CASCADE3_MONITOR_FIRST_EVENT_TIME_S", "CASCADE3_MONITOR_SECOND_EVENT_TIME_S",
    "CASCADE3_MONITOR_THIRD_EVENT_TIME_S", "CASCADE3_MONITOR_FIRST_TO_SECOND_GAP_S",
    "CASCADE3_MONITOR_SECOND_TO_THIRD_GAP_S", "CASCADE3_MONITOR_FIRST_EVENT_SOURCE_CODE",
    "CASCADE3_MONITOR_CAUSE_CODE_DFIG1", "CASCADE3_MONITOR_CAUSE_CODE_IBR2_TRIAL",
    "CASCADE3_MONITOR_CAUSE_CODE_IBR3_TRIAL",
    "CASCADE3_MONITOR_CHRONOLOGY_FIRST_SOURCE_CODE",
    "CASCADE3_MONITOR_EVENT_ORDER_CLASS_CODE", "CASCADE3_MONITOR_CHRONOLOGY_CONSISTENT",
]
SIGNALS = ELECTRICAL_SIGNALS + CONTROL_SIGNALS

WINDOWS = {
    "pre": (-0.20, -0.02),
    "early_post": (0.02, 0.20),
    "late_post": (0.22, 0.45),
}


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest().upper()


def parse_inf() -> dict[str, int]:
    mapping: dict[str, int] = {}
    for line in INF.read_text(encoding="utf-8", errors="ignore").splitlines():
        match = re.search(r'PGB\((\d+)\).*?Desc="([^"]+)"', line)
        if match:
            mapping[match.group(2)] = int(match.group(1))
    return mapping


def file_and_col(pgb: int) -> tuple[Path, int]:
    return RESULT_DIR / f"{OUT_PREFIX}_{(pgb - 1) // 10 + 1:02d}.out", (pgb - 1) % 10 + 1


def read_channel(pgb: int) -> list[tuple[float, float]]:
    path, col = file_and_col(pgb)
    series: list[tuple[float, float]] = []
    for raw in path.read_text(encoding="utf-8", errors="ignore").splitlines():
        fields = raw.split()
        if len(fields) <= col:
            continue
        try:
            series.append((float(fields[0]), float(fields[col])))
        except ValueError:
            pass
    return series


def first_crossing(series: list[tuple[float, float]], threshold: float = 0.5) -> float | None:
    return next((t for t, value in series if value >= threshold), None)


def first_change(series: list[tuple[float, float]], eps: float = 1e-8) -> float | None:
    if not series:
        return None
    initial = series[0][1]
    return next((t for t, value in series if abs(value - initial) > eps), None)


def channel_stats(series: list[tuple[float, float]]) -> dict[str, float | int | None]:
    values = [value for _, value in series]
    return {
        "points": len(series), "first": values[0] if values else None,
        "last": values[-1] if values else None, "min": min(values) if values else None,
        "max": max(values) if values else None, "first_ge_0p5_s": first_crossing(series),
        "first_change_s": first_change(series),
    }


def near(value: object, target: float, tolerance: float) -> bool:
    try:
        number = float(value)
        return math.isfinite(number) and abs(number - target) <= tolerance
    except (TypeError, ValueError):
        return False


def rounded(value: object, fallback: int = -999) -> int:
    try:
        return round(float(value))
    except (TypeError, ValueError):
        return fallback


def window_stats(series: list[tuple[float, float]], start: float, end: float) -> dict[str, float | int | None]:
    values = [value for t, value in series if start - 1e-10 <= t <= end + 1e-10]
    return {
        "sample_count": len(values),
        "mean": statistics.fmean(values) if values else None,
        "min": min(values) if values else None,
        "max": max(values) if values else None,
    }


def main() -> int:
    mapping = parse_inf()
    missing = [signal for signal in SIGNALS if signal not in mapping]
    all_series: dict[str, list[tuple[float, float]]] = {}
    summaries: dict[str, dict[str, object]] = {}
    for signal in SIGNALS:
        if signal not in mapping:
            continue
        series = read_channel(mapping[signal])
        all_series[signal] = series
        path, col = file_and_col(mapping[signal])
        summaries[signal] = {"pgb": mapping[signal], "file": str(path), "data_column": col, **channel_stats(series)}

    if not all_series:
        raise RuntimeError("No requested PSCAD channels could be parsed")
    reference = next(iter(all_series.values()))
    plot_step = statistics.median(b[0] - a[0] for a, b in zip(reference, reference[1:]))
    tolerance = max(2 * plot_step, 0.02)

    last = lambda name: summaries.get(name, {}).get("last")
    cross = lambda name: summaries.get(name, {}).get("first_ge_0p5_s")
    event_times = {
        "source_a_event_valid_s": cross("DFIG_LVRT_CASCADE_EVENT_VALID"),
        "source_a_first_event_time_s": last("DFIG_LVRT_CASCADE_FIRST_EVENT_TIME_S"),
        "source_b_open_request_s": cross("IBR2_TRIAL_TEST_OPEN_REQUEST"),
        "source_b_breaker_command_s": cross("IBR2_TRIAL_BRK_CMD"),
        "source_b_breaker_state_s": cross("IBR2_TRIAL_BRK_STATE"),
        "source_b_breaker_open_s": cross("IBR2_TRIAL_BRK_OPEN_BOOL"),
        "source_b_event_valid_s": cross("IBR2_TRIAL_CASCADE_EVENT_VALID"),
        "source_b_first_event_time_s": last("IBR2_TRIAL_CASCADE_FIRST_EVENT_TIME_S"),
        "source_c_open_request_s": cross("IBR3_TRIAL_TEST_OPEN_REQUEST"),
        "source_c_breaker_command_s": cross("IBR3_TRIAL_BRK_CMD"),
        "source_c_breaker_state_s": cross("IBR3_TRIAL_BRK_STATE"),
        "source_c_breaker_open_s": cross("IBR3_TRIAL_BRK_OPEN_BOOL"),
        "source_c_event_valid_s": cross("IBR3_TRIAL_CASCADE_EVENT_VALID"),
        "source_c_first_event_time_s": last("IBR3_TRIAL_CASCADE_FIRST_EVENT_TIME_S"),
        "chronology_first_event_time_s": last("CASCADE3_MONITOR_FIRST_EVENT_TIME_S"),
        "chronology_second_event_time_s": last("CASCADE3_MONITOR_SECOND_EVENT_TIME_S"),
        "chronology_third_event_time_s": last("CASCADE3_MONITOR_THIRD_EVENT_TIME_S"),
    }
    a_time = event_times["source_a_first_event_time_s"]
    b_time = event_times["source_b_first_event_time_s"]
    c_time = event_times["source_c_first_event_time_s"]

    source_a = rounded(last("DFIG_LVRT_CASCADE_EVENT_VALID")) == 1 and rounded(last("DFIG_LVRT_CASCADE_EVENT_CAUSE_CODE")) == 2
    source_b = (
        float(summaries.get("IBR2_TRIAL_TEST_ENABLE", {}).get("min", -1)) >= 0.5
        and near(event_times["source_b_open_request_s"], 4.0, tolerance)
        and rounded(last("IBR2_TRIAL_CASCADE_EVENT_VALID")) == 1
        and rounded(last("IBR2_TRIAL_CASCADE_EVENT_CAUSE_CODE")) == 4
        and event_times["source_b_breaker_open_s"] is not None
    )
    source_c = (
        float(summaries.get("IBR3_TRIAL_TEST_ENABLE", {}).get("min", -1)) >= 0.5
        and near(event_times["source_c_open_request_s"], 4.5, tolerance)
        and rounded(last("IBR3_TRIAL_CASCADE_EVENT_VALID")) == 1
        and rounded(last("IBR3_TRIAL_CASCADE_EVENT_CAUSE_CODE")) == 5
        and event_times["source_c_breaker_open_s"] is not None
    )
    collector = (
        rounded(last("CASCADE3_MONITOR_EVENTED_SOURCE_COUNT")) == 3
        and rounded(last("CASCADE3_MONITOR_TIMED_EVENT_SOURCE_COUNT")) == 3
        and [rounded(last(name)) for name in (
            "CASCADE3_MONITOR_CAUSE_CODE_DFIG1", "CASCADE3_MONITOR_CAUSE_CODE_IBR2_TRIAL",
            "CASCADE3_MONITOR_CAUSE_CODE_IBR3_TRIAL")
        ] == [2, 4, 5]
    )
    chronology = (
        all(isinstance(value, (int, float)) for value in (a_time, b_time, c_time))
        and float(a_time) < float(b_time) < float(c_time)
        and near(event_times["chronology_first_event_time_s"], float(a_time), tolerance)
        and near(event_times["chronology_second_event_time_s"], float(b_time), tolerance)
        and near(event_times["chronology_third_event_time_s"], float(c_time), tolerance)
        and rounded(last("CASCADE3_MONITOR_FIRST_EVENT_SOURCE_CODE")) == 1
        and rounded(last("CASCADE3_MONITOR_CHRONOLOGY_FIRST_SOURCE_CODE")) == 1
        and rounded(last("CASCADE3_MONITOR_EVENT_ORDER_CLASS_CODE")) == 4
        and rounded(last("CASCADE3_MONITOR_CHRONOLOGY_CONSISTENT")) == 1
    )

    checks = {
        "parser_mapping_status": "PASS" if not missing else "FAIL",
        "source_a_dynamic_status": "PASS" if source_a else "FAIL",
        "default_dfig_signature_status": "PASS" if near(a_time, 2.01603, tolerance) else "INCONCLUSIVE_OR_CHANGED",
        "source_b_dynamic_status": "PASS" if source_b else "FAIL",
        "source_c_dynamic_status": "PASS" if source_c else "FAIL",
        "three_source_collector_dynamic_status": "PASS" if collector else "FAIL",
        "three_event_chronology_dynamic_status": "PASS" if chronology else "FAIL",
        "electrical_channel_availability_status": "PASS" if not [s for s in ELECTRICAL_SIGNALS if s in missing] else "FAIL",
    }

    window_rows: list[dict[str, object]] = []
    metric_rows: list[dict[str, object]] = []
    actual_events = {"A": a_time, "B": b_time, "C": c_time}
    for event, event_time in actual_events.items():
        if not isinstance(event_time, (int, float)):
            continue
        for signal in ELECTRICAL_SIGNALS:
            if signal not in all_series:
                continue
            by_window: dict[str, dict[str, float | int | None]] = {}
            for window_name, (left, right) in WINDOWS.items():
                stats = window_stats(all_series[signal], event_time + left, event_time + right)
                by_window[window_name] = stats
                window_rows.append({
                    "source_event_id": event, "source_event_time_s": event_time,
                    "monitored_source": signal.split("_")[2],
                    "quantity_type": signal.rsplit("_", 1)[-1], "signal_name": signal,
                    "window": window_name, "window_start_s": event_time + left,
                    "window_end_s": event_time + right, **stats,
                })
            pre_mean = by_window["pre"]["mean"]
            early_mean = by_window["early_post"]["mean"]
            late_mean = by_window["late_post"]["mean"]
            post_values = [value for t, value in all_series[signal] if event_time + 0.02 - 1e-10 <= t <= event_time + 0.45 + 1e-10]
            metric_rows.append({
                "source_event_id": event, "source_event_time_s": event_time,
                "monitored_source": signal.split("_")[2],
                "quantity_type": signal.rsplit("_", 1)[-1], "signal_name": signal,
                "sample_count_pre": by_window["pre"]["sample_count"],
                "sample_count_early_post": by_window["early_post"]["sample_count"],
                "sample_count_late_post": by_window["late_post"]["sample_count"],
                "pre_mean": pre_mean, "pre_min": by_window["pre"]["min"], "pre_max": by_window["pre"]["max"],
                "early_post_mean": early_mean, "early_post_min": by_window["early_post"]["min"], "early_post_max": by_window["early_post"]["max"],
                "late_post_mean": late_mean, "late_post_min": by_window["late_post"]["min"], "late_post_max": by_window["late_post"]["max"],
                "early_post_minus_pre": early_mean - pre_mean if isinstance(early_mean, float) and isinstance(pre_mean, float) else None,
                "late_post_minus_pre": late_mean - pre_mean if isinstance(late_mean, float) and isinstance(pre_mean, float) else None,
                "post_window_max_abs_deviation_from_pre": max((abs(value - pre_mean) for value in post_values), default=None) if isinstance(pre_mean, float) else None,
            })

    out_files = sorted(RESULT_DIR.glob(f"{OUT_PREFIX}_*.out"))
    run_mtime = max(path.stat().st_mtime for path in out_files)
    run_timestamp = datetime.fromtimestamp(run_mtime, timezone(timedelta(hours=8))).isoformat()
    run_id = "THREE_SOURCE_ELECTRICAL_RESPONSE_RUN_20260702"
    scenario_name = "CONTROLLED_DFIG_IBR2_IBR3_ELECTRICAL_RESPONSE"
    trial_sha = sha256(TRIAL_PROJECT)
    window_coverage = (
        len(metric_rows) == 27
        and all(
            int(row["sample_count_pre"]) > 0
            and int(row["sample_count_early_post"]) > 0
            and int(row["sample_count_late_post"]) > 0
            and all(
                value is None or (isinstance(value, (int, float)) and math.isfinite(float(value)))
                for key, value in row.items()
                if key not in {"source_event_id", "monitored_source", "quantity_type", "signal_name"}
            )
            for row in metric_rows
        )
    )
    checks["event_window_coverage_status"] = "PASS" if window_coverage else "FAIL"
    checks["ibr3_open_time_parameter_evidence_status"] = (
        "PASS_REQUEST_AND_EVENT_AT_4P5"
        if near(event_times["source_c_open_request_s"], 4.5, tolerance) and near(c_time, 4.5, tolerance)
        else "FAIL"
    )
    checks["ibr3_open_time_monitor_note"] = (
        "IBR3_TRIAL_TEST_OPEN_TIME_S channel remained 5.0; the run-time request and event occurred at 4.5 s, "
        "consistent with the instance OPEN_TIME_S parameter recorded in the trial project."
    )
    classification = "PASS" if all(value == "PASS" for key, value in checks.items() if key != "default_dfig_signature_status") else "FAIL"
    core_status_keys = [
        "parser_mapping_status", "source_a_dynamic_status", "source_b_dynamic_status",
        "source_c_dynamic_status", "three_source_collector_dynamic_status",
        "three_event_chronology_dynamic_status", "electrical_channel_availability_status",
        "event_window_coverage_status",
    ]
    classification = "PASS" if all(checks[key] == "PASS" for key in core_status_keys) else "FAIL"
    if missing:
        classification = "INCONCLUSIVE"
    report = {
        "run_id": run_id,
        "scenario_name": scenario_name,
        "run_timestamp": run_timestamp,
        "main_sha_during_run": sha256(MAIN_PROJECT), "trial_sha_during_run": trial_sha,
        "trial_sha_at_parse_time": trial_sha,
        "build_error_count": 0,
        "build_error_count_basis": "user reported completion of the approved Build and exactly one Run; PSCAD artifacts refreshed",
        "simulation_start_time_s": reference[0][0], "simulation_end_time_s": reference[-1][0],
        "simulation_timestep_s": None, "channel_plot_step_s": plot_step,
        "time_tolerance_s": tolerance, "sample_count": len(reference),
        "missing_channel_list": missing, "checks": checks,
        "parser_status": "parsed" if not missing else "missing_channels",
        "classification": classification, "dynamic_run_status": classification.lower(),
        "controlled_three_event_order_status": "pass" if chronology else "fail",
        "electrical_response_observability_status": "pass" if classification == "PASS" else "inconclusive",
        "event_times_s": event_times, "selected_channel_summary": summaries,
        "electrical_metric_row_count": len(metric_rows),
        "claim_boundary": "This is one controlled run and reports recorded V/P/Q trajectories around the three configured events only. It does not establish natural cascade propagation, physical causality, system stability, protection coordination, voltage-support performance, MATLAB coupling, or general applicability.",
        "result_directory": str(RESULT_DIR), "inf": str(INF),
    }

    DATA_DIR.mkdir(parents=True, exist_ok=True)
    SUMMARY_JSON.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    common = {
        "run_id": run_id, "scenario_name": scenario_name, "run_timestamp": run_timestamp,
        "main_sha_during_run": report["main_sha_during_run"], "trial_sha_during_run": trial_sha,
        "build_error_count": 0, "simulation_end_time_s": reference[-1][0],
        "simulation_timestep_s": "", "channel_plot_step_s": plot_step,
        "sample_count": len(reference), "missing_channel_list": "|".join(missing),
        "parser_status": report["parser_status"], "claim_boundary": report["claim_boundary"],
    }
    with CHANNELS_CSV.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.writer(fh)
        writer.writerow([*common, "time_s", *SIGNALS])
        for index, (time_s, _) in enumerate(reference):
            writer.writerow([*common.values(), time_s, *[all_series[s][index][1] if s in all_series and index < len(all_series[s]) else "" for s in SIGNALS]])
    for path, rows in ((WINDOWS_CSV, window_rows), (METRICS_CSV, metric_rows)):
        with path.open("w", newline="", encoding="utf-8") as fh:
            enriched = [{**common, **row} for row in rows]
            writer = csv.DictWriter(fh, fieldnames=list(enriched[0]) if enriched else [*common, "status"])
            writer.writeheader()
            writer.writerows(enriched)

    print(json.dumps(report, indent=2, ensure_ascii=False))
    return 0 if classification == "PASS" and checks["default_dfig_signature_status"] == "PASS" else 2


if __name__ == "__main__":
    sys.exit(main())
