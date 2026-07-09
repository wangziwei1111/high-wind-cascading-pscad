#!/usr/bin/env python3
"""Offline calibration for a paper-constrained first TLine trip trial.

This script is intentionally read-only with respect to PSCAD artifacts.  It
reuses the already completed 20 s N29 fault run, scans every current network
TLine using dual-end P/Q output channels, and freezes one equivalent capacity
parameter for a single GUI/Build/Run stage.
"""

from __future__ import annotations

import csv
import hashlib
import json
import math
import re
import statistics
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Any


REPO = Path(__file__).resolve().parents[2]
GF46 = Path(r"C:\pscad_work\pnnl_39_3ibr_pscad46_strip5\PSCAD\3IBR_DFIG1_TRIAL.gf46")
MAIN_PSCX = Path(r"C:\pscad_work\pnnl_39_3ibr_pscad46_strip5\PSCAD\3IBR.pscx")
TRIAL_PSCX = Path(r"C:\pscad_work\pnnl_39_3ibr_pscad46_strip5\PSCAD\3IBR_DFIG1_TRIAL.pscx")
TRIAL_BACKUP = Path(r"C:\pscad_work\pnnl_39_3ibr_pscad46_strip5\_backups\stage7_before_paper_calibrated_first_trip")
OUT_PREFIX = "3IBR_DFIG1_TRIAL"
THRESHOLD_MULTIPLIER = 1.1
DEFINITE_DELAY_S = 5.0
DFIG_EVENT_TIME_S = 2.43
FAULT_START_S = 0.50
FAULT_CLEAR_S = 2.50

WINDOWS = {
    "pre_fault": (0.20, 0.45),
    "fault_on": (0.50, 2.50),
    "post_clear_early": (2.60, 3.00),
    "post_clear_late": (5.00, 19.50),
}


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest().upper()


def git(*args: str) -> str:
    return subprocess.check_output(["git", *args], cwd=REPO, text=True, encoding="utf-8").strip()


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fields: list[str] = []
    for row in rows:
        for key in row:
            if key not in fields:
                fields.append(key)
    with path.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows(rows)


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def parse_inf(inf: Path) -> dict[str, int]:
    mapping: dict[str, int] = {}
    for line in inf.read_text(encoding="utf-8", errors="ignore").splitlines():
        m = re.search(r'PGB\((\d+)\).*?Desc="([^"]+)"', line)
        if m:
            mapping[m.group(2)] = int(m.group(1))
    return mapping


def pgb_file_and_col(pgb: int) -> tuple[Path, int]:
    return GF46 / f"{OUT_PREFIX}_{(pgb - 1) // 10 + 1:02d}.out", (pgb - 1) % 10 + 1


class ChannelReader:
    def __init__(self, mapping: dict[str, int]) -> None:
        self.mapping = mapping
        self.cache: dict[Path, list[list[float]]] = {}

    def _read_out(self, path: Path) -> list[list[float]]:
        if path not in self.cache:
            rows: list[list[float]] = []
            for line in path.read_text(encoding="utf-8", errors="ignore").splitlines():
                parts = line.split()
                if not parts:
                    continue
                try:
                    rows.append([float(x) for x in parts])
                except ValueError:
                    continue
            self.cache[path] = rows
        return self.cache[path]

    def series(self, signal: str) -> list[tuple[float, float]]:
        pgb = self.mapping.get(signal)
        if pgb is None:
            return []
        path, col = pgb_file_and_col(pgb)
        rows = self._read_out(path)
        return [(row[0], row[col]) for row in rows if len(row) > col and math.isfinite(row[0]) and math.isfinite(row[col])]


def values_in(series: list[tuple[float, float]], start: float, end: float) -> list[float]:
    return [v for t, v in series if start - 1e-12 <= t <= end + 1e-12]


def max_in(series: list[tuple[float, float]], start: float, end: float) -> float:
    vals = values_in(series, start, end)
    return max(vals) if vals else math.nan


