#!/usr/bin/env python3
"""Analyze Type-3 DFIG LVRT duration-boundary sweep outputs.

This script is read-only with respect to PSCAD artifacts. Each scenario must be
archived into its own directory containing that scenario's `3IBR.inf` and
`3IBR_*.out` files. The script parses the scenario-local `3IBR.inf`, rebuilds
the PGB-to-output mapping, and computes dynamic statistics using windows based
on that scenario's own fault duration.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
from pathlib import Path
from typing import Any

from analyze_type3_dfig_fault_resistance_sweep import (
    active_duration,
    get_signal,
    load_out,
    max_abs_across,
    parse_inf,
    stats,
    subset,
)


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
    "fault_duration_s",
    "run_status",
    "build_errors",
    "build_warnings",
    "emtdc_completed",
    "output_end_time_s",
    "V_min_pu",
    "V_min_time_s",
    "V_fault_mean_pu",
    "V_fault_time_below_0p90_s",
    "V_recovery_time_s",
    "V_recovery_status",
    "Edc_pu_fault_peak",
    "Ecap_Det_fault_peak_kV",
    "BRK_CHOP_active_during_fault",
    "BRK_CHOP_duration_during_fault_s",
    "DFIG_CROWBAR_STATE_active",
    "RSC_max_abs_terminal_current",
    "GSC_max_abs_terminal_current",
    "Crowbar_current_max_abs",
    "Wpu_pre_mean",
    "Wpu_late_post_mean",
    "DFIG_BRK_STATE_fault_mean",
    "DFIG_DBLK_CMD_fault_mean",
]


def make_windows(fault_start: float, fault_duration: float, output_end: float | None) -> dict[str, list[float]]:
    clear = fault_start + fault_duration
    end = output_end if output_end is not None else max(8.0, clear + 0.5)
    return {
        "pre_fault": [1.8, fault_start],
        "fault": [fault_start, clear],
        "early_post_fault": [clear, min(clear + 0.5, end)],
        "late_post_fault": [max(7.0, clear + 0.5), end],
    }


def window_stats(times: list[float], values: list[float], windows: dict[str, list[float]]) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for name, (start, end) in windows.items():
        tw, vw = subset(times, values, start, end)
        out[name] = stats(tw, vw)
    out["end_time_s"] = times[-1] if times else None
    return out


def all_out_files(case_dir: Path) -> list[Path]:
    return sorted(case_dir.glob("3IBR_*.out"))


def check_output_integrity(case_dir: Path) -> dict[str, Any]:
    files = all_out_files(case_dir)
    checked: list[dict[str, Any]] = []
    has_nan_or_inf = False
    parse_errors: list[str] = []
    end_times: list[float] = []
    for path in files:
        try:
            rows = load_out(path)
            if not rows:
                parse_errors.append(f"{path.name}: empty")
                continue
            flat = [value for row in rows for value in row]
            if any((not math.isfinite(value)) for value in flat):
                has_nan_or_inf = True
            end_times.append(rows[-1][0])
            checked.append(
                {
                    "file": path.name,
                    "rows": len(rows),
                    "columns_last_row": len(rows[-1]),
                    "end_time_s": rows[-1][0],
                }
            )
        except Exception as exc:  # noqa: BLE001 - reported in JSON
            parse_errors.append(f"{path.name}: {type(exc).__name__}: {exc}")
    return {
        "out_file_count": len(files),
        "checked_files": checked,
        "parse_errors": parse_errors,
        "has_nan_or_inf": has_nan_or_inf,
        "min_output_end_time_s": min(end_times) if end_times else None,
        "max_output_end_time_s": max(end_times) if end_times else None,
    }


def time_below_threshold(times: list[float], values: list[float], threshold: float, start: float, end: float) -> float:
    tw, vw = subset(times, values, start, end)
    if len(tw) < 2:
        return 0.0
    total = 0.0
    for i in range(len(tw) - 1):
        if vw[i] < threshold:
            total += max(0.0, tw[i + 1] - tw[i])
    return total


def first_stable_recovery_time(
    times: list[float],
    values: list[float],
    start: float,
    end: float | None,
    lo: float = 0.95,
    hi: float = 1.05,
) -> float | None:
    post = [(t, v) for t, v in zip(times, values) if t >= start and (end is None or t <= end)]
    for i, (t, v) in enumerate(post):
        if lo <= v <= hi and all(lo <= vv <= hi for _, vv in post[i:]):
            return t
    return None


def stat_value(signals: dict[str, dict[str, Any]], desc: str, window: str, key: str) -> Any:
    return signals.get(desc, {}).get("statistics", {}).get(window, {}).get(key)


def max_value(signals: dict[str, dict[str, Any]], desc: str, window: str) -> Any:
    return stat_value(signals, desc, window, "max")


def build_summary(args: argparse.Namespace) -> dict[str, Any]:
    case_dir = Path(args.case_dir).resolve()
    inf_path = Path(args.inf).resolve() if args.inf else case_dir / "3IBR.inf"
    pgbs = parse_inf(inf_path)
    by_desc: dict[str, list[Any]] = {}
    for pgb in pgbs:
        by_desc.setdefault(pgb.desc, []).append(pgb)

    integrity = check_output_integrity(case_dir)
    output_end = integrity.get("min_output_end_time_s")
    windows = make_windows(args.fault_start_s, args.fault_duration_s, output_end)

    signals: dict[str, dict[str, Any]] = {}
    missing: list[str] = []
    duplicate_desc: dict[str, list[dict[str, Any]]] = {}
    for desc in TARGET_SIGNALS:
        entries = by_desc.get(desc, [])
        if not entries:
            missing.append(desc)
            continue
        if len(entries) > 1:
            duplicate_desc[desc] = [entry.__dict__ for entry in entries]
        pgb = entries[0]
        times, values = get_signal(case_dir, pgb)
        signals[desc] = {
            "pgb": pgb.index,
            "original_desc": pgb.desc,
            "group": pgb.group,
            "units_from_inf": pgb.units,
            "out_file": pgb.out_file,
            "column": pgb.column,
            "duplicate_count_for_desc": len(entries),
            "statistics": window_stats(times, values, windows),
        }

    fault_start = args.fault_start_s
    fault_clear = args.fault_start_s + args.fault_duration_s

    v_recovery = None
    v_recovery_status = "not_available"
    v_below_0p90 = None
    if "VIBR1_2" in signals:
        pgb = by_desc["VIBR1_2"][0]
        vt, vv = get_signal(case_dir, pgb)
        v_recovery = first_stable_recovery_time(vt, vv, fault_clear, output_end)
        v_recovery_status = "recovered" if v_recovery is not None else "not_recovered_within_output"
        v_below_0p90 = time_below_threshold(vt, vv, 0.90, fault_start, fault_clear)

    brk_chop_fault_duration = None
    brk_chop_early_post_duration = None
    if "BRK_CHOP" in signals:
        pgb = by_desc["BRK_CHOP"][0]
        t, v = get_signal(case_dir, pgb)
        tw, vw = subset(t, v, *windows["fault"])
        brk_chop_fault_duration = active_duration(tw, vw)
        tw, vw = subset(t, v, *windows["early_post_fault"])
        brk_chop_early_post_duration = active_duration(tw, vw)

    s1_duration = None
    if "S1" in signals:
        pgb = by_desc["S1"][0]
        t, v = get_signal(case_dir, pgb)
        tw, vw = subset(t, v, *windows["fault"])
        s1_duration = active_duration(tw, vw)

    summary_row = {
        "scenario_id": args.scenario_id,
        "R_fault_ohm": args.fault_ohm,
        "fault_duration_s": args.fault_duration_s,
        "run_status": args.run_status,
        "build_errors": args.build_errors,
        "build_warnings": args.build_warnings,
        "emtdc_completed": args.emtdc_completed,
        "output_end_time_s": output_end,
        "V_min_pu": stat_value(signals, "VIBR1_2", "fault", "min"),
        "V_min_time_s": stat_value(signals, "VIBR1_2", "fault", "min_time_s"),
        "V_fault_mean_pu": stat_value(signals, "VIBR1_2", "fault", "mean"),
        "V_fault_time_below_0p90_s": v_below_0p90,
        "V_recovery_time_s": v_recovery if v_recovery is not None else "not_recovered_within_8s",
        "V_recovery_status": v_recovery_status,
        "Edc_pu_fault_peak": max_value(signals, "Edc_pu", "fault"),
        "Edc_pu_fault_peak_time_s": stat_value(signals, "Edc_pu", "fault", "max_time_s"),
        "Edc_pu_post_peak": max(
            [
                value
                for value in [
                    max_value(signals, "Edc_pu", "early_post_fault"),
                    max_value(signals, "Edc_pu", "late_post_fault"),
                ]
                if isinstance(value, (int, float))
            ],
            default=None,
        ),
        "Ecap_Det_fault_peak_kV": max_value(signals, "Ecap_Det", "fault"),
        "Ecap_Det_post_peak_kV": max(
            [
                value
                for value in [
                    max_value(signals, "Ecap_Det", "early_post_fault"),
                    max_value(signals, "Ecap_Det", "late_post_fault"),
                ]
                if isinstance(value, (int, float))
            ],
            default=None,
        ),
        "BRK_CHOP_active_during_fault": (max_value(signals, "BRK_CHOP", "fault") or 0) > 0.5
        if "BRK_CHOP" in signals
        else None,
        "BRK_CHOP_duration_during_fault_s": brk_chop_fault_duration,
        "BRK_CHOP_duration_early_post_fault_s": brk_chop_early_post_duration,
        "DFIG_CROWBAR_STATE_active": (max_value(signals, "S1", "fault") or 0) > 0.5 if "S1" in signals else None,
        "DFIG_CROWBAR_STATE_duration_s": s1_duration,
        "Crowbar_current_max_abs": max_abs_across(
            ["Crowbar current:1", "Crowbar current:2", "Crowbar current:3"], signals, "fault"
        ),
        "RSC_max_abs_terminal_current": max_abs_across(["I_RS:1", "I_RS:2", "I_RS:3"], signals, "fault"),
        "GSC_max_abs_terminal_current": max_abs_across(["Iconv:1", "Iconv:2", "Iconv:3"], signals, "fault"),
        "P_fault_min_mean_max": [
            stat_value(signals, "PIBR1_2", "fault", "min"),
            stat_value(signals, "PIBR1_2", "fault", "mean"),
            stat_value(signals, "PIBR1_2", "fault", "max"),
        ],
        "Q_fault_min_mean_max": [
            stat_value(signals, "QIBR1_2", "fault", "min"),
            stat_value(signals, "QIBR1_2", "fault", "mean"),
            stat_value(signals, "QIBR1_2", "fault", "max"),
        ],
        "P_late_post_mean_range": [
            stat_value(signals, "PIBR1_2", "late_post_fault", "mean"),
            stat_value(signals, "PIBR1_2", "late_post_fault", "range"),
        ],
        "Q_late_post_mean_range": [
            stat_value(signals, "QIBR1_2", "late_post_fault", "mean"),
            stat_value(signals, "QIBR1_2", "late_post_fault", "range"),
        ],
        "Wpu_pre_mean": stat_value(signals, "Wpu", "pre_fault", "mean"),
        "Wpu_fault_mean_range": [
            stat_value(signals, "Wpu", "fault", "mean"),
            stat_value(signals, "Wpu", "fault", "range"),
        ],
        "Wpu_late_post_mean": stat_value(signals, "Wpu", "late_post_fault", "mean"),
        "Wpu_late_post_range": stat_value(signals, "Wpu", "late_post_fault", "range"),
        "Dblk_VdcCtrl_state_summary": state_summary(signals, "Dblk_VdcCtrl"),
        "Dblk_Rotor_state_summary": state_summary(signals, "Dblk_Rotor"),
        "DFIG_DBLK_CMD_state_summary": state_summary(signals, "DFIG_DBLK_CMD"),
        "DFIG_BRK_STATE_state_summary": state_summary(signals, "DFIG_BRK_STATE"),
        "DFIG_BRK_STATE_fault_mean": stat_value(signals, "DFIG_BRK_STATE", "fault", "mean"),
        "DFIG_DBLK_CMD_fault_mean": stat_value(signals, "DFIG_DBLK_CMD", "fault", "mean"),
        "Freq_PLL_min_max": [
            stat_value(signals, "Freq_PLL", "fault", "min"),
            stat_value(signals, "Freq_PLL", "fault", "max"),
        ],
    }
    if isinstance(summary_row["Edc_pu_fault_peak"], (int, float)) and isinstance(
        summary_row["Ecap_Det_fault_peak_kV"], (int, float)
    ):
        approx_kv = summary_row["Edc_pu_fault_peak"] * 1.45
        summary_row["Edc_pu_times_1p45_kV"] = approx_kv
        summary_row["Edc_Ecap_consistency_note"] = (
            "approximately_consistent"
            if abs(approx_kv - summary_row["Ecap_Det_fault_peak_kV"]) < 0.05
            else "sample_or_filter_difference_possible"
        )

    return {
        "analysis_version": 1,
        "script": "analysis/pscad_tools/analyze_type3_dfig_lvrt_duration_boundary.py",
        "scenario_id": args.scenario_id,
        "configuration": {
            "fault_on_resistance_ohm": args.fault_ohm,
            "fault_off_resistance_ohm": 1.0e6,
            "fault_type": "ABC-to-ground",
            "fault_start_s": args.fault_start_s,
            "fault_duration_s": args.fault_duration_s,
            "run_duration_s": 8.0,
            "time_step_us": 5.0,
            "wind_speed_mps": 11.0,
        },
        "run_status": {
            "status": args.run_status,
            "build_errors": args.build_errors,
            "build_warnings": args.build_warnings,
            "emtdc_completed": args.emtdc_completed,
        },
        "warning_records": args.warning_records,
        "source": {
            "case_dir": str(case_dir),
            "inf_path": str(inf_path),
        },
        "windows_s": windows,
        "output_integrity": integrity,
        "pgb_mapping": [pgb.__dict__ for pgb in pgbs],
        "duplicate_signal_descriptions": duplicate_desc,
        "signals": signals,
        "missing_signals": missing,
        "summary": summary_row,
        "semantic_limits": [
            "This run does not implement LVRT trip logic and does not operate BRK_DFIG.",
            "S1=1 is treated as the GUI-confirmed crowbar switch command active state; S1=0 means the crowbar switch is not commanded on.",
            "Crowbar current:1..3 are internal crowbar branch currents, but exact phase order and positive direction remain unconfirmed.",
            "I_RS:1..3 and Iconv:1..3 are instantaneous three-phase terminal currents, not RMS values.",
            "DFIG_IFLT_A/B/C_KA are external fault-element currents, not internal converter or crowbar branch currents.",
            "DFIG_DBLK_CMD is not a physical trip state.",
        ],
    }


def state_summary(signals: dict[str, dict[str, Any]], desc: str) -> dict[str, Any]:
    if desc not in signals:
        return {"available": False}
    summary: dict[str, Any] = {"available": True}
    for window, values in signals[desc]["statistics"].items():
        if not isinstance(values, dict) or "count" not in values:
            continue
        summary[window] = {
            "min": values.get("min"),
            "mean": values.get("mean"),
            "max": values.get("max"),
            "active_gt_0p5": (values.get("max") or 0) > 0.5 if values.get("count") else None,
        }
    return summary


def write_csv(summary_files: list[Path], csv_path: Path) -> None:
    rows = []
    for path in summary_files:
        data = json.loads(path.read_text(encoding="utf-8"))
        rows.append(data["summary"])
    csv_path.parent.mkdir(parents=True, exist_ok=True)
    with csv_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=SUMMARY_COLUMNS, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({key: row.get(key) for key in SUMMARY_COLUMNS})


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--case-dir", required=True, help="Directory containing scenario-local 3IBR.inf and 3IBR_*.out")
    parser.add_argument("--inf", help="Optional explicit 3IBR.inf path")
    parser.add_argument("--scenario-id", required=True)
    parser.add_argument("--fault-ohm", type=float, required=True)
    parser.add_argument("--fault-duration-s", type=float, required=True)
    parser.add_argument("--fault-start-s", type=float, default=2.0)
    parser.add_argument("--run-status", default="completed")
    parser.add_argument("--build-errors", type=int, default=0)
    parser.add_argument("--build-warnings", type=int, default=0)
    parser.add_argument("--emtdc-completed", action="store_true")
    parser.add_argument("--warning-records", nargs="*", default=[])
    parser.add_argument("--output-json", required=True)
    parser.add_argument("--summary-csv")
    parser.add_argument("--summary-input", nargs="*", default=[])
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
