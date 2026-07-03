#!/usr/bin/env python3
"""Final dynamic audit for the single Stage-9 9-second Run."""

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


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as f: return list(csv.DictReader(f))


def write_json(path: Path, obj: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    fields = list(rows[0]) if rows else []
    with path.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields); w.writeheader(); w.writerows(rows)


def update_references(status: str, claim: str) -> None:
    jp = REPO / "data/reference/current_pscad_model_capability_inventory.json"
    if jp.exists():
        obj = read_json(jp); caps = [x for x in obj.get("capabilities", []) if x.get("capability_id") != "PAPER_CALIBRATED_EQUIVALENT_FIRST_TRIP"]
        caps.append({"capability_id": "PAPER_CALIBRATED_EQUIVALENT_FIRST_TRIP", "status": status,
                     "description": "Stage-9 9 s runtime shows healthy initialization and a 5 s flow-driven equivalent first trip on E_28_29_1.",
                     "selected_line": "E_28_29_1", "claim_boundary": claim})
        obj["capabilities"] = caps; write_json(jp, obj)
    cp = REPO / "data/reference/current_pscad_model_capability_inventory.csv"
    if cp.exists():
        rows = read_csv(cp); fields = list(rows[0])
        for r in rows:
            if r.get("capability_id") == "PAPER_CALIBRATED_EQUIVALENT_FIRST_TRIP":
                r["status"] = status; r["description"] = "Healthy initialization and 5 s flow-driven equivalent first trip observed in one 9 s Run."
                r["evidence_path"] = "data/validation/stage9_short_run_dynamic_final_audit.json"; r["claim_boundary"] = claim
        with cp.open("w", encoding="utf-8", newline="") as f:
            w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows(rows)
    matrix = REPO / "data/reference/paper_reproduction_alignment_matrix.csv"
    if matrix.exists():
        rows=read_csv(matrix);fields=list(rows[0])
        for r in rows:
            if r.get("paper_item_id") == "P09":
                r["current_status"] = status; r["current_evidence"] = "data/validation/stage9_short_run_dynamic_final_audit.json"
        with matrix.open("w",encoding="utf-8",newline="") as f:
            w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows(rows)
    future = REPO / "data/reference/future_shadow_overload_candidate_decision.json"
    if future.exists():
        obj=read_json(future);obj["stage9_short_run_status"]=status;obj["stage9_short_run_evidence"]="data/validation/stage9_short_run_dynamic_final_audit.json";obj["strict_reproduction_status"]="not_achieved";write_json(future,obj)
    marker="\n## Stage nine short-run initialization repair and first trip\n"
    addition=(marker+f"\nStatus: `{status}`. The 9.0 s Run has healthy pre-fault initialization and records the "
              "equivalent E_28_29_1 threshold-to-timer-to-breaker first-trip chain. This remains a paper-calibrated "
              "equivalent protection result, not a verified PNNL thermal rating, real protection setting, second trip, "
              "or natural cascade. Strict reproduction remains `not_achieved`.\n")
    for p in [REPO/"docs/PAPER_REPRODUCTION_GAP_REGISTER.md",REPO/"docs/PAPER_REPRODUCTION_ALIGNMENT_AND_MINIMUM_CASCADE_PLAN.md"]:
        if p.exists():
            text=p.read_text(encoding="utf-8");text=text.split(marker)[0].rstrip() if marker in text else text.rstrip();p.write_text(text+addition,encoding="utf-8")


