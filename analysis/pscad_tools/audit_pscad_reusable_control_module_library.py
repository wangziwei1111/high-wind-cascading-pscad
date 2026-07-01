"""Read-only static audit for the reusable PSCAD control-module library."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import xml.etree.ElementTree as ET
from collections import Counter
from pathlib import Path


PSCAD = Path(r"C:\pscad_work\pnnl_39_3ibr_pscad46_strip5\PSCAD")
MAIN = PSCAD / "3IBR.pscx"
TRIAL = PSCAD / "3IBR_DFIG1_TRIAL.pscx"
P3F = PSCAD / "3IBR_DFIG1_TRIAL.gf46" / "P3.f"
P3DTA = P3F.with_suffix(".dta")
EXPECTED_MAIN_SHA = "CBA120BB167CB7FA6C4A1AE4471268850AB61761EC1877EB7B87015627FE9DAB"
EXPECTED_OUTPUT_CHANNEL_COUNT = 224

MODULE_SPECS = {
    "MONITORED_OBJECT_EVENT_PACKET": {
        "inputs": (
            "IN_OBJECT_OPEN_BOOL",
            "IN_OBJECT_AVAILABLE",
            "IN_ARMED",
            "IN_TIME",
        ),
        "outputs": (
            "OUT_EVENT_VALID",
            "OUT_CAUSE_CODE",
            "OUT_OBJECT_OPEN",
            "OUT_OBJECT_AVAILABLE",
            "OUT_FIRST_EVENT_TIME_S",
        ),
        "parameters": {
            "CAUSE_CODE_VALUE": "4",
            "EVENT_LATCH_INITIAL": "0",
            "FIRST_TIME_INITIAL": "-1",
        },
        "test_instance": "MODTEST_OBJECT_EVENT_PACKET",
        "minimum_components": {
            "master:import": 7,
            "master:export": 5,
            "master:mult": 3,
            "master:select": 4,
            "master:zminusone": 2,
            "master:compare": 2,
        },
    },
    "ONE_SHOT_BREAKER_OPEN_STIMULUS": {
        "inputs": ("IN_TEST_ENABLE", "IN_ARMED", "IN_TIME"),
        "outputs": ("OUT_TIME_REACHED", "OUT_OPEN_REQUEST", "OUT_BREAKER_COMMAND"),
        "parameters": {"OPEN_TIME_S": "4"},
        "test_instance": "MODTEST_ONE_SHOT_STIMULUS",
        "minimum_components": {
            "master:import": 4,
            "master:export": 3,
            "master:sumjct": 1,
            "master:compare": 1,
            "master:mult": 2,
            "master:hardlimit": 1,
        },
    },
    "TWO_EVENT_CHRONOLOGY_MONITOR": {
        "inputs": (
            "IN_EVENT_VALID_A",
            "IN_FIRST_EVENT_TIME_A_S",
            "IN_EVENT_VALID_B",
            "IN_FIRST_EVENT_TIME_B_S",
        ),
        "outputs": (
            "OUT_EVENTED_OBJECT_COUNT",
            "OUT_BOTH_EVENTS_RECORDED",
            "OUT_FIRST_EVENT_TIME_S",
            "OUT_SECOND_EVENT_TIME_S",
            "OUT_EVENT_TIME_GAP_S",
            "OUT_FIRST_EVENT_SOURCE_CODE",
            "OUT_EVENT_SEQUENCE_CODE",
            "OUT_CHRONOLOGY_CONSISTENT",
        ),
        "parameters": {},
        "test_instance": "MODTEST_TWO_EVENT_CHRONOLOGY",
        "minimum_components": {
            "master:import": 4,
            "master:export": 8,
            "master:sumjct": 9,
            "master:mult": 4,
            "master:compare": 4,
            "master:maxmin": 2,
            "master:select": 8,
            "master:gain": 2,
        },
    },
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def param_values(element: ET.Element) -> dict[str, str]:
    return {
        item.get("name", ""): item.get("value", "")
        for item in element.findall("./paramlist/param")
    }


def form_values(definition: ET.Element) -> dict[str, str]:
    values: dict[str, str] = {}
    for parameter in definition.findall("./form/category/parameter"):
        if parameter.get("name") == "Name":
            continue
        values[parameter.get("name", "")] = (parameter.findtext("value") or "").strip()
    return values


def normalized_number(value: str) -> str:
    try:
        return f"{float(value):g}"
    except ValueError:
        return value.strip()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--require-complete",
        action="store_true",
        help="Require all three reusable module definitions and harness instances.",
    )
    args = parser.parse_args()

    required_paths = (MAIN, TRIAL, P3F, P3DTA)
    missing = [str(path) for path in required_paths if not path.exists()]
    if missing:
        print(json.dumps({"execution_status": "static_audit_failed", "missing": missing}, indent=2))
        return 2

    trial_root = ET.parse(TRIAL).getroot()
    trial_xml = TRIAL.read_text(encoding="utf-8-sig")
    p3 = P3F.read_text(encoding="utf-8", errors="replace")
    dta = P3DTA.read_text(encoding="utf-8", errors="replace")
    definitions = {item.get("name", ""): item for item in trial_root.iter("Definition")}
    harness = definitions.get("MODULE_TEMPLATE_TEST_HARNESS")

    statuses: dict[str, str] = {
        "main_project_integrity_status": "pass" if sha256(MAIN) == EXPECTED_MAIN_SHA else "fail",
        "trial_xml_parse_status": "pass" if trial_root.get("version") == "4.6.2" else "fail",
        "library_page_status": "pass" if "CASCADE_CONTROL_MODULE_LIBRARY" in definitions else "fail",
        "test_harness_page_status": "pass" if harness is not None else "fail",
    }

    protected_formulas = (
        "IBR2_TRIAL_BRK_CMD = 1.0 * IBR2_TEST_CMD_LIMITED",
        "BRK_IBR2_TRIAL = 1.0 * IBR2_TRIAL_BRK_CMD",
        "IBR2_CAS_EVT_OBS = IBR2_CAS_BRK_OPEN * REAL(DFIG_LVRT_ARMED)",
        "IBR2_CAS_FIRST_S = 1.0 * IBR2_CAS_TIME_MEM",
        "CAS_COL_EVENTED_COUNT",
        "CAS_CHR_SECOND_TIME_S",
        "CAS_CHR_SEQUENCE_CODE",
        "CAS_CHR_CHRONOLOGY_CONSISTENT",
    )
    boundary_edges = re.findall(r"// 9\s+NT_8\([123]\)\s+NT_16\([123]\)", dta)
    statuses["existing_model_preservation_status"] = (
        "pass" if all(fragment in p3 for fragment in protected_formulas) and len(boundary_edges) == 3 else "fail"
    )

    output_channel_count = sum(
        user.get("defn") == "master:pgb" for user in trial_root.iter("User")
    )
    statuses["output_channel_preservation_status"] = (
        "pass" if output_channel_count == EXPECTED_OUTPUT_CHANNEL_COUNT else "fail"
    )
    forbidden = {
        "automatic_reclose": bool(re.search(r"AUTO[_ -]?RECLOSE|AUTORECLOSE", trial_xml, re.I)),
        "matlab_component": any("matlab" in (user.get("defn") or "").lower() for user in trial_root.iter("User")),
        "third_cascade_source": bool(re.search(r"CAS_(?:COL_)?(?:S3|SOURCE_?3)|IBR3_CAS", trial_xml, re.I)),
        "virtual_cascade_source": bool(re.search(r"VIRTUAL_(?:CAS|SOURCE)|CAS_VIRTUAL", trial_xml, re.I)),
    }
    statuses["forbidden_structure_absence_status"] = "pass" if not any(forbidden.values()) else "fail"

    module_results: dict[str, object] = {}
    for module_name, spec in MODULE_SPECS.items():
        definition = definitions.get(module_name)
        if definition is None:
            state = "fail" if args.require_complete or module_name == "MONITORED_OBJECT_EVENT_PACKET" else "not_applicable"
            statuses[f"{module_name.lower()}_status"] = state
            module_results[module_name] = {"present": False}
            continue

        ports = {
            port.get("name", ""): {
                "mode": port.get("mode"),
                "type": port.get("type"),
                "dim": port.get("dim"),
            }
            for port in definition.findall("./svg/port")
        }
        expected_ports = {
            **{name: {"mode": "Input", "type": "Real", "dim": "1"} for name in spec["inputs"]},
            **{name: {"mode": "Output", "type": "Real", "dim": "1"} for name in spec["outputs"]},
        }
        actual_parameters = form_values(definition)
        expected_parameters = spec["parameters"]
        parameters_ok = all(
            normalized_number(actual_parameters.get(name, "")) == normalized_number(value)
            for name, value in expected_parameters.items()
        )

        instances = []
        if harness is not None:
            for user in harness.findall("./schematic/User"):
                if user.get("defn") == f"3IBR_DFIG1_TRIAL:{module_name}":
                    values = param_values(user)
                    if values.get("Name") == spec["test_instance"]:
                        instances.append(values)
        instance_parameters_ok = bool(instances) and all(
            normalized_number(instances[0].get(name, "")) == normalized_number(value)
            for name, value in expected_parameters.items()
        )

        components = Counter(
            user.get("defn", "") for user in definition.findall("./schematic/User")
        )
        minimum_components = spec.get("minimum_components", {})
        components_ok = all(components[name] >= count for name, count in minimum_components.items())
        internal_labels = [
            param_values(user).get("Name", "")
            for user in definition.findall("./schematic/User")
            if user.get("defn") == "master:datalabel"
        ]
        label_scope_ok = not any(
            re.search(r"IBR2|DFIG|CAS_CHR|LINE_|BRK_", label, re.I)
            for label in internal_labels
        )
        passed = (
            ports == expected_ports
            and parameters_ok
            and instance_parameters_ok
            and components_ok
            and label_scope_ok
        )
        statuses[f"{module_name.lower()}_status"] = "pass" if passed else "fail"
        module_results[module_name] = {
            "present": True,
            "ports": ports,
            "parameters": actual_parameters,
            "test_instance_count": len(instances),
            "component_counts": dict(components),
            "local_label_scope_status": "pass" if label_scope_ok else "fail",
        }

    failed = [name for name, state in statuses.items() if state == "fail"]
    result = {
        "execution_status": "pscad_reusable_control_module_library_static_audit_passed" if not failed else "static_audit_failed",
        "read_only": True,
        "require_complete": args.require_complete,
        "projects": {
            "main": {"path": str(MAIN), "sha256": sha256(MAIN)},
            "trial": {"path": str(TRIAL), "sha256": sha256(TRIAL)},
        },
        "output_channel_count": output_channel_count,
        "forbidden_structures": forbidden,
        "modules": module_results,
        "statuses": statuses,
    }
    print(json.dumps(result, indent=2))
    return 0 if not failed else 2


if __name__ == "__main__":
    raise SystemExit(main())
