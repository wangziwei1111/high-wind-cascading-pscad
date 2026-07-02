#!/usr/bin/env python3
"""Read-only preflight for the paper-aligned 20 s bus-29 fault scenario.

This script intentionally does not edit PSCAD files, build, or run EMTDC.  It
only checks whether the current trial model and paper evidence are sufficient
to proceed to a manual PSCAD GUI static configuration step.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
from datetime import datetime
from pathlib import Path
import xml.etree.ElementTree as ET


REPO = Path(__file__).resolve().parents[2]
DEFAULT_MAIN = Path(r"C:\pscad_work\pnnl_39_3ibr_pscad46_strip5\PSCAD\3IBR.pscx")
DEFAULT_TRIAL = Path(r"C:\pscad_work\pnnl_39_3ibr_pscad46_strip5\PSCAD\3IBR_DFIG1_TRIAL.pscx")

EXPECTED_MAIN_SHA = "CBA120BB167CB7FA6C4A1AE4471268850AB61761EC1877EB7B87015627FE9DAB"
EXPECTED_TRIAL_SHA = "A9DC610D20C61022CDE2F2D73612C12499FB7E5D29C43562BA08D9D89EADF360"
REQUIRED_EVIDENCE = {"E009", "E010", "E017", "E018"}


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest().upper()


def load_xml(path: Path) -> ET.Element:
    return ET.fromstring(path.read_text(encoding="utf-8", errors="replace"))


def parent_map(root: ET.Element) -> dict[ET.Element, ET.Element]:
    return {child: parent for parent in root.iter() for child in parent}


def element_path(root: ET.Element, target: ET.Element) -> str:
    parents = parent_map(root)
    parts: list[str] = []
    el: ET.Element | None = target
    while el is not None:
        key = el.attrib.get("name") or el.attrib.get("id") or el.attrib.get("defn") or ""
        parts.append(f"{el.tag}[{key}]")
        el = parents.get(el)
    return "/".join(reversed(parts))


def params_under(user: ET.Element) -> dict[str, str]:
    out: dict[str, str] = {}
    for param in user.findall(".//param"):
        name = param.attrib.get("name")
        if name:
            out[name] = param.attrib.get("value", "")
    return out


def read_csv_dicts(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def write_json(path: Path, data: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames: list[str] = []
    for row in rows:
        for key in row:
            if key not in fieldnames:
                fieldnames.append(key)
    with path.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        w.writerows(rows)


def find_evidence() -> tuple[dict[str, dict[str, str]], dict[str, object]]:
    registry = read_csv_dicts(REPO / "data/reference/paper_reproduction_evidence_registry.csv")
    rows = {row.get("evidence_id", ""): row for row in registry}
    selected = {eid: rows.get(eid, {}) for eid in sorted(REQUIRED_EVIDENCE)}
    gates = {}
    for eid, row in selected.items():
        gates[eid] = {
            "present": bool(row),
            "has_section": bool(row.get("paper_section")),
            "has_pages": bool(row.get("paper_page")),
            "has_anchor": bool(row.get("paper_figure_or_table")),
            "claim": row.get("paper_statement_paraphrase") or "",
            "quote_or_paraphrase": row.get("exact_short_quote_if_available") or "",
        }
    return selected, {"registry_path": "data/reference/paper_reproduction_evidence_registry.csv", "gates": gates}


def find_fault(root: ET.Element) -> dict[str, object]:
    users = [u for u in root.iter("User") if "tfault" in u.attrib.get("defn", "").lower()]
    traces = []
    for u in users:
        traces.append(
            {
                "id": u.attrib.get("id"),
                "defn": u.attrib.get("defn"),
                "definition_path": element_path(root, u),
                "x": u.attrib.get("x"),
                "y": u.attrib.get("y"),
                "w": u.attrib.get("w"),
                "h": u.attrib.get("h"),
                "params": params_under(u),
            }
        )
    return {
        "fault_component_count": len(users),
        "fault_components": traces,
        "existing_fault_component_status": "pass" if len(users) == 1 else "fail",
    }


def find_n29(root: ET.Element) -> dict[str, object]:
    parents = parent_map(root)
    labels = []
    for param in root.iter("param"):
        if param.attrib.get("name") == "Name" and param.attrib.get("value") == "N29":
            user = parents.get(parents.get(param)) if parents.get(param) is not None else None
            labels.append(
                {
                    "param_path": element_path(root, param),
                    "user": user.attrib if user is not None else {},
                }
            )
    inventory = json.loads((REPO / "data/reference/full_network_tline_inventory.json").read_text(encoding="utf-8"))
    n29_lines = []
    for line in inventory.get("tlines", []):
        endpoints = {line.get("terminal_a_node"), line.get("terminal_b_node")}
        if "N29" in endpoints:
            n29_lines.append(line)
    return {
        "n29_label_count": len(labels),
        "n29_labels": labels,
        "n29_adjacent_tlines": [
            {
                "tline": x.get("tline_name") or x.get("component_name"),
                "network_branch_id": x.get("network_branch_id"),
                "tline_instance_name": x.get("tline_instance_name"),
                "terminal_a_node": x.get("terminal_a_node"),
                "terminal_b_node": x.get("terminal_b_node"),
                "component_id": x.get("component_id"),
                "inclusion_status": x.get("inclusion_status"),
                "paper_evidence_id": x.get("paper_evidence_id"),
            }
            for x in n29_lines
        ],
        "mapping_status": "structurally_aligned_adaptation"
        if len(labels) == 1 and len(n29_lines) >= 2
        else "insufficient",
    }


def output_channels(root: ET.Element) -> tuple[dict[str, object], list[dict[str, object]]]:
    rows = []
    seen = {}
    for u in root.iter("User"):
        if u.attrib.get("defn") == "master:pgb":
            p = params_under(u)
            name = p.get("Name") or p.get("Title") or u.attrib.get("name") or u.attrib.get("id")
            seen[name] = seen.get(name, 0) + 1
            rows.append(
                {
                    "id": u.attrib.get("id"),
                    "name": name,
                    "x": u.attrib.get("x"),
                    "y": u.attrib.get("y"),
                    "status": "baseline_preserved_pre_gui",
                }
            )
    return {
        "xml_output_channel_count": len(rows),
        "duplicate_names": {k: v for k, v in seen.items() if v > 1},
        "status": "pass" if len(rows) == 448 else "fail",
    }, rows


def project_settings(root: ET.Element) -> dict[str, str]:
    return {p.attrib.get("name", ""): p.attrib.get("value", "") for p in root.findall("./paramlist/param")}


def trial_defaults(root: ET.Element) -> dict[str, object]:
    traces: dict[str, list[dict[str, str]]] = {
        "IBR2_TEST_ENABLE": [],
        "IBR3_TEST_ENABLE": [],
        "IBR2_TEST_OPEN_TIME_S": [],
        "IBR3_TEST_OPEN_TIME_S": [],
    }
    for el in root.iter():
        for value in el.attrib.values():
            for key in traces:
                if key in str(value):
                    traces[key].append({"tag": el.tag, **el.attrib})
    stimulus_values = []
    for user in root.iter("User"):
        name = user.attrib.get("name", "")
        defn = user.attrib.get("defn", "")
        if "OPEN_STIMULUS" in name or "OPEN_STIMULUS" in defn:
            stimulus_values.append({"user": user.attrib, "params": params_under(user)})
    return {"label_traces": traces, "open_stimulus_instances": stimulus_values}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--main-pscx", type=Path, default=DEFAULT_MAIN)
    ap.add_argument("--trial-pscx", type=Path, default=DEFAULT_TRIAL)
    args = ap.parse_args()

    gates: dict[str, object] = {}
    errors: list[str] = []

    main_exists = args.main_pscx.exists()
    trial_exists = args.trial_pscx.exists()
    gates["main_file_exists"] = main_exists
    gates["trial_file_exists"] = trial_exists
    if not main_exists:
        errors.append(f"missing main PSCAD file: {args.main_pscx}")
    if not trial_exists:
        errors.append(f"missing trial PSCAD file: {args.trial_pscx}")
    if errors:
        preflight = {"execution_status": "fail", "errors": errors, "gates": gates}
        write_json(REPO / "data/validation/paper_aligned_fault_scenario_preflight.json", preflight)
        print(json.dumps(preflight, ensure_ascii=False, indent=2))
        return 2

    main_sha = sha256(args.main_pscx)
    trial_sha = sha256(args.trial_pscx)
    trial_root = load_xml(args.trial_pscx)

    evidence_rows, evidence_extract = find_evidence()
    fault_trace = find_fault(trial_root)
    target_mapping = find_n29(trial_root)
    channel_baseline, channel_rows = output_channels(trial_root)
    settings = project_settings(trial_root)
    defaults = trial_defaults(trial_root)

    final_audit = json.loads((REPO / "data/validation/full_network_tline_measurement_final_audit.json").read_text(encoding="utf-8"))

    scenario_design = {
        "scenario_id": "paper_aligned_20s_bus29_three_phase_fault_static",
        "claim_boundary": "static structural adaptation, not a complete paper identity proof",
        "paper_fault": {
            "location": "near bus 29",
            "fault_type": "three-phase short circuit",
            "start_s": 0.50,
            "duration_s": 2.00,
            "clear_s": 2.50,
            "simulation_duration_s": 20.00,
            "supporting_evidence": ["E009", "E010", "E017", "E018"],
        },
        "manual_gui_actions_required": [
            "reuse the single existing master:tfaultn component; do not add a new fault component",
            "move/reconnect the existing fault component to the P3 N29 node boundary",
            "set TF=0.50 s and DF=2.00 s, so clearing occurs at 2.50 s",
            "set project Duration of Run to 20.00 s",
            "save and Build only; do not Run",
        ],
        "preserve": {
            "output_channel_count": 448,
            "full_network_tline_measurement_layer": "unchanged",
            "IBR2_TEST_ENABLE": 0,
            "IBR3_TEST_ENABLE": 0,
            "IBR2_TEST_OPEN_TIME_S": 4.0,
            "IBR3_TEST_OPEN_TIME_S": 5.0,
        },
    }

    gates.update(
        {
            "main_sha_matches_expected": main_sha == EXPECTED_MAIN_SHA,
            "trial_sha_matches_full_network_tline_baseline": trial_sha == EXPECTED_TRIAL_SHA,
            "evidence_rows_present": all(bool(evidence_rows.get(eid)) for eid in REQUIRED_EVIDENCE),
            "evidence_page_section_anchor_present": all(
                bool(evidence_rows[eid].get("paper_section"))
                and bool(evidence_rows[eid].get("paper_page"))
                and bool(evidence_rows[eid].get("paper_figure_or_table"))
                for eid in REQUIRED_EVIDENCE
            ),
            "single_existing_fault_component": fault_trace["existing_fault_component_status"] == "pass",
            "n29_structural_mapping_available": target_mapping["mapping_status"] == "structurally_aligned_adaptation",
            "output_channel_count_448": channel_baseline["status"] == "pass",
            "full_network_tline_audit_pass": final_audit.get("execution_status") == "pass",
            "current_trial_duration_is_editable_pre_gui": settings.get("time_duration") in {"5", "20", "20.0", "20.00"},
        }
    )

    if not gates["main_sha_matches_expected"]:
        errors.append("main project SHA does not match protected baseline")
    if not gates["trial_sha_matches_full_network_tline_baseline"]:
        errors.append("trial project SHA does not match the full-network TLine measurement baseline")
    if not gates["evidence_rows_present"] or not gates["evidence_page_section_anchor_present"]:
        errors.append("required paper evidence E009/E010/E017/E018 is incomplete")
    if not gates["single_existing_fault_component"]:
        errors.append("expected exactly one existing master:tfaultn fault component")
    if not gates["n29_structural_mapping_available"]:
        errors.append("N29 structural target mapping is insufficient")
    if not gates["output_channel_count_448"]:
        errors.append("existing Output Channel count is not 448")
    if not gates["full_network_tline_audit_pass"]:
        errors.append("full-network TLine measurement baseline audit is not pass")

    preflight = {
        "audit_name": "paper_aligned_fault_scenario_preflight",
        "generated_at_local": datetime.now().isoformat(timespec="seconds"),
        "execution_status": "pass" if not errors else "fail",
        "main_pscx": str(args.main_pscx),
        "trial_pscx": str(args.trial_pscx),
        "main_sha256": main_sha,
        "trial_sha256": trial_sha,
        "gates": gates,
        "errors": errors,
        "current_project_settings": {
            "time_duration": settings.get("time_duration"),
            "time_step": settings.get("time_step"),
            "sample_step": settings.get("sample_step"),
        },
        "current_trial_defaults_trace": defaults,
        "fault_component_summary": fault_trace,
        "target_mapping_summary": target_mapping,
        "channel_baseline_summary": channel_baseline,
        "next_action": "manual_gui_static_configuration_and_build_only" if not errors else "do_not_enter_gui_record_fallback",
    }

    write_json(REPO / "data/reference/paper_fault_scenario_evidence_extract.json", evidence_extract)
    write_json(REPO / "data/reference/current_trial_fault_component_trace.json", fault_trace)
    write_json(REPO / "data/reference/paper_fault_target_mapping.json", target_mapping)
    write_json(REPO / "data/reference/paper_aligned_fault_scenario_design.json", scenario_design)
    write_json(REPO / "data/validation/paper_aligned_fault_scenario_preflight.json", preflight)
    write_json(REPO / "data/validation/paper_aligned_fault_scenario_existing_channel_baseline.json", channel_baseline)
    write_csv(REPO / "data/validation/paper_aligned_fault_scenario_channel_baseline.csv", channel_rows)

    print(json.dumps(preflight, ensure_ascii=False, indent=2))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
