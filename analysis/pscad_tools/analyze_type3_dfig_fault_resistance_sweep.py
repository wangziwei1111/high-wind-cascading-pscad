#!/usr/bin/env python3
"""Analyze Type-3 DFIG LVRT fault-resistance sweep outputs.

The script is intentionally read-only with respect to PSCAD artifacts. It
parses the current 3IBR.inf PGB list, maps every PGB to its corresponding
3IBR_XX.out file and column, and writes a structured per-scenario summary.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

try:
    import numpy as np
except Exception:  # pragma: no cover - fallback for minimal Python envs
    np = None


WINDOWS = {
    "pre_fault": (1.8, 2.0),
    "fault": (2.0, 2.15),
    "post_fault": (4.0, 5.0),
}

TARGET_SIGNALS = [
    "VIBR1_2",
    "PIBR1_2",
    "QIBR1_2",
    "SPD30",
    "DFIG_DBLK_CMD",
    "DFIG_BRK_STATE",
    "DFIG_VWIND_MS",
    "DFIG_IFLT_A_KA",
    "DFIG_IFLT_B_KA",
    "DFIG_IFLT_C_KA",
    "Edc_pu",
    "Ecap_Det",
    "BRK_CHOP",
    "S1",
    "Crowbar current:1",
    "Crowbar current:2",
    "Crowbar current:3",
    "I_RS:1",
    "I_RS:2",
    "I_RS:3",
    "Iconv:1",
    "Iconv:2",
    "Iconv:3",
    "Voltage_dip",
    "Low_Cu_Manag",
    "Imax_d_pu",
    "Id_pu_Gsc",
    "Iq_pu_Gsc",
    "Wpu",
    "Dblk_VdcCtrl",
    "Dblk_Rotor",
    "Freq_PLL",
]

SUMMARY_COLUMNS = [
    "scenario_id",
    "R_fault_ohm",
    "run_status",
    "build_errors",
    "build_warnings",
    "emtdc_completed",
    "output_end_time_s",
    "V_min_pu",
    "V_min_time_s",
    "V_fault_mean_pu",
    "V_recovery_time_s",
    "Edc_pu_peak",
    "Ecap_Det_peak_kV",
    "BRK_CHOP_active",
    "BRK_CHOP_duration_s",
    "DFIG_CROWBAR_STATE_active",
    "DFIG_CROWBAR_STATE_duration_s",
    "RSC_max_abs_current",
    "GSC_max_abs_current",
    "Crowbar_current_max_abs",
    "Wpu_pre_mean",
    "Wpu_post_mean",
    "DFIG_BRK_STATE_fault_mean",
    "DFIG_DBLK_CMD_fault_mean",
]


@dataclass
class Pgb:
    index: int
    desc: str
    group: str
    units: str
    out_file: str
    column: int


def parse_inf(inf_path: Path) -> list[Pgb]:
    pattern = re.compile(
        r'PGB\((\d+)\)\s+Output\s+Desc="([^"]*)"\s+Group="([^"]*)".*?Units="([^"]*)"'
    )
    pgbs: list[Pgb] = []
    for line in inf_path.read_text(encoding="utf-8", errors="replace").splitlines():
        match = pattern.search(line)
        if not match:
            continue
        idx = int(match.group(1))
        out_idx = (idx - 1) // 10 + 1
        col = (idx - 1) % 10 + 2  # col 1 is time; PGB columns start at 2.
        pgbs.append(
            Pgb(
                index=idx,
                desc=match.group(2),
                group=match.group(3),
                units=match.group(4),
                out_file=f"3IBR_{out_idx:02d}.out",
                column=col,
            )
        )
    if not pgbs:
        raise RuntimeError(f"No PGB entries parsed from {inf_path}")
    return pgbs


def load_out(path: Path) -> list[list[float]]:
    if np is not None:
        arr = np.loadtxt(path)
        if arr.ndim == 1:
            arr = arr.reshape(1, -1)
        return arr.tolist()
    rows: list[list[float]] = []
    for raw in path.read_text(encoding="utf-8", errors="ignore").splitlines():
        raw = raw.strip()
        if not raw:
            continue
        rows.append([float(part) for part in raw.split()])
    return rows


def get_signal(case_dir: Path, pgb: Pgb) -> tuple[list[float], list[float]]:
    out_path = case_dir / pgb.out_file
    if not out_path.exists():
        raise FileNotFoundError(out_path)
    rows = load_out(out_path)
    if not rows:
        raise RuntimeError(f"Empty out file: {out_path}")
    col_idx = pgb.column - 1
    times = [row[0] for row in rows if len(row) > col_idx]
    values = [row[col_idx] for row in rows if len(row) > col_idx]
    if not values:
        raise RuntimeError(f"Column {pgb.column} missing in {out_path}")
    return times, values


def subset(times: list[float], values: list[float], start: float, end: float) -> tuple[list[float], list[float]]:
    t_out: list[float] = []
    v_out: list[float] = []
    for t, v in zip(times, values):
        if start <= t <= end:
            t_out.append(t)
            v_out.append(v)
    return t_out, v_out


def stats(times: list[float], values: list[float]) -> dict[str, Any]:
    if not values:
        return {"count": 0}
    min_v = min(values)
    max_v = max(values)
    mean_v = sum(values) / len(values)
    abs_pairs = [(abs(v), t, v) for t, v in zip(times, values)]
    max_abs, max_abs_t, max_abs_signed = max(abs_pairs, key=lambda x: x[0])
    return {
        "count": len(values),
        "min": min_v,
        "mean": mean_v,
        "max": max_v,
        "range": max_v - min_v,
        "max_abs": max_abs,
        "max_abs_time_s": max_abs_t,
        "max_abs_signed_value": max_abs_signed,
        "min_time_s": times[values.index(min_v)],
        "max_time_s": times[values.index(max_v)],
    }


def signal_stats(times: list[float], values: list[float]) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for name, (start, end) in WINDOWS.items():
        tw, vw = subset(times, values, start, end)
        out[name] = stats(tw, vw)
    out["end_time_s"] = times[-1] if times else None
    return out


def first_stable_recovery_time(
    times: list[float],
    values: list[float],
    start: float = 2.15,
    lo: float = 0.95,
    hi: float = 1.05,
) -> float | None:
    post = [(t, v) for t, v in zip(times, values) if t >= start]
    for i, (t, v) in enumerate(post):
        if lo <= v <= hi and all(lo <= vv <= hi for _, vv in post[i:]):
            return t
    return None


def active_duration(times: list[float], values: list[float], threshold: float = 0.5) -> float:
    if len(times) < 2:
        return 0.0
    total = 0.0
    for i in range(len(times) - 1):
        if values[i] > threshold:
            total += max(0.0, times[i + 1] - times[i])
    return total


def max_abs_across(names: Iterable[str], signals: dict[str, dict[str, Any]], window: str = "fault") -> float | None:
    values = []
    for name in names:
        item = signals.get(name, {}).get("statistics", {}).get(window, {})
        val = item.get("max_abs")
        if isinstance(val, (int, float)) and math.isfinite(val):
            values.append(val)
    return max(values) if values else None


def classify_depth(v_min: float | None) -> str:
    if v_min is None:
        return "unknown"
    if v_min < 0.15:
        return "extreme_deep_relative_to_this_sweep"
    if v_min < 0.35:
        return "deep_relative_to_this_sweep"
    if v_min < 0.70:
        return "moderate_relative_to_this_sweep"
    return "shallow_relative_to_this_sweep"


def build_summary(args: argparse.Namespace) -> dict[str, Any]:
    case_dir = Path(args.case_dir).resolve()
    inf_path = Path(args.inf).resolve() if args.inf else case_dir / "3IBR.inf"
    pgbs = parse_inf(inf_path)
    by_desc: dict[str, list[Pgb]] = {}
    for pgb in pgbs:
        by_desc.setdefault(pgb.desc, []).append(pgb)

    signals: dict[str, dict[str, Any]] = {}
    missing: list[str] = []
    for desc in TARGET_SIGNALS:
        entries = by_desc.get(desc, [])
        if not entries:
            missing.append(desc)
            continue
        pgb = entries[0]
        times, values = get_signal(case_dir, pgb)
        signals[desc] = {
            "pgb": pgb.index,
            "group": pgb.group,
            "units_from_inf": pgb.units,
            "out_file": pgb.out_file,
            "column": pgb.column,
            "duplicate_count_for_desc": len(entries),
            "statistics": signal_stats(times, values),
        }

    output_end = None
    if signals:
        output_end = min(
            item["statistics"].get("end_time_s")
            for item in signals.values()
            if item["statistics"].get("end_time_s") is not None
        )

    v_item = signals.get("VIBR1_2")
    v_recovery = None
    if v_item:
        v_pgb = by_desc["VIBR1_2"][0]
        vt, vv = get_signal(case_dir, v_pgb)
        v_recovery = first_stable_recovery_time(vt, vv)

    brk_chop_duration = None
    if "BRK_CHOP" in signals:
        pgb = by_desc["BRK_CHOP"][0]
        t, v = get_signal(case_dir, pgb)
        tw, vw = subset(t, v, WINDOWS["fault"][0], WINDOWS["fault"][1])
        brk_chop_duration = active_duration(tw, vw)

    s1_duration = None
    if "S1" in signals:
        pgb = by_desc["S1"][0]
        t, v = get_signal(case_dir, pgb)
        tw, vw = subset(t, v, WINDOWS["fault"][0], WINDOWS["fault"][1])
        s1_duration = active_duration(tw, vw)

    def stat_value(desc: str, window: str, key: str) -> Any:
        return signals.get(desc, {}).get("statistics", {}).get(window, {}).get(key)

    summary_row = {
        "scenario_id": args.scenario_id,
        "R_fault_ohm": args.fault_ohm,
        "run_status": args.run_status,
        "build_errors": args.build_errors,
        "build_warnings": args.build_warnings,
        "emtdc_completed": args.emtdc_completed,
        "output_end_time_s": output_end,
        "V_min_pu": stat_value("VIBR1_2", "fault", "min"),
        "V_min_time_s": stat_value("VIBR1_2", "fault", "min_time_s"),
        "V_fault_mean_pu": stat_value("VIBR1_2", "fault", "mean"),
        "V_recovery_time_s": v_recovery if v_recovery is not None else "not_recovered_within_5s",
        "Edc_pu_peak": stat_value("Edc_pu", "fault", "max"),
        "Ecap_Det_peak_kV": stat_value("Ecap_Det", "fault", "max"),
        "BRK_CHOP_active": (stat_value("BRK_CHOP", "fault", "max") or 0) > 0.5 if "BRK_CHOP" in signals else None,
        "BRK_CHOP_duration_s": brk_chop_duration,
        "DFIG_CROWBAR_STATE_active": (stat_value("S1", "fault", "max") or 0) > 0.5 if "S1" in signals else None,
        "DFIG_CROWBAR_STATE_duration_s": s1_duration,
        "RSC_max_abs_current": max_abs_across(["I_RS:1", "I_RS:2", "I_RS:3"], signals),
        "GSC_max_abs_current": max_abs_across(["Iconv:1", "Iconv:2", "Iconv:3"], signals),
        "Crowbar_current_max_abs": max_abs_across(
            ["Crowbar current:1", "Crowbar current:2", "Crowbar current:3"], signals
        ),
        "Wpu_pre_mean": stat_value("Wpu", "pre_fault", "mean"),
        "Wpu_post_mean": stat_value("Wpu", "post_fault", "mean"),
        "DFIG_BRK_STATE_fault_mean": stat_value("DFIG_BRK_STATE", "fault", "mean"),
        "DFIG_DBLK_CMD_fault_mean": stat_value("DFIG_DBLK_CMD", "fault", "mean"),
    }
    summary_row["voltage_sag_class_relative"] = classify_depth(summary_row["V_min_pu"])
    if "Edc_pu" in signals and "Ecap_Det" in signals:
        peak_pu = summary_row["Edc_pu_peak"]
        peak_kv = summary_row["Ecap_Det_peak_kV"]
        summary_row["Edc_pu_times_1p45_kV"] = peak_pu * 1.45 if isinstance(peak_pu, (int, float)) else None
        summary_row["Edc_Ecap_peak_difference_kV"] = (
            abs(summary_row["Edc_pu_times_1p45_kV"] - peak_kv)
            if isinstance(summary_row["Edc_pu_times_1p45_kV"], (int, float)) and isinstance(peak_kv, (int, float))
            else None
        )

    return {
        "analysis_version": 1,
        "script": "analysis/pscad_tools/analyze_type3_dfig_fault_resistance_sweep.py",
        "scenario_id": args.scenario_id,
        "configuration": {
            "fault_on_resistance_ohm": args.fault_ohm,
            "fault_type": "ABC-to-ground",
            "fault_window_s": [2.0, 2.15],
            "run_duration_s": 5.0,
            "time_step_us": 5.0,
        },
        "run_status": {
            "status": args.run_status,
            "build_errors": args.build_errors,
            "build_warnings": args.build_warnings,
            "emtdc_completed": args.emtdc_completed,
            "notes": args.notes,
        },
        "source": {
            "case_dir": str(case_dir),
            "inf_path": str(inf_path),
        },
        "windows_s": WINDOWS,
        "pgb_mapping": [pgb.__dict__ for pgb in pgbs],
        "signals": signals,
        "missing_signals": missing,
        "summary": summary_row,
        "semantic_limits": [
            "Crowbar current:1..3 are confirmed as crowbar branch current, but unit is not independently confirmed if the PSCAD component does not expose a unit label.",
            "Crowbar current positive direction remains unconfirmed unless explicitly observed in the GUI.",
            "Exact A/B/C mapping of vector indices 1..3 remains unconfirmed unless explicitly observed in the GUI.",
            "DFIG_IFLT_A/B/C_KA are external fault-element currents, not internal converter or crowbar branch currents.",
            "Freq_PLL is a Type-3 internal PLL candidate and is not a substitute for system frequency.",
        ],
    }


def write_csv(summary_files: list[Path], csv_path: Path) -> None:
    rows = []
    for path in summary_files:
        data = json.loads(path.read_text(encoding="utf-8"))
        rows.append(data["summary"])
    with csv_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=SUMMARY_COLUMNS)
        writer.writeheader()
        for row in rows:
            writer.writerow({key: row.get(key) for key in SUMMARY_COLUMNS})


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--case-dir", required=True, help="Directory containing 3IBR.inf and 3IBR_*.out")
    parser.add_argument("--inf", help="Optional explicit 3IBR.inf path")
    parser.add_argument("--scenario-id", required=True)
    parser.add_argument("--fault-ohm", type=float, required=True)
    parser.add_argument("--output-json", required=True)
    parser.add_argument("--summary-csv")
    parser.add_argument("--summary-input", nargs="*", default=[])
    parser.add_argument("--run-status", default="completed")
    parser.add_argument("--build-errors", type=int, default=0)
    parser.add_argument("--build-warnings", type=int, default=0)
    parser.add_argument("--emtdc-completed", action="store_true")
    parser.add_argument("--notes", default="")
    args = parser.parse_args()

    result = build_summary(args)
    output_json = Path(args.output_json)
    output_json.parent.mkdir(parents=True, exist_ok=True)
    output_json.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    if args.summary_csv:
        files = [Path(p) for p in args.summary_input] + [output_json]
        write_csv(files, Path(args.summary_csv))

    print(json.dumps(result["summary"], ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
