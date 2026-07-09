#!/usr/bin/env python3
"""Classify the Stage-8 single run and record strict claim boundaries."""

from __future__ import annotations

import csv
import json
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Any


REPO = Path(__file__).resolve().parents[2]


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, obj: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fields = list(rows[0]) if rows else []
    with path.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader(); w.writerows(rows)


def update_reference_files(status: str, claim: str) -> None:
    inv_path = REPO / "data/reference/current_pscad_model_capability_inventory.json"
    if inv_path.exists():
        inv = read_json(inv_path)
        caps = [x for x in inv.get("capabilities", []) if x.get("capability_id") != "PAPER_CALIBRATED_EQUIVALENT_FIRST_TRIP"]
        caps.append({"capability_id": "PAPER_CALIBRATED_EQUIVALENT_FIRST_TRIP", "status": status,
                     "description": "Stage-8 runtime outputs are readable, but the relay/breaker chain is asserted before the fault while ABOVE_THRESHOLD remains zero.",
                     "selected_line": "E_28_29_1", "claim_boundary": claim})
        inv["capabilities"] = caps
        write_json(inv_path, inv)
    inv_csv = REPO / "data/reference/current_pscad_model_capability_inventory.csv"
    if inv_csv.exists():
        with inv_csv.open(encoding="utf-8", newline="") as f:
            rows = list(csv.DictReader(f)); fields = list(rows[0]) if rows else []
        for row in rows:
            if row.get("capability_id") == "PAPER_CALIBRATED_EQUIVALENT_FIRST_TRIP":
                row["status"] = status
                row["description"] = "Runtime outputs readable; pre-fault false trip while ABOVE_THRESHOLD remains zero."
                row["evidence_path"] = "data/validation/stage8_paper_ovl1_dynamic_final_audit.json"
                if "claim_boundary" in row:
                    row["claim_boundary"] = claim
        with inv_csv.open("w", encoding="utf-8", newline="") as f:
            w = csv.DictWriter(f, fieldnames=fields); w.writeheader(); w.writerows(rows)
    matrix = REPO / "data/reference/paper_reproduction_alignment_matrix.csv"
    if matrix.exists():
        with matrix.open(encoding="utf-8", newline="") as f:
            rows = list(csv.DictReader(f)); fields = list(rows[0]) if rows else []
        for row in rows:
            if row.get("paper_item_id") == "P09":
                if "current_status" in row: row["current_status"] = status
                if "current_evidence" in row: row["current_evidence"] = "data/validation/stage8_paper_ovl1_dynamic_final_audit.json"
        with matrix.open("w", encoding="utf-8", newline="") as f:
            w = csv.DictWriter(f, fieldnames=fields); w.writeheader(); w.writerows(rows)
    future = REPO / "data/reference/future_shadow_overload_candidate_decision.json"
    if future.exists():
        obj = read_json(future)
        obj["stage8_runtime_status"] = status
        obj["stage8_runtime_evidence"] = "data/validation/stage8_paper_ovl1_dynamic_final_audit.json"
        obj["strict_reproduction_status"] = "not_achieved"
        write_json(future, obj)
    marker = "\n## Stage eight runtime observability and dynamic result\n"
    addition = (marker + "\nRuntime Output Channel observability passed: all 13 canonical `PAPER_OVL1_*` "
                "channels are readable over 0-20 s. Dynamic classification is " + f"`{status}`: "
                "`ABOVE_THRESHOLD` never asserted, while timer, trip request, breaker command, and open "
                "state were present at t=0. Flow-driven first-trip causality is not proven, no post-trip "
                "redistribution ranking is valid, and strict reproduction remains `not_achieved`.\n")
    for doc_path in [REPO / "docs/PAPER_REPRODUCTION_GAP_REGISTER.md",
                     REPO / "docs/PAPER_REPRODUCTION_ALIGNMENT_AND_MINIMUM_CASCADE_PLAN.md"]:
        if not doc_path.exists():
            continue
        text = doc_path.read_text(encoding="utf-8")
        if marker in text:
            text = text.split(marker)[0].rstrip()
        doc_path.write_text(text + addition, encoding="utf-8")


