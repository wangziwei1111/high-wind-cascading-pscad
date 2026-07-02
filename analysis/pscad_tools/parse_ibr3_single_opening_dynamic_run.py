#!/usr/bin/env python3
"""Parse the one manual IBR3 single-opening PSCAD run.

The parser reads PSCAD 4.6 Output Channel files:
  - 3IBR_DFIG1_TRIAL.inf for PGB number -> signal name
  - 3IBR_DFIG1_TRIAL_NN.out for time-series values, 10 PGBs per file

It emits JSON only; it does not edit/build/run PSCAD projects.
"""

from __future__ import annotations

import json
import csv
import hashlib
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
SUMMARY_JSON = DATA_DIR / "ibr3_trial_single_opening_run_summary.json"
CHANNELS_CSV = DATA_DIR / "ibr3_trial_single_opening_run_channels.csv"
METRICS_CSV = DATA_DIR / "ibr3_trial_single_opening_run_metrics.csv"

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
    text = INF.read_text(encoding="utf-8", errors="ignore")
    mapping: dict[str, int] = {}
    for line in text.splitlines():
        m = re.search(r"PGB\((\d+)\).*?Desc=\"([^\"]+)\"", line)
        if not m:
            continue
        mapping[m.group(2)] = int(m.group(1))
    return mapping


def file_and_col(pgb: int) -> tuple[Path, int]:
    # PSCAD 4.6 writes 10 Output Channels per .out file.  Column 0 is time,
    # data columns 1..10 are the PGBs for that file.
    file_index = (pgb - 1) // 10 + 1
    data_col = (pgb - 1) % 10 + 1
    return RESULT_DIR / f"{OUT_PREFIX}_{file_index:02d}.out", data_col


def read_channel(pgb: int) -> list[tuple[float, float]]:
    path, col = file_and_col(pgb)
    if not path.exists():
        raise FileNotFoundError(path)
    series: list[tuple[float, float]] = []
    for raw in path.read_text(encoding="utf-8", errors="ignore").splitlines():
        parts = raw.split()
        if not parts:
            continue
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


def first_change(series: list[tuple[float, float]], initial: float | None = None, eps: float = 1e-6) -> float | None:
    if not series:
        return None
    base = series[0][1] if initial is None else initial
    for t, v in series:
        if abs(v - base) > eps:
            return t
    return None


def minmax_last(series: list[tuple[float, float]]) -> dict[str, float | None]:
    if not series:
        return {"min": None, "max": None, "first": None, "last": None}
    vals = [v for _, v in series]
    return {"min": min(vals), "max": max(vals), "first": vals[0], "last": vals[-1]}


def near(value: float | None, target: float, tol: float) -> bool:
    return value is not None and math.isfinite(value) and abs(value - target) <= tol


def write_outputs(report: dict, all_series: dict[str, list[tuple[float, float]]]) -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    SUMMARY_JSON.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    # Wide time-series CSV.  The PSCAD output channels all share the same
    # Channel Plot Step in this run; align by row index to preserve exact samples.
    first_signal = next(iter(all_series))
    times = [t for t, _ in all_series[first_signal]]
    with CHANNELS_CSV.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.writer(fh)
        writer.writerow(["time_s", *all_series.keys()])
        for i, t in enumerate(times):
            row = [t]
            for sig, series in all_series.items():
                row.append(series[i][1] if i < len(series) else "")
            writer.writerow(row)

    with METRICS_CSV.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.writer(fh)
        writer.writerow(["metric", "value"])
        for key, value in report["checks"].items():
            writer.writerow([key, value])
        for key, value in report["event_times_s"].items():
            writer.writerow([key, value])
        writer.writerow(["dynamic_run_status", report["dynamic_run_status"]])
        writer.writerow(["classification", report["classification"]])


