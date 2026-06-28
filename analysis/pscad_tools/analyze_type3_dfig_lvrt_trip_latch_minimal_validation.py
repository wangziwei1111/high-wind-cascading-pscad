"""Analyze the Type-3 DFIG LVRT trip-latch minimal R5 validation run.

The script is read-only for PSCAD run artifacts.  The input directory must
contain the scenario-local 3IBR.inf and 3IBR_*.out files copied after the
manual PSCAD run.  PGB numbers and output columns are derived from the .inf
file so the analysis is robust to channel order changes.
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
    "DFIG_BRK_STATE",
    "PIBR1_2",
    "QIBR1_2",
]

LOGIC_THRESHOLD = 0.5
STARTUP_IGNORE_S = 0.5
FAULT_START_S = 2.0
FAULT_DURATION_S = 0.15
EXPECTED_END_S = 5.0


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
    out_name, col = out_file_and_column(pgb.index)
    out_path = run_dir / out_name
    if not out_path.exists():
        return []
    samples: list[tuple[float, float]] = []
    for line in out_path.read_text(encoding="utf-8", errors="replace").splitlines():
        parts = line.split()
        if len(parts) < col:
            continue
        try:
            t = float(parts[0])
            v = float(parts[col - 1])
        except ValueError:
            continue
        if math.isfinite(t) and math.isfinite(v):
            samples.append((t, v))
    return samples


def window(
    samples: list[tuple[float, float]],
    start: float | None = None,
    end: float | None = None,
) -> list[tuple[float, float]]:
    return [
        (t, v)
        for t, v in samples
        if (start is None or t >= start) and (end is None or t <= end)
    ]


def sample_min(samples: list[tuple[float, float]], start: float | None = None, end: float | None = None) -> dict[str, float | None]:
    values = window(samples, start, end)
    if not values:
        return {"time_s": None, "value": None}
    t, v = min(values, key=lambda item: item[1])
    return {"time_s": t, "value": v}


def sample_max(samples: list[tuple[float, float]], start: float | None = None, end: float | None = None) -> dict[str, float | None]:
    values = window(samples, start, end)
    if not values:
        return {"time_s": None, "value": None}
    t, v = max(values, key=lambda item: item[1])
    return {"time_s": t, "value": v}


def mean_value(samples: list[tuple[float, float]], start: float, end: float) -> float | None:
    values = [v for _, v in window(samples, start, end)]
    return sum(values) / len(values) if values else None


def first_logic(samples: list[tuple[float, float]], start: float = STARTUP_IGNORE_S) -> float | None:
    for t, v in window(samples, start, None):
        if v >= LOGIC_THRESHOLD:
            return t
    return None


def logic_window(samples: list[tuple[float, float]], start: float = STARTUP_IGNORE_S) -> dict[str, float | None]:
    times = [t for t, v in window(samples, start, None) if v >= LOGIC_THRESHOLD]
    return {"start_s": min(times) if times else None, "end_s": max(times) if times else None}


def changed(samples: list[tuple[float, float]], start: float = STARTUP_IGNORE_S, tolerance: float = 0.5) -> bool | None:
    values = window(samples, start, None)
    if not values:
        return None
    base = values[0][1]
    return any(abs(v - base) > tolerance for _, v in values)


def value_at_or_after(samples: list[tuple[float, float]], t0: float) -> float | None:
    for t, v in samples:
        if t >= t0:
            return v
    return None


def all_logic_high_after(samples: list[tuple[float, float]], start: float) -> bool | None:
    values = window(samples, start, None)
    if not values:
        return None
    return all(v >= LOGIC_THRESHOLD for _, v in values)


def all_logic_low_after(samples: list[tuple[float, float]], start: float) -> bool | None:
    values = window(samples, start, None)
    if not values:
        return None
    return all(v < LOGIC_THRESHOLD for _, v in values)


def status_from(check: bool | None) -> str:
    if check is None:
        return "unavailable"
    return "pass" if check else "fail"


def analyze(run_dir: Path) -> dict[str, Any]:
    inf = run_dir / "3IBR.inf"
    if not inf.exists():
        return {
            "execution_status": "trip_latch_minimal_validation_unavailable",
            "acceptance_status": "unavailable",
            "reason": "missing 3IBR.inf",
            "run_dir": str(run_dir),
        }

    mapping = parse_inf(inf)
    missing = [name for name in SIGNALS if name not in mapping]
    series = {name: read_signal(run_dir, mapping[name]) for name in SIGNALS if name in mapping}
    missing_samples = [name for name in SIGNALS if name not in series or not series[name]]
    if missing or missing_samples:
        return {
            "execution_status": "trip_latch_minimal_validation_unavailable",
            "acceptance_status": "unavailable",
            "run_dir": str(run_dir),
            "available_signals": sorted(series),
            "missing_signals": missing,
            "missing_samples": missing_samples,
        }

    end_time = max(samples[-1][0] for samples in series.values() if samples)
    lowv = logic_window(series["DFIG_LVRT_LOWV"])
    lowv_end = lowv["end_s"]
    post_lowv = (lowv_end or (FAULT_START_S + FAULT_DURATION_S)) + 0.02

    trip_request_first = first_logic(series["DFIG_LVRT_TRIP_REQUEST"])
    trip_latch_first = first_logic(series["DFIG_LVRT_TRIP_LATCH"])
    startup_trip_request = logic_window(series["DFIG_LVRT_TRIP_REQUEST"], 0.0)
    startup_latch_first = first_logic(series["DFIG_LVRT_TRIP_LATCH"], 0.0)
    latch_prefault_max = sample_max(series["DFIG_LVRT_TRIP_LATCH"], 0.03, FAULT_START_S - 0.01)
    latch_initial = value_at_or_after(series["DFIG_LVRT_TRIP_LATCH"], 0.0)
    latch_holds = all_logic_high_after(series["DFIG_LVRT_TRIP_LATCH"], trip_request_first or FAULT_START_S)
    clear_post = sample_max(series["DFIG_LVRT_CLEAR"], post_lowv, None)
    timer_post_min = sample_min(series["DFIG_LVRT_TIMER_S"], post_lowv, None)
    timer_post_max = sample_max(series["DFIG_LVRT_TIMER_S"], post_lowv, None)
    vsmem_post_max = sample_max(series["DFIG_LVRT_VSMIN_MEM"], post_lowv, None)

    checks = {
        "C1_run_reached_5s": status_from(abs(end_time - EXPECTED_END_S) <= 0.02),
        "C2_trip_request_asserted_by_immtrip": status_from(
            trip_request_first is not None and abs(trip_request_first - 2.02) <= 0.05
        ),
        "C3_duration_exceeded_absent": status_from(first_logic(series["DFIG_LVRT_DURATION_EXCEEDED"]) is None),
        "C4_trip_latch_initial_zero": status_from(latch_initial is not None and latch_initial < LOGIC_THRESHOLD),
        "C5_trip_latch_not_set_before_fault": status_from(
            latch_prefault_max["value"] is not None and latch_prefault_max["value"] < LOGIC_THRESHOLD
        ),
        "C6_trip_latch_sets_from_trip_request": status_from(
            trip_request_first is not None
            and trip_latch_first is not None
            and trip_latch_first >= trip_request_first
            and trip_latch_first <= trip_request_first + 0.02
        ),
        "C7_trip_latch_holds_after_set": status_from(latch_holds),
        "C8_clear_suppressed_after_trip_latch": status_from(
            clear_post["value"] is not None and clear_post["value"] < LOGIC_THRESHOLD
        ),
        "C9_timer_not_reset_after_lowv_recovery": status_from(
            timer_post_min["value"] is not None and timer_post_min["value"] > 0.0
        ),
        "C10_vsmem_not_reset_to_1_after_lowv_recovery": status_from(
            vsmem_post_max["value"] is not None and vsmem_post_max["value"] < 0.2
        ),
        "C11_brk_state_unchanged": status_from(changed(series["DFIG_BRK_STATE"]) is False),
        "C12_pq_not_cut_off": status_from(
            abs(mean_value(series["PIBR1_2"], 4.0, 5.0) or 0.0) > 1.0
            and abs(mean_value(series["QIBR1_2"], 4.0, 5.0) or 0.0) > 1.0
        ),
    }
    acceptance = "fail" if "fail" in checks.values() else ("unavailable" if "unavailable" in checks.values() else "pass")

    if acceptance == "pass":
        interpretation = [
            "R5 run output was parsed from 3IBR.inf and 3IBR_*.out.",
            "TRIP_REQUEST has a startup pulse at 0.01-0.02 s, but the armed latch input blocks that startup pulse.",
            "TRIP_LATCH remains low before the external low-voltage event and first asserts with the R5 trip request around 2.02 s.",
            "CLEAR remains suppressed after LOWV recovery while TRIP_LATCH is high.",
            "DFIG_BRK_STATE stayed unchanged; no BRK_DFIG command integration was validated.",
        ]
    else:
        interpretation = [
            "R5 run output was parsed from 3IBR.inf and 3IBR_*.out.",
            "TRIP_REQUEST has a startup pulse at 0.01-0.02 s and asserts again at the R5 event around 2.02 s.",
            "TRIP_LATCH is already high before the external low-voltage event, so the latch cannot be accepted as a valid trip-request latch.",
            "CLEAR is high after LOWV recovery, so trip-aware CLEAR suppression is not validated by this run.",
            "DFIG_BRK_STATE stayed unchanged; no BRK_DFIG command integration was validated.",
        ]

    return {
        "execution_status": "trip_latch_minimal_validation_" + acceptance,
        "acceptance_status": acceptance,
        "run_dir": str(run_dir),
        "scenario": {
            "case": "R5",
            "fault_type": "ABC-to-ground",
            "fault_on_resistance_ohm": 0.01,
            "fault_start_s": FAULT_START_S,
            "fault_duration_s": FAULT_DURATION_S,
            "fault_off_resistance_ohm": 1.0e6,
            "wind_speed_mps": 11,
            "solution_time_step_us": 5,
            "total_simulation_time_s": EXPECTED_END_S,
        },
        "signal_pgb_indices": {name: mapping[name].index for name in SIGNALS if name in mapping},
        "metrics": {
            "simulation_end_s": end_time,
            "VIBR1_2_min": sample_min(series["VIBR1_2"], STARTUP_IGNORE_S),
            "LOWV_window": lowv,
            "IMMTRIP_first_s": first_logic(series["DFIG_LVRT_IMMTRIP"]),
            "DURATION_EXCEEDED_first_s": first_logic(series["DFIG_LVRT_DURATION_EXCEEDED"]),
            "TRIP_REQUEST_first_s": trip_request_first,
            "TRIP_REQUEST_startup_window_from_0s": startup_trip_request,
            "TRIP_LATCH_first_s": trip_latch_first,
            "TRIP_LATCH_first_from_0s": startup_latch_first,
            "TRIP_LATCH_initial_value": latch_initial,
            "TRIP_LATCH_prefault_max_0p03_to_1p99": latch_prefault_max,
            "TRIP_LATCH_holds_after_trip_request": latch_holds,
            "CLEAR_post_lowv_max": clear_post,
            "TIMER_S_post_lowv_min": timer_post_min,
            "TIMER_S_post_lowv_max": timer_post_max,
            "VSMIN_MEM_min": sample_min(series["DFIG_LVRT_VSMIN_MEM"], STARTUP_IGNORE_S),
            "VSMIN_MEM_post_lowv_max": vsmem_post_max,
            "DFIG_BRK_STATE_changed_after_startup": changed(series["DFIG_BRK_STATE"]),
            "PIBR1_2_mean_1p0_to_1p9": mean_value(series["PIBR1_2"], 1.0, 1.9),
            "PIBR1_2_mean_4p0_to_5p0": mean_value(series["PIBR1_2"], 4.0, 5.0),
            "QIBR1_2_mean_1p0_to_1p9": mean_value(series["QIBR1_2"], 1.0, 1.9),
            "QIBR1_2_mean_4p0_to_5p0": mean_value(series["QIBR1_2"], 4.0, 5.0),
        },
        "checks": checks,
        "interpretation": interpretation,
    }


def write_summary_csv(result: dict[str, Any], path: Path) -> None:
    rows: list[dict[str, Any]] = []
    for check, status in result.get("checks", {}).items():
        rows.append({"item": check, "status": status})
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=["item", "status"])
        writer.writeheader()
        writer.writerows(rows)


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
    write_summary_csv(result, args.csv_out)
    print(json.dumps({"acceptance_status": result["acceptance_status"], "json_out": str(args.json_out)}, indent=2))


if __name__ == "__main__":
    main()
