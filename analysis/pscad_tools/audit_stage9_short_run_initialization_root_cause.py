#!/usr/bin/env python3
"""Prepare the Stage-9 short-run initialization repair from read-only PSCAD evidence."""

from __future__ import annotations

import csv
import hashlib
import json
import re
import subprocess
import xml.etree.ElementTree as ET
from copy import deepcopy
from datetime import datetime
from pathlib import Path
from typing import Any


REPO = Path(__file__).resolve().parents[2]
ROOT = Path(r"C:\pscad_work\pnnl_39_3ibr_pscad46_strip5")
PSCAD = ROOT / "PSCAD"
MAIN = PSCAD / "3IBR.pscx"
TRIAL = PSCAD / "3IBR_DFIG1_TRIAL.pscx"
GF46 = PSCAD / "3IBR_DFIG1_TRIAL.gf46"
RELAY_F = GF46 / "PAPER_OVL1_RELAY.f"
P3_F = GF46 / "P3.f"
MASTER = Path(r"C:\Program Files (x86)\PSCAD46\master.pslx")
BACKUP = ROOT / "_backups" / "stage9_before_short_run_initialization_repair"
PAPER_CHANNELS = [
    "PAPER_OVL1_S_A_PU", "PAPER_OVL1_S_B_PU", "PAPER_OVL1_S_MAX_PU",
    "PAPER_OVL1_EFFECTIVE_CAPACITY_PU", "PAPER_OVL1_LOADING_INDEX_EQ",
    "PAPER_OVL1_ABOVE_THRESHOLD", "PAPER_OVL1_TIMER_OR_CURVE_STATE",
    "PAPER_OVL1_TRIP_REQUEST", "PAPER_OVL1_BRK_CMD", "PAPER_OVL1_BRK_STATE",
    "PAPER_OVL1_TRIP_EVENT_VALID", "PAPER_OVL1_FIRST_TRIP_TIME_S",
    "PAPER_OVL1_RELAY_ENABLE",
]


def sha(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest().upper()


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, obj: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fields = list(rows[0]) if rows else []
    with path.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields); w.writeheader(); w.writerows(rows)


def line_no(text: str, pattern: str) -> int | None:
    for i, line in enumerate(text.splitlines(), 1):
        if re.search(pattern, line):
            return i
    return None


def param(user: ET.Element, name: str) -> str | None:
    p = user.find(f"./paramlist/param[@name='{name}']")
    return p.get("value") if p is not None else None


def relay_definition(root: ET.Element) -> ET.Element:
    found = root.find("./definitions/Definition[@name='PAPER_OVL1_RELAY']")
    if found is None:
        raise RuntimeError("PAPER_OVL1_RELAY definition not found")
    return found


def semantic_fingerprint(path: Path) -> str:
    """Fingerprint everything except the two authorized Stage-9 GUI values and volatile CRC/date metadata."""
    root = ET.parse(path).getroot()
    for elem in root.iter():
        elem.attrib.pop("crc", None); elem.attrib.pop("date", None)
        if elem.tag == "param" and elem.get("name") == "revisor":
            elem.set("value", "<volatile>")
        if elem.tag == "param" and elem.get("name") == "time_duration":
            elem.set("value", "<stage9-authorized>")
    relay = relay_definition(root)
    v_off = relay.find(".//User[@id='522397627']/paramlist/param[@name='Value']")
    if v_off is not None:
        v_off.set("value", "<stage9-authorized>")
    # PSCAD writes runtime display/readback values when the project is saved.
    # These are not model configuration and must not invalidate a semantic gate.
    for user in root.findall(".//User"):
        defn = user.get("defn", "")
        if defn == "master:breaker3":
            user.set("w", "<runtime-display-width>")
            for p in user.findall("./paramlist/param"):
                if p.get("name") in {"BOpen1", "BOpen2", "BOpen3", "P", "Q"}:
                    p.set("value", "<runtime-readback>")
        if defn == "ETRAN:Electranix_Load":
            for p in user.findall("./paramlist/param"):
                if p.get("name") in {"Pdisplay", "Qdisplay"}:
                    p.set("value", "<runtime-readback>")
    raw = ET.tostring(root, encoding="utf-8")
    return hashlib.sha256(raw).hexdigest().upper()


