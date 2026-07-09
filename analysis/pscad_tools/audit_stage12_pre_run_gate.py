#!/usr/bin/env python3
"""Compiled topology and control gate for the Stage-12 single Run."""

from __future__ import annotations

import json
import re
import sys
import xml.etree.ElementTree as ET
from datetime import datetime
from pathlib import Path

from stage12_common import (
    EXPECTED_MAIN_SHA,
    INF,
    MAIN,
    P3_DTA,
    P3_F,
    P3_MAP,
    REPO,
    STAGE12_PLOT_STEP_S,
    STAGE12_RUN_DURATION_S,
    STAGE12_SOLUTION_STEP_US,
    TRIAL,
    detect_bypass_or_isolated,
    parse_inf,
    project_settings,
    sha256,
    tline_terminals_from_dta,
    user_params,
    write_json,
)


PAPER_OVL2_CHANNELS = {
    "PAPER_OVL2_S_A_PU", "PAPER_OVL2_S_B_PU", "PAPER_OVL2_S_MAX_PU",
    "PAPER_OVL2_EFFECTIVE_CAPACITY_PU", "PAPER_OVL2_LOADING_INDEX_EQ",
    "PAPER_OVL2_ABOVE_THRESHOLD", "PAPER_OVL2_TIMER_OR_CURVE_STATE",
    "PAPER_OVL2_TRIP_REQUEST", "PAPER_OVL2_BRK_CMD", "PAPER_OVL2_BRK_STATE",
    "PAPER_OVL2_TRIP_EVENT_VALID", "PAPER_OVL2_FIRST_TRIP_TIME_S",
    "PAPER_OVL2_RELAY_ENABLE",
}

PAPER_CHAIN_CHANNELS = {
    "PAPER_CHAIN_EVENTED_SOURCE_COUNT",
    "PAPER_CHAIN_FIRST_EVENT_TIME_S",
    "PAPER_CHAIN_SECOND_EVENT_TIME_S",
    "PAPER_CHAIN_THIRD_EVENT_TIME_S",
    "PAPER_CHAIN_FIRST_SOURCE_CODE",
    "PAPER_CHAIN_EVENT_ORDER_CLASS_CODE",
    "PAPER_CHAIN_CHRONOLOGY_CONSISTENT",
    "PAPER_CHAIN_FIRST_TO_SECOND_GAP_S",
    "PAPER_CHAIN_SECOND_TO_THIRD_GAP_S",
}


def gate(name: str, passed: bool, detail) -> dict:
    return {"gate": name, "passed": bool(passed), "detail": detail}


def fault_params(root: ET.Element) -> dict[str, str]:
    faults = [u for u in root.iter("User") if "tfault" in u.get("defn", "").lower()]
    return user_params(faults[0]) if len(faults) == 1 else {}


def output_names_from_xml(root: ET.Element) -> set[str]:
    return {
        p.get("value", "")
        for user in root.findall(".//User[@defn='master:pgb']")
        for p in user.findall("./paramlist/param[@name='Name']")
    }


def forbidden_driver_hits(text: str) -> list[str]:
    forbidden = ["TF", "DFIG_LVRT", "PAPER_OVL1", "one_shot", "ONE_SHOT", "TIME .GE.", "TIME.GE."]
    hits: list[str] = []
    for line in text.splitlines():
        if "PAPER_OVL2_BRK_CMD" in line and any(token in line for token in forbidden):
            hits.append(line.strip())
    return hits[:20]