def mean_in(series: list[tuple[float, float]], start: float, end: float) -> float:
    vals = values_in(series, start, end)
    return statistics.fmean(vals) if vals else math.nan


def first_crossing(series: list[tuple[float, float]], threshold: float, start: float = 0.0) -> float | None:
    for t, v in series:
        if t >= start - 1e-12 and v >= threshold:
            return t
    return None


def best_continuous_window(series: list[tuple[float, float]], start: float, end: float, duration: float) -> dict[str, float | None]:
    post = [(t, v) for t, v in series if start - 1e-12 <= t <= end + 1e-12]
    best_min = -math.inf
    best_start = None
    best_end = None
    for t, _ in post:
        t_end = t + duration
        if t_end > end + 1e-12:
            break
        seg = [v for tt, v in post if t - 1e-12 <= tt <= t_end + 1e-12]
        if not seg:
            continue
        seg_min = min(seg)
        if seg_min > best_min:
            best_min = seg_min
            best_start = t
            best_end = t_end
    return {
        "start_s": best_start,
        "end_s": best_end,
        "minimum_smax_pu": best_min if math.isfinite(best_min) else None,
    }


def continuous_time_above(series: list[tuple[float, float]], threshold: float, start: float, end: float) -> float:
    current_start: float | None = None
    best = 0.0
    last_t: float | None = None
    for t, v in series:
        if t < start - 1e-12 or t > end + 1e-12:
            continue
        if v >= threshold:
            if current_start is None:
                current_start = t
            last_t = t
            best = max(best, (last_t or t) - current_start)
        else:
            current_start = None
            last_t = None
    return best


def node_distance_to_fault(row: dict[str, str]) -> int:
    a = row["terminal_a_node"].upper().lstrip("N")
    b = row["terminal_b_node"].upper().lstrip("N")
    if "29" in {a, b}:
        return 0
    if "28" in {a, b} or "26" in {a, b}:
        return 1
    return 2


def build_baseline_manifest() -> None:
    path = REPO / "data/validation/paper_calibrated_first_trip_baseline_manifest.json"
    if path.exists():
        return
    inventory = read_csv(REPO / "data/reference/full_network_tline_inventory.csv")
    channel_baseline = read_json(REPO / "data/validation/paper_aligned_20s_dynamic_run_channel_baseline.json")
    run_manifest = read_json(REPO / "data/derived/paper_aligned_20s_run_manifest.json")
    payload = {
        "manifest_name": "paper_calibrated_first_trip_baseline_manifest",
        "created_at_local": datetime.now().isoformat(timespec="seconds"),
        "git_head_start": git("rev-parse", "HEAD"),
        "main_sha_start": sha256(MAIN_PSCX),
        "trial_sha_start": sha256(TRIAL_PSCX),
        "trial_backup_path": str(TRIAL_BACKUP),
        "trial_backup_manifest_path": str(TRIAL_BACKUP / "backup_manifest.json"),
        "stage4_dynamic_run_commit": "recorded_in_repository_history_before_stage6",
        "stage5_loading_audit_commit": "recorded_in_repository_history_before_stage6",
        "stage5b_semantic_audit_commit": "recorded_in_repository_history_before_stage6",
        "stage6_thermal_limit_recovery_commit": "8b90b3aa224daab43acb3d58004e1f3aa21e6f21",
        "paper_pdf_path": None,
        "paper_pdf_status": "not_located_in_repository; using paper evidence registry",
        "paper_evidence_registry_path": "data/reference/paper_reproduction_evidence_registry.csv",
        "tline_inventory_path": "data/reference/full_network_tline_inventory.csv",
        "tline_count": len([r for r in inventory if r.get("inclusion_status") == "included"]),
        "tline_raw_signal_count": 186,
        "xml_output_channel_count": len(channel_baseline.get("channels", [])) if isinstance(channel_baseline, dict) else 448,
        "existing_run_manifest_path": "data/derived/paper_aligned_20s_run_manifest.json",
        "existing_output_paths": [
            x.get("path") for x in run_manifest.get("output_file_inventory_after_run", [])
            if str(x.get("name", "")).endswith((".out", ".inf", ".infx"))
        ],
        "existing_tline_window_metrics_path": "data/derived/full_network_tline_window_metrics.csv",
        "existing_normalized_apparent_power_path": "data/derived/full_network_tline_normalized_apparent_power_response.csv",
        "existing_raw_mapping_path": "data/reference/current_tline_external_rating_mapping.csv",
        "existing_thermal_limit_fallback_path": "data/derived/protection_grade_tline_loading_ratio_fallback.json",
        "no_pscad_gui_build_run_by_codex": True,
    }
    write_json(path, payload)


