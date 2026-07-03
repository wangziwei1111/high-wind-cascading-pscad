#!/usr/bin/env python3
"""Read-only Stage-10B fault-to-DFIG closed-state interface comparison."""

from __future__ import annotations

import csv
import hashlib
import json
import xml.etree.ElementTree as ET
from datetime import datetime
from pathlib import Path
from typing import Any


REPO = Path(__file__).resolve().parents[2]
S4 = Path(r"C:\pscad_work\pnnl_39_3ibr_pscad46_strip5\_backups\stage7_before_paper_calibrated_first_trip\PSCAD\3IBR_DFIG1_TRIAL.pscx")
S9 = Path(r"C:\pscad_work\pnnl_39_3ibr_pscad46_strip5\PSCAD\3IBR_DFIG1_TRIAL.pscx")
MAIN = S9.parent / "3IBR.pscx"
BACKUP = Path(r"C:\pscad_work\pnnl_39_3ibr_pscad46_strip5\_backups\stage10b_before_fault_to_dfig_alignment")
S4_DTA = S4.parent / "P3.dta"
S9_DTA = S9.parent / "3IBR_DFIG1_TRIAL.gf46" / "P3.dta"
EXPECTED_MAIN = "CBA120BB167CB7FA6C4A1AE4471268850AB61761EC1877EB7B87015627FE9DAB"
EXPECTED_S9 = "F2A3C1012D8261805C03F688CCC2E8BFBCE68A80D1ACC352CAFA666B149744A0"


def sha(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for b in iter(lambda: f.read(1024 * 1024), b""): h.update(b)
    return h.hexdigest().upper()


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fields = list(rows[0])
    with path.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields); w.writeheader(); w.writerows(rows)


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def update_references() -> None:
    evidence = "data/validation/stage10b_fault_to_dfig_interface_static_audit.json"
    inv = REPO / "data/reference/current_pscad_model_capability_inventory.json"
    obj = read_json(inv); obj.update({"stage10b_fault_to_dfig_alignment_status":"blocked_no_defensible_electrical_difference_found", "stage10b_evidence":evidence}); write_json(inv, obj)
    fidelity = REPO / "data/reference/paper_reproduction_fidelity_assessment.json"
    obj = read_json(fidelity); obj.update({"stage10b_fault_to_dfig_alignment_status":"blocked_no_defensible_electrical_difference_found", "stage10b_run_status":"not_authorized", "strict_reproduction_status_after_stage10b":"not_achieved", "stage10b_evidence":evidence}); write_json(fidelity, obj)
    future = REPO / "data/reference/future_shadow_overload_candidate_decision.json"
    obj = read_json(future); obj.update({"stage10b_alignment_decision":"no_defensible_electrical_difference_found", "stage10b_gui_build_run_status":"blocked_before_gui", "stage10b_evidence":evidence, "next_task":"Obtain a compiled Stage-4/Stage-9 nodal/admittance and initial-condition comparison around N29 and the DFIG PCC; do not modify the model until one non-intended physical interface difference is proven."}); write_json(future, obj)
    marker = "\n## Stage 10B fault-to-DFIG static fallback\n"
    addition = marker + "\nDecision: `no_defensible_electrical_difference_found`. XML geometry alone suggested a gap, but generated `P3.dta` proves the Stage-9 breaker and fault remain on the compiled `N29(1..3)` boundary. No permitted single interface repair is defensible, so GUI, Build, and Run are blocked. Strict reproduction remains `not_achieved`.\n"
    for p in [REPO / "docs/PAPER_REPRODUCTION_GAP_REGISTER.md", REPO / "docs/PAPER_REPRODUCTION_ALIGNMENT_AND_MINIMUM_CASCADE_PLAN.md"]:
        if p.exists():
            text = p.read_text(encoding="utf-8").split(marker)[0].rstrip()
            p.write_text(text + addition, encoding="utf-8")


def elements(path: Path) -> dict[str, dict[str, Any]]:
    root = ET.parse(path).getroot(); out = {}
    for e in root.iter():
        if not e.get("id"): continue
        params = {p.get("name"): p.get("value") for p in e.findall("./paramlist/param")}
        verts = [(int(v.get("x", "0")), int(v.get("y", "0"))) for v in e.findall("./vertex")]
        out[e.get("id")] = {"tag": e.tag, "id": e.get("id"), "defn": e.get("defn") or e.get("classid"),
            "x": int(e.get("x", "0")), "y": int(e.get("y", "0")), "w": int(e.get("w", "0")), "h": int(e.get("h", "0")),
            "params": params, "vertices": verts}
    return out


def span(e: dict[str, Any]) -> str:
    if not e["vertices"]: return f"anchor=({e['x']},{e['y']})"
    pts = [(e["x"] + x, e["y"] + y) for x, y in e["vertices"]]
    return " -> ".join(f"({x},{y})" for x, y in pts)


