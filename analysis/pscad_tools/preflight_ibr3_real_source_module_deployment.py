"""Read-only gate for the IBR3 real-source and three-source collector task.

This script deliberately performs no PSCAD automation, Build, Run, or project
write.  It validates the exact trial baseline and the previously qualified
IBR3 branch fingerprint before any manual GUI work is allowed.
"""

from __future__ import annotations

import hashlib
import json
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path


PSCAD = Path(r"C:\pscad_work\pnnl_39_3ibr_pscad46_strip5\PSCAD")
MAIN = PSCAD / "3IBR.pscx"
TRIAL = PSCAD / "3IBR_DFIG1_TRIAL.pscx"
P3F = PSCAD / "3IBR_DFIG1_TRIAL.gf46" / "P3.f"
P3DTA = P3F.with_suffix(".dta")
EXPECTED_MAIN_SHA = "CBA120BB167CB7FA6C4A1AE4471268850AB61761EC1877EB7B87015627FE9DAB"
EXPECTED_TRIAL_SHA = "D56430173617DCCD16C9C9DDF3787EF7D9ADDD606EB4C9F5B8419BC290476314"
EXPECTED_OUTPUT_CHANNEL_COUNT = 224

MODULE_TESTS = {
    "MONITORED_OBJECT_EVENT_PACKET": "MODTEST_OBJECT_EVENT_PACKET",
    "ONE_SHOT_BREAKER_OPEN_STIMULUS": "MODTEST_ONE_SHOT_STIMULUS",
    "TWO_EVENT_CHRONOLOGY_MONITOR": "MODTEST_TWO_EVENT_CHRONOLOGY",
}

