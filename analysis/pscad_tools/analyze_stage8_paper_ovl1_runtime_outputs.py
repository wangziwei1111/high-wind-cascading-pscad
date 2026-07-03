#!/usr/bin/env python3
"""Parse the single Stage-8 PSCAD run without modifying PSCAD artifacts."""

from __future__ import annotations

import csv
import hashlib
import json
import math
import re
from datetime import datetime
from pathlib import Path
from typing import Any


REPO = Path(__file__).resolve().parents[2]
GF46 = Path(r"C:\pscad_work\pnnl_39_3ibr_pscad46_strip5\PSCAD\3IBR_DFIG1_TRIAL.gf46")
MAIN = GF46.parent / "3IBR.pscx"
TRIAL = GF46.parent / "3IBR_DFIG1_TRIAL.pscx"
PREFIX = "3IBR_DFIG1_TRIAL"
PAPER_CHANNELS = [
    "PAPER_OVL1_S_A_PU", "PAPER_OVL1_S_B_PU", "PAPER_OVL1_S_MAX_PU",
    "PAPER_OVL1_EFFECTIVE_CAPACITY_PU", "PAPER_OVL1_LOADING_INDEX_EQ",
    "PAPER_OVL1_ABOVE_THRESHOLD", "PAPER_OVL1_TIMER_OR_CURVE_STATE",
    "PAPER_OVL1_TRIP_REQUEST", "PAPER_OVL1_BRK_CMD", "PAPER_OVL1_BRK_STATE",
    "PAPER_OVL1_TRIP_EVENT_VALID", "PAPER_OVL1_FIRST_TRIP_TIME_S",
    "PAPER_OVL1_RELAY_ENABLE",
]


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
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
                if key not in fields:
                    fields.append(key)
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def parse_inf(path: Path) -> list[dict[str, Any]]:
    rows = []
    pat = re.compile(r'^PGB\((\d+)\)\s+Output\s+Desc="([^"]*)"\s+Group="([^"]*)".*Units="([^"]*)"')
    for line in path.read_text(encoding="utf-8", errors="ignore").splitlines():
        m = pat.search(line)
        if m:
            rows.append({"pgb_index": int(m.group(1)), "title": m.group(2), "group": m.group(3), "units": m.group(4)})
    return rows


def load_numeric(path: Path) -> list[list[float]]:
    data = []
    for line in path.read_text(encoding="ascii", errors="ignore").splitlines():
        parts = line.split()
        if parts:
            data.append([float(x) for x in parts])
    return data


def first_true_time(time: list[float], values: list[float], threshold: float = 0.5) -> float | None:
    for t, v in zip(time, values):
        if v > threshold:
            return t
    return None


def longest_true_duration(time: list[float], values: list[float], threshold: float = 0.5) -> float:
    best = 0.0
    start = None
    for t, v in zip(time, values):
        if v > threshold and start is None:
            start = t
        elif v <= threshold and start is not None:
            best = max(best, t - start)
            start = None
    if start is not None:
        best = max(best, time[-1] - start)
    return best


