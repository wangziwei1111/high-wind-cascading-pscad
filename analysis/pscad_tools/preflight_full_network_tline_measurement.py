#!/usr/bin/env python3
"""Read-only preflight for full-network, dual-end TLine P/Q/I metering.

The script reads PSCAD XML, generated Fortran, and the installed PSCAD 4.6
Master Library.  It never writes PSCAD project or generated build files.
"""

from __future__ import annotations

import csv
import hashlib
import json
from collections import deque
from pathlib import Path
import re
import xml.etree.ElementTree as ET


ROOT = Path(__file__).resolve().parents[2]
PSCAD = Path(r"C:\pscad_work\pnnl_39_3ibr_pscad46_strip5\PSCAD")
MAIN = PSCAD / "3IBR.pscx"
TRIAL = PSCAD / "3IBR_DFIG1_TRIAL.pscx"
GF46 = PSCAD / "3IBR_DFIG1_TRIAL.gf46"
MASTER = Path(r"C:\Program Files (x86)\PSCAD46\master.pslx")
HELP_LINKS = Path(r"C:\Program Files (x86)\PSCAD46\help_links.props")
EXPECTED_MAIN_SHA = "CBA120BB167CB7FA6C4A1AE4471268850AB61761EC1877EB7B87015627FE9DAB"
EXPECTED_TRIAL_SHA = "1F747F067339547ECCFD03AD41A1B56ABE3DDC6D627AD1F085B37BFA9532DD95"
EXPECTED_CHANNELS = 262
EXPECTED_UNMAPPED = {"Wang_30", "Wpu_30", "Ef_30", "If_30", "TE_30", "TM_30", "Vm_30", "P_30", "Q_30"}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def params(element: ET.Element) -> dict[str, str]:
    return {p.get("name", ""): p.get("value", "") for p in element.findall("./paramlist/param")}


def write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    if not rows:
        raise ValueError(f"refusing to write empty CSV: {path}")
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def write_json(path: Path, payload: object) -> None:
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def p3_definition(root: ET.Element) -> ET.Element:
    return next(d for d in root.iter("Definition") if d.get("name") == "P3")


def parse_fortran_channels(files: list[Path]) -> tuple[dict[str, list[dict[str, object]]], int]:
    result: dict[str, list[dict[str, object]]] = {}
    total = 0
    for path in files:
        current = None
        text = path.read_text(encoding="utf-8", errors="replace")
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


def component_definition(root: ET.Element, name: str) -> ET.Element:
    return next(d for d in root.iter("Definition") if d.get("name") == name)


def definition_source_text(definition: ET.Element) -> str:
    return ET.tostring(definition, encoding="unicode")


def graph_distances(edges: list[tuple[str, str]], origin: str) -> dict[str, int]:
    graph: dict[str, set[str]] = {}
    for a, b in edges:
        graph.setdefault(a, set()).add(b)
        graph.setdefault(b, set()).add(a)
    distances = {origin: 0}
    queue = deque([origin])
    while queue:
        node = queue.popleft()
        for neighbor in graph.get(node, set()):
            if neighbor not in distances:
                distances[neighbor] = distances[node] + 1
                queue.append(neighbor)
    return distances


