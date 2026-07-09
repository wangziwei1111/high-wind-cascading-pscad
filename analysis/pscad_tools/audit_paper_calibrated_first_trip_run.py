#!/usr/bin/env python3
"""Audit stage-seven paper-calibrated first-trip results.

This audit accepts parser fallback when the single user run did not produce
PGB runtime waveform files.  It deliberately avoids requesting a second run.
"""

from __future__ import annotations

import csv
import json
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Any


REPO = Path(__file__).resolve().parents[2]
FORBIDDEN_EXTS = (".pscx", ".gf46", ".tli", ".tlo", ".out", ".inf", ".infx", ".sav", ".exe", ".o", ".obj", ".dll")


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


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


def git_status() -> list[str]:
    return subprocess.check_output(["git", "status", "--short"], cwd=REPO, text=True, encoding="utf-8").splitlines()


def update_capability_and_alignment(audit: dict[str, Any]) -> None:
    # Capability inventory JSON/CSV: append/replace a stage-seven row.
    inv_json_path = REPO / "data/reference/current_pscad_model_capability_inventory.json"
    if inv_json_path.exists():
        inv = read_json(inv_json_path)
        caps = inv.get("capabilities", []) if isinstance(inv, dict) else []
        caps = [c for c in caps if c.get("capability_id") != "PAPER_CALIBRATED_EQUIVALENT_FIRST_TRIP"]
        caps.append({
            "capability_id": "PAPER_CALIBRATED_EQUIVALENT_FIRST_TRIP",
            "status": "parser_fallback_unverified",
            "description": "Trial-only equivalent-capacity relay and breaker boundary were generated, but runtime PGB waveforms were unavailable for dynamic causality proof.",
            "selected_line": audit["selected_line"],
            "claim_boundary": audit["claim_boundary"],
        })
        inv["capabilities"] = caps
        write_json(inv_json_path, inv)

    inv_csv_path = REPO / "data/reference/current_pscad_model_capability_inventory.csv"
    if inv_csv_path.exists():
        rows = read_csv(inv_csv_path)
        rows = [r for r in rows if r.get("capability_id") != "PAPER_CALIBRATED_EQUIVALENT_FIRST_TRIP"]
        rows.append({
            "capability_id": "PAPER_CALIBRATED_EQUIVALENT_FIRST_TRIP",
            "status": "parser_fallback_unverified",
            "description": "Trial-only equivalent-capacity relay/breaker boundary built; runtime PGB waveforms unavailable.",
            "evidence_path": "data/validation/paper_calibrated_first_trip_final_audit.json",
        })
        write_csv(inv_csv_path, rows)

    # Alignment matrix: keep strict reproduction unavailable, record parser fallback.
    matrix_path = REPO / "data/reference/paper_reproduction_alignment_matrix.csv"
    if matrix_path.exists():
        rows = read_csv(matrix_path)
        found = False
        for r in rows:
            if r.get("paper_item_id") == "P09":
                r["current_status"] = "parser_fallback_unverified"
                r["current_evidence"] = "Equivalent-capacity relay generated but no runtime PGB waveforms available; flow-driven trip not proven."
                found = True
        if not found:
            rows.append({
                "paper_item_id": "P09",
                "paper_requirement": "paper-calibrated equivalent first-stage line protection",
                "current_status": "parser_fallback_unverified",
                "current_evidence": "data/validation/paper_calibrated_first_trip_final_audit.json",
            })
        write_csv(matrix_path, rows)

    for path in [
        REPO / "data/reference/paper_reproduction_minimum_cascade_design.json",
        REPO / "data/reference/paper_reproduction_fidelity_assessment.json",
        REPO / "data/reference/future_shadow_overload_candidate_decision.json",
    ]:
        if not path.exists():
            continue
        obj = read_json(path)
        obj["stage7_paper_calibrated_first_trip_status"] = audit["execution_status"]
        obj["stage7_selected_line"] = audit["selected_line"]
        obj["stage7_boundary"] = audit["claim_boundary"]
        obj["strict_reproduction_status"] = "not_achieved"
        write_json(path, obj)