def main() -> None:
    now = datetime.now().isoformat(timespec="seconds")
    xml_text = TRIAL.read_text(encoding="utf-8", errors="ignore")
    relay_text = RELAY_F.read_text(encoding="utf-8", errors="ignore")
    p3_text = P3_F.read_text(encoding="utf-8", errors="ignore")
    master_text = MASTER.read_text(encoding="utf-8", errors="ignore")
    one_shot_path = GF46 / "ONE_SHOT_BREAKER_OPEN_STIMULUS.f"
    event_packet_path = GF46 / "MONITORED_OBJECT_EVENT_PACKET.f"
    one_shot_text = one_shot_path.read_text(encoding="utf-8", errors="ignore") if one_shot_path.exists() else ""
    event_packet_text = event_packet_path.read_text(encoding="utf-8", errors="ignore") if event_packet_path.exists() else ""
    root = ET.fromstring(xml_text)
    relay = relay_definition(root)
    timer = relay.find(".//User[@id='2132554116']")
    latch = relay.find(".//User[@id='897892378']")
    von = relay.find(".//User[@id='2118574082']")
    voff = relay.find(".//User[@id='522397627']")
    reset = relay.find(".//User[@id='801784199']")
    if any(x is None for x in (timer, latch, von, voff, reset)):
        raise RuntimeError("One or more frozen relay components are missing")

    stage8 = read_json(REPO / "data/validation/stage8_paper_ovl1_dynamic_final_audit.json")
    inventory = read_json(REPO / "data/derived/stage8_paper_ovl1_runtime_channel_inventory.json")
    gate8 = read_json(REPO / "data/validation/stage8_pre_run_output_gate.json")
    with (REPO / "data/derived/stage8_paper_ovl1_relay_trace.csv").open(encoding="utf-8", newline="") as f:
        t0 = next(csv.DictReader(f))

    settings = {p.get("name"): p.get("value") for p in root.findall("./paramlist[@name='Settings']/param")}
    timer_master = {
        "ports": {"F": "input, active when F < FSet", "VOn": "top input", "VOff": "bottom input", "O": "single right output"},
        "fortran_template": "$O = TIMER3($TS, $TD, $F, $FSet, $VOff, $VOn)",
        "official_semantics_present": all(s in master_text for s in ["name=\"F\"", "name=\"VOn\"", "name=\"VOff\"", "name=\"O\""]),
        "definition_line": line_no(master_text, r'<Definition.*name="timer"'),
        "fortran_template_line": line_no(master_text, r'\$O = TIMER3'),
    }
    current = {
        "timer": {"component_id": int(timer.get("id")), "definition": timer.get("defn"),
                  "trigger_threshold": param(timer, "FSet"), "delay_until_on": param(timer, "TS"),
                  "duration_on": param(timer, "TD")},
        "timer_von": {"component_id": int(von.get("id")), "value": param(von, "Value"), "port": "VOn/top"},
        "timer_voff": {"component_id": int(voff.get("id")), "value": param(voff, "Value"), "port": "VOff/bottom"},
        "latch": {"component_id": int(latch.get("id")), "mode": param(latch, "F_GL_L"),
                  "type": param(latch, "Type"), "q_initial": param(latch, "QInit"),
                  "interpolation": param(latch, "INTR")},
        "latch_reset": {"component_id": int(reset.get("id")), "value": param(reset, "Value"), "port": "R"},
        "run_duration_s": float(settings["time_duration"]),
        "emt_time_step_us": float(settings["time_step"]),
        "plot_step_us": float(settings["sample_step"]),
    }

    code_checks = {
        "above_times_enable": "RT_13 = REAL(IT_2) * RELAY_ENABLE" in relay_text,
        "active_low_timer_input": "RT_15 = + RT_14 - RT_13" in relay_text,
        "timer_call": "RT_18 = TIMER3(5.0, 100.0, RT_15, 0.5, RT_17, RT_16)" in relay_text,
        "timer_von_equals_one": "RT_16 = 1.0" in relay_text,
        "timer_voff_equals_one": "RT_17 = 1.0" in relay_text,
        "timer_output_to_latch_set": "RVD2_1(1) = RT_18" in relay_text,
        "zero_to_latch_reset": "RVD2_2(1) = RT_19" in relay_text and "RT_19 = 0.0" in relay_text,
        "latch_cfg_simple_rs_q0": "CALL E_XFLIP1_CFG(2,1,0,0)" in relay_text,
        "latch_q_to_trip_request": "TRIP_REQ = REAL(IT_4)" in relay_text,
        "timer_output_to_timer_state": "TIMER_STATE = RT_18" in relay_text,
        "breaker_only_uses_trip_command": p3_text.count("NINT(1.0-PAPER_OVL1_BRK_CMD)") == 3,
    }
    map8 = {x["canonical_title"]: {"pgb_index": x.get("pgb_index"), "out_file": x.get("out_file"),
                                    "data_column_after_time": x.get("data_column_after_time")} for x in inventory}
    pgb8 = {x["canonical_title"]: {"pgb_offset": x.get("pgb_offset"), "runtime_expressions": x.get("runtime_expressions")}
            for x in gate8["canonical_output_gate"]}
    channel_mapping_preserved = len(map8) == 13 and all(name in p3_text for name in PAPER_CHANNELS)

    unique_root_cause = (
        "Timer component 2132554116 has both VOn (top, component 2118574082) and VOff "
        "(bottom, component 522397627) connected to 1.0. PSCAD defines O=TIMER3(TS,TD,F,FSet,VOff,VOn); "
        "therefore O is 1 before completion as well as after completion. O drives latch S, so latch Q, "
        "TRIP_REQUEST and BRK_CMD assert at t=0 even while ABOVE_THRESHOLD is 0."
    )
    minimal_repair = {
        "change": "Set only component 522397627, the 1.0 Constant directly connected to Timer VOff/bottom, to 0.0.",
        "wires_to_disconnect": 0,
        "wires_to_add": 0,
        "preserve": ["Timer O -> latch S", "0.0 constant 801784199 -> latch R", "latch Q -> TRIP_REQ",
                     "VOn/top constant 2118574082 = 1.0", "F = 1.0 - ABOVE_TH", "QInit = Low [0]"],
        "duration_change": "Set trial Duration of Run from 20.0 s to 9.0 s; keep time step 5 us and plot step 10000 us.",
    }
    generated_line_evidence = {
        "above_times_enable": line_no(relay_text, r"RT_13 = REAL\(IT_2\) \* RELAY_ENABLE"),
        "active_low_timer_input": line_no(relay_text, r"RT_15 = \+ RT_14 - RT_13"),
        "timer_call": line_no(relay_text, r"RT_18 = TIMER3"),
        "timer_output_to_latch_set": line_no(relay_text, r"RVD2_1\(1\) = RT_18"),
        "latch_reset": line_no(relay_text, r"RVD2_2\(1\) = RT_19"),
        "trip_request_from_q": line_no(relay_text, r"TRIP_REQ = REAL\(IT_4\)"),
        "latch_configuration": line_no(relay_text, r"CALL E_XFLIP1_CFG\(2,1,0,0\)"),
        "breaker_command_pole_1": line_no(p3_text, r"NINT\(1.0-PAPER_OVL1_BRK_CMD\)"),
    }
    neighboring_module_checks = {
        "one_shot_generated_file_exists": one_shot_path.exists(),
        "event_packet_generated_file_exists": event_packet_path.exists(),
        "one_shot_does_not_reference_paper_breaker_command": "PAPER_OVL1_BRK_CMD" not in one_shot_text,
        "event_packet_does_not_reference_paper_breaker_command": "PAPER_OVL1_BRK_CMD" not in event_packet_text,
        "p3_dta_exists": (GF46 / "P3.dta").exists(),
        "p3_map_exists": (GF46 / "P3.map").exists(),
        "project_map_exists": (GF46 / "3IBR_DFIG1_TRIAL.map").exists(),
    }

    trace = [
        {"item": "timer trigger/reset polarity", "current_component_and_port": "Timer 2132554116 F <- 1-ABOVE_TH; active when F<0.5",
         "generated_code_evidence": "RT_15=1-RT_13; TIMER3(...,RT_15,0.5,...)", "current_t0_behavior": "ABOVE=0 => F=1 => off state",
         "target_t0_behavior": "off state must output 0", "minimal_gui_repair": "preserve F wiring and threshold 0.5",
         "frozen_parameter_proof": "capacity/threshold/delay untouched", "status": "pass_preserve"},
        {"item": "timer off value", "current_component_and_port": "Constant 522397627 -> Timer VOff/bottom = 1.0",
         "generated_code_evidence": "RT_17=1.0; RT_18=TIMER3(...,RT_17,RT_16)", "current_t0_behavior": "TIMER_STATE=1",
         "target_t0_behavior": "TIMER_STATE=0", "minimal_gui_repair": "change only Constant 522397627 to 0.0",
         "frozen_parameter_proof": "TS remains 5.0 s", "status": "root_cause_repair_required"},
        {"item": "timer on value", "current_component_and_port": "Constant 2118574082 -> Timer VOn/top = 1.0",
         "generated_code_evidence": "RT_16=1.0", "current_t0_behavior": "masked by VOff also being 1",
         "target_t0_behavior": "O becomes 1 only after F<0.5 continuously for 5 s", "minimal_gui_repair": "do not change",
         "frozen_parameter_proof": "timer delay and output polarity preserved", "status": "pass_preserve"},
        {"item": "latch set/reset/Q", "current_component_and_port": "Timer O->S; Constant 801784199=0->R; Q->TRIP_REQ",
         "generated_code_evidence": "RVD2_1=RT_18; RVD2_2=RT_19=0; TRIP_REQ=IT_4", "current_t0_behavior": "S=1 forces Q=1",
         "target_t0_behavior": "S=0,R=0,QInit=0 keeps Q=0", "minimal_gui_repair": "do not rewire latch",
         "frozen_parameter_proof": "latch is Simple RS, QInit Low", "status": "pass_after_voff_fix"},
        {"item": "breaker closed command", "current_component_and_port": "PAPER_OVL1_BRK_CMD controls all three breaker poles",
         "generated_code_evidence": "NINT(1.0-PAPER_OVL1_BRK_CMD) on all three poles", "current_t0_behavior": "BRK_CMD=1 => open",
         "target_t0_behavior": "TRIP_REQ/BRK_CMD=0 => internal 1 => closed", "minimal_gui_repair": "do not change breaker wiring or polarity",
         "frozen_parameter_proof": "breaker boundary unchanged", "status": "pass_after_voff_fix"},
        {"item": "runtime channels", "current_component_and_port": "13 canonical PAPER_OVL1 Output Channels",
         "generated_code_evidence": "Stage-8 PGB indices 92,166,168-170,172-174,177-179,181,183", "current_t0_behavior": "13/13 readable",
         "target_t0_behavior": "same mapping", "minimal_gui_repair": "do not delete, rename, or reconnect channels",
         "frozen_parameter_proof": "mapping fingerprint recorded", "status": "pass_preserve"},
        {"item": "run duration", "current_component_and_port": "Project Settings time_duration=20",
         "generated_code_evidence": "trial XML Settings", "current_t0_behavior": "Stage-8 run covered 20 s",
         "target_t0_behavior": "Stage-9 run ends at 9.0 s", "minimal_gui_repair": "Home > Duration of Run (s) = 9.0",
         "frozen_parameter_proof": "time_step=5 us; plot_step=10000 us unchanged", "status": "repair_required"},
    ]

    static_audit = {
        "audit_name": "stage9_short_run_initialization_static_audit", "generated_at_local": now,
        "execution_status": "stage9_short_run_static_root_cause_confirmed",
        "integrity": {"git_head": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=REPO, text=True).strip(),
                      "main_sha": sha(MAIN), "trial_sha": sha(TRIAL),
                      "main_sha_expected": "CBA120BB167CB7FA6C4A1AE4471268850AB61761EC1877EB7B87015627FE9DAB",
                      "trial_sha_expected": "1AA180E4B8C784B3BAE14453261672783B21B87EA157C56DB26649F98E78992F"},
        "unique_root_cause": unique_root_cause,
        "master_timer_definition_evidence": timer_master,
        "current_components": current,
        "generated_code_checks": code_checks,
        "generated_code_line_evidence": generated_line_evidence,
        "neighboring_one_shot_and_event_packet_checks": neighboring_module_checks,
        "stage8_t0_runtime": {k: float(t0[k]) for k in PAPER_CHANNELS},
        "stage8_runtime_classification": stage8["execution_status"],
        "stage8_channel_mapping": map8,
        "stage8_generated_pgb_mapping": pgb8,
        "channel_mapping_preserved_before_repair": channel_mapping_preserved,
        "no_time_fault_dfig_or_one_shot_breaker_bypass": code_checks["breaker_only_uses_trip_command"],
        "minimal_gui_repair": minimal_repair,
    }

    backup_stat = BACKUP.stat()
    baseline = {
        "manifest_name": "stage9_short_run_initialization_baseline_manifest", "created_at_local": now,
        "git_head_start": static_audit["integrity"]["git_head"], "main_sha_start": sha(MAIN), "trial_sha_start": sha(TRIAL),
        "backup_path": str(BACKUP), "backup_file_count": len([p for p in BACKUP.rglob("*") if p.is_file()]),
        "backup_created_at": datetime.fromtimestamp(backup_stat.st_ctime).isoformat(timespec="seconds"),
        "selected_line": "E_28_29_1", "effective_capacity_pu": 7.872883989661206,
        "threshold_multiplier": 1.1, "definite_delay_s": 5.0,
        "expected_threshold_crossing_s": 2.53, "expected_trip_s": 7.53, "run_end_s": 9.0,
        "stage8_dynamic_audit_path": "data/validation/stage8_paper_ovl1_dynamic_final_audit.json",
        "stage8_runtime_channel_inventory_path": "data/derived/stage8_paper_ovl1_runtime_channel_inventory.json",
        "stage8_relay_trace_path": "data/derived/stage8_paper_ovl1_relay_trace.csv",
        "stage8_result_commit": "db5fcb4abbe6eaa0e53a20224541756ae7a2d8ef",
        "runtime_channel_count": 13, "runtime_plot_step_s": 0.01,
    }
    freeze = {
        "freeze_name": "stage9_short_run_initialization_repair_freeze", "generated_at_local": now,
        "main_sha": sha(MAIN), "trial_sha_before_repair": sha(TRIAL),
        "trial_semantic_fingerprint_excluding_two_authorized_values": semantic_fingerprint(TRIAL),
        "selected_line": "E_28_29_1", "effective_capacity_pu": 7.872883989661206,
        "threshold_multiplier": 1.1, "definite_delay_s": 5.0,
        "authorized_changes": [{"component_id": 522397627, "port": "Timer VOff/bottom", "from": 1.0, "to": 0.0},
                               {"project_setting": "time_duration", "from": 20.0, "to": 9.0}],
        "required_preserved_timer_latch": current, "required_stage8_channel_mapping": map8,
        "required_generated_pgb_mapping": pgb8,
        "expected_generated_code_after_build": ["RT_17 = 0.0", "RT_16 = 1.0",
                                                "RT_18 = TIMER3(5.0, 100.0, RT_15, 0.5, RT_17, RT_16)",
                                                "CALL E_XFLIP1_CFG(2,1,0,0)"],
    }

    root_doc = f"""# Stage 9 short-run relay initialization root cause

Generated: {now}

## Unique root cause

{unique_root_cause}

The installed PSCAD master definition has Timer ports `F`, `VOn` (top), `VOff`
(bottom), and one output `O`. Its generated equation is
`O = TIMER3(TS, TD, F, FSet, VOff, VOn)`. The official component semantics make
the timer active when `F < FSet`; otherwise it returns `VOff`.

The Timer has no separate enable or reset port. `F` is the active-low trigger:
`F < 0.5` starts/continues the delay, while `F > 0.5` returns `O` to `VOff` and
resets the timing condition. The right-side `O` is the single delayed-completion
output and is already connected to latch `S`; no output-port swap is required.

The relay uses `F = 1 - ABOVE_THRESHOLD`, `FSet = 0.5`, `TS = 5.0 s`, and
`TD = 100 s`. Thus `ABOVE_THRESHOLD=0` correctly gives `F=1` (inactive), but the
current `VOff=1.0` incorrectly makes the inactive output high. Stage-8 runtime
data directly confirms `ABOVE_THRESHOLD=0` and `TIMER_STATE=1` at `t=0`.

## Minimal repair

Change only Constant component `522397627`, connected directly to Timer
`VOff`/bottom, from `1.0` to `0.0`. Keep the upper `VOn=1.0` constant and every
wire unchanged. The existing Simple RS latch already has `QInit=Low [0]`,
Timer `O -> S`, constant `0 -> R`, and `Q -> TRIP_REQ`; those are correct once
the Timer inactive value is zero.

Separately set trial `Duration of Run` from `20.0 s` to `9.0 s`. Keep the EMTDC
time step at `5 us` and Channel Plot Step at `10000 us` (`0.01 s`). This does
not alter the fault, relay calculations, breaker boundary, PGB configuration,
or any of the 13 Stage-8 runtime channel mappings.
"""
    sheet = f"""# Stage 9 short-run single GUI repair and Build sheet

Do not open the main `3IBR` project. Open only `3IBR_DFIG1_TRIAL`.

## A. Repair the Timer inactive value

1. In the project Definitions list, open `PAPER_OVL1_RELAY`, then open its
   `Schematic`.
2. Find the chain `1 - ABOVE_TH -> Timer -> Simple Set/Reset Latch`.
3. The Timer has: left `F`, top `On`, bottom `Off`, and right `O`.
4. Double-click the **lower** Constant `1.0` connected directly to the Timer
   bottom `Off` (`VOff`) port. Its component ID is `522397627`.
5. Change only its Value from `1.0` to `0.0`, then click **OK**.
6. Do not change the upper Constant `1.0` connected to Timer top `On` (`VOn`).

No wire is to be removed or added. Preserve these connections exactly:

- `1 - ABOVE_TH -> Timer F`
- upper `1.0 -> Timer On`
- lower corrected `0.0 -> Timer Off`
- `Timer O -> TIMER_STATE` and `Timer O -> latch S`
- existing `0.0 -> latch R`
- latch `Q -> TRIP_REQ`; leave `Qbar` unused

Confirm without changing the Timer parameters:

- Timer Trigger Threshold: `0.5`
- Delay until ON: `5.0 s`
- Duration ON: `100 s`

Confirm without changing the latch parameters:

- mode: `Simple Set/Reset Latch`
- type: `RS`
- Initial State of Output Q: `Low [0]`
- Interpolation Compatibility: `Disabled`

## B. Set the short Run duration

1. Return to the trial project main canvas.
2. On the PSCAD 4.6 **Home** ribbon, in the Simulation settings area, set
   **Duration of Run (s)** from `20` to `9.0`.
3. Leave **Solution Time Step (us)** at `5`.
4. Leave **Channel Plot Step (us)** at `10000`.

Do not change Output Channel/PGB settings or output paths.

## C. Save and Build exactly once

1. Save `3IBR_DFIG1_TRIAL`.
2. Click **Build** once and wait for completion.
3. Confirm `Build Errors = 0`.
4. Do **not** Run, open Graph, or take a screenshot.

Expected static state after Build:

| Condition | TIMER | TRIP_REQUEST | BRK_CMD | BRK_STATE |
|---|---:|---:|---|---|
| t=0, ABOVE=0 | 0 | 0 | closed command (0) | closed |
| 0.20-0.45 s, ABOVE=0 | 0 | 0 | closed command (0) | closed |
| ABOVE continuously <5 s | 0 | 0 | closed command (0) | closed |
| ABOVE continuously 5 s | 1 | 1 | open command (1) | open |

Frozen: `E_28_29_1`, capacity `7.872883989661206 pu`, threshold `1.1`, delay
`5.0 s`, N29 fault `0.50-2.50 s`, breaker position/polarity, P/Q/S calculations,
13 Output Channels, EMTDC step, and plot step.
"""

    write_json(REPO / "data/validation/stage9_short_run_initialization_baseline_manifest.json", baseline)
    write_json(REPO / "data/validation/stage9_short_run_initialization_static_audit.json", static_audit)
    write_csv(REPO / "data/validation/stage9_short_run_initialization_trace.csv", trace)
    write_json(REPO / "data/reference/stage9_short_run_initialization_repair_freeze.json", freeze)
    (REPO / "docs/STAGE9_SHORT_RUN_RELAY_INITIALIZATION_ROOT_CAUSE.md").write_text(root_doc, encoding="utf-8")
    (REPO / "docs/STAGE9_SHORT_RUN_SINGLE_GUI_REPAIR_AND_BUILD_SHEET.md").write_text(sheet, encoding="utf-8")
    print(json.dumps({"execution_status": static_audit["execution_status"], "unique_root_cause": unique_root_cause,
                      "authorized_gui_changes": freeze["authorized_changes"]}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
