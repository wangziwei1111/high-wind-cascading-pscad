#!/usr/bin/env python3
"""Replay an abstract external LVRT trip request against saved PSCAD outputs.

This script is intentionally read-only with respect to PSCAD artifacts. It
parses a scenario-local 3IBR.inf and saved 3IBR_*.out files, reads VIBR1_2,
and applies the project LVRT timer rule offline. It predicts only abstract
trip_request/trip_latch behavior; it does not imply BRK_DFIG opened in PSCAD.
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any

from analyze_type3_dfig_fault_resistance_sweep import get_signal, parse_inf


def parse_duration_from_scenario_id(scenario_id: str) -> float | None:
    match = re.search(r"_d(\d+)p(\d+)$", scenario_id)
    if not match:
        return None
    return float(f"{int(match.group(1))}.{match.group(2)}")


def t_vrt(
    vs_pu: float,
    v_trip_immediate_pu: float,
    v_event_start_pu: float,
    t_at_0p20_s: float,
    t_at_0p90_s: float,
) -> float | None:
    if vs_pu <= v_trip_immediate_pu:
        return 0.0
    if vs_pu >= v_event_start_pu:
        return None
    slope = (t_at_0p90_s - t_at_0p20_s) / (v_event_start_pu - v_trip_immediate_pu)
    return t_at_0p20_s + (vs_pu - v_trip_immediate_pu) * slope


def replay_lvrt_trip(
    times: list[float],
    values: list[float],
    args: argparse.Namespace,
) -> dict[str, Any]:
    event_active = False
    event_start_time: float | None = None
    event_end_time: float | None = None
    vs_min_latched: float | None = None
    trip_latch = False
    trip_request = False
    trip_time: float | None = None
    trip_cause: str | None = None
    event_elapsed_at_trip: float | None = None
    t_allow_at_trip: float | None = None
    recovery_reset_before_trip = False
    events: list[dict[str, Any]] = []
    current_event: dict[str, Any] | None = None

    for t, v in zip(times, values):
        if t < args.fault_start_s:
            continue

        if not event_active and not trip_latch and v < args.v_event_start_pu:
            event_active = True
            event_start_time = t
            event_end_time = None
            vs_min_latched = v
            current_event = {
                "start_time_s": t,
                "end_time_s": None,
                "Vs_min_latched_pu": v,
                "recovered_without_trip": False,
            }

        if not event_active or event_start_time is None or vs_min_latched is None:
            continue

        if v < vs_min_latched:
            vs_min_latched = v
            if current_event is not None:
                current_event["Vs_min_latched_pu"] = v

        if not trip_latch:
            elapsed = t - event_start_time
            allow = t_vrt(
                vs_min_latched,
                args.v_trip_immediate_pu,
                args.v_event_start_pu,
                args.t_at_0p20_s,
                args.t_at_0p90_s,
            )
            if allow == 0.0:
                trip_request = True
                trip_latch = True
                trip_time = t
                trip_cause = "immediate_low_voltage"
                event_elapsed_at_trip = elapsed
                t_allow_at_trip = allow
                if current_event is not None:
                    current_event["trip_time_s"] = t
                    current_event["trip_cause"] = trip_cause
            elif allow is not None and elapsed >= allow:
                trip_request = True
                trip_latch = True
                trip_time = t
                trip_cause = "duration_exceeded"
                event_elapsed_at_trip = elapsed
                t_allow_at_trip = allow
                if current_event is not None:
                    current_event["trip_time_s"] = t
                    current_event["trip_cause"] = trip_cause

        if v >= args.v_event_start_pu:
            event_end_time = t
            if current_event is not None:
                current_event["end_time_s"] = t
                if not trip_latch:
                    current_event["recovered_without_trip"] = True
                    recovery_reset_before_trip = True
                events.append(current_event)
                current_event = None
            event_active = False
            if not trip_latch:
                event_start_time = None
                vs_min_latched = None

    if current_event is not None:
        events.append(current_event)

    final_vs_min = None
    if events:
        final_vs_min = min(event["Vs_min_latched_pu"] for event in events if event.get("Vs_min_latched_pu") is not None)
    elif values:
        final_vs_min = min(values)

    final_t_allow = (
        t_vrt(
            final_vs_min,
            args.v_trip_immediate_pu,
            args.v_event_start_pu,
            args.t_at_0p20_s,
            args.t_at_0p90_s,
        )
        if final_vs_min is not None
        else None
    )

    fault_clear_time = None
    trip_before_fault_clear = None
    if args.fault_duration_s is not None:
        fault_clear_time = args.fault_start_s + args.fault_duration_s
        if trip_time is not None:
            trip_before_fault_clear = trip_time <= fault_clear_time

    return {
        "event_count": len(events),
        "events": events,
        "event_start_time_s": events[0]["start_time_s"] if events else None,
        "event_end_time_s": events[0].get("end_time_s") if events else None,
        "Vs_min_latched_pu": final_vs_min,
        "t_allow_s": final_t_allow,
        "event_elapsed_at_trip_s": event_elapsed_at_trip,
        "abstract_trip_request": trip_request,
        "trip_latch": trip_latch,
        "trip_time_s": trip_time,
        "trip_cause": trip_cause,
        "fault_clear_time_s": fault_clear_time,
        "trip_before_fault_clear": trip_before_fault_clear,
        "recovery_reset_before_trip": recovery_reset_before_trip,
        "no_auto_reset_after_trip": trip_latch,
    }


def build_result(args: argparse.Namespace) -> dict[str, Any]:
    case_dir = Path(args.case_dir).resolve()
    inf_path = case_dir / "3IBR.inf"
    pgbs = parse_inf(inf_path)
    matches = [pgb for pgb in pgbs if pgb.desc == "VIBR1_2"]
    if not matches:
        raise RuntimeError(f"VIBR1_2 not found in {inf_path}")
    pgb = matches[0]
    times, values = get_signal(case_dir, pgb)
    if not times:
        raise RuntimeError(f"No VIBR1_2 samples found in {case_dir}")

    duration = args.fault_duration_s
    if duration is None:
        duration = parse_duration_from_scenario_id(args.scenario_id)
    args.fault_duration_s = duration

    replay = replay_lvrt_trip(times, values, args)
    return {
        "task": "offline_external_lvrt_trip_replay",
        "scenario_id": args.scenario_id,
        "case_dir": str(case_dir),
        "fault_start_s": args.fault_start_s,
        "fault_duration_s": duration,
        "fault_ohm": args.fault_ohm,
        "rule": {
            "V_trip_immediate_pu": args.v_trip_immediate_pu,
            "V_event_start_pu": args.v_event_start_pu,
            "t_at_0p20_s": args.t_at_0p20_s,
            "t_at_0p90_s": args.t_at_0p90_s,
            "timer_method": "minimum-voltage latch within continuous low-voltage event",
        },
        "VIBR1_2_mapping": {
            "pgb": pgb.index,
            "group": pgb.group,
            "unit": pgb.units,
            "out_file": pgb.out_file,
            "column": pgb.column,
        },
        "output_end_time_s": times[-1],
        "replay": replay,
        "limitations": [
            "Offline prediction only; PSCAD LVRT logic was not implemented.",
            "abstract_trip_request does not mean BRK_DFIG opened.",
            "VIBR1_2 is a candidate external POC voltage input; final PSCAD control wiring and filtering remain unconfirmed.",
        ],
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--case-dir", required=True)
    parser.add_argument("--scenario-id", required=True)
    parser.add_argument("--fault-start-s", type=float, required=True)
    parser.add_argument("--fault-duration-s", type=float)
    parser.add_argument("--fault-ohm", type=float, default=0.10)
    parser.add_argument("--output-json", required=True)
    parser.add_argument("--v-trip-immediate-pu", type=float, default=0.20)
    parser.add_argument("--v-event-start-pu", type=float, default=0.90)
    parser.add_argument("--t-at-0p20-s", type=float, default=0.625)
    parser.add_argument("--t-at-0p90-s", type=float, default=2.0)
    args = parser.parse_args()

    result = build_result(args)
    output_path = Path(args.output_json).resolve()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(
        f"{args.scenario_id}: trip={result['replay']['abstract_trip_request']} "
        f"time={result['replay']['trip_time_s']} cause={result['replay']['trip_cause']}"
    )


if __name__ == "__main__":
    main()