IBR3_LOCAL_FINGERPRINT = {
    "202861579": ("3IBR_DFIG1_TRIAL:IBR_AVM_2_1_1", "990", "1656"),
    "31436320": ("master:multimeter", "936", "1656"),
    "1076244314": ("ETRAN:Electranix_xfmr_2w", "864", "1656"),
    "1370481906": ("master:multimeter", "792", "1656"),
    "1109457673": ("master:inductor", "720", "1656"),
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


def fail_result(reason: str, **details: object) -> int:
    result = {
        "execution_status": "ibr3_real_source_static_fallback",
        "failure_reason": reason,
        **details,
    }
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 2


def main() -> int:
    missing = [str(path) for path in (MAIN, TRIAL, P3F, P3DTA) if not path.exists()]
    if missing:
        return fail_result("required_path_missing", missing=missing)

    try:
        main_root = ET.parse(MAIN).getroot()
        trial_root = ET.parse(TRIAL).getroot()
    except ET.ParseError as exc:
        return fail_result("project_xml_parse_error", error=str(exc))

    trial_text = TRIAL.read_text(encoding="utf-8-sig")
    p3f = P3F.read_text(encoding="utf-8", errors="replace")
    p3dta = P3DTA.read_text(encoding="utf-8", errors="replace")
    definitions = {item.get("name", ""): item for item in trial_root.iter("Definition")}
    p3_page = definitions.get("P3")
    harness = definitions.get("MODULE_TEMPLATE_TEST_HARNESS")
    if p3_page is None:
        return fail_result("P3_page_missing")

    users_by_id = {item.get("id", ""): item for item in p3_page.findall("./schematic/User")}
    wires_by_id = {item.get("id", ""): item for item in p3_page.findall("./schematic/Wire")}
    main_sha = sha256(MAIN)
    trial_sha = sha256(TRIAL)

    statuses: dict[str, str] = {}
    statuses["main_project_integrity_status"] = (
        "pass"
        if main_sha == EXPECTED_MAIN_SHA and main_root.get("version") == "4.6.2"
        else "fail"
    )

    output_channels = sum(
        user.get("defn") == "master:pgb" for user in trial_root.iter("User")
    )
    statuses["trial_project_status"] = (
        "pass"
        if trial_sha == EXPECTED_TRIAL_SHA
        and trial_root.get("version") == "4.6.2"
        and output_channels == EXPECTED_OUTPUT_CHANNEL_COUNT
        else "fail"
    )

    module_details: dict[str, object] = {}
    modules_ok = harness is not None and "CASCADE_CONTROL_MODULE_LIBRARY" in definitions
    for module_name, test_name in MODULE_TESTS.items():
        definition = definitions.get(module_name)
        test_instances = []
        if harness is not None:
            test_instances = [
                user
                for user in harness.findall("./schematic/User")
                if user.get("defn") == f"3IBR_DFIG1_TRIAL:{module_name}"
                and params(user).get("Name") == test_name
            ]
        ports = definition.findall("./svg/port") if definition is not None else []
        module_ok = definition is not None and bool(ports) and len(test_instances) == 1
        modules_ok = modules_ok and module_ok
        module_details[module_name] = {
            "definition_present": definition is not None,
            "port_count": len(ports),
            "test_instance": test_name,
            "test_instance_count": len(test_instances),
        }
    statuses["module_library_status"] = "pass" if modules_ok else "fail"

    candidate = users_by_id.get("202861579")
    candidate_ok = bool(
        candidate is not None
        and candidate.get("defn") == "3IBR_DFIG1_TRIAL:IBR_AVM_2_1_1"
        and candidate.get("x") == "990"
        and candidate.get("y") == "1656"
    )
    statuses["ibr3_candidate_component_status"] = "pass" if candidate_ok else "fail"

    output_names = {
        params(user).get("Name", "")
        for user in trial_root.iter("User")
        if user.get("defn") == "master:pgb"
    }
    observable_ok = {"VIBR3", "PIBR3", "QIBR3"}.issubset(output_names) and all(
        re.search(rf"\b{name}\b", p3f) for name in ("VIBR3", "PIBR3", "QIBR3")
    )
    statuses["ibr3_observable_status"] = "pass" if observable_ok else "fail"

    ibr2 = users_by_id.get("1220231535")
    distinct_ok = bool(
        candidate_ok
        and ibr2 is not None
        and ibr2.get("id") != candidate.get("id")
        and ibr2.get("y") != candidate.get("y")
        and {"VIBR2", "PIBR2", "QIBR2"}.issubset(output_names)
    )
    statuses["ibr3_distinct_branch_status"] = "pass" if distinct_ok else "fail"

    fingerprint_ok = True
    local_objects: dict[str, object] = {}
    for component_id, (definition, x, y) in IBR3_LOCAL_FINGERPRINT.items():
        user = users_by_id.get(component_id)
        ok = bool(
            user is not None
            and user.get("defn") == definition
            and user.get("x") == x
            and user.get("y") == y
        )
        fingerprint_ok = fingerprint_ok and ok
        local_objects[component_id] = {
            "present": user is not None,
            "definition": user.get("defn") if user is not None else None,
            "x": user.get("x") if user is not None else None,
            "y": user.get("y") if user is not None else None,
            "name": (params(user).get("Name") or params(user).get("NAME")) if user is not None else None,
        }

    trace_wire = wires_by_id.get("751376585")
    vertices = (
        [(vertex.get("x"), vertex.get("y")) for vertex in trace_wire.findall("./vertex")]
        if trace_wire is not None
        else []
    )
    wire_ok = bool(
        trace_wire is not None
        and trace_wire.get("classid") == "WireOrthogonal"
        and trace_wire.get("x") == "720"
        and trace_wire.get("y") == "1656"
        and vertices == [("0", "0"), ("54", "0")]
    )
    insertion_ok = fingerprint_ok and wire_ok
    statuses["ibr3_unique_series_insertion_status"] = "pass" if insertion_ok else "fail"

    local_y_wires = [
        wire
        for wire in p3_page.findall("./schematic/Wire")
        if wire.get("y") == "1656" and 650 <= int(wire.get("x", "-1")) <= 990
    ]
    no_bypass_ok = insertion_ok and len(local_y_wires) == 1
    statuses["ibr3_no_parallel_bypass_status"] = "pass" if no_bypass_ok else "fail"

    forbidden_exact = (
        "BRK_IBR3_TRIAL",
        "IBR3_TRIAL_BRK_CMD",
        "IBR3_TRIAL_BRK_STATE",
        "IBR3_TRIAL_BRK_OPEN_BOOL",
        "IBR3_TRIAL_SOURCE_AVAILABLE",
        "IBR3_TRIAL_CASCADE_EVENT_VALID",
        "IBR3_TRIAL_CASCADE_EVENT_CAUSE_CODE",
        "IBR3_TRIAL_CASCADE_EVENT_BRK_OPEN",
        "IBR3_TRIAL_CASCADE_SOURCE_AVAILABLE",
        "IBR3_TRIAL_CASCADE_FIRST_EVENT_TIME_S",
        "CASCADE3_TRIAL_EVENT_COLLECTOR",
        "BREAKER_STATE_ADAPTER",
        "THREE_SOURCE_EVENT_COLLECTOR",
    )
    exact_absent = all(token not in trial_text for token in forbidden_exact)
    structural_forbidden = {
        "automatic_reclose": bool(re.search(r"AUTO[_ -]?RECLOSE|AUTORECLOSE", trial_text, re.I)),
        "matlab_component": any(
            "matlab" in (user.get("defn") or "").lower() for user in trial_root.iter("User")
        ),
        "virtual_source": bool(re.search(r"VIRTUAL_(?:CAS|SOURCE)|CAS_VIRTUAL", trial_text, re.I)),
    }
    clean_ok = exact_absent and not any(structural_forbidden.values())
    statuses["ibr3_clean_state_status"] = "pass" if clean_ok else "fail"

    breakers = [
        user
        for user in p3_page.findall("./schematic/User")
        if user.get("defn") == "master:breaker3" and params(user).get("NAME") == "BRK_IBR2_TRIAL"
    ]
    breaker_values = params(breakers[0]) if len(breakers) == 1 else {}
    breaker_reference_ok = bool(
        len(breakers) == 1
        and breaker_values.get("Ctrl") == "0"
        and breaker_values.get("ENAB") == "0"
        and breaker_values.get("SBRA") == "IBR2_TRIAL_BRK_STATE"
        and all(breaker_values.get(name) == "2" for name in ("BOpen1", "BOpen2", "BOpen3"))
        and "BRK_IBR2_TRIAL = 1.0 * IBR2_TRIAL_BRK_CMD" in p3f
        and len(re.findall(r"// 9\s+NT_8\([123]\)\s+NT_16\([123]\)", p3dta)) == 3
    )
    statuses["breaker_semantics_reference_status"] = "pass" if breaker_reference_ok else "fail"

    armed_interfaces = [
        {
            "component_id": user.get("id"),
            "x": user.get("x"),
            "y": user.get("y"),
        }
        for user in p3_page.findall("./schematic/User")
        if user.get("defn") == "master:datalabel" and params(user).get("Name") == "DFIG_LVRT_ARMED"
    ]
    time_sources = [
        {
            "component_id": user.get("id"),
            "x": user.get("x"),
            "y": user.get("y"),
            "orient": user.get("orient"),
        }
        for user in p3_page.findall("./schematic/User")
        if user.get("defn") == "master:time-sig"
    ]
    if not armed_interfaces or not time_sources:
        statuses["breaker_semantics_reference_status"] = "fail"

    failed = [name for name, state in statuses.items() if state != "pass"]
    result = {
        "execution_status": (
            "ibr3_real_source_gui_authorized" if not failed else "ibr3_real_source_static_fallback"
        ),
        "statuses": statuses,
        "failed_statuses": failed,
        "main_sha": main_sha,
        "trial_sha": trial_sha,
        "output_channel_count": output_channels,
        "candidate": {
            "source_id": "IBR3_TRIAL",
            "candidate_component": "IBR_AVM_2_1_1_2",
            "component_id": "202861579",
            "page_path": "3IBR_DFIG1_TRIAL:Main(0):P1(0):P3(0)",
            "observables": ["VIBR3", "PIBR3", "QIBR3"],
        },
        "series_insertion_interface": {
            "description": (
                "Insert BRK_IBR3_TRIAL in series between the 0.6 kV side of "
                "transformer E_2_30_1 (id 1076244314) and the low-voltage "
                "multimeter (id 31436320) feeding IBR_AVM_2_1_1_2."
            ),
            "branch_trace_wire_id": "751376585",
            "branch_trace_wire_vertices": vertices,
            "local_objects": local_objects,
            "parallel_local_wire_count": len(local_y_wires),
        },
        "breaker_reference": {
            "definition": breakers[0].get("defn") if len(breakers) == 1 else None,
            "component_id": breakers[0].get("id") if len(breakers) == 1 else None,
            "parameters": breaker_values,
            "command_semantics": "0=closed, 1=open; command is IBR2_TRIAL_BRK_CMD",
            "state_semantics": "SBRA exports IBR2_TRIAL_BRK_STATE; >=0.5 means open",
        },
        "armed_interfaces": armed_interfaces,
        "time_sources": time_sources,
        "module_details": module_details,
        "forbidden_structure_evidence": structural_forbidden,
        "limitations": [
            "Static XML/generated-code evidence only; no PSCAD Build or Run was performed.",
            "The branch gate proves the unchanged qualified local fingerprint, not EMT behavior.",
        ],
    }
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0 if not failed else 2


if __name__ == "__main__":
    sys.exit(main())
