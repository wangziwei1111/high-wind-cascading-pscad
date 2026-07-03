#!/usr/bin/env python3
"""Lightweight read-only gate for the Stage-11 20 s / 50 us single Run."""

from __future__ import annotations

import hashlib
import json
import re
import xml.etree.ElementTree as ET
from datetime import datetime
from pathlib import Path
from typing import Any

REPO = Path(__file__).resolve().parents[2]
PSCAD = Path(r"C:\pscad_work\pnnl_39_3ibr_pscad46_strip5\PSCAD")
MAIN = PSCAD / "3IBR.pscx"
TRIAL = PSCAD / "3IBR_DFIG1_TRIAL.pscx"
GF46 = PSCAD / "3IBR_DFIG1_TRIAL.gf46"
P3_DTA = GF46 / "P3.dta"
P3_F = GF46 / "P3.f"
INF = GF46 / "3IBR_DFIG1_TRIAL.inf"

EXPECTED_MAIN_SHA = "CBA120BB167CB7FA6C4A1AE4471268850AB61761EC1877EB7B87015627FE9DAB"
STAGE10D_TRIAL_SHA = "C7C9E2D1B4DED92B8609116448D10201C88A18E12B3B86C41DAB36ADE8EC0E17"

PAPER_CHANNELS = {
    "PAPER_OVL1_S_A_PU", "PAPER_OVL1_S_B_PU", "PAPER_OVL1_S_MAX_PU",
    "PAPER_OVL1_EFFECTIVE_CAPACITY_PU", "PAPER_OVL1_LOADING_INDEX_EQ",
    "PAPER_OVL1_ABOVE_THRESHOLD", "PAPER_OVL1_TIMER_OR_CURVE_STATE",
    "PAPER_OVL1_TRIP_REQUEST", "PAPER_OVL1_BRK_CMD", "PAPER_OVL1_BRK_STATE",
    "PAPER_OVL1_TRIP_EVENT_VALID", "PAPER_OVL1_FIRST_TRIP_TIME_S",
    "PAPER_OVL1_RELAY_ENABLE",
}

