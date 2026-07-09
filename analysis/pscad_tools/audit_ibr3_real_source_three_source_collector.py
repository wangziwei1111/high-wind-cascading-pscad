"""Final read-only audit for the IBR3 real-source three-source collector task.

The audit parses PSCAD XML and already-generated Fortran/network files.  It
does not write either PSCAD project, invoke Build, or execute the model.
"""

from __future__ import annotations

import hashlib
import json
import re
import sys
import xml.etree.ElementTree as ET
from copy import deepcopy
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
PSCAD = Path(r"C:\pscad_work\pnnl_39_3ibr_pscad46_strip5\PSCAD")
MAIN = PSCAD / "3IBR.pscx"
TRIAL = PSCAD / "3IBR_DFIG1_TRIAL.pscx"
P3F = PSCAD / "3IBR_DFIG1_TRIAL.gf46" / "P3.f"
P3DTA = P3F.with_suffix(".dta")
BACKUP = Path(
    r"C:\pscad_work\backups\ibr3_real_source_three_source_collector_20260701_162217"
)
BACKUP_MAIN = BACKUP / "3IBR.pscx"
BACKUP_TRIAL = BACKUP / "3IBR_DFIG1_TRIAL.pscx"
SNAPSHOT = (
    ROOT
    / "external"
    / "pscad_snapshot_20260701_ibr3_real_source_three_source_collector_static"
    / "pnnl_39_3ibr_pscad46_strip5_PSCAD"
    / "3IBR_DFIG1_TRIAL.pscx"
)

EXPECTED_MAIN_SHA = "CBA120BB167CB7FA6C4A1AE4471268850AB61761EC1877EB7B87015627FE9DAB"
EXPECTED_START_TRIAL_SHA = "D56430173617DCCD16C9C9DDF3787EF7D9ADDD606EB4C9F5B8419BC290476314"

PROTECTED_MODULES = (
    "MONITORED_OBJECT_EVENT_PACKET",
    "ONE_SHOT_BREAKER_OPEN_STIMULUS",
    "TWO_EVENT_CHRONOLOGY_MONITOR",
)

ADAPTER_PORTS = {
    "IN_BREAKER_STATE": "Input",
    "OUT_BREAKER_OPEN_BOOL": "Output",
    "OUT_SOURCE_AVAILABLE": "Output",
}

COLLECTOR_INPUTS = tuple(
    name
    for source in "ABC"
    for name in (
        f"IN_EVENT_VALID_{source}",
        f"IN_BREAKER_OPEN_{source}",
        f"IN_SOURCE_AVAILABLE_{source}",
        f"IN_FIRST_EVENT_TIME_{source}_S",
        f"IN_CAUSE_CODE_{source}",
    )
)
COLLECTOR_OUTPUTS = (
    "OUT_ANY_EVENT_VALID",
    "OUT_ANY_BREAKER_OPEN",
    "OUT_AVAILABLE_SOURCE_COUNT",
    "OUT_EVENTED_SOURCE_COUNT",
    "OUT_FIRST_EVENT_TIME_S",
    "OUT_FIRST_EVENT_SOURCE_CODE",
    "OUT_CAUSE_CODE_A",
    "OUT_CAUSE_CODE_B",
    "OUT_CAUSE_CODE_C",
)

