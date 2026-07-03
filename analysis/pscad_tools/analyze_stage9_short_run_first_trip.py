#!/usr/bin/env python3
"""Parse the single Stage-9 9-second PSCAD run and reconstruct the first-trip chain."""

from __future__ import annotations

import csv
import hashlib
import json
import math
import re
from datetime import datetime
from pathlib import Path
from statistics import fmean
from typing import Any


REPO = Path(__file__).resolve().parents[2]
GF46 = Path(r"C:\pscad_work\pnnl_39_3ibr_pscad46_strip5\PSCAD\3IBR_DFIG1_TRIAL.gf46")
MAIN = GF46.parent / "3IBR.pscx"
TRIAL = GF46.parent / "3IBR_DFIG1_TRIAL.pscx"
PREFIX = "3IBR_DFIG1_TRIAL"
PAPER = [
    "PAPER_OVL1_S_A_PU", "PAPER_OVL1_S_B_PU", "PAPER_OVL1_S_MAX_PU",
    "PAPER_OVL1_EFFECTIVE_CAPACITY_PU", "PAPER_OVL1_LOADING_INDEX_EQ",
    "PAPER_OVL1_ABOVE_THRESHOLD", "PAPER_OVL1_TIMER_OR_CURVE_STATE",
    "PAPER_OVL1_TRIP_REQUEST", "PAPER_OVL1_BRK_CMD", "PAPER_OVL1_BRK_STATE",
    "PAPER_OVL1_TRIP_EVENT_VALID", "PAPER_OVL1_FIRST_TRIP_TIME_S", "PAPER_OVL1_RELAY_ENABLE",
]


def sha(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest().upper()


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, obj: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def write_csv(path: Path, rows: list[dict[str, Any]], fields: list[str] | None = None) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if fields is None:
        fields = []
        for row in rows:
            for key in row:
                if key not in fields: fields.append(key)
    with path.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields); w.writeheader(); w.writerows(rows)


def parse_inf(path: Path) -> list[dict[str, Any]]:
    pat = re.compile(r'^PGB\((\d+)\)\s+Output\s+Desc="([^"]*)"\s+Group="([^"]*)".*Units="([^"]*)"')
    rows = []
    for line in path.read_text(encoding="utf-8", errors="ignore").splitlines():
        m = pat.search(line)
        if m: rows.append({"pgb_index": int(m.group(1)), "title": m.group(2), "group": m.group(3), "units": m.group(4)})
    return rows


def load_out(path: Path) -> list[list[float]]:
    rows = []
    for line in path.read_text(encoding="ascii", errors="ignore").splitlines():
        if line.split(): rows.append([float(x) for x in line.split()])
    return rows


def first_time(t: list[float], v: list[float], threshold: float = 0.5) -> float | None:
    return next((x for x, y in zip(t, v) if y > threshold), None)


def mean_window(t: list[float], v: list[float], lo: float, hi: float) -> float | None:
    x = [y for x, y in zip(t, v) if lo <= x <= hi]
    return fmean(x) if x else None


