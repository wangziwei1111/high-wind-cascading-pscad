#!/usr/bin/env python3
"""Create 100-MVA normalized TLine sanity metrics from existing outputs."""

from __future__ import annotations

import csv
import json
import statistics
from datetime import datetime
from pathlib import Path


REPO = Path(__file__).resolve().parents[2]


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fields: list[str] = []
    for row in rows:
        for key in row:
            if key not in fields:
                fields.append(key)
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def f(row: dict[str, str], key: str) -> float:
    return float(row[key])


def main() -> int:
    metrics = read_csv(REPO / "data/derived/full_network_tline_loading_ratio_metrics.csv")
    ranking = read_csv(REPO / "data/derived/full_network_tline_loading_candidate_ranking.csv")
    rows: list[dict[str, object]] = []
    for row in metrics:
        pre_max = f(row, "pre_fault_loading_max")
        rows.append(
            {
                "network_branch_id": row["network_branch_id"],
                "pre_fault_S_max_mean": f(row, "pre_fault_loading_mean"),
                "pre_fault_S_max_median": "",
                "pre_fault_S_max_max": pre_max,
                "fault_on_S_max_max": f(row, "fault_on_loading_max"),
                "post_clear_early_S_max_max": f(row, "post_clear_early_loading_max"),
                "post_clear_late_S_max_max": f(row, "post_clear_late_loading_max"),
                "ratio_to_100MVA_pre_fault_mean": f(row, "pre_fault_loading_mean"),
                "ratio_to_100MVA_pre_fault_max": pre_max,
                "ratio_to_100MVA_post_clear_late_max": f(row, "post_clear_late_loading_max"),
                "pre_fault_ratio_above_one_flag": pre_max > 1.0,
                "pre_fault_ratio_above_two_flag": pre_max > 2.0,
                "pre_fault_ratio_above_five_flag": pre_max > 5.0,
                "semantic_reading": "100-MVA-normalized apparent-power response index; not thermal/protection loading ratio",
            }
        )
    pre_max_values = [float(r["pre_fault_S_max_max"]) for r in rows]
    summary = {
        "artifact": "full_network_tline_100mva_sanity_metrics",
        "generated_at_local": datetime.now().isoformat(timespec="seconds"),
        "source_metric_file": "data/derived/full_network_tline_loading_ratio_metrics.csv",
        "source_reuse_status": "reused_existing_stage5_numeric_values_without_rerun",
        "line_count": len(rows),
        "pre_fault_ratio_above_one_count": sum(1 for v in pre_max_values if v > 1.0),
        "pre_fault_ratio_above_two_count": sum(1 for v in pre_max_values if v > 2.0),
        "pre_fault_ratio_above_five_count": sum(1 for v in pre_max_values if v > 5.0),
        "pre_fault_S_max_mean_across_lines": statistics.fmean(pre_max_values),
        "pre_fault_S_max_median_across_lines": statistics.median(pre_max_values),
        "pre_fault_S_max_max_across_lines": max(pre_max_values),
        "baseline_sanity_status": "strong_negative_evidence_against_using_uniform_100mva_as_protection_grade_thermal_limit",
        "interpretation": "Large pre-fault normalized values and absence of runtime thermal/protection usage support re-labeling as S/model Total MVA field, not overload indication.",
        "rows": rows,
    }
    response_rows: list[dict[str, object]] = []
    for r in ranking:
        response_rows.append(
            {
                "rank": r.get("rank", ""),
                "network_branch_id": r["network_branch_id"],
                "pre_fault_index_mean": r["pre_fault_loading_mean"],
                "pre_fault_index_max": r["pre_fault_loading_max"],
                "fault_on_index_max": r["fault_on_loading_max"],
                "post_clear_early_index_mean": r["post_clear_early_loading_mean"],
                "post_clear_early_index_max": r["post_clear_early_loading_max"],
                "post_clear_late_index_mean": r["post_clear_late_loading_mean"],
                "post_clear_late_index_max": r["post_clear_late_loading_max"],
                "index_formula": "max(sqrt(P_A^2+Q_A^2),sqrt(P_B^2+Q_B^2))/(model Total MVA field / 100 MVA)",
                "semantic_status": "100mva_normalized_apparent_power_response_index_not_overload_ratio",
            }
        )
    response_json = {
        "artifact": "full_network_tline_normalized_apparent_power_response",
        "generated_at_local": datetime.now().isoformat(timespec="seconds"),
        "semantic_status": "corrected_stage5_fallback_not_protection_grade_loading_ratio",
        "highest_normalized_apparent_power_response_line": response_rows[0]["network_branch_id"] if response_rows else None,
        "warning": "Do not interpret index > 1 as overload without verified continuous thermal/protection-grade line ratings.",
        "rows": response_rows,
    }
    write_csv(REPO / "data/derived/full_network_tline_100mva_sanity_metrics.csv", rows)
    write_json(REPO / "data/derived/full_network_tline_100mva_sanity_metrics.json", summary)
    write_csv(REPO / "data/derived/full_network_tline_normalized_apparent_power_response.csv", response_rows)
    write_json(REPO / "data/derived/full_network_tline_normalized_apparent_power_response.json", response_json)
    print(json.dumps({k: summary[k] for k in ["pre_fault_ratio_above_one_count", "pre_fault_ratio_above_two_count", "pre_fault_ratio_above_five_count", "baseline_sanity_status"]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