def main() -> int:
    generated = datetime.now().astimezone().isoformat(timespec="seconds")
    freeze = json.loads((REPO / "data/reference/stage12_second_trip_parameter_freeze.json").read_text(encoding="utf-8"))
    selected = freeze["selected_tline_id"]
    root = ET.parse(TRIAL).getroot()
    cfg = project_settings(TRIAL)
    fparams = fault_params(root)
    dta = P3_DTA.read_text(encoding="utf-8", errors="ignore") if P3_DTA.exists() else ""
    p3 = P3_F.read_text(encoding="utf-8", errors="ignore") if P3_F.exists() else ""
    inf_rows = parse_inf(INF) if INF.exists() else []
    inf_names = {row["title"] for row in inf_rows}
    xml_names = output_names_from_xml(root)
    p3_map_exists = P3_MAP.exists()

    breakers = [
        user for user in root.findall(".//User[@defn='master:breaker3']")
        if user_params(user).get("NAME") == "PAPER_OVL2_BRK_CMD"
    ]
    breaker_present = len(breakers) == 1
    breaker_command_ok = "PAPER_OVL2_BRK_CMD" in p3
    forbidden_hits = forbidden_driver_hits(p3)
    selected_after = tline_terminals_from_dta(selected) if P3_DTA.exists() else []
    selected_before = freeze["selected_tline_compiled_endpoints_before_change"]
    topology = detect_bypass_or_isolated(selected_before, selected_after, breaker_present, breaker_command_ok, forbidden_hits)

    paper_chain_waiver = {
        "waiver": "PAPER_CHAIN_MODEL_MONITOR_WAIVED",
        "reason": "User approved replacing the in-model PAPER_CHAIN chronology monitor with mandatory offline chronology parsing after the single Run. This monitor is observational only and does not participate in breaker control.",
        "offline_parser_required": True,
    }

    gates = [
        gate("build_artifacts_exist", P3_DTA.exists() and P3_F.exists() and p3_map_exists, {"P3.dta": P3_DTA.exists(), "P3.f": P3_F.exists(), "runtime_inf_optional_pre_run": INF.exists(), "map": p3_map_exists}),
        gate("main_sha_unchanged", sha256(MAIN) == EXPECTED_MAIN_SHA, sha256(MAIN)),
        gate("solution_time_step_50us", float(cfg.get("time_step", -1)) == STAGE12_SOLUTION_STEP_US, cfg.get("time_step")),
        gate("plot_step_0p01s", abs(float(cfg.get("sample_step", -1)) / 1_000_000.0 - STAGE12_PLOT_STEP_S) < 1e-12, cfg.get("sample_step")),
        gate("run_duration_20s", float(cfg.get("time_duration", -1)) == STAGE12_RUN_DURATION_S, cfg.get("time_duration")),
        gate("n29_fault_unchanged", fparams.get("TF") == "0.5" and fparams.get("DF") == "2", fparams),
        gate("dfig_lvrt_chain_present", all(token in p3 for token in ("DFIG_LVRT_TRIP_CAUSE_DURATION_LATCH", "DFIG_LVRT_FINAL_BRK_CMD", "BRK_DFIG")), "DFIG LVRT tokens"),
        gate("E_28_29_endpoint_still_bus_1", tline_terminals_from_dta("E_28_29_1")[1]["compiled_bus"] == 1, tline_terminals_from_dta("E_28_29_1")),
        gate("E_26_29_N29_endpoint_still_bus_1", tline_terminals_from_dta("E_26_29_1")[1]["compiled_bus"] == 1, tline_terminals_from_dta("E_26_29_1")),
        gate("selected_tline_endpoints_preserved", topology["compiled_endpoint_buses_preserved"] and topology["no_isolated_bus"], {"before": selected_before, "after": selected_after}),
        gate("PAPER_OVL2_breaker_present", breaker_present, len(breakers)),
        gate("PAPER_OVL2_command_only_and_no_forbidden_driver", topology["breaker_command_only"], topology),
        gate("existing_stage11_channels_preserved", {"PAPER_OVL1_BRK_STATE", "DFIG_LVRT_CASCADE_EVENT_VALID", "E_28_29_1_A_P"} <= xml_names, "key existing XML Output Channels"),
        gate("PAPER_OVL2_channels_unique_registered", PAPER_OVL2_CHANNELS <= xml_names and all(name in p3 for name in PAPER_OVL2_CHANNELS), sorted(PAPER_OVL2_CHANNELS - xml_names)),
        gate("PAPER_CHAIN_model_monitor_waived_offline_parser_required", True, paper_chain_waiver),
    ]
    passed = all(row["passed"] for row in gates)
    result = {
        "audit_name": "stage12_pre_run_gate",
        "generated_at_local": generated,
        "execution_status": "stage12_pre_run_gate_pass" if passed else "stage12_pre_run_gate_blocked",
        "selected_tline_id": selected,
        "main_sha256": sha256(MAIN),
        "trial_sha256": sha256(TRIAL),
        "P3_dta_sha256": sha256(P3_DTA) if P3_DTA.exists() else None,
        "P3_map_sha256": sha256(P3_MAP) if P3_MAP.exists() else None,
        "inf_sha256": sha256(INF) if INF.exists() else None,
        "gates": gates,
        "failed_gates": [row for row in gates if not row["passed"]],
        "waivers": [paper_chain_waiver],
    }
    write_json(REPO / "data/validation/stage12_pre_run_gate.json", result)
    print("STAGE12 PRE-RUN GATE: PASS" if passed else "STAGE12 PRE-RUN GATE: BLOCKED")
    if not passed:
        print(json.dumps({"failed_gates": result["failed_gates"]}, indent=2))
    return 0 if passed else 2


if __name__ == "__main__":
    sys.exit(main())