def write_docs(audit: dict[str, Any]) -> None:
    doc = f"""# Paper-calibrated first-trip run and topology response

Generated: {audit['generated_at_local']}

## Result

- Execution status: `{audit['execution_status']}`
- Selected TLine: `{audit['selected_line']}`
- Equivalent capacity: `{audit['effective_capacity_pu']}`
- Threshold multiplier: `{audit['threshold_multiplier']}`
- Protection curve: `{audit['protection_curve_type']}`
- Delay: `{audit['definite_delay_s']} s`

## What was verified

The generated PSCAD code contains the trial-only relay and breaker boundary:

- Relay subroutine generated: `{audit['generated_code_chain_checks']['relay_subroutine_generated']}`
- Relay inputs use `E_28_29_1` dual-end P/Q signals: `{audit['generated_code_chain_checks']['relay_inputs_from_selected_tline_pq']}`
- Three-phase breaker generated: `{audit['generated_code_chain_checks']['breaker_generated']}`
- Breaker uses `PAPER_OVL1_BRK_CMD`: `{audit['generated_code_chain_checks']['breaker_uses_relay_command']}`
- Breaker state signal generated: `{audit['generated_code_chain_checks']['breaker_state_signal_generated']}`

## Parser fallback boundary

The single user stage did not leave parsable PSCAD Output Channel runtime files:

`{audit['runtime_pgb_output_detection']['reason']}`

Therefore this audit does not claim that the full chain
real TLine P/Q -> loading index -> timer -> trip request -> breaker command -> actual breaker open
was dynamically observed.

## Claim boundary

{audit['claim_boundary']}

This stage is a paper-constrained equivalent-protection adaptation.  It does not verify
PNNL continuous thermal limits, true thermal overload, true protection settings,
protection coordination, a second line trip, natural cascading propagation,
UFLS/UVLS, conventional generator protection, MATLAB coupling, SVC/STATCOM, or strict
paper reproduction.
"""
    (REPO / "docs/PAPER_CALIBRATED_FIRST_TRIP_RUN_AND_TOPOLOGY_RESPONSE.md").write_text(doc, encoding="utf-8")

    snippets = [
        REPO / "docs/PAPER_REPRODUCTION_ALIGNMENT_AND_MINIMUM_CASCADE_PLAN.md",
        REPO / "docs/PAPER_REPRODUCTION_GAP_REGISTER.md",
        REPO / "docs/PAPER_ALIGNED_20S_DYNAMIC_RUN_AND_TLINE_RESPONSE.md",
    ]
    for path in snippets:
        if not path.exists():
            continue
        text = path.read_text(encoding="utf-8")
        marker = "\n## Stage seven paper-calibrated equivalent first-trip attempt\n"
        addition = (
            marker
            + f"\nStatus: `{audit['execution_status']}`.  Selected line `{audit['selected_line']}` with "
            + f"equivalent capacity `{audit['effective_capacity_pu']}` and 1.1 + 5 s fallback logic. "
            + "Generated code confirms the trial relay/breaker chain, but runtime PGB waveforms were unavailable; "
            + "therefore no dynamic flow-driven trip or actual breaker-open causality is claimed.\n"
        )
        if marker in text:
            text = text.split(marker)[0].rstrip() + addition
        else:
            text = text.rstrip() + "\n" + addition
        path.write_text(text + "\n", encoding="utf-8")