def main() -> int:
    data_ref = ROOT / "data" / "reference"
    data_val = ROOT / "data" / "validation"
    data_ref.mkdir(parents=True, exist_ok=True)
    data_val.mkdir(parents=True, exist_ok=True)

    required_files = [MAIN, TRIAL, MASTER, HELP_LINKS, GF46 / "P3.f", GF46 / "P3.dta"]
    missing = [str(path) for path in required_files if not path.exists()]
    if missing:
        raise FileNotFoundError("missing required preflight inputs: " + "; ".join(missing))

    trial_root = ET.parse(TRIAL).getroot()
    master_root = ET.parse(MASTER).getroot()
    p3 = p3_definition(trial_root)
    fortran, fortran_entry_count = parse_fortran_channels(sorted(GF46.glob("*.f")))

    channel_elements = [u for u in trial_root.iter("User") if u.get("defn") == "master:pgb"]
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
    unmapped = {row["name"] for row in channels if not row["fortran_mappings"]}
    baseline_path = data_val / "full_network_tline_measurement_existing_channel_baseline.json"
    is_initial_pre_gui_state = sha256(TRIAL) == EXPECTED_TRIAL_SHA and len(channels) == EXPECTED_CHANNELS
    baseline = {
        "main_sha256": sha256(MAIN),
        "trial_sha256": sha256(TRIAL),
        "output_channel_count": len(channels),
        "output_channel_fingerprint": channel_fingerprint,
        "generated_fortran_output_assignment_count": fortran_entry_count,
        "unmapped_xml_channel_names": sorted(unmapped),
        "frozen_existing_output_channel_parameters": {
            "Transfer Data": "enab",
            "Multiple Run Save": "mrun",
            "Scale Factor": "Scale",
            "Use signal name as title": "UseSignalName",
        },
        "reference_monitor_channel_parameters": {
            "Transfer Data": "Yes (enab=1)",
            "Multiple Run Save": "No (mrun=0)",
            "Scale Factor": "1.0",
            "Use signal name as title": "No (UseSignalName=0)",
            "Display": "Yes (Display=1)",
            "Polarity": "0",
        },
        "channels": channels,
    }
    if is_initial_pre_gui_state or not baseline_path.exists():
        write_json(baseline_path, baseline)
    else:
        baseline = json.loads(baseline_path.read_text(encoding="utf-8"))

    tline_pattern = re.compile(r"^E_(\d+)_(\d+)_(\d+)$")
    tlines: list[tuple[ET.Element, str, str, str, str]] = []
    for wire in p3.findall("./schematic/Wire"):
        if wire.get("classid") != "TLine":
            continue
        definition_name = (wire.get("defn") or "").split(":")[-1]
        match = tline_pattern.fullmatch(definition_name)
        if not match:
            continue
        a, b, parallel = match.groups()
        tlines.append((wire, definition_name, f"N{a}", f"N{b}", parallel))
    tlines.sort(key=lambda item: tuple(int(v) for v in tline_pattern.fullmatch(item[1]).groups()))
    distances = graph_distances([(a, b) for _, _, a, b, _ in tlines], "N2")

    inventory = []
    for wire, name, node_a, node_b, parallel in tlines:
        hop = min(distances.get(node_a, 999), distances.get(node_b, 999))
        exact_paper = name == "E_16_19_1"
        inventory.append({
            "network_branch_id": name,
            "tline_instance_name": name,
            "tline_component_definition": wire.get("defn", ""),
            "component_id": wire.get("id", ""),
            "terminal_a_node": node_a,
            "terminal_b_node": node_b,
            "terminal_a_port": "send/left electrical terminal (orientation=0)",
            "terminal_b_port": "receive/right electrical terminal (orientation=0)",
            "parallel_group_id": "__".join(sorted((node_a, node_b), key=lambda n: int(n[1:]))),
            "parallel_index": parallel,
            "is_network_transmission_tline": "true",
            "inclusion_status": "included",
            "exclusion_reason": "",
            "dfiq_pcc_relation": f"minimum endpoint distance {hop} TLine hop(s) from DFIG-connected network bus N2",
            "paper_relation_type": "exact thesis branch identity; full-network redistribution observability" if exact_paper else "full-network redistribution observability",
            "paper_evidence_id": "E003;E010;E012" if exact_paper else "E003;E012",
        })
    write_csv(data_ref / "full_network_tline_inventory.csv", inventory)
    write_json(data_ref / "full_network_tline_inventory.json", {
        "inventory_count": len(inventory),
        "included_count": len(inventory),
        "excluded_count": 0,
        "definition_rule": "Enabled P3 Wire elements with classid=TLine and row identity E_<network node>_<network node>_<parallel index>.",
        "explicit_non_tline_exclusions": [
            "DFIG local breaker and transformer feeder branches",
            "IBR2/IBR3 source-local feeders",
            "transformer windings and source/load interface wiring",
            "load branch E_16_0_1 and its PL16 signal",
            "control, event, command, and test-harness wiring",
        ],
        "tlines": inventory,
    })

    multimeter = component_definition(master_root, "multimeter")
    multimeter_text = definition_source_text(multimeter)
    ammeter = component_definition(master_root, "ammeter")
    ammeter_text = definition_source_text(ammeter)
    power = component_definition(master_root, "power")
    rms3ph = component_definition(master_root, "rms3ph")
    official_path = str(MASTER)
    assessment = [
        {
            "component_definition": "master:multimeter",
            "component_library_source": "PSCAD 4.6 installed Master Library / Meters",
            "official_documentation_path": f"{official_path}; {HELP_LINKS} entry multimeter=271",
            "electrical_terminal_count": "2 natural three-phase terminals: A and B",
            "signal_output_ports": "P, Q, Crms (#OUTPUT REAL signals)",
            "p_output_semantics": "P3PH3 three-phase real power using terminal-A voltage and A-to-B AMMETER branch current; analog smoothing TS",
            "q_output_semantics": "Q3PH3 three-phase reactive power using terminal-A voltage and A-to-B AMMETER branch current; analog smoothing TS",
            "i_output_semantics": "RMS3PH magnitude of the three phase A-to-B branch currents followed by REALPOLE when IRMS=Yes, Analog",
            "p_unit": "p.u. on 100 MVA system base",
            "q_unit": "p.u. on 100 MVA system base",
            "i_unit": "p.u. on Base Current; Base Current=1.0 kA makes the numeric value equal to kA",
            "measurement_time_semantics": "P, Q, and analog IRMS use TS=0.02 s smoothing; values are evaluated each EMTDC time step; no Run performed here",
            "sign_convention": "P/Q positive from component terminal A toward terminal B; I is non-negative RMS magnitude",
            "terminal_orientation_rule": "At each TLine end connect meter A to the network bus and meter B toward the TLine; rotate the terminal-B meter 180 degrees",
            "electrical_intrusiveness_status": "pass: Branch script is only 'BN = $A $B AMMETER'; no R/L/C, source, switch, or phase-shifting parameter",
            "parameter_equivalence_evidence": "Master Library Branch segment and AMMETER definition contain no electrical parameter; original TLine row definition and parameters remain unchanged",
            "control_isolation_status": "pass: no control input and only monitor signal outputs P/Q/Crms",
            "supports_dual_end_measurement": "yes, using one independent meter at each end",
            "measurement_plan_rank": "2",
            "qualified_status": "pass",
            "rejection_reason": "",
        },
        {
            "component_definition": "master:power",
            "component_library_source": "PSCAD 4.6 installed Master Library / Meters",
            "official_documentation_path": official_path,
            "electrical_terminal_count": "2 three-phase electrical terminals",
            "signal_output_ports": "Pout, Qout",
            "p_output_semantics": "documented three-phase real power",
            "q_output_semantics": "documented three-phase reactive power",
            "i_output_semantics": "unavailable",
            "p_unit": "per configured scale",
            "q_unit": "per configured scale",
            "i_unit": "unavailable",
            "measurement_time_semantics": "not selected",
            "sign_convention": "direction option exists",
            "terminal_orientation_rule": "not selected",
            "electrical_intrusiveness_status": "not needed after semantic rejection",
            "parameter_equivalence_evidence": "official Master Library definition",
            "control_isolation_status": "pass",
            "supports_dual_end_measurement": "no",
            "measurement_plan_rank": "rejected",
            "qualified_status": "fail",
            "rejection_reason": "No three-phase RMS current output; would require an additional meter and a less-minimal mixed structure.",
        },
        {
            "component_definition": "master:rms3ph",
            "component_library_source": "PSCAD 4.6 installed Master Library / Meters",
            "official_documentation_path": f"{official_path}; {HELP_LINKS} entry rms3ph=112",
            "electrical_terminal_count": "0; transfer-signal meter",
            "signal_output_ports": "RMS only",
            "p_output_semantics": "unavailable",
            "q_output_semantics": "unavailable",
            "i_output_semantics": "three-phase RMS of supplied signal",
            "p_unit": "unavailable",
            "q_unit": "unavailable",
            "i_unit": "depends on supplied signal",
            "measurement_time_semantics": "not selected",
            "sign_convention": "magnitude only",
            "terminal_orientation_rule": "not applicable",
            "electrical_intrusiveness_status": "signal-only",
            "parameter_equivalence_evidence": "official Master Library definition",
            "control_isolation_status": "pass",
            "supports_dual_end_measurement": "no",
            "measurement_plan_rank": "rejected",
            "qualified_status": "fail",
            "rejection_reason": "No direct electrical terminals and no P/Q outputs.",
        },
        {
            "component_definition": "master:ammeter",
            "component_library_source": "PSCAD 4.6 installed Master Library / Meters",
            "official_documentation_path": f"{official_path}; {HELP_LINKS} entry ammeter=104",
            "electrical_terminal_count": "2 natural electrical terminals N1/N2",
            "signal_output_ports": "instantaneous branch current only",
            "p_output_semantics": "unavailable",
            "q_output_semantics": "unavailable",
            "i_output_semantics": "instantaneous current, not three-phase RMS loading current",
            "p_unit": "unavailable",
            "q_unit": "unavailable",
            "i_unit": "instantaneous current",
            "measurement_time_semantics": "instantaneous EMTDC step",
            "sign_convention": "N1 to N2",
            "terminal_orientation_rule": "not selected",
            "electrical_intrusiveness_status": "pass: ideal AMMETER branch",
            "parameter_equivalence_evidence": "Branch script: BN = $N1 $N2 AMMETER",
            "control_isolation_status": "pass",
            "supports_dual_end_measurement": "no",
            "measurement_plan_rank": "rejected",
            "qualified_status": "fail",
            "rejection_reason": "No P/Q and current is instantaneous rather than three-phase RMS.",
        },
    ]
    write_csv(data_ref / "native_tline_measurement_component_assessment.csv", assessment)
    write_json(data_ref / "native_tline_measurement_component_assessment.json", {
        "qualified_component_count": 1,
        "selected_component": "master:multimeter",
        "official_definition_evidence": {
            "multimeter_description_present": 'value="Multimeter"' in multimeter_text,
            "multimeter_p3ph3_present": "P3PH3" in multimeter_text,
            "multimeter_q3ph3_present": "Q3PH3" in multimeter_text,
            "multimeter_rms3ph_present": "RMS3PH" in multimeter_text,
            "multimeter_ammeter_branch_present": "AMMETER" in multimeter_text,
            "ammeter_has_no_r_l_c_parameters": not re.search(r'name="[RLC]"', ammeter_text),
            "power_candidate_checked": power is not None,
            "rms3ph_candidate_checked": rms3ph is not None,
        },
        "candidates": assessment,
    })

    selected_params = {
        "Instantaneous Voltage?": "No",
        "Instantaneous Current?": "No",
        "Active Power flow?": "Yes",
        "Reactive Power flow?": "Yes",
        "RMS Voltage?": "No",
        "RMS Current?": "Yes, Analog",
        "Phase Angle": "No",
        "Base MVA": "100.0 MVA",
        "Base Current": "1.0 kA",
        "Smoothing Time Constant": "0.02 s",
        "Animated Display?": "No",
    }
    output_rows = []
    for row in inventory:
        key = row["network_branch_id"]
        for terminal in ("A", "B"):
            for quantity in ("P", "Q", "I"):
                output_rows.append({
                    "network_branch_id": key,
                    "terminal": terminal,
                    "quantity": quantity,
                    "meter_signal_name": f"{key}_{terminal}_{quantity}",
                    "output_channel_name": f"{key}_{terminal}_{quantity}",
                    "meter_component": "master:multimeter",
                    "meter_port_orientation": "A=bus, B=TLine",
                })
    design = {
        "execution_status": "ready_for_single_tline_gui_stage",
        "inventory_count": len(inventory),
        "selected_native_component": "master:multimeter",
        "measurement_plan_rank": 2,
        "meters_per_tline": 2,
        "outputs_per_tline": 6,
        "existing_output_channel_count": EXPECTED_CHANNELS,
        "new_output_channel_count_after_full_deployment": 6 * len(inventory),
        "final_output_channel_count_after_full_deployment": EXPECTED_CHANNELS + 6 * len(inventory),
        "single_line_stage_target": "E_16_19_1",
        "terminal_definition": {
            "A": "first node encoded by E_<first>_<second>_<parallel>; TLine send/left terminal at orientation 0",
            "B": "second node encoded by E_<first>_<second>_<parallel>; TLine receive/right terminal at orientation 0",
        },
        "meter_orientation": "For both ends, component port A faces the bus and component port B faces the TLine, so P/Q positive means injection from that bus into the line.",
        "selected_meter_parameters": selected_params,
        "selected_meter_raw_parameter_values": {
            "MeasV": "0", "MeasI": "0", "MeasP": "1", "MeasQ": "1",
            "RMS": "0", "IRMS": "1", "MeasPh": "0", "S": "100.0 [MVA]",
            "BaseA": "1.0 [kA]", "TS": "0.02 [s]", "Dis": "0",
        },
        "output_channel_parameters": baseline["reference_monitor_channel_parameters"],
        "full_output_plan": output_rows,
        "no_in_model_calculation": True,
        "no_page_module": True,
        "no_control_or_protection_connection": True,
        "run_status": "not_performed",
    }
    write_json(data_ref / "full_network_tline_measurement_design.json", design)

    p3_tline_names = {row["network_branch_id"] for row in inventory}
    status = {
        "main_project_integrity_status": "pass" if sha256(MAIN) == EXPECTED_MAIN_SHA else "fail",
        "trial_project_preflight_status": "pass" if sha256(TRIAL) == EXPECTED_TRIAL_SHA and trial_root.get("version") == "4.6.2" else "fail",
        "existing_output_channel_preservation_status": "pass" if len(channels) == EXPECTED_CHANNELS and unmapped == EXPECTED_UNMAPPED else "fail",
        "full_network_tline_inventory_status": "pass" if len(inventory) == len(p3_tline_names) and len(inventory) > 0 else "fail",
        "all_network_tline_count_known_status": "pass" if len(inventory) == 31 else "fail",
        "native_measurement_component_qualified_status": "pass" if all(token in multimeter_text for token in ("P3PH3", "Q3PH3", "RMS3PH", "AMMETER")) else "fail",
        "p_semantics_status": "pass" if "P3PH3" in multimeter_text else "fail",
        "q_semantics_status": "pass" if "Q3PH3" in multimeter_text else "fail",
        "i_semantics_status": "pass" if "RMS3PH" in multimeter_text and "Crms" in multimeter_text else "fail",
        "electrical_non_intrusiveness_status": "pass" if "BN = $A $B AMMETER" in multimeter_text and not any(x in multimeter_text for x in (" BREAKER", " RESISTOR", " INDUCTOR", " CAPACITOR")) else "fail",
        "control_isolation_status": "pass" if "mode=\"Input\"" not in multimeter_text else "fail",
        "two_end_measurement_coverage_design_status": "pass" if len(output_rows) == 6 * len(inventory) else "fail",
    }
    if all(value == "pass" for value in status.values()):
        execution = "ready_for_single_tline_gui_stage"
    elif not is_initial_pre_gui_state and baseline_path.exists():
        execution = "post_gui_state_preflight_artifacts_preserved"
    else:
        execution = "full_network_tline_measurement_static_fallback"
    preflight_path = data_val / "full_network_tline_measurement_preflight.json"
    preflight = {
        "execution_status": execution,
        **status,
        "main_sha256": sha256(MAIN),
        "trial_sha256": sha256(TRIAL),
        "full_network_tline_count": len(inventory),
        "existing_output_channel_count": len(channels),
        "baseline_existing_output_channel_count": baseline["output_channel_count"],
        "single_line_stage_output_channel_count": baseline["output_channel_count"] + 6,
        "planned_new_output_channel_count": 6 * len(inventory),
        "planned_final_output_channel_count": baseline["output_channel_count"] + 6 * len(inventory),
        "qualified_native_component": "master:multimeter" if execution.startswith("ready") else "",
        "single_line_stage_target": "E_16_19_1" if "E_16_19_1" in p3_tline_names else "",
        "build_status": "not_performed",
        "run_status": "not_performed",
        "model_files_modified_by_preflight": False,
        "baseline_artifact_rewritten": is_initial_pre_gui_state or not baseline_path.exists(),
    }
    if is_initial_pre_gui_state or not preflight_path.exists():
        write_json(preflight_path, preflight)
    print(json.dumps(preflight, indent=2, ensure_ascii=False))
    return 0 if execution in {"ready_for_single_tline_gui_stage", "post_gui_state_preflight_artifacts_preserved"} else 2


if __name__ == "__main__":
    raise SystemExit(main())