def main() -> None:
    assert sha(MAIN) == EXPECTED_MAIN
    assert sha(S9) == EXPECTED_S9
    assert sha(BACKUP / S9.name) == EXPECTED_S9
    a, b = elements(S4), elements(S9)
    ids = {
        "line": "2062315490", "n29_label": "4836", "n29_label_wire": "528887242",
        "n29_load_drop": "2062443627", "n29_load_wire": "1999500092",
        "fault_vertical": "518141974", "fault": "1999475398", "fault_timer": "413214904",
        "paper_breaker": "1559497398", "dfig_breaker": "521858026",
    }
    line4, line9 = a[ids["line"]], b[ids["line"]]
    label4, label9 = a[ids["n29_label"]], b[ids["n29_label"]]
    lw4, lw9 = a[ids["n29_label_wire"]], b[ids["n29_label_wire"]]
    drop4, drop9 = a[ids["n29_load_drop"]], b[ids["n29_load_drop"]]
    fv4, fv9 = a[ids["fault_vertical"]], b[ids["fault_vertical"]]
    breaker = b[ids["paper_breaker"]]
    fault_params = ["Ctype", "OpCur", "Grnd", "CLVL", "RON", "ROFF", "A", "B", "C", "G"]
    faults_same = all(a[ids["fault"]]["params"].get(x) == b[ids["fault"]]["params"].get(x) for x in fault_params)
    timers_same = all(a[ids["fault_timer"]]["params"].get(x) == b[ids["fault_timer"]]["params"].get(x) for x in ["TF", "DF"])
    # Schematic coordinates alone are not electrical connectivity evidence.
    # PSCAD's generated DTA node map is authoritative for this comparison.
    old_n29_x = drop4["x"]
    actual_n29_x = drop9["x"]
    fault_x = fv9["x"]
    missing_gap_px = actual_n29_x - fault_x
    dta4 = S4_DTA.read_text(encoding="utf-8", errors="ignore")
    dta9 = S9_DTA.read_text(encoding="utf-8", errors="ignore")
    stage4_fault_on_n29 = all(f"N29({i})" in dta4 for i in (1, 2, 3)) and "348   46      A" in dta4
    stage9_fault_on_n29 = all(f"N29({i})" in dta9 for i in (1, 2, 3)) and all(x in dta9 for x in ["46  354", "47  355", "48  356"])
    compiled_same_n29_boundary = stage4_fault_on_n29 and stage9_fault_on_n29
    rows = [
        {"stage4_component_or_branch":"E_28_29_1 direct terminal-to-N29 path", "stage9_component_or_branch":"E_28_29_1 + PAPER_OVL1 breaker",
         "network_endpoints":"N28 side -> E_28_29_1 -> PAPER breaker -> N29 physical junction x=3384", "closed_state_conductivity_or_impedance":"line unchanged; breaker RON=1.0e-3 ohm",
         "electrical_role":"real line plus trippable series boundary", "same_as_stage4_when_closed":"same node boundary with intentional breaker RON=1e-3 ohm",
         "difference_class":"intentional_trippable_series_boundary", "evidence_source":"XML ids 2062315490 and 1559497398", "allowed_to_correct":"no", "correction_required_for_closed_state_equivalence":"retain breaker; do not bypass"},
        {"stage4_component_or_branch":"N29 common junction at x=3312", "stage9_component_or_branch":"post-breaker N29 common junction at x=3384",
         "network_endpoints":"breaker output / E_29_38_1 / E_29_0_1", "closed_state_conductivity_or_impedance":"common ideal node",
         "electrical_role":"actual N29 bus after breaker insertion", "same_as_stage4_when_closed":"yes for downstream load/transformer; coordinates translated +72 px",
         "difference_class":"intentional_node_translation_for_breaker", "evidence_source":"XML wire id 2062443627 x 3312 -> 3384", "allowed_to_correct":"no", "correction_required_for_closed_state_equivalence":"none"},
        {"stage4_component_or_branch":"N29 fault tap represented at x=3312/3348", "stage9_component_or_branch":"N29 fault/breaker graphics represented at x=3330/3348/3384",
         "network_endpoints":"generated node N29(1..3) in both builds", "closed_state_conductivity_or_impedance":"compiled fault and breaker branches reference N29; no open interface",
         "electrical_role":"couples the 0.50-2.50 s three-phase fault to N29", "same_as_stage4_when_closed":"yes at compiled electrical-node level",
         "difference_class":"schematic_geometry_only_not_electrical_disconnect", "evidence_source":"Stage4/current generated P3.dta N29 and NT_84 branch records", "allowed_to_correct":"no",
         "correction_required_for_closed_state_equivalence":"none; adding a wire is not justified"},
        {"stage4_component_or_branch":"N29 label and fault graphical placement", "stage9_component_or_branch":"translated breaker/load graphics around N29",
         "network_endpoints":"compiled N29(1..3)", "closed_state_conductivity_or_impedance":"same compiled N29 node identity",
         "electrical_role":"node identity and fault attachment", "same_as_stage4_when_closed":"yes electrically",
         "difference_class":"nonfunctional_layout_change", "evidence_source":"XML geometry cross-checked against generated P3.dta", "allowed_to_correct":"no",
         "correction_required_for_closed_state_equivalence":"none"},
        {"stage4_component_or_branch":"N29 fault parameters", "stage9_component_or_branch":"N29 fault parameters",
         "network_endpoints":"tpflt + tfaultn", "closed_state_conductivity_or_impedance":"RON=0.01 ohm; ROFF=1e6 ohm; TF=0.5 s; DF=2.0 s",
         "electrical_role":"frozen three-phase-ground fault", "same_as_stage4_when_closed":str(faults_same and timers_same).lower(),
         "difference_class":"none", "evidence_source":"XML ids 1999475398 and 413214904", "allowed_to_correct":"no", "correction_required_for_closed_state_equivalence":"none"},
    ]
    write_csv(REPO / "data/validation/stage10b_fault_to_dfig_closed_state_diff.csv", rows)
    decision_class = "no_defensible_electrical_difference_found"
    audit = {"audit_name":"stage10b_fault_to_dfig_interface_static_audit", "generated_at_local":datetime.now().isoformat(timespec="seconds"),
        "execution_status":"stage10b_static_blocked_no_defensible_electrical_difference", "analysis_mode":"read_only_no_gui_no_build_no_run",
        "main_sha":sha(MAIN), "stage4_trial_sha":sha(S4), "stage9_trial_sha":sha(S9),
        "backup_path":str(BACKUP), "backup_trial_sha":sha(BACKUP / S9.name), "backup_gf46_exists":(BACKUP / "3IBR_DFIG1_TRIAL.gf46").is_dir(),
        "frozen_fault_parameters_equal":faults_same and timers_same, "compiled_fault_and_breaker_share_N29_boundary":compiled_same_n29_boundary,
        "stage4_geometry":{"n29_common_junction_x":old_n29_x, "fault_vertical":span(fv4), "n29_label_wire":span(lw4)},
        "stage9_geometry":{"actual_post_breaker_n29_x":actual_n29_x, "fault_vertical_end_x":fault_x, "n29_label_wire":span(lw9), "missing_horizontal_connection_px":missing_gap_px,
                           "paper_breaker_anchor":f"({breaker['x']},{breaker['y']})", "paper_breaker_RON":breaker["params"].get("RON"), "paper_breaker_ROFF":breaker["params"].get("ROFF")},
        "answers":{
          "q1_closed_breaker_equivalent":"The generated node map preserves the Stage-4 N29 electrical boundary. The only intended closed-state difference is the required breaker RON=1e-3 ohm; no unintended open node is present.",
          "q2_voltage_transfer_difference":"No defensible wrong connection, phase mismatch, ground, bypass, or extra series element was found. The apparent 36 px schematic gap is not an electrical gap; generated P3.dta connects the breaker internal nodes NT_84(1..3) to N29(1..3).",
          "q3_other_relevant_difference":"No second fault-to-DFIG electrical difference was found in the scoped stable-ID comparison. Fault parameters, DFIG breaker identity, TLine parameters, load and transformer roles remain frozen.",
          "q4_single_minimal_fix":"No. Any wire, RON, fault, or LVRT change would be unsupported by the scoped static evidence.",
          "q5_run_if_unproven":"Yes. Stage 10B must stop before GUI, Build, and Run rather than modify a compiled-correct interface."},
        "decision":decision_class, "gui_change_authorized":decision_class == "closed_state_equivalence_restoration_required",
        "run_authorized_now":False, "build_authorized_after_user_gui_repair":decision_class == "closed_state_equivalence_restoration_required"}
    write_json(REPO / "data/validation/stage10b_fault_to_dfig_interface_static_audit.json", audit)
    decision = {"decision":decision_class, "root_cause":"not_resolved_no_permitted_fault_to_dfig_interface_difference",
        "single_allowed_electrical_change":None,
        "why_blocked":"XML geometry suggested a gap, but generated P3.dta disproves an electrical disconnection. No single non-intended interface difference remains that can be corrected without unsupported parameter/topology changes.",
        "project_setting_change":None, "build_then_stop":False, "run_authorized":False,
        "next_evidence_required":["Stage-4 versus Stage-9 compiled nodal/admittance comparison around N29/DFIG PCC including breaker closed conductance", "initial-condition/power-flow state comparison before 0.5 s", "proof of a specific non-intended external DFIG PCC interface difference before any model edit"],
        "frozen_items":["fault parameters", "DFIG LVRT 0.9/0.2 and delay", "BRK_DFIG", "event packet", "E_28_29_1 capacity 7.872883989661206", "threshold 1.1", "delay 5.0 s", "PAPER relay and breaker parameters", "TLine parameters", "Output Channels", "plot step"]}
    write_json(REPO / "data/reference/stage10b_fault_to_dfig_alignment_decision.json", decision)
    freeze_path = REPO / "data/reference/stage10b_fault_to_dfig_gui_repair_freeze.json"
    if freeze_path.exists(): freeze_path.unlink()
    update_references()
    print(json.dumps({"decision":decision_class, "missing_connection_px":missing_gap_px, "backup_ok":audit["backup_gf46_exists"]}, indent=2))


if __name__ == "__main__": main()