NEW_CHANNELS = {
    "IBR3_TRIAL_BRK_CMD": ("0", "1.2"),
    "IBR3_TRIAL_BRK_STATE": ("0", "2.2"),
    "IBR3_TRIAL_BRK_OPEN_BOOL": ("0", "1.2"),
    "IBR3_TRIAL_SOURCE_AVAILABLE": ("0", "1.2"),
    "IBR3_TRIAL_TEST_ENABLE": ("0", "1.2"),
    "IBR3_TRIAL_TEST_OPEN_TIME_S": ("0", "10.2"),
    "IBR3_TRIAL_TEST_OPEN_REQUEST": ("0", "1.2"),
    "IBR3_TRIAL_CASCADE_EVENT_VALID": ("0", "1.2"),
    "IBR3_TRIAL_CASCADE_EVENT_CAUSE_CODE": ("0", "5.2"),
    "IBR3_TRIAL_CASCADE_EVENT_BRK_OPEN": ("0", "1.2"),
    "IBR3_TRIAL_CASCADE_SOURCE_AVAILABLE": ("0", "1.2"),
    "IBR3_TRIAL_CASCADE_FIRST_EVENT_TIME_S": ("-1.2", "10.2"),
    "CASCADE3_MONITOR_ANY_TRIP": ("0", "1.2"),
    "CASCADE3_MONITOR_ANY_BRK_OPEN": ("0", "1.2"),
    "CASCADE3_MONITOR_AVAILABLE_SOURCE_COUNT": ("0", "3.2"),
    "CASCADE3_MONITOR_EVENTED_SOURCE_COUNT": ("0", "3.2"),
    "CASCADE3_MONITOR_FIRST_EVENT_TIME_S": ("-1.2", "10.2"),
    "CASCADE3_MONITOR_FIRST_EVENT_SOURCE_CODE": ("0", "4.2"),
    "CASCADE3_MONITOR_CAUSE_CODE_DFIG1": ("0", "3.2"),
    "CASCADE3_MONITOR_CAUSE_CODE_IBR2_TRIAL": ("0", "4.2"),
    "CASCADE3_MONITOR_CAUSE_CODE_IBR3_TRIAL": ("0", "5.2"),
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def params(element: ET.Element) -> dict[str, str]:
    return {
        item.get("name", ""): item.get("value", "")
        for item in element.findall("./paramlist/param")
    }


def form_values(definition: ET.Element) -> dict[str, str]:
    return {
        parameter.get("name", ""): (parameter.findtext("value") or "").strip()
        for parameter in definition.findall("./form/category/parameter")
    }


def normalized_xml(element: ET.Element) -> bytes:
    copy = deepcopy(element)
    copy.attrib.pop("date", None)
    return ET.tostring(copy, encoding="utf-8")


def compact_fortran(text: str) -> str:
    return re.sub(r"&\s*\n\s*&?", "", text)


def pgb_map(root: ET.Element) -> dict[str, tuple[str, dict[str, str]]]:
    return {
        user.get("id", ""): (params(user).get("Name", ""), params(user))
        for user in root.iter("User")
        if user.get("defn") == "master:pgb"
    }


def instance(
    page: ET.Element, definition_name: str, instance_name: str
) -> list[ET.Element]:
    return [
        user
        for user in page.findall("./schematic/User")
        if user.get("defn") == f"3IBR_DFIG1_TRIAL:{definition_name}"
        and params(user).get("Name") == instance_name
    ]


def main() -> int:
    required = (MAIN, TRIAL, P3F, P3DTA, BACKUP_MAIN, BACKUP_TRIAL, SNAPSHOT)
    missing = [str(path) for path in required if not path.exists()]
    if missing:
        print(json.dumps({"execution_status": "static_audit_failed", "missing": missing}, indent=2))
        return 2

    main_root = ET.parse(MAIN).getroot()
    trial_root = ET.parse(TRIAL).getroot()
    backup_root = ET.parse(BACKUP_TRIAL).getroot()
    snapshot_root = ET.parse(SNAPSHOT).getroot()
    p3f = P3F.read_text(encoding="utf-8", errors="replace")
    p3dta = P3DTA.read_text(encoding="utf-8", errors="replace")
    trial_text = TRIAL.read_text(encoding="utf-8-sig")
    definitions = {item.get("name", ""): item for item in trial_root.iter("Definition")}
    backup_definitions = {
        item.get("name", ""): item for item in backup_root.iter("Definition")
    }
    p3 = definitions["P3"]
    harness = definitions["MODULE_TEMPLATE_TEST_HARNESS"]

    main_sha = sha256(MAIN)
    trial_sha = sha256(TRIAL)
    snapshot_sha = sha256(SNAPSHOT)
    backup_main_sha = sha256(BACKUP_MAIN)
    backup_trial_sha = sha256(BACKUP_TRIAL)

    statuses: dict[str, str] = {}
    statuses["main_project_integrity_status"] = (
        "pass"
        if main_sha == EXPECTED_MAIN_SHA == backup_main_sha
        and main_root.get("version") == "4.6.2"
        else "fail"
    )
    statuses["trial_project_status"] = (
        "pass"
        if backup_trial_sha == EXPECTED_START_TRIAL_SHA
        and trial_root.get("version") == "4.6.2"
        and snapshot_sha == trial_sha
        and snapshot_root.get("version") == "4.6.2"
        else "fail"
    )

    protected_unchanged = all(
        name in definitions
        and name in backup_definitions
        and normalized_xml(definitions[name]) == normalized_xml(backup_definitions[name])
        for name in PROTECTED_MODULES
    )
    statuses["protected_module_library_status"] = "pass" if protected_unchanged else "fail"

    adapter = definitions.get("BREAKER_STATE_ADAPTER")
    collector = definitions.get("THREE_SOURCE_EVENT_COLLECTOR")
    all_modules_present = all(
        name in definitions
        for name in (*PROTECTED_MODULES, "BREAKER_STATE_ADAPTER", "THREE_SOURCE_EVENT_COLLECTOR")
    )
    statuses["module_library_phase2_status"] = "pass" if all_modules_present else "fail"

    adapter_ports = (
        {
            port.get("name", ""): port.get("mode", "")
            for port in adapter.findall("./svg/port")
        }
        if adapter is not None
        else {}
    )
    adapter_forms = form_values(adapter) if adapter is not None else {}
    adapter_test = instance(
        harness, "BREAKER_STATE_ADAPTER", "MODTEST_BREAKER_STATE_ADAPTER"
    )
    adapter_f = (PSCAD / "3IBR_DFIG1_TRIAL.gf46" / "BREAKER_STATE_ADAPTER.f").read_text(
        encoding="utf-8", errors="replace"
    )
    adapter_ok = bool(
        adapter_ports == ADAPTER_PORTS
        and adapter_forms.get("OPEN_THRESHOLD") == "0.5"
        and len(adapter_test) == 1
        and "RT_1 = + IN_BREAKER_STATE - OPEN_THRESHOLD" in adapter_f
        and "OUT_BREAKER_OPEN_BOOL = REAL(IT_1)" in adapter_f
        and "OUT_SOURCE_AVAILABLE = REAL(IT_2)" in adapter_f
    )
    statuses["breaker_state_adapter_status"] = "pass" if adapter_ok else "fail"

    collector_ports = (
        {
            port.get("name", ""): (port.get("mode", ""), port.get("type", ""), port.get("dim", ""))
            for port in collector.findall("./svg/port")
        }
        if collector is not None
        else {}
    )
    expected_collector_ports = {
        **{name: ("Input", "Real", "1") for name in COLLECTOR_INPUTS},
        **{name: ("Output", "Real", "1") for name in COLLECTOR_OUTPUTS},
    }
    collector_test = instance(
        harness, "THREE_SOURCE_EVENT_COLLECTOR", "MODTEST_THREE_SOURCE_EVENT_COLLECTOR"
    )
    collector_f = (
        PSCAD / "3IBR_DFIG1_TRIAL.gf46" / "THREE_SOURCE_EVENT_COLLECTOR.f"
    ).read_text(encoding="utf-8", errors="replace")
    collector_f_compact = compact_fortran(collector_f)
    collector_formula_fragments = (
        "RT_1 = + IN_EVENT_VALID_A + IN_EVENT_VALID_B + IN_EVENT_VALID_C",
        "RT_2 = + IN_BREAKER_OPEN_A + IN_BREAKER_OPEN_B + IN_BREAKER_OPEN_C",
        "RT_3 = + IN_SOURCE_AVAILABLE_A + IN_SOURCE_AVAILABLE_B + IN_SOURCE_AVAILABLE_C",
        "RT_4 = + IN_EVENT_VALID_A + IN_EVENT_VALID_B + IN_EVENT_VALID_C",
        "MIN_AB = AMIN1(A_FIRST_TIME_LOCAL,B_FIRST_TIME_LOCAL)",
        "MIN_ABC_RAW = AMIN1(FIRST_AB,C_FIRST_TIME_LOCAL)",
        "UNIQUE_SOURCE_CODE = + RT_12 + RT_13 + RT_14",
        "OUT_FIRST_EVENT_SOURCE_CODE = RT_18",
        "OUT_FIRST_EVENT_TIME_S = FIRST_ABC",
    )
    collector_template_ok = bool(
        collector_ports == expected_collector_ports
        and len(collector_test) == 1
        and all(fragment in collector_f_compact for fragment in collector_formula_fragments)
    )
    statuses["three_source_collector_template_status"] = (
        "pass" if collector_template_ok else "fail"
    )

    scoped_labels = []
    for definition in (adapter, collector):
        if definition is not None:
            scoped_labels.extend(
                params(user).get("Name", "")
                for user in definition.findall("./schematic/User")
                if user.get("defn") == "master:datalabel"
            )
    scope_ok = not any(
        re.search(r"IBR2|IBR3|DFIG|LINE_[0-9]|BRK_IBR|CAS_CHR", label, re.I)
        for label in scoped_labels
    )
    statuses["module_scope_isolation_status"] = "pass" if scope_ok else "fail"

    users_by_id = {user.get("id", ""): user for user in p3.findall("./schematic/User")}
    candidate = users_by_id.get("202861579")
    channel_names = {name for name, _ in pgb_map(trial_root).values()}
    candidate_ok = bool(
        candidate is not None
        and candidate.get("defn") == "3IBR_DFIG1_TRIAL:IBR_AVM_2_1_1"
        and {"VIBR3", "PIBR3", "QIBR3"}.issubset(channel_names)
    )
    statuses["ibr3_candidate_status"] = "pass" if candidate_ok else "fail"

    breaker = [
        user
        for user in p3.findall("./schematic/User")
        if user.get("defn") == "master:breaker3"
        and params(user).get("NAME") == "BRK_IBR3_TRIAL"
    ]
    breaker_params = params(breaker[0]) if len(breaker) == 1 else {}
    boundary_ok = bool(
        len(breaker) == 1
        and breaker[0].get("x") == "954"
        and breaker[0].get("y") == "1656"
        and breaker_params.get("Ctrl") == "0"
        and breaker_params.get("ENAB") == "0"
        and breaker_params.get("SBRA") == "IBR3_TRIAL_BRK_STATE"
        and all(breaker_params.get(key) == "2" for key in ("BOpen1", "BOpen2", "BOpen3"))
        and "3 Phase Breaker 'BRK_IBR3_TRIAL'" in p3f
        and "IBR3_TRIAL_BRK_STATE = IVD1_1" in p3f
    )
    statuses["ibr3_local_breaker_boundary_status"] = "pass" if boundary_ok else "fail"

    local_wires = [
        wire
        for wire in p3.findall("./schematic/Wire")
        if wire.get("y") == "1656" and 900 <= int(wire.get("x", "-1")) <= 1100
    ]
    no_bypass = boundary_ok and not local_wires
    statuses["ibr3_no_parallel_bypass_status"] = "pass" if no_bypass else "fail"

    stimulus = instance(p3, "ONE_SHOT_BREAKER_OPEN_STIMULUS", "IBR3_TRIAL__OPEN_STIMULUS")
    stimulus_ok = bool(
        len(stimulus) == 1
        and params(stimulus[0]).get("OPEN_TIME_S") in {"5", "5.0"}
        and "IBR3_TRIAL__OPEN_STIMULUS" in p3f
        and "REAL(DFIG_LVRT_ARMED), IBR3_TEST_ENABLE, 5.0" in p3f.replace("&\n     &", "")
    )
    statuses["ibr3_open_stimulus_status"] = "pass" if stimulus_ok else "fail"
    default_command_ok = bool(
        "IBR3_TEST_ENABLE = 0.0" in p3f
        and "BRK_IBR3_TRIAL = 1.0 * IBR3_TRIAL_BRK_CMD" in p3f
    )
    statuses["ibr3_default_closed_command_status"] = (
        "pass" if default_command_ok else "fail"
    )

    state_adapter = instance(
        p3, "BREAKER_STATE_ADAPTER", "IBR3_TRIAL__BREAKER_STATE_ADAPTER"
    )
    state_ok = bool(
        len(state_adapter) == 1
        and params(state_adapter[0]).get("OPEN_THRESHOLD") == "0.5"
        and "CALL BREAKER_STATE_ADAPTERDyn(IBR3_TRIAL_SOURCE_AVAILABLE, IBR3_TR" in p3f
        and "IAL_BRK_OPEN_BOOL, REAL(IBR3_TRIAL_BRK_STATE), 0.5)" in p3f
    )
    statuses["ibr3_state_adapter_status"] = "pass" if state_ok else "fail"

    packet = instance(p3, "MONITORED_OBJECT_EVENT_PACKET", "IBR3_TRIAL__EVENT_PACKET")
    packet_ok = bool(
        len(packet) == 1
        and params(packet[0]).get("CAUSE_CODE_VALUE") == "5"
        and params(packet[0]).get("EVENT_LATCH_INITIAL") == "0"
        and params(packet[0]).get("FIRST_TIME_INITIAL") == "-1"
        and "IBR3_TRIAL__EVENT_PACKET" in p3f
        and "IBR3_TRIAL_SOURCE_AVAILABLE, IBR3_TRIAL_BR" in p3f
        and "K_OPEN_BOOL, 5.0, 0.0, -1.0" in p3f
    )
    statuses["ibr3_event_packet_status"] = "pass" if packet_ok else "fail"

    collector_instance = instance(
        p3, "THREE_SOURCE_EVENT_COLLECTOR", "CASCADE3_TRIAL__EVENT_COLLECTOR"
    )
    expected_call_fragments = (
        "CASCADE3_TRIAL__EVENT_COLLECTOR",
        "IBR3_CAS_CAUSE",
        "IBR2_CAS_CAUSE",
        "DFIG_LVRT_CAS_CAUSE_CODE",
        "IBR3_CAS_EVT_VALID",
        "IBR2_CAS_EVT_VALID",
        "DFIG_LVRT_CASCADE_EVENT_VALID",
    )
    collector_instance_ok = len(collector_instance) == 1 and all(
        fragment in p3f for fragment in expected_call_fragments
    )
    statuses["three_source_collector_instance_status"] = (
        "pass" if collector_instance_ok else "fail"
    )
    statuses["three_source_collector_logic_status"] = (
        "pass" if collector_template_ok and collector_instance_ok else "fail"
    )

    current_pgbs = pgb_map(trial_root)
    backup_pgbs = pgb_map(backup_root)
    by_name = Counter(name for name, _ in current_pgbs.values())
    old_preserved = all(
        component_id in current_pgbs and current_pgbs[component_id][1] == values[1]
        for component_id, values in backup_pgbs.items()
    )
    new_channels_ok = all(
        by_name[name] == 1
        and next(values for channel, values in current_pgbs.values() if channel == name).get("Min") == minimum
        and next(values for channel, values in current_pgbs.values() if channel == name).get("Max") == maximum
        and next(values for channel, values in current_pgbs.values() if channel == name).get("enab") == "1"
        and next(values for channel, values in current_pgbs.values() if channel == name).get("mrun") == "1"
        and next(values for channel, values in current_pgbs.values() if channel == name).get("Scale") == "1.0"
        and next(values for channel, values in current_pgbs.values() if channel == name).get("UseSignalName") == "0"
        for name, (minimum, maximum) in NEW_CHANNELS.items()
    )
    output_ok = len(current_pgbs) == 245 and len(backup_pgbs) == 224 and old_preserved and new_channels_ok
    statuses["output_channel_status"] = "pass" if output_ok else "fail"

    protected_assignments = (
        "DFIG_LVRT_TRIP_REQUEST",
        "DFIG_LVRT_TRIP_LATCH",
        "DFIG_LVRT_CLEAR",
        "DFIG_LVRT_FINAL_BRK_CMD",
        "BRK_DFIG",
    )
    feedback = []
    for signal in protected_assignments:
        for line in re.findall(rf"^\s*{re.escape(signal)}\s*=.*$", p3f, re.M):
            if re.search(r"IBR3_|\bC3_", line):
                feedback.append(line.strip())
    forbidden_structures = {
        "global_cause": bool(re.search(r"C3_(?:GLOBAL|TOTAL|CAUSE_SUM)|CASCADE3.*CAUSE_SUM", trial_text, re.I)),
        "fourth_source": bool(re.search(r"IN_EVENT_VALID_D|SOURCE_4|SOURCE_D", trial_text, re.I)),
        "virtual_source": bool(re.search(r"VIRTUAL_(?:CAS|SOURCE)|CAS_VIRTUAL", trial_text, re.I)),
        "automatic_reclose": bool(re.search(r"AUTO[_ -]?RECLOSE|AUTORECLOSE", trial_text, re.I)),
        "matlab": any("matlab" in (user.get("defn") or "").lower() for user in trial_root.iter("User")),
    }
    isolation_ok = not feedback and not any(forbidden_structures.values())
    statuses["control_path_isolation_status"] = "pass" if isolation_ok else "fail"

    statuses["dynamic_behavior_status"] = "unavailable"
    statuses["third_source_dynamic_behavior_status"] = "unavailable"
    statuses["three_source_dynamic_behavior_status"] = "unavailable"
    statuses["cascade_propagation_status"] = "unavailable"
    statuses["matlab_status"] = "not_added"

    required_pass = [
        name
        for name in statuses
        if name not in {
            "dynamic_behavior_status",
            "third_source_dynamic_behavior_status",
            "three_source_dynamic_behavior_status",
            "cascade_propagation_status",
            "matlab_status",
        }
    ]
    failed = [name for name in required_pass if statuses[name] != "pass"]
    result = {
        "execution_status": (
            "ibr3_real_source_three_source_collector_static_pass"
            if not failed
            else "ibr3_real_source_static_fallback"
        ),
        **statuses,
        "failed_statuses": failed,
        "hashes": {
            "main_start": backup_main_sha,
            "main_final": main_sha,
            "trial_start": backup_trial_sha,
            "trial_final": trial_sha,
            "snapshot": snapshot_sha,
        },
        "counts": {
            "protected_output_channels": len(backup_pgbs),
            "new_output_channels": len(NEW_CHANNELS),
            "final_output_channels": len(current_pgbs),
        },
        "ibr3_candidate": {
            "source_id": "IBR3_TRIAL",
            "component": "IBR_AVM_2_1_1_2",
            "component_id": "202861579",
            "observables": ["VIBR3", "PIBR3", "QIBR3"],
            "breaker": "BRK_IBR3_TRIAL",
            "breaker_component_id": breaker[0].get("id") if len(breaker) == 1 else None,
        },
        "source_mapping": {
            "A": [
                "DFIG_LVRT_CASCADE_EVENT_VALID",
                "DFIG_LVRT_CASCADE_EVENT_BRK_OPEN",
                "DFIG_LVRT_CAS_SRC_AVAIL",
                "DFIG_LVRT_CAS_FIRST_TIME_S",
                "DFIG_LVRT_CAS_CAUSE_CODE",
            ],
            "B": [
                "IBR2_CAS_EVT_VALID",
                "IBR2_CAS_BRK_OPEN",
                "IBR2_CAS_AVAIL",
                "IBR2_CAS_FIRST_S",
                "IBR2_CAS_CAUSE",
            ],
            "C": [
                "IBR3_CAS_EVT_VALID",
                "IBR3_CAS_BRK_OPEN",
                "IBR3_CAS_AVAIL",
                "IBR3_CAS_FIRST_S",
                "IBR3_CAS_CAUSE",
            ],
        },
        "forbidden_structure_evidence": forbidden_structures,
        "feedback_evidence": feedback,
        "limitations": [
            "Read-only static audit of PSCAD XML and generated files.",
            "No PSCAD Run was performed.",
            "No dynamic opening, isolation, three-source interaction, or causal cascade propagation was validated.",
        ],
    }
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0 if not failed else 2


if __name__ == "__main__":
    sys.exit(main())
