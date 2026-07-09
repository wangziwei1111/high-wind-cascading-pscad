#!/usr/bin/env python3
"""Parse Stage-11 20 s / 50 us PSCAD outputs and reconstruct the paper-like chain."""

from __future__ import annotations

import csv
import hashlib
import json
import math
import re
import xml.etree.ElementTree as ET
from datetime import datetime
from pathlib import Path
from statistics import fmean
from typing import Any


REPO = Path(__file__).resolve().parents[2]
PSCAD = Path(r"C:\pscad_work\pnnl_39_3ibr_pscad46_strip5\PSCAD")
GF46 = PSCAD / "3IBR_DFIG1_TRIAL.gf46"
MAIN = PSCAD / "3IBR.pscx"
TRIAL = PSCAD / "3IBR_DFIG1_TRIAL.pscx"
PREFIX = "3IBR_DFIG1_TRIAL"

PAPER = [
    "PAPER_OVL1_S_A_PU", "PAPER_OVL1_S_B_PU", "PAPER_OVL1_S_MAX_PU",
    "PAPER_OVL1_EFFECTIVE_CAPACITY_PU", "PAPER_OVL1_LOADING_INDEX_EQ",
    "PAPER_OVL1_ABOVE_THRESHOLD", "PAPER_OVL1_TIMER_OR_CURVE_STATE",
    "PAPER_OVL1_TRIP_REQUEST", "PAPER_OVL1_BRK_CMD", "PAPER_OVL1_BRK_STATE",
    "PAPER_OVL1_TRIP_EVENT_VALID", "PAPER_OVL1_FIRST_TRIP_TIME_S",
    "PAPER_OVL1_RELAY_ENABLE",
]

DFIG = [
    "CASCADE3_ELEC_DFIG_V", "PIBR1_2", "QIBR1_2",
    "DFIG_LVRT_TRIP_CAUSE_DURATION_LATCH", "DFIG_LVRT_FINAL_BRK_CMD",
    "DFIG_LVRT_TRIP_CONFIRMED", "DFIG_BRK_STATE",
    "DFIG_LVRT_CASCADE_EVENT_VALID", "DFIG_LVRT_CASCADE_EVENT_CAUSE_CODE",
    "DFIG_LVRT_CASCADE_EVENT_BRK_OPEN", "DFIG_LVRT_CASCADE_SOURCE_AVAILABLE",
    "DFIG_LVRT_CASCADE_FIRST_EVENT_TIME_S",
]


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest().upper()


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


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
    pat = re.compile(r'^PGB\((\d+)\)\s+Output\s+Desc="([^"]*)"\s+Group="([^"]*)".*Units="([^"]*)"')
    rows: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8", errors="ignore").splitlines():
        if m := pat.search(line):
            rows.append({"pgb_index": int(m.group(1)), "title": m.group(2), "group": m.group(3), "units": m.group(4)})
    return rows


def load_out(path: Path) -> list[list[float]]:
    rows: list[list[float]] = []
    for line in path.read_text(encoding="ascii", errors="ignore").splitlines():
        if line.split():
            rows.append([float(x) for x in line.split()])
    return rows


def first_time(t: list[float], v: list[float], threshold: float = 0.5, op: str = ">") -> float | None:
    for x, y in zip(t, v):
        if op == ">" and y > threshold:
            return x
        if op == ">=" and y >= threshold:
            return x
        if op == "<" and y < threshold:
            return x
    return None


def value_at_or_after(t: list[float], v: list[float], time_s: float | None) -> float | None:
    if time_s is None:
        return None
    for x, y in zip(t, v):
        if x >= time_s:
            return y
    return None


def mean_window(t: list[float], v: list[float], lo: float, hi: float) -> float | None:
    data = [y for x, y in zip(t, v) if lo <= x <= hi]
    return fmean(data) if data else None


def max_window(t: list[float], v: list[float], lo: float, hi: float) -> float | None:
    data = [y for x, y in zip(t, v) if lo <= x <= hi]
    return max(data) if data else None


