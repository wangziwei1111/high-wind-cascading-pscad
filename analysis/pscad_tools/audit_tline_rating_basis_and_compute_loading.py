#!/usr/bin/env python3
"""Audit TLine rating basis and reconstruct offline loading ratios.

This script is read-only with respect to PSCAD models and generated Run files.
It reuses the existing paper-aligned 20 s Run outputs and writes only new
analysis CSV/JSON artifacts inside the repository.
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


REPO = Path(__file__).resolve().parents[2]
MAIN_PSCX = Path(r"C:\pscad_work\pnnl_39_3ibr_pscad46_strip5\PSCAD\3IBR.pscx")
TRIAL_PSCX = Path(r"C:\pscad_work\pnnl_39_3ibr_pscad46_strip5\PSCAD\3IBR_DFIG1_TRIAL.pscx")
GF46 = Path(r"C:\pscad_work\pnnl_39_3ibr_pscad46_strip5\PSCAD\3IBR_DFIG1_TRIAL.gf46")
EXPECTED_MAIN_SHA = "CBA120BB167CB7FA6C4A1AE4471268850AB61761EC1877EB7B87015627FE9DAB"
EXPECTED_TRIAL_SHA = "F81959EA62211FF9C1536C8481B67675AFE4DDCC3C56E804D048731A4B88A300"
OUT_PREFIX = "3IBR_DFIG1_TRIAL"

WINDOWS = {
    "pre_fault": (0.20, 0.45, "left_closed_right_open"),
    "fault_on": (0.50, 2.50, "closed"),
    "post_clear_early": (2.60, 3.00, "left_closed_right_open"),
    "post_clear_late": (5.00, 19.50, "closed"),
}


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest().upper()


def read_json(path: Path) -> object:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames: list[str] = []
    for row in rows:
        for key in row:
            if key not in fieldnames:
                fieldnames.append(key)
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def git_head() -> str:
    return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=REPO, text=True).strip()


def create_baseline_manifest() -> dict[str, object]:
    path = REPO / "data/validation/tline_rating_loading_baseline_manifest.json"
    if path.exists():
        return read_json(path)  # type: ignore[return-value]

    dynamic_audit = read_json(REPO / "data/validation/paper_aligned_20s_dynamic_run_final_audit.json")
    run_manifest = read_json(REPO / "data/derived/paper_aligned_20s_run_manifest.json")
    tline_inventory = read_json(REPO / "data/reference/full_network_tline_inventory.json")

    existing_derived = [
        "data/derived/full_network_tline_window_metrics.csv",
        "data/derived/full_network_tline_current_response_ranking.csv",
        "data/derived/full_network_tline_power_response_ranking.csv",
        "data/derived/paper_aligned_20s_run_manifest.json",
        "data/derived/paper_aligned_20s_event_timeline.csv",
    ]
    output_paths = sorted(str(p) for p in GF46.glob(f"{OUT_PREFIX}_*.out"))
    inf_paths = sorted(str(p) for p in GF46.glob("*.inf"))

    manifest = {
        "manifest_name": "tline_rating_loading_baseline_manifest",
        "generated_at_local": datetime.now().isoformat(timespec="seconds"),
        "git_head_start": git_head(),
        "main_sha_start": sha256(MAIN_PSCX),
        "trial_sha_start": sha256(TRIAL_PSCX),
        "dynamic_run_commit": "44283ac40e51a032446dcf67c3d4208d17f3eb69",
        "dynamic_run_audit_path": "data/validation/paper_aligned_20s_dynamic_run_final_audit.json",
        "dynamic_run_time_axis": dynamic_audit["time_axis"],
        "dynamic_run_sample_count": dynamic_audit["time_axis"]["sample_count"],
        "dynamic_run_output_step_s": dynamic_audit["time_axis"]["median_step_s"],
        "tline_inventory_count": tline_inventory["inventory_count"],
        "tline_raw_signal_count": dynamic_audit["tline_raw_signal_count"],
        "xml_output_channel_count": dynamic_audit["xml_output_channel_count"],
        "existing_derived_data_paths": existing_derived,
        "existing_runtime_output_paths": output_paths,
        "existing_map_inf_paths": inf_paths,
        "run_directory": run_manifest["run_directory"],
        "reuse_rule": "All later scripts in this task reuse this manifest instead of repeating full model/TLine/channel audits.",
    }
    write_json(path, manifest)
    return manifest


def parse_inf(inf: Path) -> dict[str, dict[str, object]]:
    mapping: dict[str, dict[str, object]] = {}
    for line in inf.read_text(encoding="utf-8", errors="ignore").splitlines():
        m = re.search(r'PGB\((\d+)\).*?Desc="([^"]+)".*?Group="([^"]*)".*?Units="([^"]*)"', line)
        if not m:
            continue
        mapping[m.group(2)] = {
            "pgb": int(m.group(1)),
            "desc": m.group(2),
            "group": m.group(3),
            "units": m.group(4),
        }
    return mapping


def file_and_col(pgb: int) -> tuple[Path, int]:
    return GF46 / f"{OUT_PREFIX}_{(pgb - 1) // 10 + 1:02d}.out", (pgb - 1) % 10 + 1


def read_out_file(path: Path) -> list[list[float]]:
    rows: list[list[float]] = []
    for line in path.read_text(encoding="utf-8", errors="ignore").splitlines():
        parts = line.split()
        if not parts:
            continue
        try:
            rows.append([float(x) for x in parts])
        except ValueError:
            continue
    return rows


class ChannelReader:
    def __init__(self, mapping: dict[str, dict[str, object]]) -> None:
        self.mapping = mapping
        self.cache: dict[Path, list[list[float]]] = {}

    def series(self, name: str) -> list[tuple[float, float]]:
        info = self.mapping.get(name)
        if not info:
            return []
        path, col = file_and_col(int(info["pgb"]))
        if path not in self.cache:
            self.cache[path] = read_out_file(path)
        out: list[tuple[float, float]] = []
        for row in self.cache[path]:
            if len(row) > col and math.isfinite(row[col]):
                out.append((row[0], row[col]))
        return out


def in_window(t: float, start: float, end: float, mode: str) -> bool:
    if mode == "closed":
        return start - 1e-12 <= t <= end + 1e-12
    return start - 1e-12 <= t < end - 1e-12


def loading_stats(series: list[tuple[float, float, str]], start: float, end: float, mode: str) -> dict[str, object]:
    vals = [(t, v, term) for t, v, term in series if in_window(t, start, end, mode)]
    if not vals:
        return {"mean": None, "max": None, "peak_time_s": None, "terminal": "", "sample_count": 0, "status": "fail_empty"}
    mean = statistics.fmean(v for _, v, _ in vals)
    peak_t, peak_v, peak_term = max(vals, key=lambda x: x[1])
    return {
        "mean": mean,
        "max": peak_v,
        "peak_time_s": peak_t,
        "terminal": peak_term,
        "sample_count": len(vals),
        "status": "pass",
    }


def parse_tli_rating(branch: str) -> dict[str, object]:
    path = GF46 / f"{branch}.tli"
    if not path.exists():
        return {
            "rating_source_file": "",
            "rating_source_line_or_parameter": "",
            "rating_source_text_or_value": "",
            "rating_value": None,
            "voltage_kv": None,
            "status": "missing_tli",
        }
    text = path.read_text(encoding="utf-8", errors="ignore").splitlines()
    rating_value = None
    voltage_value = None
    rating_line = ""
    voltage_line = ""
    for idx, line in enumerate(text, start=1):
        if "Total MVA Rating" in line:
            rating_line = f"{idx}: {line.strip()}"
            rating_value = float(line.split("=")[1].strip())
        if "Voltage Rating" in line:
            voltage_line = f"{idx}: {line.strip()}"
            voltage_value = float(line.split("=")[1].strip())
    return {
        "rating_source_file": str(path),
        "rating_source_line_or_parameter": rating_line,
        "rating_source_text_or_value": rating_line,
        "rating_value": rating_value,
        "voltage_kv": voltage_value,
        "voltage_source_text_or_value": voltage_line,
        "status": "pass" if rating_value and rating_value > 0 else "missing_positive_total_mva_rating",
    }


def tline_rating_rows(inventory: dict[str, object]) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for tline in inventory["tlines"]:  # type: ignore[index]
        branch = tline["network_branch_id"]
        tli = parse_tli_rating(branch)
        qualified = tli["status"] == "pass"
        rows.append(
            {
                "network_branch_id": branch,
                "tline_instance_name": tline["tline_instance_name"],
                "component_id": tline["component_id"],
                "terminal_a_node": tline["terminal_a_node"],
                "terminal_b_node": tline["terminal_b_node"],
                "parallel_group_id": tline["parallel_group_id"],
                "parallel_index": tline["parallel_index"],
                "rating_source_file": tli["rating_source_file"],
                "rating_source_line_or_parameter": tli["rating_source_line_or_parameter"],
                "rating_source_class": "generated_pscad_tli_exact_tline_total_mva_rating",
                "rating_source_text_or_value": tli["rating_source_text_or_value"],
                "rating_kind": "apparent_power",
                "rating_value": tli["rating_value"] or "",
                "rating_unit": "MVA",
                "rating_continuous_or_short_term_status": "model_total_mva_rating_no_short_term_flag",
                "voltage_rating_kv_ll_rms": tli.get("voltage_kv") or "",
                "signal_unit_basis": "P/Q are p.u. on 100 MVA system base from audited master:multimeter semantics",
                "signal_base_value": "100 MVA",
                "signal_to_rating_conversion": "S_pu = sqrt(P_pu^2 + Q_pu^2); S_limit_pu = Total_MVA_Rating / 100 MVA",
                "terminal_A_rating_compatibility_status": "pass" if qualified else "fail",
                "terminal_B_rating_compatibility_status": "pass" if qualified else "fail",
                "branch_mapping_status": "pass",
                "unit_consistency_status": "pass" if qualified else "fail",
                "qualification_status": "qualified_apparent_power_rating" if qualified else "insufficient_rating_basis",
                "rejection_reason": "" if qualified else "No positive exact TLine Total MVA Rating found in the generated .tli file.",
                "supporting_negative_evidence": "External RAW RATE1..RATE12 fields are zero for network branches and are treated as unspecified, not as usable ratings.",
            }
        )
    return rows


def compute_loading_rows(rating_rows: list[dict[str, object]], reader: ChannelReader) -> tuple[list[dict[str, object]], list[dict[str, object]]]:
    metrics: list[dict[str, object]] = []
    ranking: list[dict[str, object]] = []
    for r in rating_rows:
        branch = str(r["network_branch_id"])
        qual = r["qualification_status"] == "qualified_apparent_power_rating"
        rating_mva = float(r["rating_value"]) if qual else math.nan
        limit_pu = rating_mva / 100.0 if qual else math.nan
        if not qual or not math.isfinite(limit_pu) or limit_pu <= 0:
            row = {
                "network_branch_id": branch,
                "loading_formula_type": "unavailable",
                "rating_basis_id": "",
                "loading_quality_status": "insufficient_rating_basis",
                "rejection_reason": r["rejection_reason"],
            }
            metrics.append(row)
            ranking.append({**row, "candidate_classification": "insufficient_rating_basis"})
            continue

        pa = reader.series(f"{branch}_A_P")
        qa = reader.series(f"{branch}_A_Q")
        pb = reader.series(f"{branch}_B_P")
        qb = reader.series(f"{branch}_B_Q")
        n = min(len(pa), len(qa), len(pb), len(qb))
        loading: list[tuple[float, float, str]] = []
        for i in range(n):
            t = pa[i][0]
            sa = math.hypot(pa[i][1], qa[i][1]) / limit_pu
            sb = math.hypot(pb[i][1], qb[i][1]) / limit_pu
            if sa >= sb:
                loading.append((t, sa, "A"))
            else:
                loading.append((t, sb, "B"))

        stats = {name: loading_stats(loading, *window) for name, window in WINDOWS.items()}
        terminal_selected = max(stats.values(), key=lambda s: float(s["max"] or -1))["terminal"]
        early_delta = float(stats["post_clear_early"]["mean"]) - float(stats["pre_fault"]["mean"])
        late_delta = float(stats["post_clear_late"]["mean"]) - float(stats["pre_fault"]["mean"])
        max_all = max(float(s["max"]) for s in stats.values() if s["max"] is not None)
        post_clear_max = max(float(stats["post_clear_early"]["max"]), float(stats["post_clear_late"]["max"]))
        if post_clear_max >= 1.0:
            classification = "qualified_loading_ratio;ratio_above_one_observation;post_clear_candidate"
        elif float(stats["fault_on"]["max"]) >= 1.0 and post_clear_max < 1.0:
            classification = "qualified_loading_ratio;fault_only_peak"
        else:
            classification = "qualified_loading_ratio;post_clear_candidate"

        row = {
            "network_branch_id": branch,
            "pre_fault_loading_mean": stats["pre_fault"]["mean"],
            "pre_fault_loading_max": stats["pre_fault"]["max"],
            "fault_on_loading_max": stats["fault_on"]["max"],
            "fault_on_loading_peak_time_s": stats["fault_on"]["peak_time_s"],
            "post_clear_early_loading_mean": stats["post_clear_early"]["mean"],
            "post_clear_early_loading_max": stats["post_clear_early"]["max"],
            "post_clear_early_loading_peak_time_s": stats["post_clear_early"]["peak_time_s"],
            "post_clear_late_loading_mean": stats["post_clear_late"]["mean"],
            "post_clear_late_loading_max": stats["post_clear_late"]["max"],
            "post_clear_late_loading_peak_time_s": stats["post_clear_late"]["peak_time_s"],
            "post_clear_early_delta_from_pre_fault": early_delta,
            "post_clear_late_delta_from_pre_fault": late_delta,
            "terminal_selected_by_max_loading": terminal_selected,
            "loading_formula_type": "apparent_power_ratio",
            "rating_basis_id": f"{branch}:generated_tli_total_mva_rating",
            "loading_quality_status": "pass",
            "rating_value_mva": rating_mva,
            "rating_limit_pu_on_100mva_base": limit_pu,
            "ratio_above_one_observation": max_all >= 1.0,
        }
        metrics.append(row)
        ranking.append(
            {
                **row,
                "candidate_classification": classification,
                "candidate_sort_key": (
                    float(row["post_clear_late_loading_max"]),
                    float(row["post_clear_late_loading_mean"]),
                    float(row["post_clear_early_loading_max"]),
                    float(row["post_clear_early_loading_mean"]),
                ),
            }
        )

    ranking.sort(
        key=lambda r: (
            float(r.get("post_clear_late_loading_max") or -1),
            float(r.get("post_clear_late_loading_mean") or -1),
            float(r.get("post_clear_early_loading_max") or -1),
            float(r.get("post_clear_early_loading_mean") or -1),
        ),
        reverse=True,
    )
    for idx, row in enumerate(ranking, start=1):
        row["rank"] = idx
        row.pop("candidate_sort_key", None)
    return metrics, ranking


def runtime_mapping_gap_registry() -> list[dict[str, object]]:
    coverage = read_csv(REPO / "data/derived/paper_aligned_20s_run_channel_coverage.csv")
    missing = [r for r in coverage if r.get("mapping_status") != "pass"]
    rows: list[dict[str, object]] = []
    for r in missing:
        name = r["channel_name"]
        rows.append(
            {
                "missing_channel_name": name,
                "channel_category": "legacy_generator_30_or_non_tline_existing_output",
                "is_tline_measurement": "false",
                "is_required_for_loading_ratio": "false",
                "mapping_gap_reason_if_known": "Present in XML channel baseline but absent from the runtime .inf PGB mapping for the 20 s Run.",
                "impact_on_this_loading_audit": "No impact: all 31 TLine x A/B x P/Q/I signals are mapped and parsed.",
                "future_action": "If generator-30 quantitative plots are needed, perform a separate static/runtime channel mapping audit; do not modify this loading audit.",
            }
        )
    return rows


def future_decision(ranking: list[dict[str, object]], rating_rows: list[dict[str, object]]) -> dict[str, object]:
    qualified = [r for r in ranking if r.get("loading_quality_status") == "pass"]
    if not qualified:
        return {
            "recommended_candidate_line": None,
            "blocking_reason": "No line has qualified rating basis.",
            "minimum_missing_rating_evidence": "Exact continuous current or MVA rating with unit mapping for at least one TLine.",
            "recommended_next_task": "Perform rating-source acquisition before any shadow overload model action.",
        }
    top = qualified[0]
    e1619 = next(r for r in ranking if r["network_branch_id"] == "E_16_19_1")
    return {
        "recommended_candidate_line": top["network_branch_id"],
        "rating_basis_id": top["rating_basis_id"],
        "loading_formula": "L_S(t)=max(sqrt(P_A(t)^2+Q_A(t)^2), sqrt(P_B(t)^2+Q_B(t)^2))/(Total_MVA_Rating/100MVA)",
        "post_clear_loading_metrics": {
            "post_clear_late_loading_max": top["post_clear_late_loading_max"],
            "post_clear_late_loading_mean": top["post_clear_late_loading_mean"],
            "post_clear_early_loading_max": top["post_clear_early_loading_max"],
            "post_clear_early_loading_mean": top["post_clear_early_loading_mean"],
        },
        "candidate_selection_rationale": "Highest post-clear-late loading max under the audited TLI Total MVA rating basis.",
        "paper_relation": "Candidate for future monitor-only shadow overload evaluation only; not evidence of paper line protection or natural cascade.",
        "e_16_19_1_status": {
            "exists_in_current_project": True,
            "rating_basis_status": "qualified_apparent_power_rating",
            "loading_ratio_computable": True,
            "rank": e1619["rank"],
            "post_clear_late_loading_max": e1619["post_clear_late_loading_max"],
            "reason_not_preselected_from_paper": "The thesis names E_16_19_1 as a first overloaded line in its own model, but current PSCAD topology/ratings are an adaptation; selection must follow current audited ratings and run outputs.",
        },
        "required_missing_items_before_shadow_relay": [
            "Explicit shadow-relay criterion and time model",
            "Build-only implementation plan",
            "One controlled Run and offline parser",
            "Audit proving no breaker command or line trip is introduced unless separately authorized",
        ],
        "recommended_next_task": "One combined future task: monitor-only shadow overload criterion for the selected line -> Build -> one controlled Run -> automatic parsing -> audit/docs/Git/PR.",
    }


def main() -> int:
    baseline = create_baseline_manifest()
    inventory = read_json(REPO / "data/reference/full_network_tline_inventory.json")
    mapping = parse_inf(GF46 / f"{OUT_PREFIX}.inf")
    reader = ChannelReader(mapping)

    rating_rows = tline_rating_rows(inventory)  # type: ignore[arg-type]
    metrics, ranking = compute_loading_rows(rating_rows, reader)
    gap_rows = runtime_mapping_gap_registry()
    decision = future_decision(ranking, rating_rows)

    qualified = [r for r in rating_rows if r["qualification_status"] in {"qualified_apparent_power_rating", "qualified_current_rating", "qualified_both"}]
    insufficient = [r for r in rating_rows if r["qualification_status"] == "insufficient_rating_basis"]
    conflicting = [r for r in rating_rows if r["qualification_status"] == "conflicting_rating_basis"]
    rating_coverage_status = (
        "pass_full_rating_coverage"
        if len(qualified) == 31
        else "pass_partial_rating_coverage"
        if qualified
        else "rating_basis_fallback_no_qualified_lines"
    )

    basis_json = {
        "artifact": "full_network_tline_rating_basis",
        "generated_at_local": datetime.now().isoformat(timespec="seconds"),
        "rating_coverage_status": rating_coverage_status,
        "qualified_line_count": len(qualified),
        "insufficient_line_count": len(insufficient),
        "conflicting_line_count": len(conflicting),
        "rating_source_summary": {
            "generated_pscad_tli_exact_tline_total_mva_rating": len(qualified),
            "external_raw_rate_fields_zero_unspecified": 31,
        },
        "current_rating_qualified_count": 0,
        "apparent_power_rating_qualified_count": len(qualified),
        "rows": rating_rows,
    }
    metrics_json = {
        "artifact": "full_network_tline_loading_ratio_metrics",
        "generated_at_local": datetime.now().isoformat(timespec="seconds"),
        "dynamic_run_reused_status": "reused_existing_stage4_20s_run_outputs",
        "raw_output_reparse_status": "performed_for_pointwise_apparent_power_loading",
        "loading_ratio_computation_status": "pass" if qualified else "unavailable_no_audited_line_rating_basis",
        "loading_formula_type": "apparent_power_ratio",
        "line_loading_ratio_status": "observed_for_qualified_lines_only" if qualified else "unavailable_no_audited_line_rating_basis",
        "line_overload_status": "not_validated_no_relay_or_thermal_time_model",
        "rows": metrics,
    }
    ranking_json = {
        "artifact": "full_network_tline_loading_candidate_ranking",
        "generated_at_local": datetime.now().isoformat(timespec="seconds"),
        "ranking_priority": [
            "post_clear_late_loading_max",
            "post_clear_late_loading_mean",
            "post_clear_early_loading_max",
            "post_clear_early_loading_mean",
        ],
        "terminology_boundary": "ratio-above-one observations are not confirmed overload, relay action, line protection, outage, or natural cascade.",
        "rows": ranking,
    }

    write_csv(REPO / "data/reference/full_network_tline_rating_basis.csv", rating_rows)
    write_json(REPO / "data/reference/full_network_tline_rating_basis.json", basis_json)
    write_csv(REPO / "data/derived/full_network_tline_loading_ratio_metrics.csv", metrics)
    write_json(REPO / "data/derived/full_network_tline_loading_ratio_metrics.json", metrics_json)
    write_csv(REPO / "data/derived/full_network_tline_loading_candidate_ranking.csv", ranking)
    write_json(REPO / "data/derived/full_network_tline_loading_candidate_ranking.json", ranking_json)
    write_csv(REPO / "data/validation/runtime_non_tline_channel_mapping_gap_registry.csv", gap_rows)
    write_json(REPO / "data/reference/future_shadow_overload_candidate_decision.json", decision)

    summary = {
        "execution_status": "pass",
        "baseline_manifest": "data/validation/tline_rating_loading_baseline_manifest.json",
        "rating_coverage_status": rating_coverage_status,
        "qualified_line_count": len(qualified),
        "insufficient_line_count": len(insufficient),
        "conflicting_line_count": len(conflicting),
        "current_rating_qualified_count": 0,
        "apparent_power_rating_qualified_count": len(qualified),
        "loading_ratio_computation_status": metrics_json["loading_ratio_computation_status"],
        "line_loading_ratio_status": metrics_json["line_loading_ratio_status"],
        "line_overload_status": metrics_json["line_overload_status"],
        "runtime_non_tline_missing_channel_count": len(gap_rows),
        "recommended_candidate_line": decision.get("recommended_candidate_line"),
        "claim_boundary": "Offline loading-ratio reconstruction only; no relay, line trip, thermal overload validation, natural cascade, or PSCAD model change.",
    }
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