def main() -> None:
    manifest = read_json(REPO / "data/derived/paper_calibrated_first_trip_run_manifest.json")
    freeze = read_json(REPO / "data/reference/paper_calibrated_first_trip_parameter_freeze.json")
    timeline = read_csv(REPO / "data/derived/paper_calibrated_first_trip_event_timeline.csv")
    relay_trace = read_csv(REPO / "data/derived/paper_calibrated_first_trip_relay_trace.csv")
    post_trip = read_csv(REPO / "data/derived/paper_calibrated_first_trip_post_trip_tline_response.csv")

    runtime_present = manifest["runtime_pgb_output_detection"]["status"] == "runtime_pgb_outputs_present"
    generated_ok = all(manifest["generated_code_chain_checks"].values())
    execution_status = "paper_calibrated_first_trip_parser_fallback"
    if runtime_present:
        execution_status = "paper_calibrated_first_trip_no_trip_observed"

    forbidden_status = [s for s in git_status() if any(ext in s.lower() for ext in FORBIDDEN_EXTS)]

    audit = {
        "audit_name": "paper_calibrated_first_trip_final_audit",
        "generated_at_local": datetime.now().isoformat(timespec="seconds"),
        "execution_status": execution_status,
        "selected_line": manifest["selected_line"],
        "effective_capacity_pu": manifest["effective_capacity_pu"],
        "threshold_multiplier": manifest["threshold_multiplier"],
        "protection_curve_type": manifest["protection_curve_type"],
        "definite_delay_s": manifest["definite_delay_s"],
        "main_sha_start": manifest["main_sha_start"],
        "main_sha_final": manifest["main_sha_after_user_stage"],
        "trial_sha_start": manifest["trial_sha_start"],
        "trial_sha_after_user_stage": manifest["trial_sha_after_user_stage"],
        "runtime_pgb_output_detection": manifest["runtime_pgb_output_detection"],
        "generated_code_chain_checks": manifest["generated_code_chain_checks"],
        "generated_code_chain_static_status": "pass" if generated_ok else "fail",
        "paper_channel_count_in_generated_code": manifest["paper_pgb_channel_count_in_generated_code"],
        "all_required_paper_channels_present_in_generated_code": manifest["all_required_paper_channels_present_in_generated_code"],
        "event_timeline_rows": len(timeline),
        "relay_trace_rows": len(relay_trace),
        "post_trip_response_rows": len(post_trip),
        "first_threshold_crossing_time_s": None,
        "timer_start_time_s": None,
        "trip_request_time_s": None,
        "breaker_command_time_s": None,
        "actual_breaker_open_time_s": None,
        "first_trip_order_check": "unavailable_runtime_pgb_outputs_missing",
        "pre_fault_false_trip_check": "unavailable_runtime_pgb_outputs_missing",
        "relay_to_breaker_causality_check": "unavailable_runtime_pgb_outputs_missing",
        "no_time_trigger_bypass_check": "static_pass_no_fixed_time_source_detected_in_generated_chain",
        "flow_driven_causality_proven": False,
        "post_trip_topology_response_computed": False,
        "strict_reproduction_status": "not_achieved",
        "needs_second_parameter_version": True,
        "minimum_second_version_direction": "Ensure PSCAD writes PGB Output Channel runtime .inf/.out files for PAPER_OVL1_* channels before changing equivalent-capacity parameters; do not run a second parameter version in this audit.",
        "claim_boundary": (
            "This stage documents a trial-only paper-calibrated equivalent protection attempt. "
            "It does not represent PNNL real continuous thermal capacity or true protection-setting validation."
        ),
        "forbidden_git_artifact_status": "pass" if not forbidden_status else "fail",
        "forbidden_git_status_entries": forbidden_status,
    }

    trace = [
        {"check": "generated relay/breaker static chain", "status": audit["generated_code_chain_static_status"]},
        {"check": "runtime PGB output availability", "status": manifest["runtime_pgb_output_detection"]["status"]},
        {"check": "dynamic causality proof", "status": "unavailable_runtime_pgb_outputs_missing"},
        {"check": "forbidden Git artifacts", "status": audit["forbidden_git_artifact_status"]},
    ]

    write_json(REPO / "data/validation/paper_calibrated_first_trip_final_audit.json", audit)
    write_csv(REPO / "data/validation/paper_calibrated_first_trip_integrity_trace.csv", trace)
    update_capability_and_alignment(audit)
    write_docs(audit)
    print(json.dumps({"execution_status": execution_status, "selected_line": audit["selected_line"]}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