def main() -> None:
    m = read_json(REPO / "data/derived/stage8_paper_ovl1_run_manifest.json")
    readable = m["paper_channels_all_readable"] and m["inf_exists"] and m["prefixed_out_file_count"] > 0
    pre_fault_trip = m["trip_request_time_s"] is not None and m["trip_request_time_s"] < m["fault_start_time_s"]
    above_never = m["first_threshold_crossing_time_s"] is None
    if not readable:
        status = "stage8_runtime_output_parser_fallback"
    elif pre_fault_trip:
        status = "stage8_pre_fault_false_trip"
    elif m["actual_breaker_open_time_s"] is None:
        status = "stage8_no_trip_observed"
    else:
        status = "stage8_relay_breaker_causality_failure"

    p3 = Path(r"C:\pscad_work\pnnl_39_3ibr_pscad46_strip5\PSCAD\3IBR_DFIG1_TRIAL.gf46\PAPER_OVL1_RELAY.f")
    code = p3.read_text(encoding="utf-8", errors="ignore") if p3.exists() else ""
    generated_cause = {
        "timer_output_drives_latch_set": "RVD2_1(1) = RT_18" in code,
        "latch_q_is_trip_request": "TRIP_REQ = REAL(IT_4)" in code,
        "timer_state_is_timer_output": "TIMER_STATE = RT_18" in code,
        "above_threshold_is_zero_runtime": above_never,
        "timer_trip_and_breaker_asserted_at_t0": pre_fault_trip and m["timer_start_time_s"] == 0.0 and m["breaker_command_time_s"] == 0.0,
    }
    claim = ("Stage 8 proves runtime Output Channel observability only. It does not prove flow-driven protection: "
             "the timer/latch/command chain is asserted at t=0 while ABOVE_THRESHOLD remains zero. The capacity is "
             "paper-calibrated equivalent capacity, not a PNNL continuous thermal rating or real protection setting.")
    no_fixed_bypass = "not_proven_pre_fault_assertion_invalidates_causal_order"
    audit = {
        "audit_name": "stage8_paper_ovl1_dynamic_final_audit",
        "generated_at_local": datetime.now().isoformat(timespec="seconds"),
        "execution_status": status,
        "branch": subprocess.check_output(["git", "branch", "--show-current"], cwd=REPO, text=True).strip(),
        "selected_line": m["selected_line"], "effective_capacity_pu": m["effective_capacity_pu"],
        "threshold_multiplier": m["threshold_multiplier"], "definite_delay_s": m["definite_delay_s"],
        "main_sha_start": m["main_sha_start"], "main_sha_final": m["main_sha_final"],
        "trial_sha_start": m["trial_sha_start"], "trial_sha_final": m["trial_sha_after_stage8_repair"],
        "runtime_channel_integrity": "pass" if readable else "fail",
        "inf_exists": m["inf_exists"], "out_file_count": m["prefixed_out_file_count"],
        "canonical_paper_channel_count": m["paper_channel_count"], "all_13_runtime_channels_readable": readable,
        "time_start_s": m["time_start_s"], "time_end_s": m["time_end_s"], "plot_step_s": m["plot_step_s"],
        "fault_start_time_s": m["fault_start_time_s"], "fault_clear_time_s": m["fault_clear_time_s"],
        "dfig_event_time_s": m["dfig_event_time_s"],
        "first_threshold_crossing_time_s": m["first_threshold_crossing_time_s"],
        "continuous_above_threshold_duration_s": m["continuous_above_threshold_duration_s"],
        "timer_start_time_s": m["timer_start_time_s"], "trip_request_time_s": m["trip_request_time_s"],
        "breaker_command_time_s": m["breaker_command_time_s"], "actual_breaker_open_time_s": m["actual_breaker_open_time_s"],
        "pre_fault_max_loading_index_eq": m["pre_fault_max_loading_index_eq"],
        "pre_fault_false_trip_status": "fail" if pre_fault_trip else "pass",
        "relay_to_breaker_causality_status": "fail_trip_and_breaker_open_precede_threshold_and_fault" if pre_fault_trip else "not_evaluated",
        "no_fixed_time_bypass_status": no_fixed_bypass,
        "first_trip_order_status": "fail_breaker_open_at_initial_sample" if pre_fault_trip else "not_evaluated",
        "flow_driven_causality_proven": False,
        "post_trip_tline_response_computed": False,
        "post_trip_reason": "No valid trip transition exists; the breaker is already open at the initial runtime sample.",
        "generated_code_root_cause_evidence": generated_cause,
        "parameter_freeze_preserved": m["main_sha_final"] == m["main_sha_start"],
        "second_run_requested": False,
        "claim_boundary": claim,
    }
    trace = [
        {"check": "runtime .inf exists", "status": "pass" if m["inf_exists"] else "fail", "evidence": m["inf_path"]},
        {"check": "runtime .out exists", "status": "pass" if m["prefixed_out_file_count"] else "fail", "evidence": str(m["prefixed_out_file_count"])},
        {"check": "13 canonical channels readable", "status": "pass" if readable else "fail", "evidence": "13/13" if readable else "incomplete"},
        {"check": "time axis 0-20 s", "status": "pass" if m["time_start_s"] == 0.0 and m["time_end_s"] == 20.0 else "fail", "evidence": f"{m['time_start_s']}..{m['time_end_s']}"},
        {"check": "pre-fault false trip absent", "status": "fail" if pre_fault_trip else "pass", "evidence": f"trip={m['trip_request_time_s']}, fault={m['fault_start_time_s']}"},
        {"check": "threshold before timer", "status": "fail" if above_never and m["timer_start_time_s"] is not None else "pass", "evidence": f"threshold={m['first_threshold_crossing_time_s']}, timer={m['timer_start_time_s']}"},
        {"check": "relay-breaker causal order", "status": "fail" if pre_fault_trip else "not_evaluated", "evidence": f"trip={m['trip_request_time_s']}, cmd={m['breaker_command_time_s']}, open={m['actual_breaker_open_time_s']}"},
        {"check": "main project unchanged", "status": "pass" if m["main_sha_final"] == m["main_sha_start"] else "fail", "evidence": m["main_sha_final"]},
        {"check": "second run avoided", "status": "pass", "evidence": "single Stage-8 run only"},
    ]
    write_json(REPO / "data/validation/stage8_paper_ovl1_dynamic_final_audit.json", audit)
    write_csv(REPO / "data/validation/stage8_paper_ovl1_dynamic_integrity_trace.csv", trace)
    update_reference_files(status, claim)

    doc = f"""# Stage 8 PAPER_OVL1 runtime output and first-trip result

Generated: {audit['generated_at_local']}

## Result

- Classification: `{status}`
- Runtime output repair: **pass** (`.inf` present, {m['prefixed_out_file_count']} numbered `.out` files, 13/13 canonical channels readable)
- Time axis: `{m['time_start_s']}` to `{m['time_end_s']}` s at `{m['plot_step_s']}` s
- Main project SHA unchanged: `{audit['parameter_freeze_preserved']}`

## Dynamic evidence

`PAPER_OVL1_ABOVE_THRESHOLD` never asserted and the maximum pre-fault loading index was only
`{m['pre_fault_max_loading_index_eq']}`. Nevertheless, `TIMER_STATE`, `TRIP_REQUEST`, and
`BRK_CMD` were already asserted at `t=0`, and `BRK_STATE=2` (open) was present at the first
sample. Therefore there is no valid threshold -> timer -> trip -> breaker transition to rank.

Generated-code evidence agrees with the waveform: timer output `RT_18` drives the latch set
input, latch Q is exported as `TRIP_REQ`, and the observed timer output starts high. This is a
pre-fault false trip, not a flow-driven first trip. No second Run is requested.

## Claim boundary

{claim}

This result does not validate real line thermal capacity, real protection settings or
coordination, a second trip, natural cascading propagation, stability, UFLS/UVLS, conventional
generator protection, MATLAB coupling, SVC/STATCOM, or strict paper reproduction.
"""
    (REPO / "docs/STAGE8_PAPER_OVL1_RUNTIME_OUTPUT_AND_FIRST_TRIP_RESULT.md").write_text(doc, encoding="utf-8")
    print(json.dumps({"execution_status": status, "runtime_channel_integrity": audit["runtime_channel_integrity"], "flow_driven_causality_proven": False}, indent=2))


if __name__ == "__main__":
    main()
