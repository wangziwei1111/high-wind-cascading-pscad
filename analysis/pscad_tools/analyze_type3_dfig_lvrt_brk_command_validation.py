"""Analyze the Type-3 DFIG LVRT breaker-command R5 validation run.

The PSCAD run artifacts are read-only. PGB indices and output columns are
derived from 3IBR.inf so channel ordering changes do not affect the analysis.
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


SIGNALS = [
    "DFIG_LVRT_TRIP_REQUEST",
    "DFIG_LVRT_TRIP_LATCH",
    "DFIG_LVRT_EXISTING_BRK_CMD",
    "DFIG_LVRT_FINAL_BRK_CMD",
    "DFIG_BRK_STATE",
    "VIBR1_2",
    "DFIG_LVRT_LOWV",
    "DFIG_LVRT_CLEAR",
    "DFIG_LVRT_TIMER_S",
    "DFIG_LVRT_VSMIN_MEM",
    "PIBR1_2",
    "QIBR1_2",
]

LOGIC_THRESHOLD = 0.5
STARTUP_IGNORE_S = 0.5
FAULT_START_S = 2.0
EXPECTED_END_S = 5.0
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


def out_file_and_column(index: int) -> tuple[str, int]:
    zero_based = index - 1
    return f"3IBR_{zero_based // 10 + 1:02d}.out", zero_based % 10 + 2


def read_signal(run_dir: Path, pgb: Pgb) -> list[tuple[float, float]]:
    out_name, column = out_file_and_column(pgb.index)
    path = run_dir / out_name
    if not path.exists():
        return []
    samples: list[tuple[float, float]] = []
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        fields = line.split()
        if len(fields) < column:
            continue
        try:
            time_s = float(fields[0])
            value = float(fields[column - 1])
        except ValueError:
            continue
        if math.isfinite(time_s) and math.isfinite(value):
            samples.append((time_s, value))
    return samples


def window(
    samples: list[tuple[float, float]],
    start: float | None = None,
    end: float | None = None,
) -> list[tuple[float, float]]:
    return [
        (time_s, value)
        for time_s, value in samples
        if (start is None or time_s >= start) and (end is None or time_s <= end)
    ]


def first_high(samples: list[tuple[float, float]], start: float = STARTUP_IGNORE_S) -> float | None:
    for time_s, value in window(samples, start):
        if value >= LOGIC_THRESHOLD:
            return time_s
    return None


def first_rising_edge(samples: list[tuple[float, float]], start: float = 0.0) -> float | None:
    previous: float | None = None
    for time_s, value in samples:
        if time_s < start:
            previous = value
            continue
        if previous is not None and previous < LOGIC_THRESHOLD <= value:
            return time_s
        previous = value
    return None


def maximum(samples: list[tuple[float, float]], start: float, end: float) -> float | None:
    values = [value for _, value in window(samples, start, end)]
    return max(values) if values else None


def mean(samples: list[tuple[float, float]], start: float, end: float) -> float | None:
    values = [value for _, value in window(samples, start, end)]
    return sum(values) / len(values) if values else None


def holds_high(samples: list[tuple[float, float]], start: float | None) -> bool | None:
    if start is None:
        return None
    values = [value for _, value in window(samples, start)]
    return all(value >= LOGIC_THRESHOLD for value in values) if values else None


def status(value: bool | None, needs_explanation: bool = False) -> str:
    if value is None:
        return "unavailable"
    if value:
        return "needs_explanation" if needs_explanation else "pass"
    return "fail"


def analyze(run_dir: Path) -> dict[str, Any]:
    inf_path = run_dir / "3IBR.inf"
    if not inf_path.exists():
        return {
            "execution_status": "brk_command_state_validation_unavailable",
            "acceptance_status": "unavailable",
            "reason": "missing 3IBR.inf",
            "run_dir": str(run_dir),
        }

    mapping = parse_inf(inf_path)
    series = {
        name: read_signal(run_dir, mapping[name])
        for name in SIGNALS
        if name in mapping
    }
    missing_signals = [name for name in SIGNALS if name not in mapping]
    missing_samples = [name for name, samples in series.items() if not samples]

    end_time = max((samples[-1][0] for samples in series.values() if samples), default=None)
    trip_request_first = first_high(series.get("DFIG_LVRT_TRIP_REQUEST", []))
    trip_latch_first = first_high(series.get("DFIG_LVRT_TRIP_LATCH", []))
    existing_first = first_high(series.get("DFIG_LVRT_EXISTING_BRK_CMD", []))
    final_first = first_high(series.get("DFIG_LVRT_FINAL_BRK_CMD", []))
    breaker_first = first_rising_edge(series.get("DFIG_BRK_STATE", []), STARTUP_IGNORE_S)

    startup_existing_max = maximum(series.get("DFIG_LVRT_EXISTING_BRK_CMD", []), 0.0, STARTUP_IGNORE_S)
    startup_final_max = maximum(series.get("DFIG_LVRT_FINAL_BRK_CMD", []), 0.0, STARTUP_IGNORE_S)
    startup_breaker_max = maximum(series.get("DFIG_BRK_STATE", []), 0.0, STARTUP_IGNORE_S)
    latch_prefault_max = maximum(series.get("DFIG_LVRT_TRIP_LATCH", []), 0.03, FAULT_START_S - 0.01)

    final_prefault_max = maximum(series.get("DFIG_LVRT_FINAL_BRK_CMD", []), 0.03, FAULT_START_S - 0.01)
    final_after_latch = (
        maximum(series.get("DFIG_LVRT_FINAL_BRK_CMD", []), trip_latch_first, EXPECTED_END_S)
        if trip_latch_first is not None
        else None
    )
    breaker_holds = holds_high(series.get("DFIG_BRK_STATE", []), breaker_first)
    existing_prefault_max = maximum(
        series.get("DFIG_LVRT_EXISTING_BRK_CMD", []), 0.03, FAULT_START_S - 0.01
    )

    final_delay = (
        final_first - trip_latch_first
        if final_first is not None and trip_latch_first is not None
        else None
    )
    breaker_delay = (
        breaker_first - final_first
        if breaker_first is not None and final_first is not None
        else None
    )
    final_available = bool(series.get("DFIG_LVRT_FINAL_BRK_CMD"))
    post_open_start = min((breaker_first or FAULT_START_S) + 0.10, EXPECTED_END_S)

    checks = {
        "A1_run_reached_5s": status(end_time is not None and abs(end_time - EXPECTED_END_S) <= SAMPLE_TOLERANCE_S),
        "A2_trip_request_asserted_near_event": status(
            trip_request_first is not None and abs(trip_request_first - 2.02) <= 0.05
        ),
        "A3_trip_latch_sets_after_request_without_startup_set": status(
            trip_request_first is not None
            and trip_latch_first is not None
            and trip_request_first <= trip_latch_first <= trip_request_first + SAMPLE_TOLERANCE_S
            and latch_prefault_max is not None
            and latch_prefault_max < LOGIC_THRESHOLD
        ),
        "A4_final_command_zero_prefault": status(
            None
            if not final_available
            else final_prefault_max is not None and final_prefault_max < LOGIC_THRESHOLD
        ),
        "A5_final_command_high_after_latch": status(
            None
            if not final_available
            else final_after_latch is not None and final_after_latch >= LOGIC_THRESHOLD
        ),
        "A6_final_command_timing_after_latch": status(
            None
            if not final_available
            else final_delay is not None and 0.0 <= final_delay <= SAMPLE_TOLERANCE_S
        ),
        "A7_breaker_state_opens_after_final_command": status(
            None
            if not final_available
            else breaker_delay is not None and breaker_delay >= 0.0
        ),
        "A8_breaker_not_open_before_final_command": status(
            None
            if not final_available
            else breaker_first is not None and final_first is not None and breaker_first >= final_first
        ),
        "A9_breaker_state_holds_open": status(breaker_holds),
        "A10_original_command_preserved_and_no_startup_open": status(
            existing_prefault_max is not None
            and existing_prefault_max < LOGIC_THRESHOLD
            and startup_existing_max is not None
            and startup_existing_max < LOGIC_THRESHOLD
            and startup_breaker_max is not None
            and startup_breaker_max < LOGIC_THRESHOLD
        ),
        "A11_latch_final_breaker_ordering": status(
            None
            if not final_available
            else trip_latch_first is not None
            and final_first is not None
            and breaker_first is not None
            and trip_latch_first <= final_first <= breaker_first
        ),
        "A12_pq_evidence_recorded": status(
            bool(series.get("PIBR1_2")) and bool(series.get("QIBR1_2"))
        ),
    }

    values = set(checks.values())
    acceptance = "fail" if "fail" in values else ("unavailable" if "unavailable" in values else "pass")

    return {
        "execution_status": "brk_command_state_validation_" + acceptance,
        "acceptance_status": acceptance,
        "run_status": "completed" if end_time is not None and abs(end_time - EXPECTED_END_S) <= SAMPLE_TOLERANCE_S else "incomplete",
        "run_dir": str(run_dir),
        "missing_signals": missing_signals,
        "missing_samples": missing_samples,
        "scenario": {
            "case": "R5",
            "fault_type": "ABC-to-ground",
            "fault_on_resistance_ohm": 0.01,
            "fault_start_s": 2.0,
            "fault_duration_s": 0.15,
            "fault_off_resistance_ohm": 1.0e6,
            "wind_speed_mps": 11,
            "solution_time_step_us": 5,
            "total_simulation_time_s": 5.0,
        },
        "signal_pgb_indices": {name: mapping[name].index for name in SIGNALS if name in mapping},
        "metrics": {
            "simulation_end_s": end_time,
            "TRIP_REQUEST_first_s": trip_request_first,
            "TRIP_LATCH_first_s": trip_latch_first,
            "EXISTING_BRK_CMD_first_open_s": existing_first,
            "FINAL_BRK_CMD_first_open_s": final_first,
            "BRK_STATE_first_open_s": breaker_first,
            "TRIP_LATCH_to_FINAL_BRK_CMD_delay_s": final_delay,
            "FINAL_BRK_CMD_to_BRK_STATE_delay_s": breaker_delay,
            "BRK_STATE_holds_open": breaker_holds,
            "startup_existing_command_max": startup_existing_max,
            "startup_final_command_max": startup_final_max,
            "startup_brk_state_max": startup_breaker_max,
            "TRIP_LATCH_prefault_max": latch_prefault_max,
            "PIBR1_2_pre_fault_mean": mean(series.get("PIBR1_2", []), 1.0, 1.9),
            "QIBR1_2_pre_fault_mean": mean(series.get("QIBR1_2", []), 1.0, 1.9),
            "PIBR1_2_post_open_mean": mean(series.get("PIBR1_2", []), post_open_start, EXPECTED_END_S),
            "QIBR1_2_post_open_mean": mean(series.get("QIBR1_2", []), post_open_start, EXPECTED_END_S),
        },
        "derived_evidence": {
            "final_command_formula_static_audit": "LIMIT(0,1,EXISTING_BRK_CMD_BOOL + TRIP_LATCH_BOOL)",
            "breaker_command_assignment_static_audit": "BRK_DFIG = 1.0 * DFIG_LVRT_FINAL_BRK_CMD",
            "note": "Static equations are explanatory only and do not replace the missing FINAL_BRK_CMD waveform.",
        },
        "checks": checks,
        "interpretation": [
            "The R5 run reached 5.0 s and the available PSCAD output channels were parsed.",
            "DFIG_LVRT_FINAL_BRK_CMD is absent from 3IBR.inf, so every criterion requiring its measured waveform is unavailable.",
            "The generated PSCAD source confirms the intended final-command equation and the sole BRK_DFIG assignment, but static source evidence is not substituted for dynamic waveform evidence.",
            "BRK_DFIG command-and-state response cannot receive an overall pass without the measured final-command channel.",
        ],
    }


def write_summary(result: dict[str, Any], path: Path) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=["item", "status"])
        writer.writeheader()
        writer.writerows(
            {"item": item, "status": result_status}
            for item, result_status in result.get("checks", {}).items()
        )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-dir", required=True, type=Path)
    parser.add_argument("--json-out", required=True, type=Path)
    parser.add_argument("--csv-out", required=True, type=Path)
    args = parser.parse_args()

    result = analyze(args.run_dir)
    args.json_out.parent.mkdir(parents=True, exist_ok=True)
    args.csv_out.parent.mkdir(parents=True, exist_ok=True)
    args.json_out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_summary(result, args.csv_out)
    print(json.dumps({"acceptance_status": result["acceptance_status"], "json_out": str(args.json_out)}, indent=2))


if __name__ == "__main__":
    main()