DFIG_CHANNELS = {
    "CASCADE3_ELEC_DFIG_V", "PIBR1_2", "QIBR1_2",
    "DFIG_LVRT_TRIP_CAUSE_DURATION_LATCH", "DFIG_LVRT_FINAL_BRK_CMD",
    "DFIG_LVRT_TRIP_CONFIRMED", "DFIG_BRK_STATE",
    "DFIG_LVRT_CASCADE_EVENT_VALID", "DFIG_LVRT_CASCADE_EVENT_CAUSE_CODE",
    "DFIG_LVRT_CASCADE_EVENT_BRK_OPEN", "DFIG_LVRT_CASCADE_SOURCE_AVAILABLE",
    "DFIG_LVRT_CASCADE_FIRST_EVENT_TIME_S",
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest().upper()


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def settings(root: ET.Element) -> dict[str, str]:
    return {
        param.get("name", ""): param.get("value", "")
        for param in root.findall("./paramlist/param")
    }


def params(user: ET.Element) -> dict[str, str]:
    return {
        param.get("name", ""): param.get("value", "")
        for param in user.findall("./paramlist/param")
    }


def tline_terminals(text: str, name: str) -> list[dict[str, Any]]:
    lines = text.splitlines()
    marker = next(i for i, line in enumerate(lines) if line.strip().startswith(f"! {name}"))
    result = []
    for side, line in zip(("A", "B"), lines[marker + 2 : marker + 4]):
        values = [int(value) for value in line.split()[:4]]
        result.append({"side": side, "compiled_bus": values[0], "phase_nodes": values[1:]})
    return result


def main() -> None:
    root = ET.parse(TRIAL).getroot()
    cfg = settings(root)
    p3 = P3_F.read_text(errors="ignore")
    dta = P3_DTA.read_text(errors="ignore")
    inf = INF.read_text(errors="ignore")
    current_trial_sha = sha256(TRIAL)
    current_dta_sha = sha256(P3_DTA)

    faults = [user for user in root.iter("User") if "tfault" in user.get("defn", "").lower()]
    fault = params(faults[0]) if len(faults) == 1 else {}
    fault_start = float(fault.get("TF", "nan"))
    fault_duration = float(fault.get("DF", "nan"))
    fault_clear = fault_start + fault_duration

    e2629 = tline_terminals(dta, "E_26_29_1")
    e2829 = tline_terminals(dta, "E_28_29_1")
    pgb_names = {
        p.get("value", "")
        for user in root.findall(".//User[@defn='master:pgb']")
        for p in user.findall("./paramlist/param[@name='Name']")
    }
    pgb_count = len(root.findall(".//User[@defn='master:pgb']"))
    inf_names = set(re.findall(r'Desc="([^"]+)"', inf))
    tline_runtime_groups = {
        match.group(1)
        for title in inf_names
        if (match := re.match(r"^(E_\d+_\d+_1)_[AB]_[PQI]$", title))
    }

    breaker = next(
        (user for user in root.findall(".//User[@defn='master:breaker3']")
         if params(user).get("NAME") == "PAPER_OVL1_BRK_CMD"),
        None,
    )
    dfig_breaker = next(
        (user for user in root.findall(".//User[@defn='master:breaker3']")
         if params(user).get("NAME") == "BRK_DFIG"),
        None,
    )
    relay = root.find("./definitions/Definition[@name='PAPER_OVL1_RELAY']")
    relay_text = ET.tostring(relay, encoding="unicode") if relay is not None else ""

    gates = {
        "main_sha_unchanged": sha256(MAIN) == EXPECTED_MAIN_SHA,
        "current_trial_matches_stage10d_semantic_freeze": current_trial_sha == STAGE10D_TRIAL_SHA,
        "solution_time_step_exactly_50us": float(cfg.get("time_step", -1)) == 50.0,
        "plot_step_exactly_0p01s": float(cfg.get("sample_step", -1)) == 10000.0,
        "current_duration_is_stage10d_3s_and_gui_change_to_20s_is_authorized": float(cfg.get("time_duration", -1)) == 3.0,
        "single_N29_three_phase_fault_component": len(faults) == 1,
        "fault_start_exactly_0p50s": fault_start == 0.5,
        "fault_clear_exactly_2p50s": fault_clear == 2.5,
        "compiled_fault_timing_matches_xml": "IF ( TIME .GE. 0.5 ) IT_1 = 1" in p3 and "IF ( TIME .GE. (0.5+2.0) ) IT_1 = 0" in p3,
        "E_26_29_1_B_terminal_compiled_bus_1": e2629[1]["compiled_bus"] == 1,
        "E_28_29_1_B_terminal_compiled_bus_1": e2829[1]["compiled_bus"] == 1,
        "E_26_29_1_three_phases_join_N29": all(f"NT_80({phase})   N29({phase})" in dta for phase in (1, 2, 3)),
        "PAPER_breaker_present_and_frozen": breaker is not None and params(breaker).get("RON", "").startswith("1.0e-3"),
        "PAPER_breaker_is_series_not_bypassed": all(f"N29({phase}) NT_83({phase})" in dta for phase in (1, 2, 3)) and not any(f"N29({phase}) NT_82({phase})" in dta for phase in (1, 2, 3)),
        "BRK_DFIG_present_and_frozen": dfig_breaker is not None and params(dfig_breaker).get("RON", "").startswith("1.0e-3"),
        "existing_LVRT_chain_present": all(token in p3 for token in ("DFIG_LVRT_TRIP_CAUSE_DURATION_LATCH", "DFIG_LVRT_FINAL_BRK_CMD", "DFIG_LVRT_TRIP_CONFIRMED")),
        "PAPER_capacity_frozen": "7.872883990" in relay_text,
        "PAPER_threshold_frozen": 'name="X" value="1.1"' in relay_text,
        "PAPER_delay_frozen_5s": 'name="TS" value="5.0 [s]"' in relay_text,
        "all_DFIG_key_output_channels_registered": DFIG_CHANNELS <= pgb_names and DFIG_CHANNELS <= inf_names,
        "all_13_PAPER_output_channels_registered": PAPER_CHANNELS <= pgb_names and PAPER_CHANNELS <= inf_names,
        "all_31_TLine_dual_end_PQI_groups_registered": len(tline_runtime_groups) == 31,
        "output_channel_inventory_preserved_448_plus_13": pgb_count == 461,
        "no_unapproved_semantic_model_change": current_trial_sha == STAGE10D_TRIAL_SHA,
    }
    passed = all(gates.values())
    status = "pass" if passed else "blocked"
    generated = datetime.now().astimezone().isoformat(timespec="seconds")

    manifest = {
        "manifest_name": "stage11_20s_50us_configuration_manifest",
        "generated_at_local": generated,
        "stage10d_reference_trial_sha256": STAGE10D_TRIAL_SHA,
        "current_trial_sha256": current_trial_sha,
        "current_P3_dta_sha256": current_dta_sha,
        "solution_time_step_s": 0.00005,
        "solution_time_step_us": 50,
        "plot_step_s": 0.01,
        "run_duration_current_s": float(cfg.get("time_duration", -1)),
        "run_duration_target_s": 20.0,
        "configuration_change_origin": "user_preexisting_before_stage11",
        "numerical_mode": "fast_step_50us",
        "reference_numerical_mode": "stage10d_5us",
        "reference_numerical_mode_evidence_note": "The task declares Stage 10D as 5 us, but the retained Stage-10D trial SHA itself stores time_step=50 us. Therefore 5 us equivalence is a historical claim boundary, not proven by that artifact.",
        "fault_start_s": fault_start,
        "fault_clear_s": fault_clear,
        "pre_fault_window_s": [0.0, fault_start - 0.01],
        "xml_output_channel_count": pgb_count,
        "output_channel_count_interpretation": "448 pre-PAPER channels plus 13 PAPER_OVL1 channels = 461 current channels",
        "claim_boundary": "50us results are a separate numerical configuration; event-order consistency must be checked before claiming paper-like dynamic behavior.",
    }
    audit = {
        "audit_name": "stage11_20s_50us_pre_run_gate",
        "generated_at_local": generated,
        "execution_status": f"stage11_20s_50us_pre_run_gate_{status}",
        "run_authorization": "ONE_20S_RUN_AFTER_ZERO_ERROR_BUILD" if passed else "RUN_BLOCKED",
        "main_sha256": sha256(MAIN),
        "trial_sha256": current_trial_sha,
        "P3_dta_sha256": current_dta_sha,
        "actual_fault_start_s": fault_start,
        "actual_fault_clear_s": fault_clear,
        "pre_fault_window_s": [0.0, fault_start - 0.01],
        "E_26_29_1_terminals": e2629,
        "E_28_29_1_terminals": e2829,
        "PAPER_breaker_series_boundary": "N29 <-> NT_83 through RS breaker stamps; E_28_29_1 terminal passes NT_82 <-> NT_83 through meter stamps",
        "gates": gates,
        "failed_gates": [name for name, value in gates.items() if not value],
    }
    freeze = {
        "freeze_name": "stage11_20s_50us_run_freeze",
        "gate_status": status,
        "authorized_gui_changes": {"time_duration": {"from_s": 3.0, "to_s": 20.0}},
        "must_remain": {"time_step_us": 50, "plot_step_s": 0.01, "fault_start_s": 0.5, "fault_clear_s": 2.5, "E_26_29_1_B_bus": 1, "E_28_29_1_B_bus": 1},
        "run_count_authorized": 1 if passed else 0,
        "build_requirement": "Build Errors = 0 before the one Run",
        "trial_sha_before_authorized_duration_change": current_trial_sha,
        "P3_dta_sha_before_build": current_dta_sha,
    }
    write_json(REPO / "data/reference/stage11_20s_50us_configuration_manifest.json", manifest)
    write_json(REPO / "data/validation/stage11_20s_50us_pre_run_gate.json", audit)
    if passed:
        write_json(REPO / "data/reference/stage11_20s_50us_run_freeze.json", freeze)
        (REPO / "docs/STAGE11_20S_50US_SINGLE_GUI_BUILD_AND_RUN_SHEET.md").write_text(
            "# Stage 11 single GUI, Build, and Run sheet\n\n"
            "1. Open `3IBR_DFIG1_TRIAL.pscx`.\n"
            "2. Confirm Solution Time Step = `50 µs`, Run Duration = `20.0 s`, Plot Step = `0.01 s`.\n"
            "3. Change nothing else; save the trial.\n"
            "4. Build once. Continue only if Build Errors = `0`.\n"
            "5. Without changing anything, Run once to `20.0 s`.\n"
            "6. Do not open Graph, rebuild, rerun, take screenshots, or change parameters.\n\n"
            "Reply only: `阶段十一唯一一次 20 s / 50 µs Run 完成`\n",
            encoding="utf-8",
        )
    print(f"stage11_20s_50us_pre_run_gate = {status}")


if __name__ == "__main__":
    main()