def paper_transcription() -> dict[str, Any]:
    evidence = read_csv(REPO / "data/reference/paper_reproduction_evidence_registry.csv")
    e003 = next((r for r in evidence if r.get("evidence_id") == "E003"), {})
    payload = {
        "source": "data/reference/paper_reproduction_evidence_registry.csv",
        "paper_evidence_id": "E003",
        "paper_section": e003.get("paper_section"),
        "paper_page": e003.get("paper_page"),
        "paper_figure_or_table": e003.get("paper_figure_or_table"),
        "registered_statement": e003.get("paper_statement_paraphrase"),
        "registered_short_quote": e003.get("exact_short_quote_if_available"),
        "equation_recovery_status": "semantic_constraints_recovered_but_exact_inverse_time_equations_not_unambiguously_reconstructed",
        "implemented_curve_type": "paper-inspired definite-time fallback",
        "threshold_multiplier": THRESHOLD_MULTIPLIER,
        "definite_delay_s": DEFINITE_DELAY_S,
        "claim_boundary": (
            "This is a paper-constrained equivalent protection parameterization. "
            "It is not a transcription of a fully recovered inverse-time equation and "
            "is not a PNNL physical thermal rating."
        ),
    }
    write_json(REPO / "data/reference/paper_overload_protection_transcription.json", payload)
    return payload