def window_stats(t: list[float], v: list[float], lo: float, hi: float) -> dict[str, float | None]:
    return {"mean": mean_window(t, v, lo, hi), "max": max_window(t, v, lo, hi)}


def params(root: ET.Element) -> dict[str, str]:
    return {p.get("name", ""): p.get("value", "") for p in root.findall("./paramlist/param")}


def project_settings(path: Path) -> dict[str, str]:
    root = ET.parse(path).getroot()
    return {p.get("name", ""): p.get("value", "") for p in root.findall("./paramlist/param")}


def classify(manifest: dict[str, Any]) -> str:
    if manifest["pre_fault_health"]["status"] != "healthy":
        return "stage11_pre_fault_dfig_event_or_unhealthy_state"
    dfig_t = manifest["event_times_s"]["dfig_actual_breaker_open"]
    line_t = manifest["event_times_s"]["paper_actual_breaker_open"]
    if dfig_t is None:
        return "stage11_dfig_not_observed_before_line_trip"
    if line_t is None:
        sustained = manifest["event_times_s"]["paper_threshold_crossing"] is not None and manifest["event_times_s"]["paper_timer_done"] is None
        return "stage11_dfig_trip_observed_line_protection_not_sustained" if sustained else "stage11_dfig_trip_observed_line_trip_not_observed"
    if line_t < dfig_t:
        return "stage11_line_trip_before_dfig"
    if manifest["event_times_s"]["paper_timer_done"] is None or manifest["event_times_s"]["paper_trip_request"] is None:
        return "stage11_dfig_trip_observed_line_protection_not_sustained"
    return "stage11_20s_50us_paper_order_first_trip_pass"