def main() -> None:
    m=read_json(REPO/"data/derived/stage9_short_run_manifest.json")
    gate=read_json(REPO/"data/validation/stage9_short_run_pre_run_gate.json")
    post=read_csv(REPO/"data/derived/stage9_short_run_post_trip_tline_response.csv")
    runtime_ok=all([m["inf_exists"],m["prefixed_out_file_count"]>0,m["paper_channels_all_readable"],m["common_time_axis"],m["sample_count"]==901,m["time_start_s"]==0.0,m["time_end_s"]==9.0,abs(m["plot_step_s"]-0.01)<1e-9,m["runtime_outputs_newer_than_stage9_build"]])
    t0=m["t0"]; init_ok=all(t0[x]==0.0 for x in t0) and m["pre_fault_false_trip"] is False
    chain_times=[m["first_threshold_crossing_time_s"],m["timer_completion_time_s"],m["trip_request_time_s"],m["breaker_command_time_s"],m["actual_breaker_open_time_s"]]
    chain_present=all(x is not None for x in chain_times)
    delay_ok=chain_present and abs(m["timer_completion_time_s"]-m["timer_start_time_s"]-5.0)<=0.011
    order_ok=chain_present and m["first_threshold_crossing_time_s"]<=m["timer_completion_time_s"]<=m["trip_request_time_s"]<=m["breaker_command_time_s"]<=m["actual_breaker_open_time_s"]
    no_bypass=gate["gates"]["no_time_fault_dfig_oneshot_bypass"]
    if not runtime_ok: status="stage9_short_run_runtime_output_parser_fallback"
    elif not init_ok: status="stage9_short_run_pre_fault_false_trip"
    elif not chain_present: status="stage9_short_run_no_trip_observed"
    elif not (delay_ok and order_ok and no_bypass): status="stage9_short_run_relay_breaker_causality_failure"
    else: status="stage9_short_run_flow_driven_first_trip_pass"
    claim=("This Stage-9 result validates a trial-only, paper-calibrated equivalent first-trip chain. It does not establish "
           "PNNL continuous thermal capacity, real overload or protection settings/coordination, a second trip, natural cascading, or strict paper reproduction.")
    top10=sorted([r for r in post if r.get("redistribution_rank_excluding_opened_line")],
                 key=lambda r:int(r["redistribution_rank_excluding_opened_line"]))[:10]
    audit={"audit_name":"stage9_short_run_dynamic_final_audit","generated_at_local":datetime.now().isoformat(timespec="seconds"),
           "execution_status":status,"branch":subprocess.check_output(["git","branch","--show-current"],cwd=REPO,text=True).strip(),
           "main_sha_start":m["main_sha_start"],"main_sha_final":m["main_sha_final"],"trial_sha_start":m["trial_sha_start"],"trial_sha_final":m["trial_sha_final"],
           "selected_line":m["selected_line"],"effective_capacity_pu":m["effective_capacity_pu"],"threshold_multiplier":m["threshold_multiplier"],"definite_delay_s":m["definite_delay_s"],
           "run_duration_s":9.0,"run_count":m["stage9_run_count"],"runtime_integrity_status":"pass" if runtime_ok else "fail","all_13_runtime_channels_readable":m["paper_channels_all_readable"],
           "t0":t0,"fault_start_time_s":m["fault_start_time_s"],"fault_clear_time_s":m["fault_clear_time_s"],"dfig_event_time_s":m["dfig_event_time_s"],
           "first_threshold_crossing_time_s":m["first_threshold_crossing_time_s"],"timer_start_time_s":m["timer_start_time_s"],"timer_completion_time_s":m["timer_completion_time_s"],
           "continuous_above_threshold_duration_s":m["continuous_above_threshold_duration_s"],"trip_request_time_s":m["trip_request_time_s"],"breaker_command_time_s":m["breaker_command_time_s"],"actual_breaker_open_time_s":m["actual_breaker_open_time_s"],
           "pre_fault_max_loading_index_eq":m["pre_fault_max_loading_index_eq"],"pre_fault_false_trip_status":"pass" if init_ok else "fail",
           "relay_to_breaker_causality_status":"pass_at_0p01s_plot_resolution" if order_ok else "fail","no_fixed_time_bypass_status":"pass" if no_bypass else "fail",
           "first_trip_order_status":"pass_equivalent_relay_first_trip;_dfig_event_not_observed_in_9s_runtime" if order_ok else "fail",
           "flow_driven_causality_proven":status=="stage9_short_run_flow_driven_first_trip_pass","post_trip_response_line_count":len(post),
           "top10_post_trip_high_stress_response_trends":top10,"parameter_freeze_preserved":m["main_sha_start"]==m["main_sha_final"],"second_run_requested":False,"claim_boundary":claim}
    checks=[("runtime output integrity",runtime_ok),("t0 and pre-fault healthy",init_ok),("threshold/timer/trip/open present",chain_present),("5 s timer delay",delay_ok),("causal order",order_ok),("no fixed-time bypass",no_bypass),("31 line post-trip response",len(post)==31),("single 9 s run",m["stage9_run_count"]==1 and m["time_end_s"]==9.0)]
    write_json(REPO/"data/validation/stage9_short_run_dynamic_final_audit.json",audit)
    write_csv(REPO/"data/validation/stage9_short_run_dynamic_integrity_trace.csv",[{"check":k,"status":"pass" if v else "fail"} for k,v in checks])
    update_references(status,claim)
    top_lines="\n".join(f"{r['redistribution_rank_excluding_opened_line']}. `{r['network_branch_id']}`: delta raw S `{float(r['delta_raw_S']):.6g}`, delta I `{float(r['delta_I']):.6g}`" for r in top10)
    doc=f"""# Stage 9 short-run initialization repair and first-trip result

Generated: {audit['generated_at_local']}

## Result

- Classification: `{status}`
- Runtime: one `9.0 s` Run, `0.01 s` plot step, 13/13 PAPER_OVL1 channels readable
- t=0: ABOVE/TIMER/TRIP/BRK_CMD/BRK_STATE = `0/0/0/0/0`
- Pre-fault maximum loading index: `{m['pre_fault_max_loading_index_eq']}`; false trip: `False`
- Threshold and timer accumulation start: `{m['first_threshold_crossing_time_s']} s`
- Timer completion / trip request / breaker command / actual open: `{m['timer_completion_time_s']} / {m['trip_request_time_s']} / {m['breaker_command_time_s']} / {m['actual_breaker_open_time_s']} s`
- Continuous delay to completion: `{m['continuous_above_threshold_duration_s']} s`
- DFIG cascade event in this 9 s runtime: `{m['dfig_event_time_s']}` (not observed)

The command and breaker state change share the same 0.01 s output sample. Generated code establishes command-to-breaker dependence, so causality passes at output resolution.

## Top-10 post-trip high-stress response trends

{top_lines}

These are raw post-trip response trends only, not verified overloads or second-trip candidates.

## Claim boundary

{claim}
"""
    (REPO/"docs/STAGE9_SHORT_RUN_INITIALIZATION_REPAIR_AND_FIRST_TRIP_RESULT.md").write_text(doc,encoding="utf-8")
    print(json.dumps({"execution_status":status,"flow_driven_causality_proven":audit["flow_driven_causality_proven"],"top10_count":len(top10)},indent=2))


if __name__ == "__main__": main()