def scan_candidates() -> tuple[list[dict[str, Any]], dict[str, Any]]:
    inf = GF46 / f"{OUT_PREFIX}.inf"
    mapping = parse_inf(inf)
    reader = ChannelReader(mapping)
    inventory = [r for r in read_csv(REPO / "data/reference/full_network_tline_inventory.csv") if r.get("inclusion_status") == "included"]
    rows: list[dict[str, Any]] = []
    selected: dict[str, Any] | None = None

    for inv in inventory:
        branch = inv["network_branch_id"]
        names = [f"{branch}_A_P", f"{branch}_A_Q", f"{branch}_B_P", f"{branch}_B_Q"]
        sers = [reader.series(name) for name in names]
        if not all(sers):
            rows.append({
                "network_branch_id": branch,
                "selection_status": "rejected",
                "rejection_reason": "missing_required_dual_end_pq_runtime_channel",
            })
            continue
        smax: list[tuple[float, float]] = []
        for (t, pa), (_, qa), (_, pb), (_, qb) in zip(*sers):
            smax.append((t, max(math.hypot(pa, qa), math.hypot(pb, qb))))

        pre_max = max_in(smax, *WINDOWS["pre_fault"])
        fault_max = max_in(smax, *WINDOWS["fault_on"])
        early_max = max_in(smax, *WINDOWS["post_clear_early"])
        late_max = max_in(smax, *WINDOWS["post_clear_late"])
        late_mean = mean_in(smax, *WINDOWS["post_clear_late"])
        window = best_continuous_window(smax, 2.60, 19.50, DEFINITE_DELAY_S)
        rolling_min = window["minimum_smax_pu"]
        if rolling_min is None:
            feasible = False
            lower = upper = robust_lower = robust_upper = None
        else:
            lower = pre_max / THRESHOLD_MULTIPLIER
            upper = rolling_min / THRESHOLD_MULTIPLIER
            robust_lower = lower / 0.98
            robust_upper = upper / 1.02
            feasible = robust_upper > robust_lower

        selected_capacity = None
        threshold = None
        crossing = None
        expected_trip = None
        robust_minus2 = robust_plus2 = robust_minus5 = robust_plus5 = False
        continuous_duration = 0.0
        if feasible and robust_lower is not None and robust_upper is not None:
            selected_capacity = (robust_lower + robust_upper) / 2.0
            threshold = selected_capacity * THRESHOLD_MULTIPLIER
            crossing = first_crossing(smax, threshold, start=max(FAULT_CLEAR_S, DFIG_EVENT_TIME_S))
            continuous_duration = continuous_time_above(smax, threshold, max(FAULT_CLEAR_S, DFIG_EVENT_TIME_S), 19.50)
            expected_trip = crossing + DEFINITE_DELAY_S if crossing is not None else None
            robust_minus2 = selected_capacity * 0.98 > pre_max / THRESHOLD_MULTIPLIER and continuous_time_above(smax, selected_capacity * 0.98 * THRESHOLD_MULTIPLIER, 2.60, 19.50) >= DEFINITE_DELAY_S
            robust_plus2 = selected_capacity * 1.02 > pre_max / THRESHOLD_MULTIPLIER and continuous_time_above(smax, selected_capacity * 1.02 * THRESHOLD_MULTIPLIER, 2.60, 19.50) >= DEFINITE_DELAY_S
            robust_minus5 = selected_capacity * 0.95 > pre_max / THRESHOLD_MULTIPLIER and continuous_time_above(smax, selected_capacity * 0.95 * THRESHOLD_MULTIPLIER, 2.60, 19.50) >= DEFINITE_DELAY_S
            robust_plus5 = selected_capacity * 1.05 > pre_max / THRESHOLD_MULTIPLIER and continuous_time_above(smax, selected_capacity * 1.05 * THRESHOLD_MULTIPLIER, 2.60, 19.50) >= DEFINITE_DELAY_S

        distance = node_distance_to_fault(inv)
        fault_relation_score = 1.0 if distance == 0 else (0.7 if distance == 1 else 0.4)
        flow_persistence_score = min(1.0, continuous_duration / DEFINITE_DELAY_S) if feasible else 0.0
        robust_width = (robust_upper - robust_lower) if feasible and robust_lower is not None and robust_upper is not None else -1.0
        parameter_robustness_score = min(1.0, max(0.0, robust_width / 5.0))
        post_strength_score = min(1.0, late_max / 15.0 if math.isfinite(late_max) else 0.0)
        paper_alignment_score = 0.35 * fault_relation_score + 0.25 * flow_persistence_score + 0.25 * parameter_robustness_score + 0.15 * post_strength_score

        rejection_reason = ""
        if not feasible:
            rejection_reason = "no_capacity_band_satisfies_prefault_no_trip_and_5s_postclear_continuous_overthreshold_with_2pct_robustness"
        elif expected_trip is None or expected_trip >= 20.0:
            rejection_reason = "expected_trip_window_outside_20s"
        elif not (robust_minus2 and robust_plus2):
            rejection_reason = "fails_mandatory_plus_minus_2_percent_robustness"
        row: dict[str, Any] = {
            "network_branch_id": branch,
            "paper_identity_relation": "paper-constrained adapted-network first-trip candidate",
            "fault_bus_distance_or_relation": f"endpoint distance class {distance} from N29 fault; endpoints {inv['terminal_a_node']}-{inv['terminal_b_node']}",
            "pre_fault_S_max": pre_max,
            "fault_on_S_max": fault_max,
            "post_clear_early_S_max": early_max,
            "post_clear_late_S_max": late_max,
            "candidate_effective_capacity_band_lower": lower,
            "candidate_effective_capacity_band_upper": upper,
            "selected_effective_capacity_pu": selected_capacity,
            "pre_fault_no_trip_margin": (selected_capacity * THRESHOLD_MULTIPLIER - pre_max) if selected_capacity else None,
            "threshold_crossing_time_window": crossing,
            "expected_timer_completion_window": expected_trip,
            "expected_first_trip_window": expected_trip,
            "robustness_under_minus_2_percent_limit": robust_minus2,
            "robustness_under_plus_2_percent_limit": robust_plus2,
            "robustness_under_minus_5_percent_limit": robust_minus5,
            "robustness_under_plus_5_percent_limit": robust_plus5,
            "paper_alignment_score": paper_alignment_score,
            "flow_persistence_score": flow_persistence_score,
            "parameter_robustness_score": parameter_robustness_score,
            "selection_status": "eligible" if feasible and not rejection_reason else "rejected",
            "rejection_reason": rejection_reason,
            "terminal_a_node": inv["terminal_a_node"],
            "terminal_b_node": inv["terminal_b_node"],
            "best_5s_window_start_s": window["start_s"],
            "best_5s_window_end_s": window["end_s"],
            "best_5s_window_minimum_smax_pu": rolling_min,
            "post_clear_late_S_mean": late_mean,
        }
        rows.append(row)

    eligible = [r for r in rows if r["selection_status"] == "eligible"]
    eligible.sort(key=lambda r: (
        int(str(r["fault_bus_distance_or_relation"]).startswith("endpoint distance class 0")),
        float(r["paper_alignment_score"]),
        float(r["parameter_robustness_score"]),
        float(r["post_clear_late_S_max"]),
    ), reverse=True)
    if eligible:
        selected = dict(eligible[0])
        for r in rows:
            if r["network_branch_id"] == selected["network_branch_id"]:
                r["selection_status"] = "selected"
                r["rejection_reason"] = ""
            elif r["selection_status"] == "eligible":
                r["selection_status"] = "not_selected"
                r["rejection_reason"] = "eligible_but_lower_fixed_selection_score_or_less_direct_N29_fault_relation"
    else:
        selected = {}

    write_csv(REPO / "data/derived/paper_calibrated_first_trip_candidate_scan.csv", rows)
    write_json(REPO / "data/derived/paper_calibrated_first_trip_candidate_scan.json", {"candidate_count": len(rows), "selected": selected, "rows": rows})
    return rows, selected


