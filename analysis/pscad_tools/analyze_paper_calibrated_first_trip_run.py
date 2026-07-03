#!/usr/bin/env python3
"""Analyze the stage-seven paper-calibrated first-trip run attempt.

The script does not call PSCAD, Build, or Run.  It inspects generated code and
available run-output files after the single user GUI/Build/Run stage.  If the
PGB runtime `.inf/.out` channel files are unavailable, it records a parser
fallback rather than requesting another run.
"""

from __future__ import annotations

import csv
import hashlib
import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any


REPO = Path(__file__).resolve().parents[2]
GF46 = Path(r"C:\pscad_work\pnnl_39_3ibr_pscad46_strip5\PSCAD\3IBR_DFIG1_TRIAL.gf46")
MAIN_PSCX = Path(r"C:\pscad_work\pnnl_39_3ibr_pscad46_strip5\PSCAD\3IBR.pscx")
TRIAL_PSCX = Path(r"C:\pscad_work\pnnl_39_3ibr_pscad46_strip5\PSCAD\3IBR_DFIG1_TRIAL.pscx")
OUT_PREFIX = "3IBR_DFIG1_TRIAL"
PAPER_CHANNELS = [
    "PAPER_OVL1_S_A_PU",
    "PAPER_OVL1_S_B_PU",
    "PAPER_OVL1_S_MAX_PU",
    "PAPER_OVL1_EFFECTIVE_CAPACITY_PU",
    "PAPER_OVL1_LOADING_INDEX_EQ",
    "PAPER_OVL1_ABOVE_THRESHOLD",
    "PAPER_OVL1_TIMER_OR_CURVE_STATE",
    "PAPER_OVL1_TRIP_REQUEST",
    "PAPER_OVL1_BRK_CMD",
    "PAPER_OVL1_BRK_STATE",
    "PAPER_OVL1_TRIP_EVENT_VALID",
    "PAPER_OVL1_FIRST_TRIP_TIME_S",
    "PAPER_OVL1_RELAY_ENABLE",
]


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest().upper()


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


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def p3_text() -> str:
    path = GF46 / "P3.f"
    return path.read_text(encoding="utf-8", errors="ignore") if path.exists() else ""


def find_paper_pgb_bindings(text: str) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    lines = text.splitlines()
    for i, line in enumerate(lines):
        m = re.search(r"\[pgb\] Output Channel '([^']+)'", line)
        if not m or not m.group(1).startswith("PAPER_OVL1_"):
            continue
        title = m.group(1)
        assignment = ""
        for nxt in lines[i + 1 : i + 6]:
            if "PGB(" in nxt:
                assignment = nxt.strip()
                break
        pgb_idx = None
        signal = None
        m2 = re.search(r"PGB\(IPGB\+(\d+)\)\s*=\s*(.*)", assignment)
        if m2:
            pgb_idx = int(m2.group(1))
            signal = m2.group(2).strip()
        rows.append({
            "channel_title": title,
            "generated_code_status": "present",
            "pgb_offset": pgb_idx,
            "assigned_signal_expression": signal,
        })
    return rows


def generated_chain_checks(text: str) -> dict[str, Any]:
    return {
        "relay_subroutine_generated": "CALL PAPER_OVL1_RELAYDyn" in text,
        "relay_inputs_from_selected_tline_pq": all(s in text for s in [
            "E_28_29_1_B_Q",
            "E_28_29_1_B_P",
            "E_28_29_1_A_Q",
            "E_28_29_1_A_P",
        ]),
        "breaker_generated": "3 Phase Breaker 'PAPER_OVL1_BRK_CMD'" in text,
        "breaker_uses_relay_command": "NINT(1.0-PAPER_OVL1_BRK_CMD)" in text,
        "breaker_state_signal_generated": "PAPER_OVL1_BRK_STATE = IVD1_1" in text,
    }


def runtime_inventory() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    if not GF46.exists():
        return rows
    for p in sorted(GF46.iterdir(), key=lambda x: x.name.lower()):
        if not p.is_file():
            continue
        if p.suffix.lower() not in {".inf", ".infx", ".out", ".tli", ".tlo", ".log", ".f", ".dta", ".o", ".exe", ".map", ".mak"}:
            continue
        rows.append({
            "name": p.name,
            "path": str(p),
            "suffix": p.suffix.lower(),
            "length": p.stat().st_size,
            "mtime_local": datetime.fromtimestamp(p.stat().st_mtime).isoformat(timespec="seconds"),
        })
    return rows


def detect_runtime_pgb_outputs(inv: list[dict[str, Any]]) -> dict[str, Any]:
    inf = GF46 / f"{OUT_PREFIX}.inf"
    out_files = sorted(GF46.glob(f"{OUT_PREFIX}_*.out"))
    if inf.exists() and out_files:
        return {
            "status": "runtime_pgb_outputs_present",
            "inf_path": str(inf),
            "out_file_count": len(out_files),
        }
    return {
        "status": "runtime_pgb_outputs_missing",
        "inf_path": str(inf),
        "inf_exists": inf.exists(),
        "prefixed_out_file_count": len(out_files),
        "available_line_constant_out_count": len([r for r in inv if re.match(r"E_\d+_\d+_1\.out$", r["name"])]),
        "reason": "The run directory contains updated TLine Line Constants .out files, but no PSCAD Output Channel .inf or 3IBR_DFIG1_TRIAL_NN.out files for PGB waveform parsing.",
    }