def main() -> None:
    inf_path = GF46 / f"{PREFIX}.inf"
    out_files = sorted(GF46.glob(f"{PREFIX}_*.out"))
    freeze = read_json(REPO / "data/reference/stage8_output_observability_repair_freeze.json")
    baseline = read_json(REPO / "data/validation/stage8_output_observability_baseline_manifest.json")
    gate = read_json(REPO / "data/validation/stage8_pre_run_output_gate.json")

    inf_rows = parse_inf(inf_path) if inf_path.exists() else []
    title_rows: dict[str, list[dict[str, Any]]] = {}
    for row in inf_rows:
        title_rows.setdefault(row["title"], []).append(row)

    cache: dict[int, list[list[float]]] = {}
    channels_per_file = 0
    if out_files:
        first = load_numeric(out_files[0])
        channels_per_file = len(first[0]) - 1 if first else 0
        cache[1] = first

    series: dict[str, tuple[list[float], list[float]]] = {}
    inventory: list[dict[str, Any]] = []
    for title in PAPER_CHANNELS:
        matches = title_rows.get(title, [])
        row: dict[str, Any] = {
            "canonical_title": title,
            "inf_title_count": len(matches),
            "runtime_status": "missing",
        }
        if len(matches) == 1 and channels_per_file:
            pgb = matches[0]["pgb_index"]
            file_no = (pgb - 1) // channels_per_file + 1
            data_col = (pgb - 1) % channels_per_file + 1
            if file_no not in cache:
                path = GF46 / f"{PREFIX}_{file_no:02d}.out"
                cache[file_no] = load_numeric(path) if path.exists() else []
            data = cache[file_no]
            if data and all(len(r) > data_col for r in data):
                time = [r[0] for r in data]
                values = [r[data_col] for r in data]
                series[title] = (time, values)
                row.update({
                    "pgb_index": pgb, "out_file_number": file_no,
                    "out_file": f"{PREFIX}_{file_no:02d}.out", "data_column_after_time": data_col,
                    "units": matches[0]["units"], "sample_count": len(values),
                    "time_start_s": time[0], "time_end_s": time[-1],
                    "min": min(values), "max": max(values), "initial": values[0], "final": values[-1],
                    "runtime_status": "readable",
                })
        inventory.append(row)

    all_readable = len(series) == len(PAPER_CHANNELS)
    common_time = series[PAPER_CHANNELS[0]][0] if all_readable else []
    relay_trace = []
    if all_readable:
        for i, t in enumerate(common_time):
            relay_trace.append({"time_s": t, **{name: series[name][1][i] for name in PAPER_CHANNELS}})

    def vals(name: str) -> list[float]:
        return series.get(name, ([], []))[1]

    above_time = first_true_time(common_time, vals("PAPER_OVL1_ABOVE_THRESHOLD")) if all_readable else None
    timer_time = first_true_time(common_time, vals("PAPER_OVL1_TIMER_OR_CURVE_STATE")) if all_readable else None
    trip_time = first_true_time(common_time, vals("PAPER_OVL1_TRIP_REQUEST")) if all_readable else None
    cmd_time = first_true_time(common_time, vals("PAPER_OVL1_BRK_CMD")) if all_readable else None
    brk_time = first_true_time(common_time, vals("PAPER_OVL1_BRK_STATE"), 1.0) if all_readable else None
    dfig_time = None
    if "DFIG_LVRT_CASCADE_EVENT_VALID" in title_rows and channels_per_file:
        pgb = title_rows["DFIG_LVRT_CASCADE_EVENT_VALID"][0]["pgb_index"]
        fno, col = (pgb - 1) // channels_per_file + 1, (pgb - 1) % channels_per_file + 1
        data = cache.get(fno) or load_numeric(GF46 / f"{PREFIX}_{fno:02d}.out")
        dfig_time = first_true_time([r[0] for r in data], [r[col] for r in data])

    timeline = [
        {"event": "fault_start", "time_s": 0.5, "status": "frozen_reference"},
        {"event": "fault_clear", "time_s": 2.5, "status": "frozen_reference"},
        {"event": "dfig_event", "time_s": dfig_time, "status": "observed" if dfig_time is not None else "not_observed"},
        {"event": "threshold_crossing", "time_s": above_time, "status": "observed" if above_time is not None else "not_observed"},
        {"event": "timer_state_asserted", "time_s": timer_time, "status": "observed" if timer_time is not None else "not_observed"},
        {"event": "trip_request_asserted", "time_s": trip_time, "status": "observed" if trip_time is not None else "not_observed"},
        {"event": "breaker_command_asserted", "time_s": cmd_time, "status": "observed" if cmd_time is not None else "not_observed"},
        {"event": "breaker_open_state", "time_s": brk_time, "status": "observed" if brk_time is not None else "not_observed"},
    ]

    pre_fault_idx = [i for i, t in enumerate(common_time) if 0.05 <= t < 0.5]
    loading = vals("PAPER_OVL1_LOADING_INDEX_EQ")
    pre_fault_max = max((loading[i] for i in pre_fault_idx), default=None)
    continuous = longest_true_duration(common_time, vals("PAPER_OVL1_ABOVE_THRESHOLD")) if all_readable else 0.0
    pre_fault_false_trip = trip_time is not None and trip_time < 0.5

    # There is no defensible post-trip window when the breaker is already open at t=0.
    tline_ids = sorted({m.group(1) for r in inf_rows if (m := re.match(r"(E_\d+_\d+_1)_[AB]_[PQI]$", r["title"]))})
    post_trip = [{
        "network_branch_id": branch,
        "post_trip_early": None,
        "post_trip_late": None,
        "response_rank": None,
        "status": "not_computed_breaker_open_from_initial_sample_pre_fault_false_trip",
    } for branch in tline_ids]

    out_mtimes = [datetime.fromtimestamp(p.stat().st_mtime).isoformat(timespec="seconds") for p in out_files]
    inf_duplicates = sorted(k for k, v in title_rows.items() if len(v) > 1)
    execution_status = "stage8_runtime_outputs_detected" if all_readable else "stage8_runtime_output_parser_fallback"
    manifest = {
        "manifest_name": "stage8_paper_ovl1_run_manifest",
        "generated_at_local": datetime.now().isoformat(timespec="seconds"),
        "execution_status": execution_status,
        "single_run_evidence": {"inf_mtime": datetime.fromtimestamp(inf_path.stat().st_mtime).isoformat(timespec="seconds") if inf_path.exists() else None,
                                "out_latest_mtime": max(out_mtimes) if out_mtimes else None},
        "selected_line": freeze["selected_line"],
        "effective_capacity_pu": freeze["effective_capacity_pu"],
        "threshold_multiplier": freeze["threshold_multiplier"],
        "protection_curve_type": freeze["protection_curve_type"],
        "definite_delay_s": freeze["definite_delay_s"],
        "main_sha_start": baseline["main_sha_start"], "main_sha_final": sha256(MAIN),
        "trial_sha_start": baseline["trial_sha_start"], "trial_sha_after_stage8_repair": sha256(TRIAL),
        "trial_sha_pre_run_gate": gate["trial_sha_after_gui_repair_and_build"],
        "inf_exists": inf_path.exists(), "inf_path": str(inf_path), "inf_channel_count": len(inf_rows),
        "prefixed_out_file_count": len(out_files), "channels_per_out_file": channels_per_file,
        "paper_channel_count": len(PAPER_CHANNELS), "paper_channels_all_unique_in_inf": all(len(title_rows.get(x, [])) == 1 for x in PAPER_CHANNELS),
        "paper_channels_all_readable": all_readable, "duplicate_inf_titles": inf_duplicates,
        "sample_count": len(common_time), "time_start_s": common_time[0] if common_time else None,
        "time_end_s": common_time[-1] if common_time else None,
        "plot_step_s": common_time[1] - common_time[0] if len(common_time) > 1 else None,
        "fault_start_time_s": 0.5, "fault_clear_time_s": 2.5, "dfig_event_time_s": dfig_time,
        "first_threshold_crossing_time_s": above_time,
        "continuous_above_threshold_duration_s": continuous,
        "timer_start_time_s": timer_time, "trip_request_time_s": trip_time,
        "breaker_command_time_s": cmd_time, "actual_breaker_open_time_s": brk_time,
        "pre_fault_max_loading_index_eq": pre_fault_max,
        "pre_fault_false_trip_status": "fail_pre_fault_trip_at_initial_sample" if pre_fault_false_trip else "pass",
        "raw_runtime_artifacts_not_committed": True,
    }

    write_csv(REPO / "data/derived/stage8_paper_ovl1_runtime_channel_inventory.csv", inventory)
    write_json(REPO / "data/derived/stage8_paper_ovl1_runtime_channel_inventory.json", inventory)
    write_csv(REPO / "data/derived/stage8_paper_ovl1_event_timeline.csv", timeline)
    write_csv(REPO / "data/derived/stage8_paper_ovl1_relay_trace.csv", relay_trace, ["time_s", *PAPER_CHANNELS])
    write_csv(REPO / "data/derived/stage8_paper_ovl1_post_trip_tline_response.csv", post_trip)
    write_json(REPO / "data/derived/stage8_paper_ovl1_run_manifest.json", manifest)
    print(json.dumps({k: manifest[k] for k in ["execution_status", "inf_channel_count", "prefixed_out_file_count", "paper_channels_all_readable", "time_end_s", "pre_fault_false_trip_status"]}, indent=2))


if __name__ == "__main__":
    main()