def write_freeze(selected: dict[str, Any], rows: list[dict[str, Any]], transcription: dict[str, Any]) -> None:
    if not selected:
        fallback = {
            "execution_status": "paper_calibrated_first_trip_calibration_fallback",
            "reason": "no robust candidate found",
            "candidate_count": len(rows),
        }
        write_json(REPO / "data/reference/paper_calibrated_first_trip_parameter_freeze.json", fallback)
        return

    cap = float(selected["selected_effective_capacity_pu"])
    threshold_abs = cap * THRESHOLD_MULTIPLIER
    freeze = {
        "selected_network_branch_id": selected["network_branch_id"],
        "selection_reason": (
            "Selected by fixed score over all 31 current TLines: direct N29 fault relation first, "
            "then paper-aligned post-clear persistent flow and parameter robustness. "
            "The selected line has no pre-fault false trip and remains robust under +/-2% effective-capacity perturbation."
        ),
        "paper_relation": selected["paper_identity_relation"],
        "effective_capacity_pu": cap,
        "paper_calibrated_effective_capacity_pu_on_100MVA_base": cap,
        "effective_capacity_equivalent_on_100MVA_base": cap,
        "threshold_multiplier": THRESHOLD_MULTIPLIER,
        "absolute_s_threshold_pu_on_100MVA_base": threshold_abs,
        "protection_curve_type": transcription["implemented_curve_type"],
        "definite_delay_s_or_exact_paper_curve_parameters": {
            "definite_delay_s": DEFINITE_DELAY_S,
            "exact_inverse_time_equation_status": transcription["equation_recovery_status"],
        },
        "expected_threshold_crossing_window": selected["threshold_crossing_time_window"],
        "expected_trip_window": selected["expected_first_trip_window"],
        "pre_fault_margin": selected["pre_fault_no_trip_margin"],
        "robustness_summary": {
            "minus_2_percent": selected["robustness_under_minus_2_percent_limit"],
            "plus_2_percent": selected["robustness_under_plus_2_percent_limit"],
            "minus_5_percent": selected["robustness_under_minus_5_percent_limit"],
            "plus_5_percent": selected["robustness_under_plus_5_percent_limit"],
            "candidate_effective_capacity_band_lower": selected["candidate_effective_capacity_band_lower"],
            "candidate_effective_capacity_band_upper": selected["candidate_effective_capacity_band_upper"],
        },
        "all_rejected_candidates": [
            {"network_branch_id": r["network_branch_id"], "status": r["selection_status"], "reason": r["rejection_reason"]}
            for r in rows if r["network_branch_id"] != selected["network_branch_id"]
        ],
        "modeling_claim_boundary": (
            "effective_capacity_pu is a calibrated equivalent parameter for paper-mechanism reproduction; "
            "it is not a PNNL original continuous thermal rating, not a true protection setting, and not a real thermal limit."
        ),
        "parameter_freeze_timestamp": datetime.now().isoformat(timespec="seconds"),
    }
    manifest = {
        "manifest_name": "paper_calibrated_effective_capacity_manifest",
        "selected_network_branch_id": selected["network_branch_id"],
        "parameter_name": "paper_calibrated_effective_capacity_pu_on_100MVA_base",
        "parameter_value": cap,
        "unit": "p.u. on existing 100 MVA system base",
        "threshold_multiplier": THRESHOLD_MULTIPLIER,
        "protection_time_parameters": {
            "curve_type": transcription["implemented_curve_type"],
            "definite_delay_s": DEFINITE_DELAY_S,
        },
        "source_data": {
            "existing_run_manifest_path": "data/derived/paper_aligned_20s_run_manifest.json",
            "candidate_scan_path": "data/derived/paper_calibrated_first_trip_candidate_scan.csv",
        },
        "claim_boundary": freeze["modeling_claim_boundary"],
    }
    static_mapping = {
        "selected_network_branch_id": selected["network_branch_id"],
        "terminal_a_node": selected["terminal_a_node"],
        "terminal_b_node": selected["terminal_b_node"],
        "gui_insertion_boundary": (
            f"Insert BRK_PAPER_OVL1_TRIAL in series with the real TLine {selected['network_branch_id']} "
            "on one electrical side without changing the TLine R/X/B, length, end nodes, or the existing A/B multimeters."
        ),
        "preserve_meter_order": [
            "Keep the existing terminal-A P/Q/I measurement source feeding the selected line A-side labels.",
            "Keep the existing terminal-B P/Q/I measurement source feeding the selected line B-side labels.",
            "Do not add a third TLine measurement component.",
        ],
        "no_bypass_check_text": (
            "After insertion, visually confirm that there is no parallel wire or branch around BRK_PAPER_OVL1_TRIAL; "
            "all current through the selected real TLine boundary must pass through this breaker."
        ),
    }
    write_json(REPO / "data/reference/paper_calibrated_first_trip_parameter_freeze.json", freeze)
    write_json(REPO / "data/reference/paper_calibrated_effective_capacity_manifest.json", manifest)
    write_json(REPO / "data/reference/stage7_selected_tline_static_mapping.json", static_mapping)


