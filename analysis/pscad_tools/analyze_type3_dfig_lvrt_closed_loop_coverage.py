"""Analyze Type-3 DFIG external-LVRT closed-loop coverage runs.

Each archived scenario is decoded from its own PSCAD ``3IBR.inf`` file.  PGB
indices, output file numbers, and columns are therefore never hard-coded.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any


SIGNALS = (
    "VIBR1_2",
    "DFIG_LVRT_LOWV",
    "DFIG_LVRT_IMMTRIP",
    "DFIG_LVRT_CLEAR",
    "DFIG_LVRT_TIMER_S",
    "DFIG_LVRT_VSMIN_MEM",
    "DFIG_LVRT_TALLOW_S",
    "DFIG_LVRT_DURATION_EXCEEDED",
    "DFIG_LVRT_TRIP_REQUEST",
    "DFIG_LVRT_TRIP_LATCH",
    "DFIG_LVRT_EXISTING_BRK_CMD",
    "DFIG_LVRT_FINAL_BRK_CMD",
    "DFIG_BRK_STATE",
    "PIBR1_2",
    "QIBR1_2",
)

SCENARIOS = {
    "C1": {
        "directory": "C1_no_fault_5s",
        "expected_end_s": 5.0,
        "fault_start_s": None,
        "fault_clear_s": None,
    },
    "C2": {
        "directory": "C2_R2_ride_through",
        "expected_end_s": 8.0,
        "fault_start_s": 2.0,
        "fault_clear_s": 2.75,
    },
    "C3": {
        "directory": "C3_R4_duration_trip_breaker",
        "expected_end_s": 8.0,
        "fault_start_s": 2.0,
        "fault_clear_s": 3.25,
    },
}

LOGIC = 0.5
STARTUP_END_S = 0.5
SAMPLE_TOLERANCE_S = 0.02


@dataclass(frozen=True)
class Pgb:
    index: int
    desc: str


def parse_inf(path: Path) -> dict[str, Pgb]:
    text = path.read_text(encoding="utf-8", errors="replace")
    mapping: dict[str, Pgb] = {}
    for match in re.finditer(r'PGB\((\d+)\).*?Desc="([^"]+)"', text):
        mapping.setdefault(match.group(2), Pgb(int(match.group(1)), match.group(2)))
    return mapping


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


def values(
    samples: list[tuple[float, float]], start: float | None = None, end: float | None = None
) -> list[float]:
    return [
        value
        for time_s, value in samples
        if (start is None or time_s >= start) and (end is None or time_s <= end)
    ]


def extreme(
    samples: list[tuple[float, float]], function: Any, start: float | None = None, end: float | None = None
) -> float | None:
    selected = values(samples, start, end)
    return function(selected) if selected else None


def mean(samples: list[tuple[float, float]], start: float, end: float) -> float | None:
    selected = values(samples, start, end)
    return sum(selected) / len(selected) if selected else None


def first_high(samples: list[tuple[float, float]], start: float = STARTUP_END_S) -> float | None:
    for time_s, value in samples:
        if time_s >= start and value >= LOGIC:
            return time_s
    return None


def first_falling_after(samples: list[tuple[float, float]], start: float | None) -> float | None:
    if start is None:
        return None
    previous: float | None = None
    for time_s, value in samples:
        if time_s < start:
            previous = value
            continue
        if previous is not None and previous >= LOGIC > value:
            return time_s
        previous = value
    return None


def lowv_interval(samples: list[tuple[float, float]]) -> tuple[float | None, float | None]:
    start = first_high(samples)
    return start, first_falling_after(samples, start)


def held_high(samples: list[tuple[float, float]], start: float | None) -> bool | None:
    if start is None:
        return None
    selected = values(samples, start)
    return all(value >= LOGIC for value in selected) if selected else None


def check(condition: bool | None) -> str:
    if condition is None:
        return "unavailable"
    return "pass" if condition else "fail"


def low_after_start(samples: list[tuple[float, float]]) -> bool | None:
    maximum = extreme(samples, max, STARTUP_END_S)
    return None if maximum is None else maximum < LOGIC


def near(value: float | None, reference: float, tolerance: float) -> bool | None:
    return None if value is None else abs(value - reference) <= tolerance


def analyze_scenario(name: str, run_root: Path) -> dict[str, Any]:
    config = SCENARIOS[name]
    run_dir = run_root / config["directory"]
    inf_path = run_dir / "3IBR.inf"
    if not inf_path.exists():
        return {
            "run_status": "unavailable",
            "acceptance_status": "unavailable",
            "run_dir": str(run_dir),
            "missing_signals": list(SIGNALS),
            "checks": {"artifacts_available": "unavailable"},
        }

    mapping = parse_inf(inf_path)
    series = {signal: read_signal(run_dir, mapping[signal]) for signal in SIGNALS if signal in mapping}
    missing_signals = [signal for signal in SIGNALS if signal not in mapping or not series.get(signal)]
    end_time = max((samples[-1][0] for samples in series.values() if samples), default=None)
    expected_end = config["expected_end_s"]
    lowv_start, lowv_end = lowv_interval(series.get("DFIG_LVRT_LOWV", []))

    first = {
        "IMMTRIP_first_s": first_high(series.get("DFIG_LVRT_IMMTRIP", [])),
        "DURATION_EXCEEDED_first_s": first_high(series.get("DFIG_LVRT_DURATION_EXCEEDED", [])),
        "TRIP_REQUEST_first_s": first_high(series.get("DFIG_LVRT_TRIP_REQUEST", [])),
        "TRIP_LATCH_first_s": first_high(series.get("DFIG_LVRT_TRIP_LATCH", [])),
        "FINAL_BRK_CMD_first_s": first_high(series.get("DFIG_LVRT_FINAL_BRK_CMD", [])),
        "BRK_STATE_first_open_s": first_high(series.get("DFIG_BRK_STATE", [])),
    }
    minima = {
        "VIBR1_2_minimum": extreme(series.get("VIBR1_2", []), min, STARTUP_END_S),
        "VSMIN_MEM_minimum": extreme(series.get("DFIG_LVRT_VSMIN_MEM", []), min, STARTUP_END_S),
    }
    tallow_min = extreme(series.get("DFIG_LVRT_TALLOW_S", []), min, STARTUP_END_S)
    tallow_max = extreme(series.get("DFIG_LVRT_TALLOW_S", []), max, STARTUP_END_S)
    startup_max = {
        signal: extreme(series.get(signal, []), max, 0.03, STARTUP_END_S)
        for signal in (
            "DFIG_LVRT_TRIP_LATCH",
            "DFIG_LVRT_FINAL_BRK_CMD",
            "DFIG_BRK_STATE",
        )
    }
    fault_start = config["fault_start_s"] or 2.0
    pre_start, pre_end = 1.0, min(1.9, fault_start - 0.1)
    post_start = min((config["fault_clear_s"] or 2.0) + 1.0, expected_end - 0.5)
    power = {
        "PIBR1_2_pre_fault_mean": mean(series.get("PIBR1_2", []), pre_start, pre_end),
        "QIBR1_2_pre_fault_mean": mean(series.get("QIBR1_2", []), pre_start, pre_end),
        "PIBR1_2_post_event_mean": mean(series.get("PIBR1_2", []), post_start, expected_end),
        "QIBR1_2_post_event_mean": mean(series.get("QIBR1_2", []), post_start, expected_end),
    }

    checks: dict[str, str] = {
        "all_required_signals_available": check(not missing_signals),
        "simulation_reached_expected_end": check(
            end_time is not None and abs(end_time - expected_end) <= SAMPLE_TOLERANCE_S
        ),
    }
    if name == "C1":
        for signal in (
            "DFIG_LVRT_LOWV",
            "DFIG_LVRT_IMMTRIP",
            "DFIG_LVRT_DURATION_EXCEEDED",
            "DFIG_LVRT_TRIP_REQUEST",
            "DFIG_LVRT_TRIP_LATCH",
            "DFIG_LVRT_EXISTING_BRK_CMD",
            "DFIG_LVRT_FINAL_BRK_CMD",
            "DFIG_BRK_STATE",
        ):
            checks[f"{signal}_remains_low"] = check(low_after_start(series.get(signal, [])))
        vmin = minima["VIBR1_2_minimum"]
        vmax = extreme(series.get("VIBR1_2", []), max, STARTUP_END_S)
        checks["voltage_normal_steady_state"] = check(
            None if vmin is None or vmax is None else 0.90 <= vmin <= vmax <= 1.10
        )
        clear_max = extreme(series.get("DFIG_LVRT_CLEAR", []), max, STARTUP_END_S)
        checks["clear_semantics_available"] = check(
            None if clear_max is None else clear_max >= LOGIC
        )
        p_post = power["PIBR1_2_post_event_mean"]
        checks["active_power_not_cut_off"] = check(None if p_post is None else abs(p_post) >= 10.0)
    elif name == "C2":
        checks.update(
            {
                "LOWV_event_present": check(lowv_start is not None and lowv_end is not None),
                "VIBR1_2_minimum_matches_reference": check(near(minima["VIBR1_2_minimum"], 0.459160, 0.02)),
                "VSMIN_MEM_minimum_matches_reference": check(near(minima["VSMIN_MEM_minimum"], 0.458438, 0.02)),
                "TALLOW_within_bounds": check(
                    None if tallow_min is None or tallow_max is None else tallow_min >= 0.625 and tallow_max <= 2.0
                ),
            }
        )
        for signal in (
            "DFIG_LVRT_IMMTRIP",
            "DFIG_LVRT_DURATION_EXCEEDED",
            "DFIG_LVRT_TRIP_REQUEST",
            "DFIG_LVRT_TRIP_LATCH",
            "DFIG_LVRT_FINAL_BRK_CMD",
            "DFIG_BRK_STATE",
        ):
            checks[f"{signal}_remains_low"] = check(low_after_start(series.get(signal, [])))
        recovery_start = (lowv_end or config["fault_clear_s"]) + 0.1
        clear_post = extreme(series.get("DFIG_LVRT_CLEAR", []), max, recovery_start)
        timer_post = extreme(series.get("DFIG_LVRT_TIMER_S", []), max, recovery_start)
        vsmin_post_min = extreme(series.get("DFIG_LVRT_VSMIN_MEM", []), min, recovery_start)
        vsmin_post_max = extreme(series.get("DFIG_LVRT_VSMIN_MEM", []), max, recovery_start)
        checks.update(
            {
                "CLEAR_recovers_high": check(None if clear_post is None else clear_post >= LOGIC),
                "TIMER_resets_near_zero": check(None if timer_post is None else abs(timer_post) <= 0.02),
                "VSMIN_MEM_resets_near_one": check(
                    None if vsmin_post_min is None or vsmin_post_max is None else 0.95 <= vsmin_post_min <= vsmin_post_max <= 1.05
                ),
                "active_power_not_cut_off": check(
                    None if power["PIBR1_2_post_event_mean"] is None else abs(power["PIBR1_2_post_event_mean"]) >= 10.0
                ),
            }
        )
    else:
        duration = first["DURATION_EXCEEDED_first_s"]
        request = first["TRIP_REQUEST_first_s"]
        latch = first["TRIP_LATCH_first_s"]
        final = first["FINAL_BRK_CMD_first_s"]
        breaker = first["BRK_STATE_first_open_s"]
        checks.update(
            {
                "IMMTRIP_remains_low": check(low_after_start(series.get("DFIG_LVRT_IMMTRIP", []))),
                "VSMIN_MEM_minimum_matches_reference": check(near(minima["VSMIN_MEM_minimum"], 0.379649, 0.02)),
                "TALLOW_within_bounds": check(
                    None if tallow_min is None or tallow_max is None else tallow_min >= 0.625 and tallow_max <= 2.0
                ),
                "DURATION_EXCEEDED_asserts": check(duration is not None),
                "TRIP_REQUEST_asserts_near_reference": check(near(request, 3.03780, 0.05)),
                "TRIP_REQUEST_precedes_fault_clear": check(request is not None and request < config["fault_clear_s"]),
                "duration_to_request_ordering": check(duration is not None and request is not None and duration <= request),
                "request_to_latch_delay": check(
                    request is not None and latch is not None and 0.0 <= latch - request <= 0.02
                ),
                "latch_to_final_delay": check(
                    latch is not None and final is not None and 0.0 <= final - latch <= 0.02
                ),
                "final_to_breaker_ordering": check(
                    final is not None and breaker is not None and 0.0 <= breaker - final and breaker <= expected_end
                ),
                "TRIP_LATCH_holds_high": check(held_high(series.get("DFIG_LVRT_TRIP_LATCH", []), latch)),
                "FINAL_BRK_CMD_holds_high": check(held_high(series.get("DFIG_LVRT_FINAL_BRK_CMD", []), final)),
                "BRK_STATE_holds_open": check(held_high(series.get("DFIG_BRK_STATE", []), breaker)),
                "no_startup_false_open": check(
                    all(value is not None and value < LOGIC for value in startup_max.values())
                ),
                "PQ_electrical_response_recorded": check(
                    bool(series.get("PIBR1_2")) and bool(series.get("QIBR1_2"))
                ),
            }
        )

    statuses = set(checks.values())
    acceptance = "fail" if "fail" in statuses else ("unavailable" if "unavailable" in statuses else "pass")
    return {
        "run_status": "completed" if checks["simulation_reached_expected_end"] == "pass" else "incomplete",
        "acceptance_status": acceptance,
        "run_dir": str(run_dir),
        "missing_signals": missing_signals,
        "signal_pgb_indices": {signal: mapping[signal].index for signal in SIGNALS if signal in mapping},
        "metrics": {
            "simulation_end_s": end_time,
            **minima,
            "TALLOW_minimum_s": tallow_min,
            "TALLOW_maximum_s": tallow_max,
            "LOWV_start_s": lowv_start,
            "LOWV_end_s": lowv_end,
            **first,
            "TRIP_LATCH_to_FINAL_BRK_CMD_delay_s": (
                first["FINAL_BRK_CMD_first_s"] - first["TRIP_LATCH_first_s"]
                if first["FINAL_BRK_CMD_first_s"] is not None and first["TRIP_LATCH_first_s"] is not None
                else None
            ),
            "FINAL_BRK_CMD_to_BRK_STATE_delay_s": (
                first["BRK_STATE_first_open_s"] - first["FINAL_BRK_CMD_first_s"]
                if first["BRK_STATE_first_open_s"] is not None and first["FINAL_BRK_CMD_first_s"] is not None
                else None
            ),
            "startup_maxima": startup_max,
            **power,
        },
        "checks": checks,
    }


def analyze(run_root: Path) -> dict[str, Any]:
    scenarios = {name: analyze_scenario(name, run_root) for name in SCENARIOS}
    metadata_path = run_root / "task_metadata.json"
    execution_record = None
    if metadata_path.exists():
        execution_record = json.loads(metadata_path.read_text(encoding="utf-8-sig"))
        recorded = execution_record.get("scenario_results", {})
        for name, result in scenarios.items():
            if name in recorded:
                result["execution_record"] = recorded[name]
    statuses = {result["acceptance_status"] for result in scenarios.values()}
    all_pass = statuses == {"pass"}
    return {
        "execution_status": (
            "type3_lvrt_closed_loop_coverage_pass"
            if all_pass
            else "type3_lvrt_closed_loop_coverage_partial"
        ),
        "acceptance_status": "pass" if all_pass else "partial",
        "run_root": str(run_root),
        "scenarios": scenarios,
        "execution_record": execution_record,
        "prior_R5_immediate_trip_path": "pass",
        "original_command_priority": {
            "status": "static_only",
            "statement": "Static command-composition audit passed. The original command source is constant 0 in the tested model, so a dynamic original-command-open stimulus was not performed.",
        },
        "scope_statement": "Single-machine Type-3 external LVRT closed-loop coverage is validated in PSCAD only when C1, C2, and C3 all pass.",
    }


def write_csv(result: dict[str, Any], path: Path) -> None:
    rows: list[dict[str, Any]] = []
    for scenario, scenario_result in result["scenarios"].items():
        for item, status in scenario_result.get("checks", {}).items():
            rows.append({"scenario": scenario, "item": item, "status": status})
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=["scenario", "item", "status"])
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-root", required=True, type=Path)
    parser.add_argument("--json-out", required=True, type=Path)
    parser.add_argument("--csv-out", required=True, type=Path)
    args = parser.parse_args()
    result = analyze(args.run_root)
    args.json_out.parent.mkdir(parents=True, exist_ok=True)
    args.csv_out.parent.mkdir(parents=True, exist_ok=True)
    args.json_out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_csv(result, args.csv_out)
    print(json.dumps({"execution_status": result["execution_status"], "scenarios": {name: item["acceptance_status"] for name, item in result["scenarios"].items()}}, indent=2))


if __name__ == "__main__":
    main()
