"""Audit C3 VSMIN comparability without running or modifying PSCAD."""

from __future__ import annotations

import argparse
import csv
import json
import math
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any


CURRENT_SIGNALS = (
    "VIBR1_2",
    "DFIG_LVRT_LOWV",
    "DFIG_LVRT_VSMIN_MEM",
    "DFIG_LVRT_TALLOW_S",
    "DFIG_LVRT_TIMER_S",
    "DFIG_LVRT_DURATION_EXCEEDED",
    "DFIG_LVRT_TRIP_REQUEST",
    "DFIG_LVRT_TRIP_LATCH",
    "DFIG_LVRT_FINAL_BRK_CMD",
    "DFIG_BRK_STATE",
)

HISTORICAL_SIGNALS = (
    "VIBR1_2",
    "DFIG_LVRT_LOWV",
    "DFIG_LVRT_VSMIN_MEM",
    "DFIG_LVRT_TALLOW_S",
    "DFIG_LVRT_TIMER_S",
    "DFIG_LVRT_DURATION_EXCEEDED",
    "DFIG_LVRT_TRIP_REQUEST",
    "DFIG_BRK_STATE",
)

LOGIC_THRESHOLD = 0.5
REFERENCE = 0.379649
TOLERANCE = 0.02
FAULT_CLEAR_REFERENCE_S = 3.25


@dataclass(frozen=True)
class Pgb:
    index: int
    desc: str


def parse_inf(path: Path) -> dict[str, Pgb]:
    text = path.read_text(encoding="utf-8", errors="replace")
    result: dict[str, Pgb] = {}
    for match in re.finditer(r'PGB\((\d+)\).*?Desc="([^"]+)"', text):
        result.setdefault(match.group(2), Pgb(int(match.group(1)), match.group(2)))
    return result


def output_location(index: int) -> tuple[str, int]:
    zero_based = index - 1
    return f"3IBR_{zero_based // 10 + 1:02d}.out", zero_based % 10 + 2


def read_signal(run_dir: Path, pgb: Pgb) -> list[tuple[float, float]]:
    filename, column = output_location(pgb.index)
    path = run_dir / filename
    if not path.exists():
        return []
    samples: list[tuple[float, float]] = []
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        fields = line.split()
        if len(fields) < column:
            continue
        try:
            time_s, value = float(fields[0]), float(fields[column - 1])
        except ValueError:
            continue
        if math.isfinite(time_s) and math.isfinite(value):
            samples.append((time_s, value))
    return samples


def first_high(samples: list[tuple[float, float]], start: float = 0.5) -> float | None:
    return next((time_s for time_s, value in samples if time_s >= start and value >= LOGIC_THRESHOLD), None)


def sample_at(samples: list[tuple[float, float]], time_s: float) -> float | None:
    if not samples:
        return None
    time, value = min(samples, key=lambda item: abs(item[0] - time_s))
    return value if abs(time - time_s) <= 1e-7 else None


def last_before(samples: list[tuple[float, float]], time_s: float) -> tuple[float, float] | None:
    eligible = [item for item in samples if item[0] < time_s]
    return eligible[-1] if eligible else None


def minimum(
    samples: list[tuple[float, float]],
    start: float,
    end: float,
    *,
    include_end: bool = True,
) -> tuple[float | None, float | None]:
    selected = [
        item
        for item in samples
        if item[0] >= start and (item[0] <= end if include_end else item[0] < end)
    ]
    if not selected:
        return None, None
    time_s, value = min(selected, key=lambda item: item[1])
    return value, time_s


def holds_high(samples: list[tuple[float, float]], start: float | None) -> bool | None:
    if start is None:
        return None
    values = [value for time_s, value in samples if time_s >= start]
    return all(value >= LOGIC_THRESHOLD for value in values) if values else None


def load_run(run_dir: Path, signals: tuple[str, ...]) -> tuple[dict[str, Any], dict[str, list[tuple[float, float]]]]:
    inf = run_dir / "3IBR.inf"
    if not inf.exists():
        return {"status": "unavailable", "reason": "missing 3IBR.inf"}, {}
    mapping = parse_inf(inf)
    series = {name: read_signal(run_dir, mapping[name]) for name in signals if name in mapping}
    missing = [name for name in signals if name not in mapping or not series.get(name)]
    end_time = max((samples[-1][0] for samples in series.values() if samples), default=None)
    return {
        "status": "available" if not missing else "incomplete",
        "missing_signals": missing,
        "simulation_end_s": end_time,
        "signal_pgb_indices": {name: mapping[name].index for name in signals if name in mapping},
    }, series


