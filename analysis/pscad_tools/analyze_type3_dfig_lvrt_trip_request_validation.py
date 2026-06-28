"""Analyze Type-3 DFIG LVRT trip-request monitoring runs.

The script is intentionally read-only for PSCAD artifacts.  It parses a
scenario-local ``3IBR.inf`` file, rebuilds the PGB-to-output mapping, and then
loads the matching ``3IBR_*.out`` files without hard-coding PGB numbers, output
file numbers, or column numbers.
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


def first_crossing(samples: list[tuple[float, float]], threshold: float = 0.5) -> float | None:
    for t, v in samples:
        if v >= threshold:
            return t
    return None


def min_sample(samples: list[tuple[float, float]]) -> dict[str, float | None]:
    finite = [(t, v) for t, v in samples if math.isfinite(v)]
    if not finite:
        return {"time_s": None, "value": None}
    t, v = min(finite, key=lambda item: item[1])
    return {"time_s": t, "value": v}


def max_sample(samples: list[tuple[float, float]]) -> dict[str, float | None]:
    finite = [(t, v) for t, v in samples if math.isfinite(v)]
    if not finite:
        return {"time_s": None, "value": None}
    t, v = max(finite, key=lambda item: item[1])
    return {"time_s": t, "value": v}


def mean_in_window(samples: list[tuple[float, float]], start: float, end: float) -> float | None:
    values = [v for t, v in samples if start <= t <= end and math.isfinite(v)]
    return sum(values) / len(values) if values else None


def active_window(samples: list[tuple[float, float]], threshold: float = 0.5) -> dict[str, float | None]:
    times = [t for t, v in samples if v >= threshold]
    return {"start_s": min(times) if times else None, "end_s": max(times) if times else None}


def monotonic_nonincreasing(samples: list[tuple[float, float]], start: float | None, end: float | None) -> bool | None:
    if start is None or end is None:
        return None
    values = [v for t, v in samples if start <= t <= end and math.isfinite(v)]
    if len(values) < 2:
        return None
    return all(values[i] <= values[i - 1] + 1e-6 for i in range(1, len(values)))


def analyze_case(case_dir: Path, scenario_id: str) -> dict[str, Any]:
    inf = case_dir / "3IBR.inf"
    if not inf.exists():
        return {"scenario_id": scenario_id, "run_status": "unavailable", "reason": "missing 3IBR.inf"}
    mapping = parse_inf(inf)
    series = {name: read_signal(case_dir, mapping[name]) for name in SIGNALS if name in mapping}
    lowv_window = active_window(series.get("DFIG_LVRT_LOWV", []))
    brk = series.get("DFIG_BRK_STATE", [])
    brk_changed = None
    if brk:
        first = brk[0][1]
        brk_changed = any(abs(v - first) > 0.5 for _, v in brk)
    required = [
        "DFIG_LVRT_TALLOW_S",
        "DFIG_LVRT_DURATION_EXCEEDED",
        "DFIG_LVRT_TRIP_REQUEST",
    ]
    missing = [name for name in SIGNALS if name not in mapping]
    return {
        "scenario_id": scenario_id,
        "run_status": "parsed",
        "available_signals": sorted(series),
        "missing_signals": missing,
        "acceptance_status": "unavailable" if any(name in missing for name in required) else "pending_rules",
        "Vs_steady_pu": mean_in_window(series.get("VIBR1_2", []), 1.8, 2.0),
        "Vs_min": min_sample(series.get("VIBR1_2", [])),
        "LOWV": lowv_window,
        "VSMIN_MEM_min": min_sample(series.get("DFIG_LVRT_VSMIN_MEM", [])),
        "TALLOW_min": min_sample(series.get("DFIG_LVRT_TALLOW_S", [])),
        "TALLOW_max": max_sample(series.get("DFIG_LVRT_TALLOW_S", [])),
        "TALLOW_nonincreasing_during_LOWV": monotonic_nonincreasing(
            series.get("DFIG_LVRT_TALLOW_S", []), lowv_window["start_s"], lowv_window["end_s"]
        ),
        "IMMTRIP_first_s": first_crossing(series.get("DFIG_LVRT_IMMTRIP", [])),
        "DURATION_EXCEEDED_first_s": first_crossing(series.get("DFIG_LVRT_DURATION_EXCEEDED", [])),
        "TRIP_REQUEST_first_s": first_crossing(series.get("DFIG_LVRT_TRIP_REQUEST", [])),
        "DFIG_BRK_STATE_changed": brk_changed,
        "P_pre_mean": mean_in_window(series.get("PIBR1_2", []), 1.8, 2.0),
        "Q_pre_mean": mean_in_window(series.get("QIBR1_2", []), 1.8, 2.0),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("case_dirs", nargs="*", type=Path)
    parser.add_argument("--json-out", type=Path)
    parser.add_argument("--csv-out", type=Path)
    args = parser.parse_args()
    case_dirs = args.case_dirs or [Path(r"C:\pscad_work\pnnl_39_3ibr_pscad46_strip5\PSCAD\3IBR.gf46")]
    results = [analyze_case(path, path.name) for path in case_dirs]
    if args.json_out:
        args.json_out.parent.mkdir(parents=True, exist_ok=True)
        args.json_out.write_text(json.dumps(results, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    if args.csv_out:
        args.csv_out.parent.mkdir(parents=True, exist_ok=True)
        fields = ["scenario_id", "run_status", "acceptance_status", "available_signals", "missing_signals"]
        with args.csv_out.open("w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fields)
            writer.writeheader()
            for row in results:
                writer.writerow({field: row.get(field) for field in fields})
    print(json.dumps(results, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