def write_gui_sheet(selected: dict[str, Any]) -> None:
    if not selected:
        return
    branch = selected["network_branch_id"]
    cap = float(selected["selected_effective_capacity_pu"])
    text = f"""# STAGE7 single GUI / Build / Run sheet

本清单只用于 `3IBR_DFIG1_TRIAL.pscx`。不要打开、保存或修改 main 工程 `3IBR.pscx`。

本阶段只允许你完成一次完整 PSCAD GUI 阶段：改 trial → 保存 → Build 一次 → 若 Build Errors = 0，则 Run 一次 20 s。不要截图、不要打开 Graph、不要复制 `.out/.inf`，不要第二次 Build/Run。

## 0. 冻结参数

- 选中真实线路：`{branch}`
- 参数名：`paper_calibrated_effective_capacity_pu_on_100MVA_base`
- 参数值：`{cap:.9f}`
- 阈值倍数：`1.1`
- 保护时间：`5.0 s definite-time fallback`
- 本参数是“论文标定等效承载能力”，不是 PNNL 真实线路连续热容量，也不是真实保护整定。

## 1. 只打开 trial 工程

打开：

`C:\\pscad_work\\pnnl_39_3ibr_pscad46_strip5\\PSCAD\\3IBR_DFIG1_TRIAL.pscx`

不要打开 main 工程。

## 2. 在 `{branch}` 上插入真实三相断路器

目标：新增 `BRK_PAPER_OVL1_TRIAL`，串联在 `{branch}` 的真实电气路径上。

要求：

- 元件类型：Three-Phase Breaker。
- 实例名 / Name：`BRK_PAPER_OVL1_TRIAL`。
- 初始状态：闭合。
- 控制信号：只接 `PAPER_OVL1_BRK_CMD`。
- 不改 `{branch}` 的 R/X/B、长度、两端节点、并联身份。
- 保留原来的 A 端和 B 端 multimeter / P/Q/I 测量。
- 不新增第三个线路测量元件。
- 断路器周围不能有并联旁路。

断路器命令极性不要凭空猜。请按 trial 里已成功 Build/Run 的 `BRK_IBR2_TRIAL` 或 `BRK_IBR3_TRIAL` 查同类 Three-Phase Breaker 的控制含义：沿用同一种“命令为 1 时打开 / 命令为 0 时闭合”的受审计语义。如果你看到该 breaker 参数显示相反极性，必须按已有 trial breaker 的实际参数保持一致。

## 3. 新建 Page Module：`PAPER_CALIBRATED_OVERLOAD_RELAY`

模块输入端口：

- `P_A`
- `Q_A`
- `P_B`
- `Q_B`
- `RELAY_ENABLE`

模块参数：

- `EFFECTIVE_CAPACITY_PU = {cap:.9f}`
- `THRESHOLD_MULTIPLIER = 1.1`
- `PROTECTION_TIME_PARAMETERS = 5.0`

模块输出端口：

- `S_A_PU`
- `S_B_PU`
- `S_MAX_PU`
- `EFFECTIVE_CAPACITY_PU_OUT`
- `LOADING_INDEX_EQ`
- `ABOVE_THRESHOLD`
- `TIMER_OR_CURVE_STATE`
- `TRIP_REQUEST`
- `FIRST_TRIP_TIME_S`

内部逻辑：

1. `S_A_PU = sqrt(P_A*P_A + Q_A*Q_A)`
2. `S_B_PU = sqrt(P_B*P_B + Q_B*Q_B)`
3. `S_MAX_PU = max(S_A_PU, S_B_PU)`
4. `EFFECTIVE_CAPACITY_PU_OUT = EFFECTIVE_CAPACITY_PU`
5. `LOADING_INDEX_EQ = S_MAX_PU / EFFECTIVE_CAPACITY_PU`
6. `ABOVE_THRESHOLD = RELAY_ENABLE AND (LOADING_INDEX_EQ >= 1.1)`
7. `TIMER_OR_CURVE_STATE` 只由 `ABOVE_THRESHOLD` 累计；`ABOVE_THRESHOLD = 0` 时复位为 0。
8. `TRIP_REQUEST` 在 `ABOVE_THRESHOLD` 连续保持 5.0 s 后置 1，并锁存到本次 Run 结束。
9. `FIRST_TRIP_TIME_S` 只在 `TRIP_REQUEST` 第一次从 0 到 1 时锁存当前仿真时间。

禁止接入任何固定绝对时间、故障时刻、DFIG event time、外部 one-shot stimulus 或人工定时源。

## 4. 放置 relay 实例并接线

在 `{branch}` 附近或一个清晰的新页面放置 `PAPER_CALIBRATED_OVERLOAD_RELAY` 实例。

接线：

- `{branch}` A 端真实 P → relay `P_A`
- `{branch}` A 端真实 Q → relay `Q_A`
- `{branch}` B 端真实 P → relay `P_B`
- `{branch}` B 端真实 Q → relay `Q_B`
- 常数 `1.0` → Data Label `PAPER_OVL1_RELAY_ENABLE` → relay `RELAY_ENABLE`
- relay `TRIP_REQUEST` → Data Label `PAPER_OVL1_TRIP_REQUEST`
- `PAPER_OVL1_TRIP_REQUEST` → 按已审计 breaker 极性形成 `PAPER_OVL1_BRK_CMD`
- `PAPER_OVL1_BRK_CMD` → `BRK_PAPER_OVL1_TRIAL` 控制端

## 5. 新增 13 个 Output Channel

只新增，不删除、不重命名、不重连已有 448 个 Output Channel。

每个 Output Channel 参数建议：

- `Use Signal Name as Title? = No`
- `Display Title on Icon? = Yes`
- `Scale Factor = 1.0`
- `Multiple Run Save = Last Run Only`
- `Is Input in Polar Form? = No`

新增通道 Title / 信号：

1. `PAPER_OVL1_S_A_PU`
2. `PAPER_OVL1_S_B_PU`
3. `PAPER_OVL1_S_MAX_PU`
4. `PAPER_OVL1_EFFECTIVE_CAPACITY_PU`
5. `PAPER_OVL1_LOADING_INDEX_EQ`
6. `PAPER_OVL1_ABOVE_THRESHOLD`
7. `PAPER_OVL1_TIMER_OR_CURVE_STATE`
8. `PAPER_OVL1_TRIP_REQUEST`
9. `PAPER_OVL1_BRK_CMD`
10. `PAPER_OVL1_BRK_STATE`
11. `PAPER_OVL1_TRIP_EVENT_VALID`
12. `PAPER_OVL1_FIRST_TRIP_TIME_S`
13. `PAPER_OVL1_RELAY_ENABLE`

语义：

- `PAPER_OVL1_BRK_STATE` 必须来自 `BRK_PAPER_OVL1_TRIAL` 的实际状态/状态适配输出，不允许直接复制命令当状态。
- `PAPER_OVL1_TRIP_EVENT_VALID` 可由实际 breaker open 状态或 `TRIP_REQUEST` 锁存后形成，但审计时会以实际 breaker state 为准。

## 6. 保存、Build、Run

1. 保存 trial。
2. Build 一次。
3. 如果 Build Errors 不等于 0：立刻停止，不要 Run，只把精确错误文本发给我。
4. 如果 Build Errors = 0：Run 一次，Duration of Run 保持 `20 s`。
5. 等唯一一次 20 s Run 完整结束。
6. 不打开 Graph，不截图，不复制 `.out/.inf`，不再次 Build，不第二次 Run。
7. 回到 Codex 只回复：

`阶段一 GUI / Build / Run 完成`
"""
    path = REPO / "docs/STAGE7_SINGLE_GUI_BUILD_AND_RUN_SHEET.md"
    path.write_text(text, encoding="utf-8")


def main() -> None:
    build_baseline_manifest()
    transcription = paper_transcription()
    rows, selected = scan_candidates()
    write_freeze(selected, rows, transcription)
    write_gui_sheet(selected)
    summary = {
        "execution_status": "pass" if selected else "paper_calibrated_first_trip_calibration_fallback",
        "selected_network_branch_id": selected.get("network_branch_id") if selected else None,
        "candidate_count": len(rows),
        "selected_effective_capacity_pu": selected.get("selected_effective_capacity_pu") if selected else None,
    }
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
