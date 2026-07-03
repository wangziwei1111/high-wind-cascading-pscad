#!/usr/bin/env python3
"""Analyze the single Stage-12 two-line-trip runtime after user GUI/Build/Run."""

from __future__ import annotations

import json
from datetime import datetime

from stage12_common import (
    DEFINITE_DELAY_S,
    REPO,
    STAGE11_DFIG_TRIP_S,
    STAGE11_FIRST_LINE_OPEN_S,
    RuntimeReader,
    first_true_run,
    sha256,
    MAIN,
    TRIAL,
    P3_DTA,
    INF,
    write_csv,
    write_json,
)


PAPER2 = [
    "PAPER_OVL2_S_A_PU", "PAPER_OVL2_S_B_PU", "PAPER_OVL2_S_MAX_PU",
    "PAPER_OVL2_EFFECTIVE_CAPACITY_PU", "PAPER_OVL2_LOADING_INDEX_EQ",
    "PAPER_OVL2_ABOVE_THRESHOLD", "PAPER_OVL2_TIMER_OR_CURVE_STATE",
    "PAPER_OVL2_TRIP_REQUEST", "PAPER_OVL2_BRK_CMD", "PAPER_OVL2_BRK_STATE",
    "PAPER_OVL2_TRIP_EVENT_VALID", "PAPER_OVL2_FIRST_TRIP_TIME_S",
    "PAPER_OVL2_RELAY_ENABLE",
]
def first_time(t, v, threshold=0.5, op=">"):
    for x, y in zip(t, v):
        if op == ">" and y > threshold:
            return x
        if op == ">=" and y >= threshold:
            return x
        if op == "<" and y < threshold:
            return x
    return None


def mean_window(t, v, lo, hi):
    xs = [y for x, y in zip(t, v) if lo <= x <= hi]
    return sum(xs) / len(xs) if xs else None


def classify_trend(before, after):
    if before is None or after is None:
        return "no_data"
    delta = after - before
    tol = max(1e-9, abs(before) * 0.05)
    if delta > tol:
        return "sustained_increase"
    if delta < -tol:
        return "sustained_decrease"
    return "recovered_or_flat"


