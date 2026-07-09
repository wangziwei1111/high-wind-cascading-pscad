"""Analyze manual Type-3 DFIG LVRT trip-request validation runs.

The script is read-only for PSCAD artifacts.  Each case directory must contain
the scenario-local 3IBR.inf and 3IBR_*.out files copied after that PSCAD run.
PGB numbers and output columns are derived from the .inf file for each case.
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
    "DFIG_BRK_STATE",
    "PIBR1_2",
    "QIBR1_2",
    "Edc_pu",
    "Ecap_Det",
    "BRK_CHOP",
    "S1",
]

CORE_SIGNALS = [
    "VIBR1_2",
    "DFIG_LVRT_LOWV",
    "DFIG_LVRT_IMMTRIP",
    "DFIG_LVRT_TIMER_S",
    "DFIG_LVRT_VSMIN_MEM",
    "DFIG_LVRT_TALLOW_S",
    "DFIG_LVRT_DURATION_EXCEEDED",
    "DFIG_LVRT_TRIP_REQUEST",
    "DFIG_BRK_STATE",
    "PIBR1_2",
    "QIBR1_2",
]


CASE_CONFIGS: dict[str, dict[str, Any]] = {
    "R1": {"duration_s": 5.0, "kind": "no_fault"},
    "R2": {
        "duration_s": 8.0,
        "kind": "ride_through",
        "vs_ref": 0.459160,
        "vsmem_ref": 0.458438,
        "tallow_ref": 1.132645,
    },
    "R3": {
        "duration_s": 8.0,
        "kind": "duration_trip",
        "trip_ref_s": 3.05025,
    },
    "R4": {
        "duration_s": 8.0,
        "kind": "duration_trip_before_clear",
        "vsmem_ref": 0.379649,
        "tallow_ref": 0.977883,
        "trip_ref_s": 3.03780,
        "fault_clear_s": 3.25,
    },
    "R5": {
        "duration_s": 5.0,
        "kind": "immediate_trip",
        "vs_ref": 0.057865,
    },
}

STARTUP_IGNORE_S = 0.5
LOGIC_THRESHOLD = 0.5


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


def read_signal(case_dir: Path, pgb: Pgb) -> list[tuple[float, float]]:
    out_name, col = out_file_and_column(pgb.index)
    out_path = case_dir / out_name
    if not out_path.exists():
        return []
    samples: list[tuple[float, float]] = []
    for line in out_path.read_text(encoding="utf-8", errors="replace").splitlines():
        parts = line.split()
        if len(parts) < col:
            continue
        try:
            samples.append((float(parts[0]), float(parts[col - 1])))
        except ValueError:
            continue
    return samples


def finite(samples: list[tuple[float, float]]) -> list[tuple[float, float]]:
    return [(t, v) for t, v in samples if math.isfinite(t) and math.isfinite(v)]


def window(samples: list[tuple[float, float]], start: float | None = None, end: float | None = None) -> list[tuple[float, float]]:
    return [
        (t, v)
        for t, v in finite(samples)
        if (start is None or t >= start) and (end is None or t <= end)
    ]


def mean_value(samples: list[tuple[float, float]], start: float | None = None, end: float | None = None) -> float | None:
    values = [v for _, v in window(samples, start, end)]
    return sum(values) / len(values) if values else None


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


def first_logic(samples: list[tuple[float, float]], start: float | None = None, threshold: float = LOGIC_THRESHOLD) -> float | None:
    for t, v in window(samples, start, None):
        if v >= threshold:
            return t
    return None


def logic_window(samples: list[tuple[float, float]], start: float | None = None, threshold: float = LOGIC_THRESHOLD) -> dict[str, float | None]:
    times = [t for t, v in window(samples, start, None) if v >= threshold]
    return {"start_s": min(times) if times else None, "end_s": max(times) if times else None}


def changed(samples: list[tuple[float, float]], start: float = STARTUP_IGNORE_S, tolerance: float = 0.5) -> bool | None:
    values = window(samples, start, None)
    if not values:
        return None
    base = values[0][1]
    return any(abs(v - base) > tolerance for _, v in values)


def max_rise(samples: list[tuple[float, float]], start: float | None, end: float | None) -> float | None:
    values = window(samples, start, end)
    if len(values) < 2:
        return None
    return max(values[i][1] - values[i - 1][1] for i in range(1, len(values)))


def latest_time(series: dict[str, list[tuple[float, float]]]) -> float | None:
    times = [samples[-1][0] for samples in series.values() if samples]
    return max(times) if times else None


def approx(value: float | None, target: float, tol: float) -> bool:
    return value is not None and abs(value - target) <= tol


def status_from_checks(checks: dict[str, str]) -> str:
    if any(value == "fail" for value in checks.values()):
        return "fail"
    if any(value == "unavailable" for value in checks.values()):
        return "unavailable"
    if any(value == "needs_explanation" for value in checks.values()):
        return "needs_explanation"
    return "pass"


def scenario_key(case_dir: Path) -> str:
    match = re.match(r"(R[1-5])", case_dir.name, re.IGNORECASE)
    return match.group(1).upper() if match else case_dir.name.upper()


def analyze_case(case_dir: Path) -> dict[str, Any]:
    key = scenario_key(case_dir)
    config = CASE_CONFIGS.get(key, {})
    inf = case_dir / "3IBR.inf"
    if not inf.exists():
        return {
            "scenario_id": case_dir.name,
            "case_key": key,
            "run_status": "unavailable",
            "acceptance_status": "unavailable",
            "reason": "missing 3IBR.inf",
        }

    mapping = parse_inf(inf)
    series = {name: read_signal(case_dir, mapping[name]) for name in SIGNALS if name in mapping}
    missing = [name for name in SIGNALS if name not in mapping]
    missing_core = [name for name in CORE_SIGNALS if name not in mapping or not series.get(name)]
    if missing_core:
        return {
            "scenario_id": case_dir.name,
            "case_key": key,
            "run_status": "parsed",
            "acceptance_status": "unavailable",
            "available_signals": sorted(series),
            "missing_signals": missing,
            "missing_core_signals": missing_core,
        }

    end_time = latest_time(series)
    expected_duration = config.get("duration_s")
    lowv = logic_window(series["DFIG_LVRT_LOWV"], STARTUP_IGNORE_S)
    lowv_start = lowv["start_s"]
    lowv_end = lowv["end_s"]
    tallow_min = sample_min(series["DFIG_LVRT_TALLOW_S"], STARTUP_IGNORE_S)
    tallow_max = sample_max(series["DFIG_LVRT_TALLOW_S"], STARTUP_IGNORE_S)
    tallow_fault_mean = mean_value(series["DFIG_LVRT_TALLOW_S"], lowv_start, lowv_end) if lowv_start else None
    tallow_rise = (
        max_rise(series["DFIG_LVRT_TALLOW_S"], lowv_start, lowv_end)
        if lowv_start is not None and lowv_end is not None
        else None
    )
    trip_first = first_logic(series["DFIG_LVRT_TRIP_REQUEST"], STARTUP_IGNORE_S)
    duration_first = first_logic(series["DFIG_LVRT_DURATION_EXCEEDED"], STARTUP_IGNORE_S)
    immtrip_first = first_logic(series["DFIG_LVRT_IMMTRIP"], STARTUP_IGNORE_S)

    metrics: dict[str, Any] = {
        "simulation_end_s": end_time,
        "steady_voltage_pu": mean_value(series["VIBR1_2"], 1.5, 1.95),
        "VIBR1_2_min": sample_min(series["VIBR1_2"], STARTUP_IGNORE_S),
        "LOWV_window_after_startup": lowv,
        "VSMIN_MEM_min": sample_min(series["DFIG_LVRT_VSMIN_MEM"], STARTUP_IGNORE_S),
        "TALLOW_min": tallow_min,
        "TALLOW_max": tallow_max,
        "TALLOW_fault_mean": tallow_fault_mean,
        "TALLOW_max_step_rise_during_LOWV": tallow_rise,
        "IMMTRIP_first_s": immtrip_first,
        "DURATION_EXCEEDED_first_s": duration_first,
        "TRIP_REQUEST_first_s": trip_first,
        "DFIG_BRK_STATE_changed_after_startup": changed(series["DFIG_BRK_STATE"]),
        "PIBR1_2_pre_fault_mean": mean_value(series["PIBR1_2"], 1.5, 1.95),
        "PIBR1_2_post_fault_mean": mean_value(series["PIBR1_2"], 4.0, end_time) if end_time else None,
        "QIBR1_2_pre_fault_mean": mean_value(series["QIBR1_2"], 1.5, 1.95),
        "QIBR1_2_post_fault_mean": mean_value(series["QIBR1_2"], 4.0, end_time) if end_time else None,
    }

    checks = evaluate(key, config, metrics, series)
    return {
        "scenario_id": case_dir.name,
        "case_key": key,
        "run_status": "parsed",
        "acceptance_status": status_from_checks(checks),
        "checks": checks,
        "available_signals": sorted(series),
        "missing_signals": missing,
        "metrics": metrics,
    }


def evaluate(key: str, config: dict[str, Any], metrics: dict[str, Any], series: dict[str, list[tuple[float, float]]]) -> dict[str, str]:
    checks: dict[str, str] = {}
    end_time = metrics["simulation_end_s"]
    expected_duration = config.get("duration_s")
    checks["simulation_duration"] = "pass" if expected_duration and approx(end_time, expected_duration, 0.02) else "unavailable"
    checks["breaker_state_unchanged"] = "pass" if metrics["DFIG_BRK_STATE_changed_after_startup"] is False else "fail"

    tmin = metrics["TALLOW_min"]["value"]
    tmax = metrics["TALLOW_max"]["value"]
    checks["TALLOW_within_limits"] = (
        "pass" if tmin is not None and tmax is not None and tmin >= 0.625 - 1e-6 and tmax <= 2.0 + 1e-6 else "fail"
    )

    kind = config.get("kind")
    if kind == "no_fault":
        checks["steady_voltage_about_1pu"] = "pass" if approx(metrics["steady_voltage_pu"], 1.0, 0.03) else "fail"
        checks["LOWV_absent_after_startup"] = "pass" if metrics["LOWV_window_after_startup"]["start_s"] is None else "fail"
        checks["IMMTRIP_absent_after_startup"] = "pass" if metrics["IMMTRIP_first_s"] is None else "fail"
        timer_max = sample_max(series["DFIG_LVRT_TIMER_S"], STARTUP_IGNORE_S)["value"]
        checks["TIMER_zero_after_startup"] = "pass" if timer_max is not None and timer_max <= 1e-6 else "fail"
        checks["VSMIN_MEM_about_1pu_after_startup"] = (
            "pass" if sample_min(series["DFIG_LVRT_VSMIN_MEM"], STARTUP_IGNORE_S)["value"] is not None
            and sample_min(series["DFIG_LVRT_VSMIN_MEM"], STARTUP_IGNORE_S)["value"] >= 0.98
            else "fail"
        )
        checks["TALLOW_about_2s_after_startup"] = "pass" if approx(tmin, 2.0, 0.02) and approx(tmax, 2.0, 0.02) else "fail"
        checks["DURATION_EXCEEDED_absent"] = "pass" if metrics["DURATION_EXCEEDED_first_s"] is None else "fail"
        checks["TRIP_REQUEST_absent"] = "pass" if metrics["TRIP_REQUEST_first_s"] is None else "fail"
        return checks

    lowv_start = metrics["LOWV_window_after_startup"]["start_s"]
    lowv_end = metrics["LOWV_window_after_startup"]["end_s"]
    checks["LOWV_present"] = "pass" if lowv_start is not None and lowv_end is not None else "fail"
    checks["TALLOW_nonincreasing_during_LOWV"] = (
        "pass" if metrics["TALLOW_max_step_rise_during_LOWV"] is not None
        and metrics["TALLOW_max_step_rise_during_LOWV"] <= 1e-5
        else "unavailable"
    )
    if "vs_ref" in config:
        checks["VIBR1_2_min_reference"] = (
            "pass" if approx(metrics["VIBR1_2_min"]["value"], config["vs_ref"], 0.02) else "needs_explanation"
        )
    if "vsmem_ref" in config:
        checks["VSMIN_MEM_min_reference"] = (
            "pass" if approx(metrics["VSMIN_MEM_min"]["value"], config["vsmem_ref"], 0.02) else "needs_explanation"
        )
    if key == "R2":
        vs_min = metrics["VIBR1_2_min"]["value"]
        vsmem_min = metrics["VSMIN_MEM_min"]["value"]
        checks["VSMIN_tracks_voltage_min"] = (
            "pass" if vs_min is not None and vsmem_min is not None and abs(vs_min - vsmem_min) <= 0.005 else "fail"
        )
        checks["DURATION_EXCEEDED_absent"] = "pass" if metrics["DURATION_EXCEEDED_first_s"] is None else "fail"
        checks["TRIP_REQUEST_absent"] = "pass" if metrics["TRIP_REQUEST_first_s"] is None else "fail"
    if key in {"R3", "R4"}:
        checks["IMMTRIP_absent"] = "pass" if metrics["IMMTRIP_first_s"] is None else "fail"
        checks["DURATION_EXCEEDED_present"] = "pass" if metrics["DURATION_EXCEEDED_first_s"] is not None else "fail"
        checks["TRIP_REQUEST_present"] = "pass" if metrics["TRIP_REQUEST_first_s"] is not None else "fail"
        if metrics["TRIP_REQUEST_first_s"] is not None:
            err = abs(metrics["TRIP_REQUEST_first_s"] - config["trip_ref_s"])
            checks["TRIP_REQUEST_time_reference"] = "pass" if err <= 0.05 else "needs_explanation"
        else:
            checks["TRIP_REQUEST_time_reference"] = "unavailable"
        if key == "R4":
            checks["TRIP_REQUEST_before_fault_clear"] = (
                "pass" if metrics["TRIP_REQUEST_first_s"] is not None
                and metrics["TRIP_REQUEST_first_s"] < config["fault_clear_s"]
                else "fail"
            )
    if key == "R5":
        checks["IMMTRIP_present"] = "pass" if metrics["IMMTRIP_first_s"] is not None else "fail"
        checks["TRIP_REQUEST_present"] = "pass" if metrics["TRIP_REQUEST_first_s"] is not None else "fail"
        checks["TRIP_REQUEST_from_IMMTRIP"] = (
            "pass" if metrics["IMMTRIP_first_s"] is not None and metrics["TRIP_REQUEST_first_s"] is not None
            and abs(metrics["TRIP_REQUEST_first_s"] - metrics["IMMTRIP_first_s"]) <= 0.02
            else "fail"
        )
    return checks


def flatten_for_csv(result: dict[str, Any]) -> dict[str, Any]:
    metrics = result.get("metrics", {})
    return {
        "scenario_id": result.get("scenario_id"),
        "case_key": result.get("case_key"),
        "run_status": result.get("run_status"),
        "acceptance_status": result.get("acceptance_status"),
        "simulation_end_s": metrics.get("simulation_end_s"),
        "VIBR1_2_min": (metrics.get("VIBR1_2_min") or {}).get("value"),
        "VIBR1_2_min_time_s": (metrics.get("VIBR1_2_min") or {}).get("time_s"),
        "VSMIN_MEM_min": (metrics.get("VSMIN_MEM_min") or {}).get("value"),
        "TALLOW_fault_mean": metrics.get("TALLOW_fault_mean"),
        "IMMTRIP_first_s": metrics.get("IMMTRIP_first_s"),
        "DURATION_EXCEEDED_first_s": metrics.get("DURATION_EXCEEDED_first_s"),
        "TRIP_REQUEST_first_s": metrics.get("TRIP_REQUEST_first_s"),
        "DFIG_BRK_STATE_changed": metrics.get("DFIG_BRK_STATE_changed_after_startup"),
        "missing_signals": ";".join(result.get("missing_signals", [])),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("case_dirs", nargs="*", type=Path)
    parser.add_argument("--json-out", type=Path)
    parser.add_argument("--csv-out", type=Path)
    args = parser.parse_args()
    results = [analyze_case(path) for path in args.case_dirs]
    if args.json_out:
        args.json_out.parent.mkdir(parents=True, exist_ok=True)
        args.json_out.write_text(json.dumps(results, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    if args.csv_out:
        args.csv_out.parent.mkdir(parents=True, exist_ok=True)
        rows = [flatten_for_csv(result) for result in results]
        fields = list(rows[0]) if rows else []
        with args.csv_out.open("w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fields)
            writer.writeheader()
            writer.writerows(rows)
    print(json.dumps(results, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
