#!/usr/bin/env python3
"""Select and freeze the Stage-12 second-line trip candidate from Stage-11 outputs."""

from __future__ import annotations

import dataclasses
import json
from datetime import datetime

from stage12_common import (
    DEFINITE_DELAY_S,
    EXPECTED_MAIN_SHA,
    FIRST_LINE,
    MAIN,
    REPO,
    STAGE11_COMMIT,
    STAGE11_DFIG_TRIP_S,
    STAGE11_FIRST_LINE_OPEN_S,
    STAGE12_PLOT_STEP_S,
    STAGE12_RUN_DURATION_S,
    STAGE12_SOLUTION_STEP_US,
    THRESHOLD_MULTIPLIER,
    TRIAL,
    RuntimeReader,
    evaluate_second_trip_candidate,
    sha256,
    stage12_forbidden_parameter_changes,
    tline_terminals_from_dta,
    write_csv,
    write_json,
)


def as_row(result) -> dict:
    row = dataclasses.asdict(result)
    row["candidate_status"] = "eligible" if result.eligible else "rejected"
    return row


def main() -> None:
    generated = datetime.now().astimezone().isoformat(timespec="seconds")
    reader = RuntimeReader()
    stage11_manifest = json.loads((REPO / "data/derived/stage11_20s_50us_runtime_manifest.json").read_text(encoding="utf-8"))
    if stage11_manifest["stage11_result_class"] != "stage11_20s_50us_paper_order_first_trip_pass":
        raise SystemExit("Stage 11 result is not a valid first-trip pass; Stage 12 candidate selection is blocked.")

    results = []
    s_cache: dict[str, tuple[list[float], list[float]]] = {}
    for branch_id in reader.branch_ids():
        if branch_id == FIRST_LINE:
            continue
        t, s = reader.branch_smax(branch_id)
        s_cache[branch_id] = (t, s)
        results.append(evaluate_second_trip_candidate(branch_id, t, s))

    eligible = sorted([r for r in results if r.eligible], key=lambda r: (-r.score, -(r.selection_margin or -1), r.expected_second_open_time_s or 999, r.tline_id))
    rejected = sorted(
        [r for r in results if not r.eligible],
        key=lambda r: (-(r.selection_margin if r.selection_margin is not None else -1e9), -(r.post_first_trip_5s_floor_s or -1), r.tline_id),
    )
    ranked = eligible + rejected
    ranking_rows = []
    for rank, result in enumerate(ranked, 1):
        row = as_row(result)
        row["rank"] = rank
        row["paper_target_status"] = "paper_event_order_proxy"
        row["selection_basis"] = (
            "eligible_second_trip_candidate_from_stage11_raw_dual_end_PQ"
            if result.eligible
            else result.rejection_reason
        )
        ranking_rows.append(row)

    write_csv(REPO / "data/reference/stage12_second_trip_candidate_ranking.csv", ranking_rows)
    status = "pass" if eligible else "no_defensible_second_trip_candidate"
    selected = eligible[0] if eligible else None

    audit = {
        "audit_name": "stage12_second_trip_candidate_final_audit",
        "generated_at_local": generated,
        "stage12_candidate_status": status,
        "data_source": {
            "stage11_commit": STAGE11_COMMIT,
            "stage11_runtime_manifest": "data/derived/stage11_20s_50us_runtime_manifest.json",
            "runtime_time_end_s": stage11_manifest["time_end_s"],
            "runtime_plot_step_s": stage11_manifest["plot_step_s_observed"],
            "dfig_actual_breaker_open_s": STAGE11_DFIG_TRIP_S,
            "first_line_actual_breaker_open_s": STAGE11_FIRST_LINE_OPEN_S,
            "excluded_first_line": FIRST_LINE,
        },
        "main_sha256": sha256(MAIN),
        "trial_sha256": sha256(TRIAL),
        "main_sha_matches_expected": sha256(MAIN) == EXPECTED_MAIN_SHA,
        "candidate_count": len(results),
        "eligible_count": len(eligible),
        "top_three_screened_lines": [as_row(r) for r in ranked[:3]],
        "top_three_eligible_candidates": [as_row(r) for r in eligible[:3]],
        "selected_tline_id": selected.tline_id if selected else None,
        "claim_boundary": "Second-line capacity is paper-calibrated effective capacity from Stage-11 raw P/Q response. It is not a PNNL thermal rating or real protection setting.",
    }
    write_json(REPO / "data/validation/stage12_second_trip_candidate_final_audit.json", audit)

    decision = {
        "decision_name": "stage12_paper_event_order_proxy_decision",
        "generated_at_local": generated,
        "paper_target_status": "paper_event_order_proxy",
        "reason": "No exact paper branch-to-current-PSCAD-line identity is defensibly recovered; selection is based on paper-like event order and Stage-11 raw response.",
        "selected_tline_id": selected.tline_id if selected else None,
    }
    write_json(REPO / "data/reference/stage12_paper_event_order_proxy_decision.json", decision)

    if selected is None:
        doc = "# Stage 12 second-trip candidate fallback\n\nNo candidate satisfied the strict pre-first-trip no-pickup and post-first-trip continuous 5 s window gates. GUI, Build, and Run are blocked.\n"
        (REPO / "docs/STAGE12_SECOND_TRIP_CANDIDATE_AND_PARAMETER_FREEZE.md").write_text(doc, encoding="utf-8")
        print(json.dumps({"stage12_candidate_status": status, "eligible_count": 0}, indent=2))
        return

    endpoints = tline_terminals_from_dta(selected.tline_id)
    freeze = {
        "freeze_name": "stage12_second_trip_parameter_freeze",
        "generated_at_local": generated,
        "selected_tline_id": selected.tline_id,
        "selected_tline_compiled_endpoints_before_change": endpoints,
        "paper_target_status": "paper_event_order_proxy",
        "selection_reason": "Highest ranked eligible Stage-11 raw S response with no pre-first-trip pickup and a sustained 5 s post-first-trip window.",
        "pre_first_trip_window": [0.0, STAGE11_FIRST_LINE_OPEN_S],
        "post_first_trip_5s_window": [selected.selected_5s_window_start_s, selected.selected_5s_window_end_s],
        "pre_first_trip_max_S": selected.pre_first_trip_max_s,
        "post_first_trip_5s_floor_S": selected.post_first_trip_5s_floor_s,
        "threshold_T": selected.threshold_t,
        "effective_capacity_C_eff": selected.effective_capacity_c_eff,
        "threshold_multiplier": THRESHOLD_MULTIPLIER,
        "definite_time_delay_s": DEFINITE_DELAY_S,
        "selection_margin": selected.selection_margin,
        "expected_pickup_time_s": selected.expected_pickup_time_s,
        "expected_second_open_time_s": selected.expected_second_open_time_s,
        "first_trip_reference_time_s": STAGE11_FIRST_LINE_OPEN_S,
        "DFIG_reference_time_s": STAGE11_DFIG_TRIP_S,
        "solution_time_step_us": STAGE12_SOLUTION_STEP_US,
        "plot_step_s": STAGE12_PLOT_STEP_S,
        "run_duration_s": STAGE12_RUN_DURATION_S,
        "forbidden_parameter_changes": stage12_forbidden_parameter_changes(),
        "claim_boundary": "The frozen capacity is a paper-calibrated effective capacity inferred from Stage-11 raw relay input response; it is not a true thermal rating, real protection setting, or third-party PNNL rating.",
    }
    write_json(REPO / "data/reference/stage12_second_trip_parameter_freeze.json", freeze)
    gui_manifest = {
        "manifest_name": "stage12_gui_change_manifest",
        "generated_at_local": generated,
        "gui_stage_authorized": True,
        "selected_tline_id": selected.tline_id,
        "required_new_objects": [
            "PAPER_OVL2_RELAY",
            "BRK_PAPER_OVL2_TRIAL",
            "PAPER_CHAIN__CHRONOLOGY_MONITOR",
        ],
        "must_copy_semantics_from": "PAPER_OVL1 relay and breaker pattern",
        "forbidden_inputs_to_paper_ovl2": ["fault", "DFIG event", "PAPER_OVL1 trip request", "absolute time", "one-shot"],
        "expected_output_channel_count_minimum_after_build": 637 + 13 + 9,
    }
    write_json(REPO / "data/reference/stage12_gui_change_manifest.json", gui_manifest)

    doc = f"""# Stage 12 second-trip candidate and parameter freeze

## Candidate status

`pass`

## Selected line

- `PAPER_OVL2_SELECTED_TLINE = {selected.tline_id}`
- Paper target status: `paper_event_order_proxy`
- This is not an exact paper branch identity claim.

## Frozen protection values

| Quantity | Value |
|---|---:|
| pre-first-trip max raw S | {selected.pre_first_trip_max_s:.12g} |
| post-first-trip 5 s floor raw S | {selected.post_first_trip_5s_floor_s:.12g} |
| threshold T | {selected.threshold_t:.12g} |
| paper-calibrated effective capacity | {selected.effective_capacity_c_eff:.12g} |
| threshold multiplier | {THRESHOLD_MULTIPLIER} |
| definite delay | {DEFINITE_DELAY_S} s |
| expected pickup | {selected.expected_pickup_time_s:.2f} s |
| expected second open | {selected.expected_second_open_time_s:.2f} s |

The values are frozen. Do not tune capacity, threshold, delay, breaker settings, or the selected line after this point.
"""
    (REPO / "docs/STAGE12_SECOND_TRIP_CANDIDATE_AND_PARAMETER_FREEZE.md").write_text(doc, encoding="utf-8")
    print(json.dumps({
        "stage12_candidate_status": status,
        "selected_tline_id": selected.tline_id,
        "effective_capacity_C_eff": selected.effective_capacity_c_eff,
        "threshold_T": selected.threshold_t,
        "expected_pickup_time_s": selected.expected_pickup_time_s,
        "expected_second_open_time_s": selected.expected_second_open_time_s,
        "top_three_screened_lines": [r.tline_id for r in ranked[:3]],
        "eligible_candidates": [r.tline_id for r in eligible],
    }, indent=2))


if __name__ == "__main__":
    main()