def main() -> None:
    generated = datetime.now().astimezone().isoformat(timespec="seconds")
    reader = RuntimeReader()
    freeze = json.loads((REPO / "data/reference/stage12_second_trip_parameter_freeze.json").read_text(encoding="utf-8"))
    t = reader.time
    required = [
        "DFIG_BRK_STATE", "DFIG_LVRT_CASCADE_EVENT_VALID", "DFIG_LVRT_CASCADE_SOURCE_AVAILABLE",
        "PAPER_OVL1_BRK_STATE", "PAPER_OVL1_ABOVE_THRESHOLD", "PAPER_OVL1_TIMER_OR_CURVE_STATE",
        *PAPER2,
    ]
    data = {name: reader.series(name) for name in required}
    readable = all(data[name][0] for name in required)
    vals = {name: data[name][1] for name in required if data[name][0]}
    if not readable:
        result_class = "stage12_runtime_output_parser_fallback"
        event_times = {}
    else:
        ovl2_pre_idx = [i for i, x in enumerate(t) if x < STAGE11_FIRST_LINE_OPEN_S]
        pre_pickup = any(vals["PAPER_OVL2_ABOVE_THRESHOLD"][i] > 0.5 for i in ovl2_pre_idx)
        event_times = {
            "fault_start": 0.50,
            "fault_clear": 2.50,
            "dfig_actual_breaker_open": first_time(t, vals["DFIG_BRK_STATE"], 0.5),
            "dfig_event_valid": first_time(t, vals["DFIG_LVRT_CASCADE_EVENT_VALID"], 0.5),
            "dfig_source_availability_lost": first_time(t, vals["DFIG_LVRT_CASCADE_SOURCE_AVAILABLE"], 0.5, "<"),
            "paper_ovl1_pickup": first_time(t, vals["PAPER_OVL1_ABOVE_THRESHOLD"], 0.5),
            "paper_ovl1_timer_done": first_time(t, vals["PAPER_OVL1_TIMER_OR_CURVE_STATE"], 0.5),
            "paper_ovl1_actual_open": first_time(t, vals["PAPER_OVL1_BRK_STATE"], 1.0),
            "paper_ovl2_pickup": first_time(t, vals["PAPER_OVL2_ABOVE_THRESHOLD"], 0.5),
            "paper_ovl2_timer_done": first_time(t, vals["PAPER_OVL2_TIMER_OR_CURVE_STATE"], 0.5),
            "paper_ovl2_trip_request": first_time(t, vals["PAPER_OVL2_TRIP_REQUEST"], 0.5),
            "paper_ovl2_breaker_command": first_time(t, vals["PAPER_OVL2_BRK_CMD"], 0.5),
            "paper_ovl2_actual_open": first_time(t, vals["PAPER_OVL2_BRK_STATE"], 1.0),
        }
        if pre_pickup:
            result_class = "stage12_second_line_pre_first_trip_pickup"
        elif not (event_times["dfig_actual_breaker_open"] and event_times["paper_ovl1_actual_open"]):
            result_class = "stage12_dfig_or_first_line_order_not_preserved"
        elif event_times["paper_ovl2_actual_open"] is None:
            result_class = "stage12_second_line_trip_not_observed"
        elif event_times["paper_ovl2_actual_open"] < event_times["paper_ovl1_actual_open"]:
            result_class = "stage12_second_line_trip_before_first_line"
        elif event_times["paper_ovl2_timer_done"] is None:
            result_class = "stage12_second_line_pickup_not_sustained"
        elif event_times["dfig_actual_breaker_open"] < event_times["paper_ovl1_actual_open"] < event_times["paper_ovl2_actual_open"]:
            result_class = "stage12_two_line_paper_order_pass"
        else:
            result_class = "stage12_dfig_or_first_line_order_not_preserved"

    chain_events = []
    if readable:
        source_events = [
            ("DFIG", 1, event_times.get("dfig_actual_breaker_open")),
            ("PAPER_OVL1", 2, event_times.get("paper_ovl1_actual_open")),
            ("PAPER_OVL2", 3, event_times.get("paper_ovl2_actual_open")),
        ]
        chain_events = sorted([x for x in source_events if x[2] is not None], key=lambda x: x[2])
    timeline = [{"event": name, "time_s": value} for name, value in event_times.items()]
    if chain_events:
        timeline.extend([
            {"event": "offline_paper_chain_evented_source_count", "time_s": len(chain_events)},
            {"event": "offline_paper_chain_first_event_time_s", "time_s": chain_events[0][2]},
            {"event": "offline_paper_chain_second_event_time_s", "time_s": chain_events[1][2] if len(chain_events) > 1 else None},
            {"event": "offline_paper_chain_third_event_time_s", "time_s": chain_events[2][2] if len(chain_events) > 2 else None},
        ])
    trace = []
    if readable:
        for i, x in enumerate(t):
            if 0.0 <= x <= 20.0:
                trace.append({"time_s": x, **{name: vals[name][i] for name in ["DFIG_BRK_STATE", "PAPER_OVL1_BRK_STATE", *PAPER2] if name in vals}})
    post_first_rows = []
    post_second_rows = []
    late_rows = []
    if readable:
        ovl1_open = event_times.get("paper_ovl1_actual_open")
        ovl2_open = event_times.get("paper_ovl2_actual_open")
        for branch in reader.branch_ids():
            bt, smax = reader.branch_smax(branch)
            if not bt:
                continue
            pre = mean_window(bt, smax, 0.20, 0.49)
            post_first = mean_window(bt, smax, (ovl1_open or 7.53) + 0.02, (ovl2_open or 12.60) - 0.02)
            post_second = mean_window(bt, smax, (ovl2_open or 12.60) + 0.02, min((ovl2_open or 12.60) + 2.50, 20.0))
            late = mean_window(bt, smax, max(15.0, (ovl2_open or 12.60) + 2.0), 20.0)
            post_first_rows.append({
                "network_branch_id": branch,
                "window_s": f"{(ovl1_open or 7.53) + 0.02:.2f}-{(ovl2_open or 12.60) - 0.02:.2f}",
                "pre_fault_raw_S_mean": pre,
                "post_first_trip_raw_S_mean": post_first,
                "delta_from_prefault": post_first - pre if post_first is not None and pre is not None else None,
                "trend": classify_trend(pre, post_first),
                "claim_boundary": "raw P/Q-derived response only; no thermal rating claim",
            })
            post_second_rows.append({
                "network_branch_id": branch,
                "window_s": f"{(ovl2_open or 12.60) + 0.02:.2f}-{min((ovl2_open or 12.60) + 2.50, 20.0):.2f}",
                "post_first_trip_raw_S_mean": post_first,
                "post_second_trip_raw_S_mean": post_second,
                "delta_from_post_first": post_second - post_first if post_second is not None and post_first is not None else None,
                "trend": classify_trend(post_first, post_second),
                "claim_boundary": "raw P/Q-derived response only; no third-trip or overload claim",
            })
            late_rows.append({
                "network_branch_id": branch,
                "window_s": f"{max(15.0, (ovl2_open or 12.60) + 2.0):.2f}-20.00",
                "late_raw_S_mean": late,
                "delta_from_prefault": late - pre if late is not None and pre is not None else None,
                "trend": classify_trend(pre, late),
                "observation_candidate_only": True,
            })
        post_first_rows.sort(key=lambda r: abs(r["delta_from_prefault"] or 0), reverse=True)
        post_second_rows.sort(key=lambda r: abs(r["delta_from_post_first"] or 0), reverse=True)
        late_rows.sort(key=lambda r: abs(r["delta_from_prefault"] or 0), reverse=True)
        for rows, key in ((post_first_rows, "post_first_rank"), (post_second_rows, "post_second_rank"), (late_rows, "late_rank")):
            for i, row in enumerate(rows, 1):
                row[key] = i
    manifest = {
        "manifest_name": "stage12_run_manifest",
        "generated_at_local": generated,
        "execution_status": "stage12_runtime_outputs_detected" if readable else "stage12_runtime_output_parser_fallback",
        "stage12_result_class": result_class,
        "selected_tline_id": freeze["selected_tline_id"],
        "main_sha256": sha256(MAIN),
        "trial_sha256": sha256(TRIAL),
        "P3_dta_sha256": sha256(P3_DTA) if P3_DTA.exists() else None,
        "inf_sha256": sha256(INF) if INF.exists() else None,
        "sample_count": len(t),
        "time_start_s": t[0] if t else None,
        "time_end_s": t[-1] if t else None,
        "plot_step_s": t[1] - t[0] if len(t) > 1 else None,
        "required_channels_readable": readable,
        "event_times_s": event_times,
        "offline_paper_chain_chronology": {
            "monitor_waiver": "PAPER_CHAIN_MODEL_MONITOR_WAIVED_OFFLINE_PARSER",
            "evented_source_count": len(chain_events),
            "first_event_time_s": chain_events[0][2] if len(chain_events) > 0 else None,
            "second_event_time_s": chain_events[1][2] if len(chain_events) > 1 else None,
            "third_event_time_s": chain_events[2][2] if len(chain_events) > 2 else None,
            "first_source_code": chain_events[0][1] if len(chain_events) > 0 else None,
            "event_order_class_code": 4 if [x[1] for x in chain_events] == [1, 2, 3] else 0,
            "chronology_consistent": [x[1] for x in chain_events] == [1, 2, 3],
            "first_to_second_gap_s": chain_events[1][2] - chain_events[0][2] if len(chain_events) > 1 else None,
            "second_to_third_gap_s": chain_events[2][2] - chain_events[1][2] if len(chain_events) > 2 else None,
        },
        "claim_boundary": "Raw PSCAD runtime outputs are parsed but not committed; the second line capacity remains paper-calibrated effective capacity.",
    }
    write_json(REPO / "data/reference/stage12_run_manifest.json", manifest)
    write_csv(REPO / "data/derived/stage12_event_timeline.csv", timeline)
    write_csv(REPO / "data/derived/stage12_dfig_ovl1_ovl2_trace.csv", trace)
    write_json(REPO / "data/validation/stage12_two_line_trip_final_audit.json", {
        "audit_name": "stage12_two_line_trip_final_audit",
        "generated_at_local": generated,
        "execution_status": "pass" if result_class == "stage12_two_line_paper_order_pass" else "review",
        "stage12_result_class": result_class,
        "event_times_s": event_times,
    })
    write_csv(REPO / "data/validation/stage12_two_line_trip_integrity_trace.csv", [
        {"check": "runtime_20s", "status": "pass" if manifest["time_end_s"] == 20.0 else "fail", "value": manifest["time_end_s"]},
        {"check": "channels_readable", "status": "pass" if readable else "fail", "value": readable},
        {"check": "result_class", "status": "pass" if result_class == "stage12_two_line_paper_order_pass" else "review", "value": result_class},
    ])
    write_csv(REPO / "data/derived/stage12_post_first_trip_tline_response.csv", post_first_rows)
    write_csv(REPO / "data/derived/stage12_post_second_trip_tline_response.csv", post_second_rows)
    write_csv(REPO / "data/derived/stage12_late_network_response.csv", late_rows)
    (REPO / "docs/STAGE12_TWO_LINE_PAPER_ORDER_RESULT.md").write_text(
        f"# Stage 12 two-line paper-order result\n\nFinal class: `{result_class}`\n\nEvent times are recorded in `data/derived/stage12_event_timeline.csv`.\n",
        encoding="utf-8",
    )
    print(json.dumps({"stage12_result_class": result_class, "event_times_s": event_times}, indent=2))


if __name__ == "__main__":
    main()