def main() -> int:
    mapping = parse_inf()
    missing = [s for s in SIGNALS if s not in mapping]
    channels = {}
    summary = {}
    all_series: dict[str, list[tuple[float, float]]] = {}
    for sig in SIGNALS:
        if sig not in mapping:
            continue
        series = read_channel(mapping[sig])
        all_series[sig] = series
        channels[sig] = {
            "pgb": mapping[sig],
            "file": str(file_and_col(mapping[sig])[0]),
            "data_column": file_and_col(mapping[sig])[1],
            "points": len(series),
            **minmax_last(series),
            "first_ge_0p5_s": first_crossing(series, 0.5),
            "first_change_s": first_change(series),
        }
        summary[sig] = channels[sig]

    # Focused result checks.  Keep tolerances aligned with 0.01 s channel plot step.
    checks = {}
    checks["parser_mapping_status"] = "PASS" if not missing else "FAIL"
    checks["ibr2_test_enable_zero_status"] = (
        "PASS" if channels.get("IBR2_TRIAL_TEST_ENABLE", {}).get("max") is not None
        and abs(channels["IBR2_TRIAL_TEST_ENABLE"]["max"]) <= 1e-9
        and abs(channels["IBR2_TRIAL_TEST_ENABLE"]["min"]) <= 1e-9
        else "FAIL"
    )
    checks["ibr3_test_enable_high_status"] = (
        "PASS" if channels.get("IBR3_TRIAL_TEST_ENABLE", {}).get("min") is not None
        and channels["IBR3_TRIAL_TEST_ENABLE"]["min"] >= 0.5
        else "FAIL"
    )
    req_t = channels.get("IBR3_TRIAL_TEST_OPEN_REQUEST", {}).get("first_ge_0p5_s")
    brk_t = channels.get("IBR3_TRIAL_BRK_OPEN_BOOL", {}).get("first_ge_0p5_s")
    evt_t = channels.get("IBR3_TRIAL_CASCADE_EVENT_VALID", {}).get("first_ge_0p5_s")
    checks["ibr3_open_request_at_5s_status"] = "PASS" if near(req_t, 5.0, 0.011) else "FAIL"
    checks["ibr3_breaker_open_observed_status"] = "PASS" if brk_t is not None else "FAIL"
    checks["ibr3_event_packet_valid_status"] = "PASS" if evt_t is not None else "FAIL"
    checks["ibr3_cause_code_status"] = (
        "PASS" if round(channels.get("IBR3_TRIAL_CASCADE_EVENT_CAUSE_CODE", {}).get("last", -999)) == 5 else "FAIL"
    )
    checks["cascade3_ibr3_cause_code_status"] = (
        "PASS" if round(channels.get("CASCADE3_MONITOR_CAUSE_CODE_IBR3_TRIAL", {}).get("last", -999)) == 5 else "FAIL"
    )
    checks["cascade3_chronology_consistent_status"] = (
        "PASS" if round(channels.get("CASCADE3_MONITOR_CHRONOLOGY_CONSISTENT", {}).get("last", -999)) == 1 else "FAIL"
    )

    # PASS only if the direct IBR3 dynamic path and CASCADE3 bookkeeping all
    # observed the intended event.  Otherwise, classify the single run narrowly.
    core = [
        "parser_mapping_status",
        "ibr2_test_enable_zero_status",
        "ibr3_test_enable_high_status",
        "ibr3_open_request_at_5s_status",
        "ibr3_breaker_open_observed_status",
        "ibr3_event_packet_valid_status",
        "ibr3_cause_code_status",
        "cascade3_ibr3_cause_code_status",
        "cascade3_chronology_consistent_status",
    ]
    classification = "PASS" if all(checks[k] == "PASS" for k in core) else "FAIL"
    if checks["parser_mapping_status"] != "PASS":
        classification = "INCONCLUSIVE"

    report = {
        "run_id": "IBR3_TRIAL_SINGLE_OPENING_DYNAMIC_RUN_20260702_114837",
        "scenario_name": "IBR3_TRIAL_SINGLE_OPENING_DEFAULT_SCENARIO",
        "run_timestamp": "2026-07-02T11:48:37+08:00",
        "trial_sha_during_run": "B9F8CCE9B6C43F57644DF4693D0D651815FB6DBCC2706F9D48A0882DEA705E42",
        "trial_sha_at_parse_time": sha256(TRIAL_PROJECT),
        "main_sha_during_run": sha256(MAIN_PROJECT),
        "build_error_count": 0,
        "build_error_count_basis": "user reported Build completed before the single Run; output artifacts were generated",
        "run_completion_status": "completed_output_files_generated",
        "parser_status": "parsed" if not missing else "missing_channels",
        "claim_boundary": "This result only validates one IBR3_TRIAL trial-only local-opening run under the existing fixed model, default fault, and run settings. It does not validate cascade propagation, physical causality direction, system stability, protection coordination, or MATLAB coupling.",
        "result_directory": str(RESULT_DIR),
        "inf": str(INF),
        "missing_signals": missing,
        "simulation_start_time_s": min(t for t, _ in next(iter(all_series.values()))) if all_series else None,
        "simulation_end_time_s": max(t for t, _ in next(iter(all_series.values()))) if all_series else None,
        "simulation_timestep_s": 0.000005,
        "channel_plot_step_s": (
            statistics.median(
                b[0] - a[0]
                for a, b in zip(next(iter(all_series.values())), next(iter(all_series.values()))[1:])
            )
            if all_series and len(next(iter(all_series.values()))) > 1
            else None
        ),
        "sample_count": len(next(iter(all_series.values()))) if all_series else 0,
        "channel_parse_status": "PASS" if not missing else "FAIL",
        "checks": checks,
        "classification": classification,
        "dynamic_run_status": classification.lower(),
        "event_times_s": {
            "ibr3_test_open_request_first_ge_0p5": req_t,
            "ibr3_breaker_open_bool_first_ge_0p5": brk_t,
            "ibr3_event_valid_first_ge_0p5": evt_t,
            "cascade3_first_event_time_last": channels.get("CASCADE3_MONITOR_FIRST_EVENT_TIME_S", {}).get("last"),
            "cascade3_second_event_time_last": channels.get("CASCADE3_MONITOR_SECOND_EVENT_TIME_S", {}).get("last"),
            "cascade3_third_event_time_last": channels.get("CASCADE3_MONITOR_THIRD_EVENT_TIME_S", {}).get("last"),
        },
        "selected_channel_summary": summary,
    }
    write_outputs(report, all_series)
    print(json.dumps(report, indent=2, ensure_ascii=False))
    return 0 if classification == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