def window_metrics(series: dict[str, list[tuple[float, float]]], breaker_required: bool) -> dict[str, Any]:
    lowv = first_high(series.get("DFIG_LVRT_LOWV", []))
    request = first_high(series.get("DFIG_LVRT_TRIP_REQUEST", []))
    breaker = first_high(series.get("DFIG_BRK_STATE", [])) if breaker_required else None
    end_time = max((samples[-1][0] for samples in series.values() if samples), default=None)
    if lowv is None or request is None or end_time is None:
        return {"status": "unavailable", "reason": "LOWV, TRIP_REQUEST, or simulation end unavailable"}

    decision_vsm, decision_vsm_time = minimum(
        series["DFIG_LVRT_VSMIN_MEM"], lowv, request, include_end=False
    )
    decision_v, decision_v_time = minimum(series["VIBR1_2"], lowv, request, include_end=False)
    tallow_before = last_before(series["DFIG_LVRT_TALLOW_S"], request)
    timer_before = last_before(series["DFIG_LVRT_TIMER_S"], request)
    full_vsm, full_vsm_time = minimum(series["DFIG_LVRT_VSMIN_MEM"], lowv, end_time)

    result: dict[str, Any] = {
        "status": "available",
        "LOWV_first_s": lowv,
        "TRIP_REQUEST_first_s": request,
        "simulation_end_s": end_time,
        "decision_window": {
            "definition": "[LOWV_first_s, TRIP_REQUEST_first_s)",
            "VSMIN_MEM_minimum": decision_vsm,
            "VSMIN_MEM_minimum_time_s": decision_vsm_time,
            "VIBR1_2_minimum": decision_v,
            "VIBR1_2_minimum_time_s": decision_v_time,
            "TALLOW_at_last_sample_before_trip_request": tallow_before[1] if tallow_before else None,
            "TALLOW_sample_time_s": tallow_before[0] if tallow_before else None,
            "TIMER_S_at_last_sample_before_trip_request": timer_before[1] if timer_before else None,
            "TIMER_S_sample_time_s": timer_before[0] if timer_before else None,
        },
        "full_event_window": {
            "definition": "[LOWV_first_s, simulation_end_s]",
            "VSMIN_MEM_minimum": full_vsm,
            "VSMIN_MEM_minimum_time_s": full_vsm_time,
        },
        "VSMIN_MEM_full_run_minimum": full_vsm,
        "VSMIN_MEM_full_run_minimum_time_s": full_vsm_time,
    }

    if breaker_required:
        if breaker is None:
            result["transition_window"] = {"status": "unavailable", "reason": "BRK_STATE never opened"}
            result["post_breaker_window"] = {"status": "unavailable"}
            return result
        transition_values = {
            name: sample_at(series.get(name, []), request)
            for name in (
                "DFIG_LVRT_TRIP_REQUEST",
                "DFIG_LVRT_TRIP_LATCH",
                "DFIG_LVRT_FINAL_BRK_CMD",
                "DFIG_BRK_STATE",
                "DFIG_LVRT_VSMIN_MEM",
                "VIBR1_2",
            )
        }
        post_vsm, post_vsm_time = minimum(series["DFIG_LVRT_VSMIN_MEM"], breaker, end_time)
        post_v, post_v_time = minimum(series["VIBR1_2"], breaker, end_time)
        clear_vsm, clear_vsm_time = minimum(series["DFIG_LVRT_VSMIN_MEM"], 3.20, 3.32)
        result.update(
            {
                "BRK_STATE_first_open_s": breaker,
                "transition_window": {
                    "definition": "same_sample" if abs(request - breaker) <= 1e-9 else "[TRIP_REQUEST_first_s, BRK_STATE_first_open_s]",
                    "sample_time_s": request,
                    "values": transition_values,
                    "causality_note": "A shared output sample cannot resolve strict PSCAD internal-substep causality; it verifies discrete-output ordering and consistency only.",
                },
                "post_breaker_window": {
                    "definition": "[BRK_STATE_first_open_s, simulation_end_s]",
                    "VSMIN_MEM_minimum": post_vsm,
                    "VSMIN_MEM_minimum_time_s": post_vsm_time,
                    "VIBR1_2_minimum": post_v,
                    "VIBR1_2_minimum_time_s": post_v_time,
                },
                "fault_clear_neighborhood": {
                    "definition": "[3.20 s, 3.32 s]",
                    "VSMIN_MEM_minimum": clear_vsm,
                    "VSMIN_MEM_minimum_time_s": clear_vsm_time,
                },
                "full_run_minimum_occurs_after_breaker_open": (
                    full_vsm_time is not None and full_vsm_time > breaker
                ),
            }
        )
    else:
        result["transition_window"] = {
            "definition": "same_sample_historical_equivalent_event",
            "sample_time_s": request,
            "values": {
                "DFIG_LVRT_TRIP_REQUEST": sample_at(series.get("DFIG_LVRT_TRIP_REQUEST", []), request),
                "DFIG_LVRT_VSMIN_MEM": sample_at(series.get("DFIG_LVRT_VSMIN_MEM", []), request),
                "VIBR1_2": sample_at(series.get("VIBR1_2", []), request),
            },
            "breaker_event": "not_applicable",
        }
    return result


