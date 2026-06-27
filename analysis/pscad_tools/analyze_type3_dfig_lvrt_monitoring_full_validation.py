"""Analyze Type-3 DFIG LVRT monitoring validation output files.

The tool is read-only.  It parses a scenario-local 3IBR.inf and matching
3IBR_*.out files, rebuilds the PGB mapping from the .inf file, and reports
available LVRT monitoring signals without hard-coding output file numbers or
columns.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import re
from dataclasses import dataclass
from pathlib import Path


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
        index = int(match.group(1))
        desc = match.group(2)
        mapping.setdefault(desc, Pgb(index=index, desc=desc))
    return mapping


def out_file_and_column(pgb_index: int) -> tuple[str, int]:
    zero_based = pgb_index - 1
    file_index = zero_based // 10 + 1
    col_index = zero_based % 10 + 2
    return f"3IBR_{file_index:02d}.out", col_index


def read_signal(case_dir: Path, pgb: Pgb) -> list[tuple[float, float]]:
    out_name, col = out_file_and_column(pgb.index)
    out_path = case_dir / out_name
    if not out_path.exists():
        return []
    rows: list[tuple[float, float]] = []
    with out_path.open("r", encoding="utf-8", errors="replace") as f:
        for line in f:
            parts = line.split()
            if len(parts) <= col - 1:
                continue
            try:
                rows.append((float(parts[0]), float(parts[col - 1])))
            except ValueError:
                continue
    return rows


def first_crossing(samples: list[tuple[float, float]], threshold: float = 0.5) -> float | None:
    for t, v in samples:
        if v >= threshold:
            return t
    return None


def stable_mean(samples: list[tuple[float, float]], start: float, end: float) -> float | None:
    vals = [v for t, v in samples if start <= t <= end and math.isfinite(v)]
    if not vals:
        return None
    return sum(vals) / len(vals)


def min_value(samples: list[tuple[float, float]]) -> float | None:
    vals = [v for _, v in samples if math.isfinite(v)]
    return min(vals) if vals else None


def analyze_case(case_dir: Path, scenario_id: str) -> dict[str, object]:
    inf = case_dir / "3IBR.inf"
    if not inf.exists():
        return {"scenario_id": scenario_id, "run_status": "unavailable", "reason": f"missing {inf}"}
    mapping = parse_inf(inf)
    series = {
        name: read_signal(case_dir, mapping[name])
        for name in SIGNALS
        if name in mapping
    }
    lowv = series.get("DFIG_LVRT_LOWV", [])
    lowv_times = [t for t, v in lowv if v >= 0.5]
    lowv_start = min(lowv_times) if lowv_times else None
    lowv_end = max(lowv_times) if lowv_times else None
    brk = series.get("DFIG_BRK_STATE", [])
    brk_changed = None
    if brk:
        first = brk[0][1]
        brk_changed = any(abs(v - first) > 0.5 for _, v in brk)
    result = {
        "scenario_id": scenario_id,
        "run_status": "parsed",
        "available_signals": sorted(series),
        "missing_signals": [name for name in SIGNALS if name not in mapping],
        "Vs_steady_pu": stable_mean(series.get("VIBR1_2", []), 1.8, 2.0),
        "Vs_min_pu": min_value(series.get("VIBR1_2", [])),
        "lowv_start_s": lowv_start,
        "lowv_end_s": lowv_end,
        "vsmin_min_pu": min_value(series.get("DFIG_LVRT_VSMIN_MEM", [])),
        "tallow_s": stable_mean(series.get("DFIG_LVRT_TALLOW_S", []), 2.1, 3.0),
        "immtrip_time_s": first_crossing(series.get("DFIG_LVRT_IMMTRIP", [])),
        "duration_exceeded_time_s": first_crossing(series.get("DFIG_LVRT_DURATION_EXCEEDED", [])),
        "trip_request_time_s": first_crossing(series.get("DFIG_LVRT_TRIP_REQUEST", [])),
        "trip_latch_time_s": first_crossing(series.get("DFIG_LVRT_TRIP_LATCH", [])),
        "dfig_brk_state_changed": brk_changed,
        "acceptance_status": "unavailable",
        "notes": "Signals not present in this fallback run are reported as unavailable, not pass.",
    }
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("case_dirs", nargs="*", type=Path, default=[Path(r"C:\pscad_work\pnnl_39_3ibr_pscad46_strip5\PSCAD\3IBR.gf46")])
    parser.add_argument("--json-out", type=Path)
    parser.add_argument("--csv-out", type=Path)
    args = parser.parse_args()

    results = [analyze_case(path, path.name) for path in args.case_dirs]
    if args.json_out:
        args.json_out.parent.mkdir(parents=True, exist_ok=True)
        args.json_out.write_text(json.dumps(results, indent=2, ensure_ascii=False), encoding="utf-8")
    if args.csv_out:
        args.csv_out.parent.mkdir(parents=True, exist_ok=True)
        fields = [
            "scenario_id", "run_status", "Vs_steady_pu", "Vs_min_pu", "lowv_start_s",
            "lowv_end_s", "vsmin_min_pu", "tallow_s", "immtrip_time_s",
            "duration_exceeded_time_s", "trip_request_time_s", "trip_latch_time_s",
            "dfig_brk_state_changed", "acceptance_status", "notes",
        ]
        with args.csv_out.open("w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fields)
            writer.writeheader()
            for item in results:
                writer.writerow({field: item.get(field) for field in fields})
    print(json.dumps(results, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