def main() -> None:
    freeze = read_json(REPO / "data/reference/paper_calibrated_first_trip_parameter_freeze.json")
    baseline = read_json(REPO / "data/validation/paper_calibrated_first_trip_baseline_manifest.json")
    text = p3_text()
    inv = runtime_inventory()
    runtime = detect_runtime_pgb_outputs(inv)
    pgb_rows = find_paper_pgb_bindings(text)
    chain = generated_chain_checks(text)
    execution_status = (
        "paper_calibrated_first_trip_parser_fallback"
        if runtime["status"] != "runtime_pgb_outputs_present"
        else "paper_calibrated_first_trip_runtime_outputs_detected"
    )

    timeline_rows = [{
        "event": "fault_start",
        "time_s": 0.50,
        "source": "frozen stage-four scenario",
        "status": "reference",
    }, {
        "event": "fault_clear",
        "time_s": 2.50,
        "source": "frozen stage-four scenario",
        "status": "reference",
    }, {
        "event": "dfig_event_observed_in_baseline",
        "time_s": 2.43,
        "source": "paper_aligned_20s_event_timeline.csv",
        "status": "reference",
    }, {
        "event": "paper_ovl1_threshold_crossing",
        "time_s": None,
        "source": "PAPER_OVL1_* runtime PGB outputs",
        "status": "unavailable_runtime_pgb_outputs_missing",
    }, {
        "event": "paper_ovl1_trip_request",
        "time_s": None,
        "source": "PAPER_OVL1_* runtime PGB outputs",
        "status": "unavailable_runtime_pgb_outputs_missing",
    }, {
        "event": "paper_ovl1_actual_breaker_open",
        "time_s": None,
        "source": "PAPER_OVL1_BRK_STATE runtime PGB output",
        "status": "unavailable_runtime_pgb_outputs_missing",
    }]

    relay_trace_rows = [{
        "signal": row["channel_title"],
        "generated_code_status": row["generated_code_status"],
        "pgb_offset": row["pgb_offset"],
        "assigned_signal_expression": row["assigned_signal_expression"],
        "runtime_waveform_status": "unavailable_missing_3IBR_DFIG1_TRIAL_inf_and_prefixed_out_files",
    } for row in pgb_rows]

    post_trip_rows = []
    for name in sorted([r["name"] for r in inv if re.match(r"E_\d+_\d+_1\.out$", r["name"])]):
        branch = name[:-4]
        post_trip_rows.append({
            "network_branch_id": branch,
            "post_trip_delta_P": None,
            "post_trip_delta_Q": None,
            "post_trip_delta_I": None,
            "post_trip_raw_S_change": None,
            "post_trip_response_rank": None,
            "status": "not_computed_actual_breaker_open_time_unavailable",
        })

    manifest = {
        "manifest_name": "paper_calibrated_first_trip_run_manifest",
        "generated_at_local": datetime.now().isoformat(timespec="seconds"),
        "execution_status": execution_status,
        "selected_line": freeze.get("selected_network_branch_id"),
        "effective_capacity_pu": freeze.get("effective_capacity_pu"),
        "threshold_multiplier": freeze.get("threshold_multiplier"),
        "protection_curve_type": freeze.get("protection_curve_type"),
        "definite_delay_s": freeze.get("definite_delay_s_or_exact_paper_curve_parameters", {}).get("definite_delay_s"),
        "main_sha_start": baseline.get("main_sha_start"),
        "main_sha_after_user_stage": sha256(MAIN_PSCX),
        "trial_sha_start": baseline.get("trial_sha_start"),
        "trial_sha_after_user_stage": sha256(TRIAL_PSCX),
        "gf46_dir": str(GF46),
        "runtime_pgb_output_detection": runtime,
        "generated_code_chain_checks": chain,
        "paper_pgb_channel_count_in_generated_code": len(pgb_rows),
        "required_paper_channel_count": len(PAPER_CHANNELS),
        "all_required_paper_channels_present_in_generated_code": sorted({r["channel_title"] for r in pgb_rows}) == sorted(PAPER_CHANNELS),
        "raw_runtime_artifacts_not_committed": True,
    }

    write_csv(REPO / "data/derived/paper_calibrated_first_trip_event_timeline.csv", timeline_rows)
    write_csv(REPO / "data/derived/paper_calibrated_first_trip_relay_trace.csv", relay_trace_rows)
    write_csv(REPO / "data/derived/paper_calibrated_first_trip_post_trip_tline_response.csv", post_trip_rows)
    write_json(REPO / "data/derived/paper_calibrated_first_trip_run_manifest.json", manifest)
    print(json.dumps({
        "execution_status": execution_status,
        "selected_line": freeze.get("selected_network_branch_id"),
        "runtime_pgb_status": runtime["status"],
        "paper_pgb_channel_count_in_generated_code": len(pgb_rows),
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
