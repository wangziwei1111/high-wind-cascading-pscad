#!/usr/bin/env python3
"""Read-only preflight for paper-aligned raw branch P/Q/I observability."""

from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path
import re
import xml.etree.ElementTree as ET


ROOT = Path(__file__).resolve().parents[2]
PSCAD = Path(r"C:\pscad_work\pnnl_39_3ibr_pscad46_strip5\PSCAD")
MAIN = PSCAD / "3IBR.pscx"
TRIAL = PSCAD / "3IBR_DFIG1_TRIAL.pscx"
GF46 = PSCAD / "3IBR_DFIG1_TRIAL.gf46"
P3F = GF46 / "P3.f"
EXPECTED_MAIN_SHA = "CBA120BB167CB7FA6C4A1AE4471268850AB61761EC1877EB7B87015627FE9DAB"
EXPECTED_CHANNELS = 262
EXPECTED_UNMAPPED_UNUSED_DEFINITION_CHANNELS = {
    "Wang_30", "Wpu_30", "Ef_30", "If_30", "TE_30", "TM_30", "Vm_30", "P_30", "Q_30"
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def params(element: ET.Element) -> dict[str, str]:
    return {p.get("name", ""): p.get("value", "") for p in element.findall("./paramlist/param")}


def generated_artifact_fingerprint() -> list[dict[str, object]]:
    rows = []
    for pattern in ("*.f", "*.dta", "*.inf", "*.out", "*.exe"):
        for path in sorted(GF46.glob(pattern)):
            stat = path.stat()
            rows.append({"name": path.name, "size": stat.st_size, "mtime_ns": stat.st_mtime_ns, "sha256": sha256(path)})
    return rows


def p3_definition(root: ET.Element) -> ET.Element:
    return next(definition for definition in root.iter("Definition") if definition.get("name") == "P3")


def parse_fortran_channels(files: list[Path]) -> tuple[dict[str, list[dict[str, object]]], int]:
    result: dict[str, list[dict[str, object]]] = {}
    total = 0
    for path in files:
        text = path.read_text(encoding="utf-8", errors="replace")
        current = None
        for line_number, line in enumerate(text.splitlines(), 1):
            comment = re.search(r"Output Channel '([^']+)'", line)
            if comment:
                current = comment.group(1)
                continue
            assignment = re.search(r"PGB\(IPGB\+(\d+)\)\s*=\s*(.+)", line)
            if assignment and current:
                result.setdefault(current, []).append({
                    "generated_file": path.name,
                    "pgb_offset": int(assignment.group(1)),
                    "signal_binding": assignment.group(2).strip(),
                    "fortran_line": line_number,
                })
                total += 1
                current = None
    return result, total


def write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def main() -> int:
    data_ref = ROOT / "data" / "reference"
    data_val = ROOT / "data" / "validation"
    data_ref.mkdir(parents=True, exist_ok=True)
    data_val.mkdir(parents=True, exist_ok=True)

    root = ET.parse(TRIAL).getroot()
    p3 = p3_definition(root)
    fortran, fortran_entry_count = parse_fortran_channels(sorted(GF46.glob("*.f")))
    channel_elements = [user for user in root.iter("User") if user.get("defn") == "master:pgb"]
    channels = []
    for xml_order, user in enumerate(channel_elements, 1):
        row = params(user)
        name = row.get("Name", "")
        channels.append({
            "xml_order": xml_order,
            "name": name,
            "component_id": user.get("id", ""),
            "definition": user.get("defn", ""),
            "x": user.get("x", ""),
            "y": user.get("y", ""),
            "xml_parameters": row,
            "fortran_mappings": fortran.get(name, []),
        })
    channel_fingerprint = hashlib.sha256(json.dumps(channels, sort_keys=True).encode()).hexdigest().upper()
    unmapped_channel_names = {row["name"] for row in channels if not row["fortran_mappings"]}
    baseline = {
        "trial_sha256": sha256(TRIAL),
        "main_sha256": sha256(MAIN),
        "output_channel_count": len(channels),
        "output_channel_fingerprint": channel_fingerprint,
        "generated_fortran_output_assignment_count": fortran_entry_count,
        "unmapped_xml_channel_names": sorted(unmapped_channel_names),
        "unmapped_channel_explanation": "Nine G_30 legacy definition channels remain in XML but have no active generated call-site mapping because the replaced G_30 definition has no compiled instance; they are frozen unchanged.",
        "channels": channels,
    }
    (data_val / "branch_raw_measurements_existing_channel_baseline.json").write_text(json.dumps(baseline, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    # These are genuine P3 transmission-line components. Their row definitions
    # contain only line-constant components and expose no transfer-signal ports.
    # No inline transmission-line multimeter/ammeter exists at their terminals.
    candidates = [
        {
            "candidate_branch_id": "BR_CAND_01", "current_project_branch_name": "E_2_3_1",
            "branch_component_type": "PSCAD TLine / IBR_ConvZ_Modified5 row definition",
            "from_bus_or_node": "N2", "to_bus_or_node": "N3",
            "physical_path_evidence": "P3 TLine id 1020961389 at (288,162), directly between node labels N2 and N3; DFIG GBUS30 reaches N2 through transformer E_2_30_1.",
            "paper_relation_type": "DFIG-PCC export-adjacent redistribution corridor",
            "paper_evidence_id": "E003;E010;E012",
            "selection_rationale": "Real N2-N3 transmission line immediately adjacent to the N2 network bus receiving the DFIG GBUS30 transformer path.",
            "rejection_reason": "No existing line-terminal P/Q/I transfer signals or inline transmission-line meter; creating them would require a new measurement element or PSCAD calculation, both outside this task.",
            "measurement_terminal": "none exposed", "p_signal_name": "", "q_signal_name": "", "i_signal_name": "",
            "p_signal_semantics": "unavailable", "q_signal_semantics": "unavailable", "i_signal_semantics": "unavailable",
            "rating_parameter_name": "", "rating_parameter_value": "", "rating_unit": "",
            "rating_traceability_status": "insufficient_evidence",
            "future_offline_loading_ratio_candidate_formula": "abs(I_measured)/I_limit or sqrt(P_measured^2+Q_measured^2)/S_limit only after units/ratings are audited",
            "loading_ratio_feasibility_status": "blocked_missing_raw_PQI_and_rating",
            "eligibility_status": "rejected_missing_pqi_measurement_semantics",
        },
        {
            "candidate_branch_id": "BR_CAND_02", "current_project_branch_name": "E_1_2_1",
            "branch_component_type": "PSCAD TLine / IBR_ConvZ_Modified5 row definition",
            "from_bus_or_node": "N1", "to_bus_or_node": "N2",
            "physical_path_evidence": "P3 TLine id 1444448891 at (108,162), directly between node labels N1 and N2; N2 is coupled to DFIG GBUS30 by E_2_30_1.",
            "paper_relation_type": "DFIG-PCC export-adjacent redistribution corridor",
            "paper_evidence_id": "E003;E010;E012",
            "selection_rationale": "Real N1-N2 transmission corridor incident on the DFIG-connected N2 bus.",
            "rejection_reason": "No existing line-terminal P/Q/I transfer signals or inline transmission-line meter.",
            "measurement_terminal": "none exposed", "p_signal_name": "", "q_signal_name": "", "i_signal_name": "",
            "p_signal_semantics": "unavailable", "q_signal_semantics": "unavailable", "i_signal_semantics": "unavailable",
            "rating_parameter_name": "", "rating_parameter_value": "", "rating_unit": "",
            "rating_traceability_status": "insufficient_evidence",
            "future_offline_loading_ratio_candidate_formula": "abs(I_measured)/I_limit or sqrt(P_measured^2+Q_measured^2)/S_limit only after units/ratings are audited",
            "loading_ratio_feasibility_status": "blocked_missing_raw_PQI_and_rating",
            "eligibility_status": "rejected_missing_pqi_measurement_semantics",
        },
        {
            "candidate_branch_id": "BR_CAND_03", "current_project_branch_name": "E_2_25_1",
            "branch_component_type": "PSCAD TLine / IBR_ConvZ_Modified5 row definition",
            "from_bus_or_node": "N2", "to_bus_or_node": "N25",
            "physical_path_evidence": "P3 TLine id 1519344658 at (270,414), line identity E_2_25_1; left terminal is tied to the N2 vertical bus and right terminal continues to the N25 network bus.",
            "paper_relation_type": "DFIG-PCC export-adjacent redistribution corridor",
            "paper_evidence_id": "E003;E010;E012",
            "selection_rationale": "Third real transmission corridor incident on DFIG-connected bus N2.",
            "rejection_reason": "No existing line-terminal P/Q/I transfer signals or inline transmission-line meter.",
            "measurement_terminal": "none exposed", "p_signal_name": "", "q_signal_name": "", "i_signal_name": "",
            "p_signal_semantics": "unavailable", "q_signal_semantics": "unavailable", "i_signal_semantics": "unavailable",
            "rating_parameter_name": "", "rating_parameter_value": "", "rating_unit": "",
            "rating_traceability_status": "insufficient_evidence",
            "future_offline_loading_ratio_candidate_formula": "abs(I_measured)/I_limit or sqrt(P_measured^2+Q_measured^2)/S_limit only after units/ratings are audited",
            "loading_ratio_feasibility_status": "blocked_missing_raw_PQI_and_rating",
            "eligibility_status": "rejected_missing_pqi_measurement_semantics",
        },
        {
            "candidate_branch_id": "BR_CAND_04", "current_project_branch_name": "E_16_19_1",
            "branch_component_type": "PSCAD TLine / IBR_ConvZ_Modified5 row definition",
            "from_bus_or_node": "N16", "to_bus_or_node": "N19",
            "physical_path_evidence": "P3 TLine id 1699186643 at (2448,648), line identity E_16_19_1, right terminal node label N19 and left terminal connected to the N16 bus network.",
            "paper_relation_type": "exact branch identity appearing first in thesis Table 2-2 overload-opening sequence",
            "paper_evidence_id": "E003;E010",
            "selection_rationale": "Real transmission branch explicitly named by the primary thesis and present in the current P3 network.",
            "rejection_reason": "No existing line-terminal P/Q/I transfer signals. The nearby PL16 multimeter is on load branch E_16_0_1, enables only P, and is not a measurement of E_16_19_1.",
            "measurement_terminal": "none exposed", "p_signal_name": "", "q_signal_name": "", "i_signal_name": "",
            "p_signal_semantics": "unavailable; PL16 is excluded as load-branch power", "q_signal_semantics": "unavailable", "i_signal_semantics": "unavailable",
            "rating_parameter_name": "", "rating_parameter_value": "", "rating_unit": "",
            "rating_traceability_status": "insufficient_evidence",
            "future_offline_loading_ratio_candidate_formula": "abs(I_measured)/I_limit or sqrt(P_measured^2+Q_measured^2)/S_limit only after units/ratings are audited",
            "loading_ratio_feasibility_status": "blocked_missing_raw_PQI_and_rating",
            "eligibility_status": "rejected_missing_pqi_measurement_semantics",
        },
    ]
    write_csv(data_ref / "paper_branch_candidate_registry.csv", candidates)
    (data_ref / "paper_branch_candidate_registry.json").write_text(json.dumps({"candidate_count": len(candidates), "eligible_count": 0, "candidates": candidates}, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    existing_multimeters = []
    for user in p3.findall("./schematic/User"):
        if user.get("defn") in {"master:multimeter", "master:ammeter"}:
            existing_multimeters.append({"id": user.get("id"), "x": user.get("x"), "y": user.get("y"), "definition": user.get("defn"), "parameters": params(user)})
    line_definitions = {}
    for candidate in candidates:
        name = candidate["current_project_branch_name"]
        definition = next(d for d in root.iter("Definition") if d.get("name") == name)
        ports = [dict(port.attrib) for port in definition.iter("port")]
        users = [{"definition": user.get("defn"), "parameters": params(user)} for user in definition.findall("./schematic/User")]
        line_definitions[name] = {"classid": definition.get("classid"), "ports": ports, "internal_users": users}

    required_paper_ids = {"E003", "E010", "E012"}
    registry_ids = {row["evidence_id"] for row in csv.DictReader((data_ref / "paper_reproduction_evidence_registry.csv").open(encoding="utf-8"))}
    default_values = {
        "ibr2_enable": params(next(user for user in p3.findall("./schematic/User") if user.get("id") == "1778759091")).get("Value"),
        "ibr2_open_time_s": params(next(user for user in p3.findall("./schematic/User") if user.get("id") == "939314032")).get("Value"),
        "ibr3_enable": params(next(user for user in p3.findall("./schematic/User") if user.get("id") == "444774384")).get("Value"),
        "ibr3_open_time_s": params(next(user for user in p3.findall("./schematic/User") if params(user).get("Name") == "IBR3_TRIAL__OPEN_STIMULUS")).get("OPEN_TIME_S"),
    }
    trial_text = TRIAL.read_text(encoding="utf-8-sig", errors="replace")
    forbidden = {
        "matlab_interface": bool(re.search(r"MATLAB", trial_text, re.I)),
        "automatic_reclose": bool(re.search(r"AUTO[_ -]?RECLOSE|AUTORECLOSE", trial_text, re.I)),
        "fourth_source": bool(re.search(r"SOURCE[_ -]?4|SRC[_ -]?4|IBR4|CASCADE4", trial_text, re.I)),
        "virtual_source": bool(re.search(r"VIRTUAL_(?:SOURCE|CAS)|CAS_VIRTUAL", trial_text, re.I)),
        "line_overload_relay": bool(re.search(r"LINE[_ -]?OVERLOAD|BRANCH[_ -]?OVERLOAD", trial_text, re.I)),
    }
    statuses = {
        "main_project_integrity_status": "pass" if sha256(MAIN) == EXPECTED_MAIN_SHA else "fail",
        "trial_project_preflight_status": "pass" if root.get("version") == "4.6.2" else "fail",
        "existing_output_channel_preservation_status": "pass" if len(channels) == EXPECTED_CHANNELS and fortran_entry_count >= EXPECTED_CHANNELS and unmapped_channel_names == EXPECTED_UNMAPPED_UNUSED_DEFINITION_CHANNELS else "fail",
        "paper_branch_observability_evidence_status": "pass" if required_paper_ids <= registry_ids else "fail",
        "real_branch_traceability_status": "pass" if len(candidates) >= 2 and all(row["branch_component_type"].startswith("PSCAD TLine") for row in candidates) else "fail",
        "branch_measurement_semantics_status": "fail",
        "minimum_two_branch_selection_status": "fail",
        "monitor_only_scope_status": "pass" if not any(forbidden.values()) else "fail",
    }
    execution = "branch_raw_measurements_static_fallback"
    design = {
        "execution_status": execution,
        "selected_branch_count": 0,
        "selected_branches": [],
        "candidate_branch_count": len(candidates),
        "planned_new_output_channel_count": 0,
        "planned_final_output_channel_count": EXPECTED_CHANNELS,
        "gui_stage_authorized": False,
        "blocking_reason": "At least two real TLine branches are traceable, but none exposes an existing, semantically confirmed P/Q/I measurement path. Adding meters or calculations is prohibited by this stage's inline-first/no-new-element boundary.",
        "excluded_false_measurement": "PL16 is the P output of a multimeter on load branch E_16_0_1; it is not E_16_19_1 transmission-line power and has no Q/I outputs enabled.",
        "future_safe_resolution": "A future task must explicitly authorize inline branch meters (not a Page Module) or identify an authoritative native TLine measurement interface before Output Channels can be added.",
        "no_in_model_loading_ratio": True,
        "future_offline_formula_only": ["abs(I_measured)/I_limit", "sqrt(P_measured^2+Q_measured^2)/S_limit"],
        "claim_boundary": "Candidate real branches were traced, but no raw branch observability layer was added. Power-flow redistribution, loading ratio, overload, protection, trip, and cascade behavior remain unavailable.",
    }
    (data_ref / "paper_branch_raw_measurement_design.json").write_text(json.dumps(design, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    preflight = {
        "execution_status": execution,
        **statuses,
        "main_sha_before": sha256(MAIN), "trial_sha_before": sha256(TRIAL),
        "existing_output_channel_count": len(channels), "existing_output_channel_fingerprint": channel_fingerprint,
        "generated_artifact_fingerprint_before": generated_artifact_fingerprint(),
        "default_values": default_values, "forbidden_feature_scan": forbidden,
        "existing_p3_multimeters_and_ammeters": existing_multimeters,
        "candidate_line_definition_trace": line_definitions,
        "eligible_branch_count": 0,
        "gui_stage_authorized": False,
        "build_authorized": False,
        "run_authorized": False,
        "claim_boundary": design["claim_boundary"],
    }
    (data_val / "branch_raw_measurements_preflight.json").write_text(json.dumps(preflight, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps(preflight, indent=2, ensure_ascii=False))
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