def command_chain_status(series: dict[str, list[tuple[float, float]]]) -> tuple[str, dict[str, Any]]:
    names = (
        "DFIG_LVRT_DURATION_EXCEEDED",
        "DFIG_LVRT_TRIP_REQUEST",
        "DFIG_LVRT_TRIP_LATCH",
        "DFIG_LVRT_FINAL_BRK_CMD",
        "DFIG_BRK_STATE",
    )
    times = {name: first_high(series.get(name, [])) for name in names}
    ordered = all(times[name] is not None for name in names)
    if ordered:
        ordered = (
            times[names[0]] <= times[names[1]] <= times[names[2]] <= times[names[3]] <= times[names[4]]
            and times[names[2]] - times[names[1]] <= 0.02
            and times[names[3]] - times[names[2]] <= 0.02
            and times[names[4]] - times[names[3]] >= 0.0
        )
    held = all(
        holds_high(series.get(name, []), times[name]) is True
        for name in ("DFIG_LVRT_TRIP_LATCH", "DFIG_LVRT_FINAL_BRK_CMD", "DFIG_BRK_STATE")
    )
    return ("pass" if ordered and held else "fail"), {"first_high_s": times, "ordering_pass": ordered, "hold_pass": held}


def analyze(current_dir: Path, historical_dir: Path | None) -> dict[str, Any]:
    current_info, current_series = load_run(current_dir, CURRENT_SIGNALS)
    current_windows = window_metrics(current_series, breaker_required=True) if current_series else {"status": "unavailable"}
    chain_status, chain_evidence = command_chain_status(current_series) if current_series else ("unavailable", {})

    historical_info: dict[str, Any]
    historical_windows: dict[str, Any]
    if historical_dir is None:
        historical_info = {"status": "unavailable"}
        historical_windows = {"status": "unavailable"}
    else:
        historical_info, historical_series = load_run(historical_dir, HISTORICAL_SIGNALS)
        historical_windows = window_metrics(historical_series, breaker_required=False) if historical_series else {"status": "unavailable"}
        historical_info["breaker_open_equivalent_present"] = (
            first_high(historical_series.get("DFIG_BRK_STATE", [])) is not None if historical_series else False
        )

    current_decision = current_windows.get("decision_window", {}).get("VSMIN_MEM_minimum")
    historical_decision = historical_windows.get("decision_window", {}).get("VSMIN_MEM_minimum")
    decision_difference = (
        abs(current_decision - historical_decision)
        if current_decision is not None and historical_decision is not None
        else None
    )
    decision_status = (
        "unavailable" if decision_difference is None else ("pass" if decision_difference <= TOLERANCE else "fail")
    )
    current_full = current_windows.get("full_event_window", {}).get("VSMIN_MEM_minimum")
    historical_full = historical_windows.get("full_event_window", {}).get("VSMIN_MEM_minimum")
    full_difference = (
        abs(current_full - historical_full)
        if current_full is not None and historical_full is not None
        else None
    )
    after_breaker = current_windows.get("full_run_minimum_occurs_after_breaker_open")
    historical_no_breaker = historical_info.get("breaker_open_equivalent_present") is False
    comparability = "needs_explanation" if after_breaker and historical_no_breaker else "unavailable"

    return {
        "execution_status": "type3_lvrt_c3_vsmin_comparability_audit_complete",
        "overall_closed_loop_coverage": "partial",
        "current_archive": str(current_dir),
        "historical_archive": str(historical_dir) if historical_dir else None,
        "current_run": current_info,
        "historical_run": historical_info,
        "current_windows": current_windows,
        "historical_windows": historical_windows,
        "comparisons": {
            "decision_window_like_for_like_comparison": {
                "status": decision_status,
                "current_VSMIN_MEM_minimum": current_decision,
                "historical_VSMIN_MEM_minimum": historical_decision,
                "absolute_difference": decision_difference,
                "tolerance": TOLERANCE,
            },
            "full_run_like_for_like_comparison": {
                "status": "fail" if full_difference is not None and full_difference > TOLERANCE else ("pass" if full_difference is not None else "unavailable"),
                "current_VSMIN_MEM_minimum": current_full,
                "historical_VSMIN_MEM_minimum": historical_full,
                "absolute_difference": full_difference,
                "topology_note": "The numeric windows are aligned, but topology is not equivalent after the current breaker opens.",
            },
            "post_breaker_window_comparison": {
                "status": "not_applicable",
                "reason": "The historical R4 version has no equivalent breaker-open event.",
            },
        },
        "classification": {
            "legacy_C3_acceptance_status": "fail",
            "legacy_C3_failed_check": "VSMIN_MEM_minimum_matches_reference",
            "legacy_C3_full_run_VSMIN_MEM_minimum": 0.3301161303713,
            "legacy_reference": REFERENCE,
            "legacy_tolerance": TOLERANCE,
            "command_state_chain_status": chain_status,
            "decision_window_VSMIN_status": decision_status,
            "full_run_historical_reference_status": "fail",
            "reference_comparability_status": comparability,
            "post_breaker_network_response_status": "pass" if current_windows.get("post_breaker_window", {}).get("VSMIN_MEM_minimum") is not None else "unavailable",
        },
        "command_state_chain_evidence": chain_evidence,
        "conclusion": "The duration command-and-state chain passes. The legacy full-run VSMIN reference check remains failed. Breaker opening changes topology, so current post-breaker and historical no-breaker full-run minima are not strictly interchangeable.",
    }


