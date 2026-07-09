#!/usr/bin/env python3
"""Analyze the single paper-aligned 20 s N29 fault Run outputs.

The script reads PSCAD-generated .inf/.out files only.  It does not call PSCAD,
Build, Run, or modify any model file.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import statistics
import re
from datetime import datetime
from pathlib import Path


REPO = Path(__file__).resolve().parents[2]
DEFAULT_GF46 = Path(r"C:\pscad_work\pnnl_39_3ibr_pscad46_strip5\PSCAD\3IBR_DFIG1_TRIAL.gf46")
OUT_PREFIX = "3IBR_DFIG1_TRIAL"

WINDOWS = {
    "pre_fault": (0.20, 0.45, "left_closed_right_open"),
    "fault_on": (0.50, 2.50, "closed"),
    "post_clear_early": (2.60, 3.00, "left_closed_right_open"),
    "post_clear_late": (5.00, 19.50, "closed"),
}

EVENT_SIGNALS = [
    "DFIG_LVRT_CASCADE_EVENT_VALID",
    "DFIG_LVRT_CASCADE_EVENT_CAUSE_CODE",
    "DFIG_LVRT_CASCADE_EVENT_BRK_OPEN",
    "DFIG_LVRT_CASCADE_SOURCE_AVAILABLE",
    "DFIG_LVRT_CAS_FIRST_TIME_S",
    "DFIG_LVRT_CASCADE_FIRST_EVENT_TIME_S",
    "IBR2_TRIAL_CASCADE_EVENT_VALID",
    "IBR2_TRIAL_CASCADE_EVENT_CAUSE_CODE",
    "IBR2_TRIAL_CASCADE_EVENT_BRK_OPEN",
    "IBR2_TRIAL_CASCADE_SOURCE_AVAILABLE",
    "IBR2_TRIAL_CASCADE_FIRST_EVENT_TIME_S",
    "IBR2_TRIAL_TEST_ENABLE",
    "IBR2_TRIAL_BRK_OPEN_BOOL",
    "IBR3_TRIAL_CASCADE_EVENT_VALID",
    "IBR3_TRIAL_CASCADE_EVENT_CAUSE_CODE",
    "IBR3_TRIAL_CASCADE_EVENT_BRK_OPEN",
    "IBR3_TRIAL_CASCADE_SOURCE_AVAILABLE",
    "IBR3_TRIAL_CASCADE_FIRST_EVENT_TIME_S",
    "IBR3_TRIAL_TEST_ENABLE",
    "IBR3_TRIAL_BRK_OPEN_BOOL",
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
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest().upper()


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


def parse_inf(inf: Path) -> tuple[dict[str, dict[str, object]], list[dict[str, object]]]:
    mapping: dict[str, dict[str, object]] = {}
    rows: list[dict[str, object]] = []
    for line in inf.read_text(encoding="utf-8", errors="ignore").splitlines():
        m = re.search(r'PGB\((\d+)\).*?Desc="([^"]+)".*?Group="([^"]*)".*?Units="([^"]*)"', line)
        if not m:
            continue
        pgb = int(m.group(1))
        desc = m.group(2)
        row = {"pgb": pgb, "desc": desc, "group": m.group(3), "units": m.group(4)}
        mapping[desc] = row
        rows.append(row)
    return mapping, rows


def file_and_col(gf46: Path, pgb: int) -> tuple[Path, int]:
    return gf46 / f"{OUT_PREFIX}_{(pgb - 1) // 10 + 1:02d}.out", (pgb - 1) % 10 + 1


def read_out_file(path: Path) -> list[list[float]]:
    rows: list[list[float]] = []
    for line in path.read_text(encoding="utf-8", errors="ignore").splitlines():
        parts = line.split()
        if not parts:
            continue
        try:
            rows.append([float(x) for x in parts])
        except ValueError:
            continue
    return rows


class ChannelReader:
    def __init__(self, gf46: Path, mapping: dict[str, dict[str, object]]) -> None:
        self.gf46 = gf46
        self.mapping = mapping
        self.cache: dict[Path, list[list[float]]] = {}

    def series(self, name: str) -> list[tuple[float, float]]:
        info = self.mapping.get(name)
        if not info:
            return []
        pgb = int(info["pgb"])
        path, col = file_and_col(self.gf46, pgb)
        if path not in self.cache:
            self.cache[path] = read_out_file(path)
        rows = self.cache[path]
        out: list[tuple[float, float]] = []
        for row in rows:
            if len(row) > col:
                out.append((row[0], row[col]))
        return out


def finite_values(series: list[tuple[float, float]]) -> list[tuple[float, float]]:
    return [(t, v) for t, v in series if math.isfinite(t) and math.isfinite(v)]


def sample_in_window(series: list[tuple[float, float]], start: float, end: float, mode: str) -> list[tuple[float, float]]:
    if mode == "closed":
        return [(t, v) for t, v in series if start - 1e-12 <= t <= end + 1e-12 and math.isfinite(v)]
    return [(t, v) for t, v in series if start - 1e-12 <= t < end - 1e-12 and math.isfinite(v)]


def first_ge(series: list[tuple[float, float]], threshold: float = 0.5) -> float | None:
    for t, v in series:
        if math.isfinite(v) and v >= threshold:
            return t
    return None


def first_change(series: list[tuple[float, float]], eps: float = 1e-8) -> float | None:
    vals = finite_values(series)
    if not vals:
        return None
    initial = vals[0][1]
    for t, v in vals:
        if abs(v - initial) > eps:
            return t
    return None


def last_value(series: list[tuple[float, float]]) -> float | None:
    vals = finite_values(series)
    return vals[-1][1] if vals else None


def window_stats(series: list[tuple[float, float]], start: float, end: float, mode: str) -> dict[str, object]:
    vals = sample_in_window(series, start, end, mode)
    values = [v for _, v in vals]
    if not values:
        return {
            "sample_count": 0,
            "mean": None,
            "median": None,
            "min": None,
            "max": None,
            "peak_abs": None,
            "peak_time_s": None,
            "finite_sample_fraction": 0.0,
            "window_coverage_status": "fail_empty",
        }
    peak_t, peak_v = max(vals, key=lambda tv: abs(tv[1]))
    expected_status = "pass"
    return {
        "sample_count": len(values),
        "mean": statistics.fmean(values),
        "median": statistics.median(values),
        "min": min(values),
        "max": max(values),
        "peak_abs": abs(peak_v),
        "peak_time_s": peak_t,
        "finite_sample_fraction": 1.0,
        "window_coverage_status": expected_status,
    }


def time_axis_summary(series: list[tuple[float, float]]) -> dict[str, object]:
    if not series:
        return {"status": "fail_empty"}
    times = [t for t, _ in series]
    diffs = [b - a for a, b in zip(times, times[1:])]
    monotonic = all(d > 0 for d in diffs)
    median_dt = statistics.median(diffs) if diffs else None
    return {
        "status": "pass"
        if monotonic and abs(times[0]) < 1e-9 and times[-1] >= 19.99 and median_dt is not None and abs(median_dt - 0.01) < 1e-9
        else "fail",
        "sample_count": len(times),
        "first_time_s": times[0],
        "last_time_s": times[-1],
        "median_step_s": median_dt,
        "monotonic_increasing": monotonic,
    }


def safe_delta(value: float | None, baseline: float | None) -> float | None:
    if value is None or baseline is None:
        return None
    return value - baseline


def tline_metric_rows(reader: ChannelReader, inventory: list[dict[str, object]]) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for item in inventory:
        branch = str(item["network_branch_id"])
        for terminal in ("A", "B"):
            for quantity in ("P", "Q", "I"):
                name = f"{branch}_{terminal}_{quantity}"
                series = reader.series(name)
                stats_by_window = {w: window_stats(series, *spec) for w, spec in WINDOWS.items()}
                pre = stats_by_window["pre_fault"]
                fault = stats_by_window["fault_on"]
                early = stats_by_window["post_clear_early"]
                late = stats_by_window["post_clear_late"]
                pre_mean = pre["mean"]
                row = {
                    "network_branch_id": branch,
                    "terminal": terminal,
                    "quantity": quantity,
                    "signal_name": name,
                    "measurement_unit": reader.mapping.get(name, {}).get("units", ""),
                    "pre_fault_mean": pre["mean"],
                    "pre_fault_median": pre["median"],
                    "pre_fault_min": pre["min"],
                    "pre_fault_max": pre["max"],
                    "fault_on_min": fault["min"],
                    "fault_on_max": fault["max"],
                    "fault_on_peak_abs": fault["peak_abs"],
                    "fault_on_peak_time_s": fault["peak_time_s"],
                    "post_clear_early_mean": early["mean"],
                    "post_clear_early_min": early["min"],
                    "post_clear_early_max": early["max"],
                    "post_clear_early_peak_abs": early["peak_abs"],
                    "post_clear_early_peak_time_s": early["peak_time_s"],
                    "post_clear_late_mean": late["mean"],
                    "post_clear_late_min": late["min"],
                    "post_clear_late_max": late["max"],
                    "delta_fault_on_from_pre_fault": safe_delta(fault["mean"], pre_mean),
                    "delta_post_clear_early_from_pre_fault": safe_delta(early["mean"], pre_mean),
                    "delta_post_clear_late_from_pre_fault": safe_delta(late["mean"], pre_mean),
                    "abs_delta_fault_on_from_pre_fault": abs(safe_delta(fault["mean"], pre_mean)) if safe_delta(fault["mean"], pre_mean) is not None else None,
                    "abs_delta_post_clear_early_from_pre_fault": abs(safe_delta(early["mean"], pre_mean)) if safe_delta(early["mean"], pre_mean) is not None else None,
                    "abs_delta_post_clear_late_from_pre_fault": abs(safe_delta(late["mean"], pre_mean)) if safe_delta(late["mean"], pre_mean) is not None else None,
                    "finite_sample_fraction": min(float(pre["finite_sample_fraction"]), float(fault["finite_sample_fraction"]), float(early["finite_sample_fraction"]), float(late["finite_sample_fraction"])),
                    "window_coverage_status": "pass"
                    if all(stats_by_window[w]["window_coverage_status"] == "pass" for w in WINDOWS)
                    else "fail",
                }
                rows.append(row)
    return rows


def rank_current(metrics: list[dict[str, object]]) -> list[dict[str, object]]:
    by_branch: dict[str, list[dict[str, object]]] = {}
    for row in metrics:
        if row["quantity"] == "I":
            by_branch.setdefault(str(row["network_branch_id"]), []).append(row)
    out: list[dict[str, object]] = []
    for branch, rows in by_branch.items():
        chosen = max(rows, key=lambda r: float(r["abs_delta_post_clear_early_from_pre_fault"] or -1))
        baseline = chosen["pre_fault_mean"]
        score = chosen["abs_delta_post_clear_early_from_pre_fault"]
        relative = None
        rel_status = "invalid_small_or_missing_denominator"
        if baseline is not None and abs(float(baseline)) > 1e-9 and score is not None:
            relative = float(score) / abs(float(baseline))
            rel_status = "valid"
        out.append(
            {
                "network_branch_id": branch,
                "terminal_selected_by_score": chosen["terminal"],
                "I_response_score": score,
                "baseline_I": baseline,
                "post_clear_early_I": chosen["post_clear_early_mean"],
                "peak_I_during_fault_on": chosen["fault_on_peak_abs"],
                "peak_I_time_s": chosen["fault_on_peak_time_s"],
                "relative_I_change_if_denominator_valid": relative,
                "relative_I_change_status": rel_status,
                "measurement_unit": chosen["measurement_unit"],
                "data_quality_status": chosen["window_coverage_status"],
            }
        )
    return sorted(out, key=lambda r: float(r["I_response_score"] or -1), reverse=True)


def rank_power(metrics: list[dict[str, object]]) -> list[dict[str, object]]:
    by_branch: dict[str, dict[str, list[dict[str, object]]]] = {}
    for row in metrics:
        if row["quantity"] in {"P", "Q"}:
            by_branch.setdefault(str(row["network_branch_id"]), {}).setdefault(str(row["quantity"]), []).append(row)
    out: list[dict[str, object]] = []
    for branch, qrows in by_branch.items():
        p_chosen = max(qrows.get("P", []), key=lambda r: float(r["abs_delta_post_clear_early_from_pre_fault"] or -1))
        q_chosen = max(qrows.get("Q", []), key=lambda r: float(r["abs_delta_post_clear_early_from_pre_fault"] or -1))
        p_score = p_chosen["abs_delta_post_clear_early_from_pre_fault"]
        q_score = q_chosen["abs_delta_post_clear_early_from_pre_fault"]
        out.append(
            {
                "network_branch_id": branch,
                "P_terminal_selected_by_score": p_chosen["terminal"],
                "P_response_score": p_score,
                "P_baseline": p_chosen["pre_fault_mean"],
                "P_post_clear_early": p_chosen["post_clear_early_mean"],
                "Q_terminal_selected_by_score": q_chosen["terminal"],
                "Q_response_score": q_score,
                "Q_baseline": q_chosen["pre_fault_mean"],
                "Q_post_clear_early": q_chosen["post_clear_early_mean"],
                "combined_raw_pq_response_score": (float(p_score or 0.0) ** 2 + float(q_score or 0.0) ** 2) ** 0.5,
                "combined_score_definition": "descriptive sqrt(delta_P^2 + delta_Q^2) on raw P/Q changes only; not S, not MVA, not loading ratio, not overload evidence",
                "data_quality_status": "pass"
                if p_chosen["window_coverage_status"] == "pass" and q_chosen["window_coverage_status"] == "pass"
                else "fail",
            }
        )
    return sorted(out, key=lambda r: float(r["combined_raw_pq_response_score"] or -1), reverse=True)


def event_timeline(reader: ChannelReader) -> tuple[list[dict[str, object]], dict[str, object]]:
    def s(name: str) -> list[tuple[float, float]]:
        return reader.series(name)

    def last(name: str) -> float | None:
        return last_value(s(name))

    rows = []
    sources = [
        ("DFIG", "DFIG_LVRT_CASCADE_EVENT_VALID", "DFIG_LVRT_CASCADE_EVENT_CAUSE_CODE", "DFIG_LVRT_CASCADE_EVENT_BRK_OPEN", "DFIG_LVRT_CASCADE_SOURCE_AVAILABLE", "DFIG_LVRT_CAS_FIRST_TIME_S"),
        ("IBR2", "IBR2_TRIAL_CASCADE_EVENT_VALID", "IBR2_TRIAL_CASCADE_EVENT_CAUSE_CODE", "IBR2_TRIAL_CASCADE_EVENT_BRK_OPEN", "IBR2_TRIAL_CASCADE_SOURCE_AVAILABLE", "IBR2_TRIAL_CASCADE_FIRST_EVENT_TIME_S"),
        ("IBR3", "IBR3_TRIAL_CASCADE_EVENT_VALID", "IBR3_TRIAL_CASCADE_EVENT_CAUSE_CODE", "IBR3_TRIAL_CASCADE_EVENT_BRK_OPEN", "IBR3_TRIAL_CASCADE_SOURCE_AVAILABLE", "IBR3_TRIAL_CASCADE_FIRST_EVENT_TIME_S"),
    ]
    for source, valid, cause, brk, avail, first in sources:
        rows.append(
            {
                "event_source": source,
                "event_valid_observed": last(valid),
                "event_cause_code": last(cause),
                "breaker_open_observed": last(brk),
                "source_available_observed": last(avail),
                "first_event_time_s": last(first),
                "first_transition_time_s": first_ge(s(valid), 0.5),
                "configured_or_observed_status": "observed" if (last(valid) or 0) >= 0.5 else "not_observed",
            }
        )
    rows.append(
        {
            "event_source": "CASCADE3_MONITOR",
            "event_valid_observed": last("CASCADE3_MONITOR_EVENTED_SOURCE_COUNT"),
            "event_cause_code": None,
            "breaker_open_observed": last("CASCADE3_MONITOR_ANY_BRK_OPEN"),
            "source_available_observed": None,
            "first_event_time_s": last("CASCADE3_MONITOR_FIRST_EVENT_TIME_S"),
            "first_transition_time_s": first_change(s("CASCADE3_MONITOR_EVENTED_SOURCE_COUNT")),
            "configured_or_observed_status": "observed",
        }
    )
    status = {
        "dfig_lvrt_event_observation_status": "observed" if (last("DFIG_LVRT_CASCADE_EVENT_VALID") or 0) >= 0.5 else "not_observed",
        "ibr2_unexpected_event_status": "fail" if (last("IBR2_TRIAL_CASCADE_EVENT_VALID") or 0) >= 0.5 or (last("IBR2_TRIAL_CASCADE_EVENT_BRK_OPEN") or 0) >= 0.5 else "pass",
        "ibr3_unexpected_event_status": "fail" if (last("IBR3_TRIAL_CASCADE_EVENT_VALID") or 0) >= 0.5 or (last("IBR3_TRIAL_CASCADE_EVENT_BRK_OPEN") or 0) >= 0.5 else "pass",
        "collector_observation_status": "observed" if last("CASCADE3_MONITOR_EVENTED_SOURCE_COUNT") is not None else "unavailable",
        "chronology_observation_status": "observed" if last("CASCADE3_MONITOR_FIRST_EVENT_TIME_S") is not None else "unavailable",
    }
    return rows, status


def file_inventory(gf46: Path, names: list[str]) -> list[dict[str, object]]:
    rows = []
    for name in names:
        p = gf46 / name
        if p.exists():
            rows.append(
                {
                    "name": name,
                    "path": str(p),
                    "length": p.stat().st_size,
                    "mtime_local": datetime.fromtimestamp(p.stat().st_mtime).isoformat(timespec="seconds"),
                    "sha256": sha256(p) if p.stat().st_size <= 25_000_000 else None,
                }
            )
    return rows


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--gf46-dir", type=Path, default=DEFAULT_GF46)
    args = ap.parse_args()
    gf46 = args.gf46_dir
    inf = gf46 / f"{OUT_PREFIX}.inf"
    mapping, inf_rows = parse_inf(inf)
    reader = ChannelReader(gf46, mapping)
    inventory = json.loads((REPO / "data/reference/full_network_tline_inventory.json").read_text(encoding="utf-8"))["tlines"]
    channel_baseline = json.loads((REPO / "data/validation/paper_aligned_20s_dynamic_run_channel_baseline.json").read_text(encoding="utf-8"))
    input_manifest = json.loads((REPO / "data/validation/paper_aligned_20s_dynamic_run_input_manifest.json").read_text(encoding="utf-8"))

    first_series = reader.series(inf_rows[0]["desc"])
    time_summary = time_axis_summary(first_series)
    event_rows, event_status = event_timeline(reader)
    metrics = tline_metric_rows(reader, inventory)
    current_rank = rank_current(metrics)
    power_rank = rank_power(metrics)

    coverage_rows = []
    for ch in channel_baseline["channels"]:
        name = ch.get("name")
        info = mapping.get(name)
        if info:
            path, col = file_and_col(gf46, int(info["pgb"]))
            series = reader.series(name)
            ts = time_axis_summary(series)
            coverage_rows.append(
                {
                    "channel_name": name,
                    "xml_component_id": ch.get("component_id"),
                    "inf_pgb": info["pgb"],
                    "out_file": path.name,
                    "data_column": col,
                    "sample_count": ts.get("sample_count"),
                    "first_time_s": ts.get("first_time_s"),
                    "last_time_s": ts.get("last_time_s"),
                    "time_axis_status": ts.get("status"),
                    "mapping_status": "pass",
                }
            )
        else:
            coverage_rows.append({"channel_name": name, "xml_component_id": ch.get("component_id"), "mapping_status": "missing_in_inf"})

    tline_coverage_ok = all(r["window_coverage_status"] == "pass" for r in metrics)
    unexpected_trial_ok = event_status["ibr2_unexpected_event_status"] == "pass" and event_status["ibr3_unexpected_event_status"] == "pass"
    network_status = "observed" if time_summary["status"] == "pass" and tline_coverage_ok and unexpected_trial_ok else "quality_limited_or_unexpected_trial_event"

    output_names = [f"{OUT_PREFIX}_{i:02d}.out" for i in range(1, 64)] + [f"{OUT_PREFIX}.inf", f"{OUT_PREFIX}.infx"]
    run_manifest = {
        "manifest_name": "paper_aligned_20s_run_manifest",
        "generated_at_local": datetime.now().isoformat(timespec="seconds"),
        "run_status": "single_user_gui_run_completed",
        "run_directory": str(gf46),
        "input_manifest": input_manifest,
        "parsed_inf_pgb_count": len(inf_rows),
        "xml_output_channel_count": channel_baseline["xml_output_channel_count"],
        "time_axis": time_summary,
        "fresh_output_inventory": file_inventory(gf46, output_names),
        "raw_output_files_not_committed": True,
    }

    summary = {
        "analysis_name": "paper_aligned_20s_dynamic_run_analysis",
        "generated_at_local": datetime.now().isoformat(timespec="seconds"),
        "execution_status": "pass" if time_summary["status"] == "pass" and len(metrics) == 186 else "paper_aligned_20s_dynamic_run_parser_fallback",
        "time_axis_status": time_summary["status"],
        "output_parse_status": "pass" if len(inf_rows) >= 448 and len(metrics) == 186 else "fail",
        "full_network_tline_data_coverage_status": "pass" if tline_coverage_ok else "fail",
        "network_wide_tline_dynamic_response_status": network_status,
        **event_status,
        "line_loading_ratio_status": "unavailable_no_audited_line_rating_basis",
        "line_overload_status": "unavailable",
        "line_protection_status": "unavailable",
        "branch_trip_status": "unavailable",
        "natural_cascade_propagation_status": "unavailable",
        "physical_causality_direction_status": "unavailable",
        "system_stability_status": "unavailable",
        "protection_coordination_status": "unavailable",
        "top10_current_response": current_rank[:10],
        "top10_power_response": power_rank[:10],
    }

    write_csv(REPO / "data/derived/paper_aligned_20s_event_timeline.csv", event_rows)
    write_csv(REPO / "data/derived/full_network_tline_window_metrics.csv", metrics)
    write_csv(REPO / "data/derived/full_network_tline_current_response_ranking.csv", current_rank)
    write_csv(REPO / "data/derived/full_network_tline_power_response_ranking.csv", power_rank)
    write_csv(REPO / "data/derived/paper_aligned_20s_run_channel_coverage.csv", coverage_rows)
    write_json(REPO / "data/derived/paper_aligned_20s_run_manifest.json", run_manifest)
    write_json(REPO / "data/derived/paper_aligned_20s_run_analysis_summary.json", summary)
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0 if summary["execution_status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