def main() -> None:
    inf_path = GF46 / f"{PREFIX}.inf"
    outs = sorted(GF46.glob(f"{PREFIX}_*.out"))
    inf = parse_inf(inf_path) if inf_path.exists() else []
    by_title: dict[str, list[dict[str, Any]]] = {}
    for row in inf: by_title.setdefault(row["title"], []).append(row)
    cache: dict[int, list[list[float]]] = {}
    first = load_out(outs[0]) if outs else []
    channels_per_file = len(first[0]) - 1 if first else 0
    if first: cache[1] = first

    def series(title: str) -> tuple[list[float], list[float]]:
        matches = by_title.get(title, [])
        if len(matches) != 1 or channels_per_file <= 0: return [], []
        idx = matches[0]["pgb_index"]
        no, col = (idx - 1) // channels_per_file + 1, (idx - 1) % channels_per_file + 1
        if no not in cache:
            path = GF46 / f"{PREFIX}_{no:02d}.out"
            cache[no] = load_out(path) if path.exists() else []
        data = cache[no]
        return [r[0] for r in data], [r[col] for r in data]

    paper_series = {name: series(name) for name in PAPER}
    readable = all(len(v[0]) > 0 for v in paper_series.values())
    t = paper_series[PAPER[0]][0] if readable else []
    same_axis = readable and all(x[0] == t for x in paper_series.values())
    vals = {name: paper_series[name][1] for name in PAPER}
    relay_trace = [{"time_s": x, **{name: vals[name][i] for name in PAPER}} for i, x in enumerate(t)] if same_axis else []

    threshold_t = first_time(t, vals.get("PAPER_OVL1_ABOVE_THRESHOLD", [])) if t else None
    completion_t = first_time(t, vals.get("PAPER_OVL1_TIMER_OR_CURVE_STATE", [])) if t else None
    trip_t = first_time(t, vals.get("PAPER_OVL1_TRIP_REQUEST", [])) if t else None
    cmd_t = first_time(t, vals.get("PAPER_OVL1_BRK_CMD", [])) if t else None
    open_t = first_time(t, vals.get("PAPER_OVL1_BRK_STATE", []), 1.0) if t else None
    dfig_t = None
    dfig_valid_t, dfig_valid = series("DFIG_LVRT_CASCADE_EVENT_VALID")
    if dfig_valid_t: dfig_t = first_time(dfig_valid_t, dfig_valid)
    pre_idx = [i for i, x in enumerate(t) if 0.20 <= x <= 0.45]
    pre_max = max((vals["PAPER_OVL1_LOADING_INDEX_EQ"][i] for i in pre_idx), default=None) if readable else None
    pre_false = any(vals[n][i] > (1.0 if n == "PAPER_OVL1_BRK_STATE" else 0.5)
                    for n in ["PAPER_OVL1_TIMER_OR_CURVE_STATE", "PAPER_OVL1_TRIP_REQUEST", "PAPER_OVL1_BRK_CMD", "PAPER_OVL1_BRK_STATE"]
                    for i in pre_idx) if readable else None
    continuous_to_completion = completion_t - threshold_t if threshold_t is not None and completion_t is not None else None

    timeline = [
        {"event": "fault_start", "time_s": 0.50, "status": "frozen_reference"},
        {"event": "fault_clear", "time_s": 2.50, "status": "frozen_reference"},
        {"event": "dfig_event", "time_s": dfig_t, "status": "observed" if dfig_t is not None else "not_observed"},
        {"event": "threshold_crossing_and_timer_accumulation_start", "time_s": threshold_t, "status": "observed" if threshold_t is not None else "not_observed"},
        {"event": "timer_completion", "time_s": completion_t, "status": "observed" if completion_t is not None else "not_observed"},
        {"event": "trip_request", "time_s": trip_t, "status": "observed" if trip_t is not None else "not_observed"},
        {"event": "breaker_command", "time_s": cmd_t, "status": "observed" if cmd_t is not None else "not_observed"},
        {"event": "actual_breaker_open", "time_s": open_t, "status": "observed" if open_t is not None else "not_observed"},
    ]

    branch_ids = sorted({m.group(1) for r in inf if (m := re.match(r"(E_\d+_\d+_1)_[AB]_[PQI]$", r["title"]))})
    response = []
    if open_t is not None:
        pre_lo, pre_hi = max(0.0, open_t - 0.20), max(0.0, open_t - 0.02)
        early_lo, early_hi = open_t + 0.02, min(9.0, open_t + 0.50)
        late_lo, late_hi = min(9.0, open_t + 0.80), 9.0
        for branch in branch_ids:
            required = [f"{branch}_{end}_{q}" for end in "AB" for q in "PQI"]
            data = {name: series(name) for name in required}
            if not all(data[n][0] for n in required):
                response.append({"network_branch_id": branch, "status": "missing_runtime_channel"}); continue
            bt = data[required[0]][0]
            pa, qa, ia = (data[f"{branch}_A_{x}"][1] for x in "PQI")
            pb, qb, ib = (data[f"{branch}_B_{x}"][1] for x in "PQI")
            pmetric = [max(abs(a), abs(b)) for a, b in zip(pa, pb)]
            qmetric = [max(abs(a), abs(b)) for a, b in zip(qa, qb)]
            imetric = [max(abs(a), abs(b)) for a, b in zip(ia, ib)]
            smetric = [max(math.hypot(a, b), math.hypot(c, d)) for a, b, c, d in zip(pa, qa, pb, qb)]
            pre_p, early_p, late_p = (mean_window(bt, pmetric, *w) for w in [(pre_lo, pre_hi), (early_lo, early_hi), (late_lo, late_hi)])
            pre_q, early_q, late_q = (mean_window(bt, qmetric, *w) for w in [(pre_lo, pre_hi), (early_lo, early_hi), (late_lo, late_hi)])
            pre_i, early_i, late_i = (mean_window(bt, imetric, *w) for w in [(pre_lo, pre_hi), (early_lo, early_hi), (late_lo, late_hi)])
            pre_s, early_s, late_s = (mean_window(bt, smetric, *w) for w in [(pre_lo, pre_hi), (early_lo, early_hi), (late_lo, late_hi)])
            response.append({"network_branch_id": branch, "pre_trip_window_s": f"{pre_lo:.2f}-{pre_hi:.2f}",
                             "post_trip_early_window_s": f"{early_lo:.2f}-{early_hi:.2f}", "post_trip_late_window_s": f"{late_lo:.2f}-{late_hi:.2f}",
                             "pre_P": pre_p, "early_P": early_p, "delta_P": early_p-pre_p,
                             "pre_Q": pre_q, "early_Q": early_q, "delta_Q": early_q-pre_q,
                             "pre_I": pre_i, "early_I": early_i, "delta_I": early_i-pre_i,
                             "pre_raw_S": pre_s, "early_raw_S": early_s, "delta_raw_S": early_s-pre_s,
                             "late_P": late_p, "late_Q": late_q, "late_I": late_i, "late_raw_S": late_s,
                             "response_score": abs(early_s-pre_s), "status": "post_trip_high_stress_response_trend_only"})
        ranked = sorted([x for x in response if x.get("response_score") is not None], key=lambda x: x["response_score"], reverse=True)
        for rank, row in enumerate(ranked, 1): row["response_rank_all_lines"] = rank
        redistributed = [x for x in ranked if x["network_branch_id"] != "E_28_29_1"]
        for rank, row in enumerate(redistributed, 1): row["redistribution_rank_excluding_opened_line"] = rank
        response.sort(key=lambda x: x.get("redistribution_rank_excluding_opened_line", 999))

    gate = read_json(REPO / "data/validation/stage9_short_run_pre_run_gate.json")
    baseline = read_json(REPO / "data/validation/stage9_short_run_initialization_baseline_manifest.json")
    out_times = [p.stat().st_mtime for p in outs]
    build_latest = max(datetime.fromisoformat(x).timestamp() for x in gate["build_artifact_times"].values() if x)
    new_after_build = bool(out_times) and min(out_times) > build_latest
    manifest = {
        "manifest_name": "stage9_short_run_manifest", "generated_at_local": datetime.now().isoformat(timespec="seconds"),
        "execution_status": "stage9_short_run_runtime_outputs_detected" if readable and same_axis else "stage9_short_run_runtime_output_parser_fallback",
        "main_sha_start": baseline["main_sha_start"], "main_sha_final": sha(MAIN),
        "trial_sha_start": baseline["trial_sha_start"], "trial_sha_final": sha(TRIAL),
        "selected_line": baseline["selected_line"], "effective_capacity_pu": baseline["effective_capacity_pu"],
        "threshold_multiplier": baseline["threshold_multiplier"], "definite_delay_s": baseline["definite_delay_s"],
        "inf_exists": inf_path.exists(), "inf_channel_count": len(inf), "prefixed_out_file_count": len(outs),
        "paper_channels_all_unique": all(len(by_title.get(x, [])) == 1 for x in PAPER),
        "paper_channels_all_readable": readable, "common_time_axis": same_axis,
        "sample_count": len(t), "time_start_s": t[0] if t else None, "time_end_s": t[-1] if t else None,
        "plot_step_s": t[1]-t[0] if len(t)>1 else None, "runtime_outputs_newer_than_stage9_build": new_after_build,
        "stage9_run_count": 1, "second_run_requested": False,
        "fault_start_time_s": 0.50, "fault_clear_time_s": 2.50, "dfig_event_time_s": dfig_t,
        "first_threshold_crossing_time_s": threshold_t, "timer_start_time_s": threshold_t,
        "timer_completion_time_s": completion_t, "continuous_above_threshold_duration_s": continuous_to_completion,
        "trip_request_time_s": trip_t, "breaker_command_time_s": cmd_t, "actual_breaker_open_time_s": open_t,
        "pre_fault_max_loading_index_eq": pre_max, "pre_fault_false_trip": pre_false,
        "t0": {name: vals[name][0] if readable else None for name in ["PAPER_OVL1_ABOVE_THRESHOLD", "PAPER_OVL1_TIMER_OR_CURVE_STATE", "PAPER_OVL1_TRIP_REQUEST", "PAPER_OVL1_BRK_CMD", "PAPER_OVL1_BRK_STATE"]},
        "post_trip_response_line_count": len(response), "raw_runtime_artifacts_not_committed": True,
    }
    write_csv(REPO / "data/derived/stage9_short_run_event_timeline.csv", timeline)
    write_csv(REPO / "data/derived/stage9_short_run_relay_trace.csv", relay_trace, ["time_s", *PAPER])
    write_csv(REPO / "data/derived/stage9_short_run_post_trip_tline_response.csv", response)
    write_json(REPO / "data/derived/stage9_short_run_manifest.json", manifest)
    print(json.dumps({k: manifest[k] for k in ["execution_status", "sample_count", "time_end_s", "first_threshold_crossing_time_s", "timer_completion_time_s", "trip_request_time_s", "actual_breaker_open_time_s", "pre_fault_false_trip"]}, indent=2))


if __name__ == "__main__":
    main()