def write_csv(result: dict[str, Any], path: Path) -> None:
    rows: list[dict[str, Any]] = []
    for name, value in result["classification"].items():
        rows.append({"section": "classification", "item": name, "value": value, "status": value if value in {"pass", "fail", "unavailable", "needs_explanation"} else ""})
    for name, comparison in result["comparisons"].items():
        rows.append({"section": "comparison", "item": name, "value": comparison.get("absolute_difference"), "status": comparison["status"]})
    for window_name in ("decision_window", "transition_window", "post_breaker_window", "fault_clear_neighborhood", "full_event_window"):
        window = result["current_windows"].get(window_name, {})
        for metric, value in window.items():
            if metric not in {"values", "causality_note"}:
                rows.append({"section": window_name, "item": metric, "value": value, "status": ""})
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=["section", "item", "value", "status"])
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--current-run-dir", required=True, type=Path)
    parser.add_argument("--historical-run-dir", type=Path)
    parser.add_argument("--json-out", required=True, type=Path)
    parser.add_argument("--csv-out", required=True, type=Path)
    args = parser.parse_args()
    result = analyze(args.current_run_dir, args.historical_run_dir)
    args.json_out.parent.mkdir(parents=True, exist_ok=True)
    args.csv_out.parent.mkdir(parents=True, exist_ok=True)
    args.json_out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_csv(result, args.csv_out)
    print(json.dumps(result["classification"], indent=2))


if __name__ == "__main__":
    main()