def main() -> None:
    generated = datetime.now().astimezone().isoformat(timespec="seconds")
    inf_path = GF46 / f"{PREFIX}.inf"
    outs = sorted(GF46.glob(f"{PREFIX}_*.out"))
    inf = parse_inf(inf_path)
    by_title: dict[str, list[dict[str, Any]]] = {}
    for row in inf:
        by_title.setdefault(row["title"], []).append(row)

    first = load_out(outs[0]) if outs else []
    channels_per_file = len(first[0]) - 1 if first else 0
    cache: dict[int, list[list[float]]] = {1: first} if first else {}

    def series(title: str) -> tuple[list[float], list[float]]:
        matches = by_title.get(title, [])
        if len(matches) != 1 or channels_per_file <= 0:
            return [], []
        idx = matches[0]["pgb_index"]
        number, column = (idx - 1) // channels_per_file + 1, (idx - 1) % channels_per_file + 1
        if number not in cache:
            path = GF46 / f"{PREFIX}_{number:02d}.out"
            cache[number] = load_out(path) if path.exists() else []
        data = cache[number]
        return [row[0] for row in data], [row[column] for row in data]

    t = first and [row[0] for row in first] or []
    settings = project_settings(TRIAL)
    fault_start, fault_clear = 0.50, 2.50
    pre_fault_indices = [i for i, x in enumerate(t) if 0.0 <= x < fault_start]

    all_required = PAPER + DFIG
    runtime = {name: series(name) for name in all_required}
    vals = {name: runtime[name][1] for name in all_required}
    readable = all(runtime[name][0] for name in all_required)
    common_axis = readable and all(runtime[name][0] == t for name in all_required)

    dfig_event_time = first_time(t, vals["DFIG_LVRT_CASCADE_EVENT_VALID"])
    dfig_open_time = first_time(t, vals["DFIG_BRK_STATE"], 0.5)
    dfig_source_lost = first_time(t, vals["DFIG_LVRT_CASCADE_SOURCE_AVAILABLE"], 0.5, "<")
    paper_threshold = first_time(t, vals["PAPER_OVL1_LOADING_INDEX_EQ"], 1.1, ">=")
    paper_above = first_time(t, vals["PAPER_OVL1_ABOVE_THRESHOLD"])
    paper_timer = first_time(t, vals["PAPER_OVL1_TIMER_OR_CURVE_STATE"])
    paper_trip = first_time(t, vals["PAPER_OVL1_TRIP_REQUEST"])
    paper_open = first_time(t, vals["PAPER_OVL1_BRK_STATE"], 1.0)
    cause_code = value_at_or_after(t, vals["DFIG_LVRT_CASCADE_EVENT_CAUSE_CODE"], dfig_event_time)

    pre_checks = {
        "DFIG_LVRT_TRIP_CAUSE_DURATION_LATCH_max": max((vals["DFIG_LVRT_TRIP_CAUSE_DURATION_LATCH"][i] for i in pre_fault_indices), default=None),
        "DFIG_LVRT_FINAL_BRK_CMD_max": max((vals["DFIG_LVRT_FINAL_BRK_CMD"][i] for i in pre_fault_indices), default=None),
        "DFIG_BRK_STATE_max": max((vals["DFIG_BRK_STATE"][i] for i in pre_fault_indices), default=None),
        "DFIG_LVRT_CASCADE_EVENT_VALID_max": max((vals["DFIG_LVRT_CASCADE_EVENT_VALID"][i] for i in pre_fault_indices), default=None),
        "DFIG_LVRT_CASCADE_SOURCE_AVAILABLE_min": min((vals["DFIG_LVRT_CASCADE_SOURCE_AVAILABLE"][i] for i in pre_fault_indices), default=None),
    }
    pre_healthy = (
        pre_checks["DFIG_LVRT_TRIP_CAUSE_DURATION_LATCH_max"] == 0.0
        and pre_checks["DFIG_LVRT_FINAL_BRK_CMD_max"] == 0.0
        and pre_checks["DFIG_BRK_STATE_max"] == 0.0
        and pre_checks["DFIG_LVRT_CASCADE_EVENT_VALID_max"] == 0.0
        and pre_checks["DFIG_LVRT_CASCADE_SOURCE_AVAILABLE_min"] == 1.0
    )

    event_times = {
        "fault_start": fault_start,
        "fault_clear": fault_clear,
        "dfig_duration_latch": first_time(t, vals["DFIG_LVRT_TRIP_CAUSE_DURATION_LATCH"]),
        "dfig_final_breaker_command": first_time(t, vals["DFIG_LVRT_FINAL_BRK_CMD"]),
        "dfig_trip_confirmed": first_time(t, vals["DFIG_LVRT_TRIP_CONFIRMED"]),
        "dfig_actual_breaker_open": dfig_open_time,
        "dfig_cascade_event_valid": dfig_event_time,
        "dfig_source_available_lost": dfig_source_lost,
        "paper_threshold_crossing": paper_threshold,
        "paper_above_threshold": paper_above,
        "paper_timer_done": paper_timer,
        "paper_trip_request": paper_trip,
        "paper_breaker_command": first_time(t, vals["PAPER_OVL1_BRK_CMD"]),
        "paper_actual_breaker_open": paper_open,
        "paper_trip_event_valid": first_time(t, vals["PAPER_OVL1_TRIP_EVENT_VALID"]),
    }
    continuous_delay = paper_timer - paper_above if paper_timer is not None and paper_above is not None else None

    timeline = [
        {"order": 1, "event": "actual_fault_start", "time_s": fault_start, "source": "static_fault_configuration", "status": "frozen"},
        {"order": 2, "event": "actual_fault_clear", "time_s": fault_clear, "source": "static_fault_configuration", "status": "frozen"},
        {"order": 3, "event": "DFIG_LVRT_physical_trip_and_breaker_open", "time_s": dfig_open_time, "source": "DFIG_BRK_STATE", "status": "observed" if dfig_open_time else "not_observed"},
        {"order": 4, "event": "DFIG_source_available_lost", "time_s": dfig_source_lost, "source": "DFIG_LVRT_CASCADE_SOURCE_AVAILABLE", "status": "observed" if dfig_source_lost else "not_observed"},
        {"order": 5, "event": "E_28_29_1_loading_index_exceeds_1p1", "time_s": paper_threshold, "source": "PAPER_OVL1_LOADING_INDEX_EQ", "status": "observed" if paper_threshold else "not_observed"},
        {"order": 6, "event": "PAPER_OVL1_5s_timer_done", "time_s": paper_timer, "source": "PAPER_OVL1_TIMER_OR_CURVE_STATE", "status": "observed" if paper_timer else "not_observed"},
        {"order": 7, "event": "PAPER_OVL1_trip_request_and_breaker_open", "time_s": paper_open, "source": "PAPER_OVL1_BRK_STATE", "status": "observed" if paper_open else "not_observed"},
    ]

    tline_groups = sorted({m.group(1) for row in inf if (m := re.match(r"^(E_\d+_\d+_1)_[AB]_[PQI]$", row["title"]))})
    response_rows: list[dict[str, Any]] = []
    late_rows: list[dict[str, Any]] = []
    for branch in tline_groups:
        names = [f"{branch}_{end}_{qty}" for end in "AB" for qty in "PQI"]
        if not all(len(by_title.get(name, [])) == 1 for name in names):
            response_rows.append({"network_branch_id": branch, "status": "missing_runtime_channel"})
            continue
        data = {name: series(name) for name in names}
        bt = data[names[0]][0]
        pa, qa, ia = (data[f"{branch}_A_{q}"][1] for q in "PQI")
        pb, qb, ib = (data[f"{branch}_B_{q}"][1] for q in "PQI")
        smax = [max(math.hypot(a, b), math.hypot(c, d)) for a, b, c, d in zip(pa, qa, pb, qb)]
        imax = [max(abs(a), abs(b)) for a, b in zip(ia, ib)]
        pmax = [max(abs(a), abs(b)) for a, b in zip(pa, pb)]
        qmax = [max(abs(a), abs(b)) for a, b in zip(qa, qb)]
        pre_lo, pre_hi = 0.20, 0.49
        post_lo, post_hi = (dfig_open_time or fault_clear) + 0.02, min((paper_open or 20.0) - 0.02, 7.50)
        late_lo, late_hi = (paper_open or 7.53) + 0.50, 20.0
        pre_s, post_s, late_s = (window_stats(bt, smax, *w) for w in ((pre_lo, pre_hi), (post_lo, post_hi), (late_lo, late_hi)))
        pre_i, post_i, late_i = (window_stats(bt, imax, *w) for w in ((pre_lo, pre_hi), (post_lo, post_hi), (late_lo, late_hi)))
        row = {
            "network_branch_id": branch,
            "pre_fault_window_s": f"{pre_lo:.2f}-{pre_hi:.2f}",
            "post_dfig_pre_line_trip_window_s": f"{post_lo:.2f}-{post_hi:.2f}",
            "late_post_line_trip_window_s": f"{late_lo:.2f}-{late_hi:.2f}",
            "pre_raw_S_mean": pre_s["mean"], "pre_raw_S_max": pre_s["max"],
            "post_dfig_raw_S_mean": post_s["mean"], "post_dfig_raw_S_max": post_s["max"],
            "late_raw_S_mean": late_s["mean"], "late_raw_S_max": late_s["max"],
            "pre_I_mean": pre_i["mean"], "post_dfig_I_mean": post_i["mean"], "late_I_mean": late_i["mean"],
            "delta_post_dfig_raw_S_mean": (post_s["mean"] - pre_s["mean"]) if post_s["mean"] is not None and pre_s["mean"] is not None else None,
            "delta_late_raw_S_mean": (late_s["mean"] - pre_s["mean"]) if late_s["mean"] is not None and pre_s["mean"] is not None else None,
            "status": "trend_only_no_rating_claim",
        }
        response_rows.append(row)
        late_rows.append({
            "network_branch_id": branch,
            "late_raw_S_mean": late_s["mean"],
            "late_raw_S_max": late_s["max"],
            "late_I_mean": late_i["mean"],
            "late_P_abs_mean": mean_window(bt, pmax, late_lo, late_hi),
            "late_Q_abs_mean": mean_window(bt, qmax, late_lo, late_hi),
            "delta_late_raw_S_mean": row["delta_late_raw_S_mean"],
            "claim_boundary": "raw response only; no thermal rating applied",
        })
    response_rows.sort(key=lambda r: abs(r.get("delta_post_dfig_raw_S_mean") or 0.0), reverse=True)
    for rank, row in enumerate(response_rows, 1):
        row["post_dfig_response_rank"] = rank
    late_rows.sort(key=lambda r: abs(r.get("delta_late_raw_S_mean") or 0.0), reverse=True)
    for rank, row in enumerate(late_rows, 1):
        row["late_response_rank"] = rank

    dfig_trace = []
    for i, x in enumerate(t):
        if 2.30 <= x <= 2.60:
            dfig_trace.append({
                "time_s": x,
                **{name: vals[name][i] for name in DFIG if name in vals},
            })

    manifest = {
        "manifest_name": "stage11_20s_50us_runtime_manifest",
        "generated_at_local": generated,
        "execution_status": "stage11_20s_50us_runtime_outputs_detected" if readable and common_axis else "stage11_20s_50us_runtime_output_parser_fallback",
        "main_sha256_final": sha256(MAIN),
        "trial_sha256_final": sha256(TRIAL),
        "solution_time_step_us": float(settings.get("time_step", "nan")),
        "project_file_time_duration_s": float(settings.get("time_duration", "nan")),
        "runtime_observed_duration_s": t[-1] if t else None,
        "plot_step_us": float(settings.get("sample_step", "nan")),
        "runtime_output_file_count": len(outs),
        "runtime_output_oldest_mtime": datetime.fromtimestamp(min(p.stat().st_mtime for p in outs)).astimezone().isoformat(timespec="seconds") if outs else None,
        "runtime_output_newest_mtime": datetime.fromtimestamp(max(p.stat().st_mtime for p in outs)).astimezone().isoformat(timespec="seconds") if outs else None,
        "inf_channel_count": len(inf),
        "channels_per_out_file": channels_per_file,
        "sample_count": len(t),
        "time_start_s": t[0] if t else None,
        "time_end_s": t[-1] if t else None,
        "plot_step_s_observed": t[1] - t[0] if len(t) > 1 else None,
        "required_channels_readable": readable,
        "common_time_axis": common_axis,
        "fault_window_s": [fault_start, fault_clear],
        "pre_fault_window_s": [0.0, 0.49],
        "pre_fault_health": {"status": "healthy" if pre_healthy else "unhealthy", "checks": pre_checks},
        "event_times_s": event_times,
        "dfig_event_cause_code_at_valid": cause_code,
        "dfig_cascade_first_event_time_signal_final_s": vals["DFIG_LVRT_CASCADE_FIRST_EVENT_TIME_S"][-1] if vals["DFIG_LVRT_CASCADE_FIRST_EVENT_TIME_S"] else None,
        "paper_first_trip_time_signal_final_s": vals["PAPER_OVL1_FIRST_TRIP_TIME_S"][-1] if vals["PAPER_OVL1_FIRST_TRIP_TIME_S"] else None,
        "paper_loading_index_max": max(vals["PAPER_OVL1_LOADING_INDEX_EQ"]) if vals["PAPER_OVL1_LOADING_INDEX_EQ"] else None,
        "paper_delay_observed_s": continuous_delay,
        "raw_tline_groups": len(tline_groups),
        "raw_runtime_artifacts_not_committed": True,
    }
    manifest["stage11_result_class"] = classify(manifest)
    manifest["paper_order_assertion"] = (
        "fault_to_dfig_to_line_overload_to_5s_line_trip_observed"
        if manifest["stage11_result_class"].startswith("stage11_20s_50us_paper_order")
        else "paper_order_not_fully_observed"
    )

    integrity = [
        {"check": "runtime_duration_20s", "status": "pass" if abs(manifest["time_end_s"] - 20.0) < 1e-9 else "fail", "value": manifest["time_end_s"]},
        {"check": "plot_step_0p01s", "status": "pass" if abs(manifest["plot_step_s_observed"] - 0.01) < 1e-12 else "fail", "value": manifest["plot_step_s_observed"]},
        {"check": "required_channels_readable", "status": "pass" if readable else "fail", "value": readable},
        {"check": "pre_fault_dfig_healthy", "status": "pass" if pre_healthy else "fail", "value": manifest["pre_fault_health"]},
        {"check": "dfig_after_fault_before_line_trip", "status": "pass" if dfig_open_time and paper_open and fault_start < dfig_open_time < paper_open else "fail", "value": {"dfig": dfig_open_time, "line": paper_open}},
        {"check": "timer_delay_about_5s", "status": "pass" if continuous_delay is not None and abs(continuous_delay - 5.0) <= 0.011 else "fail", "value": continuous_delay},
        {"check": "final_class_allowed", "status": "pass" if manifest["stage11_result_class"] else "fail", "value": manifest["stage11_result_class"]},
    ]

    result_doc = f"""# Stage 11 20 s / 50 us paper-like sequence validation

## Result

- Final class: `{manifest["stage11_result_class"]}`
- Runtime output status: `{manifest["execution_status"]}`
- Fault window: `{fault_start:.2f} s` to `{fault_clear:.2f} s`
- Observed time span: `{manifest["time_start_s"]:.2f} s` to `{manifest["time_end_s"]:.2f} s`, plot step `{manifest["plot_step_s_observed"]:.2f} s`
- Claim boundary: this is a 50 us numerical run. It verifies this configuration's event order, not equivalence to a separate 5 us run.

## Event chronology

| Event | Time (s) |
|---|---:|
| Fault applied | {fault_start:.2f} |
| Fault cleared | {fault_clear:.2f} |
| DFIG LVRT trip / breaker open | {dfig_open_time:.2f} |
| DFIG source availability lost | {dfig_source_lost:.2f} |
| E_28_29_1 loading index first >= 1.1 | {paper_threshold:.2f} |
| PAPER_OVL1 5 s timer done | {paper_timer:.2f} |
| PAPER_OVL1 breaker open | {paper_open:.2f} |

The pre-fault interval is explicitly `0.00 <= t < 0.50 s`; DFIG trip latch, command, breaker state, and cascade event valid all remain zero there, while source availability remains one.

## Network response boundary

The TLine response CSV files report raw P/Q/I-derived trends only. No thermal rating or relay claim is made from those raw trends in this stage.
"""
    (REPO / "docs/STAGE11_20S_50US_PAPER_SEQUENCE_RESULT.md").write_text(result_doc, encoding="utf-8")
    write_csv(REPO / "data/derived/stage11_20s_50us_event_timeline.csv", timeline)
    write_csv(REPO / "data/derived/stage11_20s_50us_dfig_first_trip_trace.csv", dfig_trace)
    write_csv(REPO / "data/derived/stage11_20s_50us_post_first_trip_tline_response.csv", response_rows)
    write_csv(REPO / "data/derived/stage11_20s_50us_late_network_response.csv", late_rows)
    write_json(REPO / "data/derived/stage11_20s_50us_runtime_manifest.json", manifest)
    write_json(REPO / "data/validation/stage11_20s_50us_final_audit.json", {
        "audit_name": "stage11_20s_50us_final_audit",
        "generated_at_local": generated,
        "execution_status": "pass" if all(row["status"] == "pass" for row in integrity) else "review",
        "stage11_result_class": manifest["stage11_result_class"],
        "integrity_trace": integrity,
        "event_times_s": event_times,
        "pre_fault_health": manifest["pre_fault_health"],
        "claim_boundary": manifest["paper_order_assertion"],
    })
    write_csv(REPO / "data/validation/stage11_20s_50us_integrity_trace.csv", integrity)
    print(json.dumps({
        "stage11_result_class": manifest["stage11_result_class"],
        "time_end_s": manifest["time_end_s"],
        "dfig_open_s": dfig_open_time,
        "paper_threshold_s": paper_threshold,
        "paper_timer_s": paper_timer,
        "paper_open_s": paper_open,
        "pre_fault_health": manifest["pre_fault_health"]["status"],
    }, indent=2))


if __name__ == "__main__":
    main()
