"""Read-only preflight for the reusable PSCAD control-module library."""

from __future__ import annotations

import hashlib
import json
import re
import xml.etree.ElementTree as ET
from pathlib import Path


PSCAD = Path(r"C:\pscad_work\pnnl_39_3ibr_pscad46_strip5\PSCAD")
MAIN = PSCAD / "3IBR.pscx"
TRIAL = PSCAD / "3IBR_DFIG1_TRIAL.pscx"
P3F = PSCAD / "3IBR_DFIG1_TRIAL.gf46" / "P3.f"
P3DTA = P3F.with_suffix(".dta")
PSCAD46 = Path(r"C:\Program Files (x86)\PSCAD46")
WIZARD_HELP = PSCAD46 / "Forms" / "wizardhelp.htm"
WIZARD_DLL = PSCAD46 / "bin" / "win64" / "ComponentWizard.dll"
EXPECTED_MAIN_SHA = "CBA120BB167CB7FA6C4A1AE4471268850AB61761EC1877EB7B87015627FE9DAB"
EXPECTED_TRIAL_SHA = "EFE2FA9D537653C34C13C0223C2E48EE15A77788EAE35A1CC173364AA52D2959"
NEW_DEFINITIONS = (
    "MONITORED_OBJECT_EVENT_PACKET",
    "ONE_SHOT_BREAKER_OPEN_STIMULUS",
    "TWO_EVENT_CHRONOLOGY_MONITOR",
)
NEW_HARNESS_INSTANCES = (
    "MODTEST_OBJECT_EVENT_PACKET",
    "MODTEST_ONE_SHOT_STIMULUS",
    "MODTEST_TWO_EVENT_CHRONOLOGY",
)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def parameters(element: ET.Element) -> dict[str, str]:
    return {p.get("name", ""): p.get("value", "") for p in element.findall(".//param")}


def main() -> int:
    required = [MAIN, TRIAL, P3F, P3DTA, WIZARD_HELP, WIZARD_DLL]
    missing = [str(path) for path in required if not path.exists()]
    if missing:
        print(json.dumps({"execution_status": "pscad_module_library_static_fallback", "missing": missing}, indent=2))
        return 2

    main_root = ET.parse(MAIN).getroot()
    trial_root = ET.parse(TRIAL).getroot()
    trial_xml = TRIAL.read_text(encoding="utf-8", errors="replace")
    p3 = P3F.read_text(encoding="utf-8", errors="replace")
    dta = P3DTA.read_text(encoding="utf-8", errors="replace")
    wizard = WIZARD_HELP.read_text(encoding="utf-8", errors="replace")

    definitions = list(trial_root.findall(".//Definition"))
    definition_names = {definition.get("name", "") for definition in definitions}
    definition_capability = []
    for definition in definitions:
        imports = [u for u in definition.iter("User") if u.get("defn") == "master:import"]
        exports = [u for u in definition.iter("User") if u.get("defn") == "master:export"]
        form_parameters = list(definition.findall(".//form//parameter"))
        if imports and exports:
            definition_capability.append({
                "name": definition.get("name"),
                "classid": definition.get("classid"),
                "instances": definition.get("instances"),
                "import_count": len(imports),
                "export_count": len(exports),
                "form_parameter_count": len(form_parameters),
            })

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
    output_channels = [
        parameters(user).get("Name", "")
        for user in trial_root.iter("User")
        if user.get("defn") == "master:pgb"
    ]
    new_tokens_absent = {
        token: token not in trial_xml
        for token in NEW_DEFINITIONS + NEW_HARNESS_INSTANCES + (
            "CASCADE CONTROL MODULE LIBRARY",
            "MODULE TEMPLATE TEST HARNESS",
        )
    }
    wizard_capability = {
        "user_component": "User Component" in wizard,
        "page_module": "Page Module" in wizard,
        "add_ports": "Add Ports" in wizard,
        "component_wizard_entry": "Create...</span>" in wizard and "Component, TLine or Cable" in wizard,
        "definition_only_mechanism": "Module Definition" in wizard or "Module Definiton" in wizard,
    }
    forbidden = {
        "automatic_reclose": bool(re.search(r"AUTO[_ -]?RECLOSE|AUTORECLOSE", trial_xml, re.I)),
        "matlab_component": any("matlab" in (u.get("defn") or "").lower() for u in trial_root.iter("User")),
        "third_cascade_source": bool(re.search(r"CAS_(?:COL_)?(?:S3|SOURCE_?3)|IBR3_CAS", trial_xml, re.I)),
        "virtual_cascade_source": bool(re.search(r"VIRTUAL_(?:CAS|SOURCE)|CAS_VIRTUAL", trial_xml, re.I)),
    }

    statuses = {
        "project_paths_distinct_status": "pass" if MAIN.resolve() != TRIAL.resolve() else "fail",
        "main_project_integrity_status": "pass" if sha256(MAIN) == EXPECTED_MAIN_SHA else "fail",
        "trial_start_integrity_status": "pass" if sha256(TRIAL) == EXPECTED_TRIAL_SHA else "fail",
        "trial_xml_parse_status": "pass" if trial_root.get("version") == "4.6.2" else "fail",
        "existing_model_preservation_status": "pass" if all(fragment in p3 for fragment in protected_formulas) and len(boundary_edges) == 3 else "fail",
        "native_definition_mechanism_status": "pass" if definition_capability else "fail",
        "native_port_mechanism_status": "pass" if any(item["import_count"] and item["export_count"] for item in definition_capability) else "fail",
        "native_parameter_form_status": "pass" if any(item["form_parameter_count"] for item in definition_capability) else "fail",
        "component_wizard_capability_status": "pass" if all(wizard_capability.values()) else "fail",
        "new_library_clean_state_status": "pass" if all(new_tokens_absent.values()) else "fail",
        "forbidden_structure_absence_status": "pass" if not any(forbidden.values()) else "fail",
    }
    passed = all(value == "pass" for value in statuses.values())
    result = {
        "execution_status": "pscad_reusable_control_module_library_preflight_passed" if passed else "pscad_module_library_static_fallback",
        "read_only": True,
        "projects": {
            "main": {"path": str(MAIN), "sha256": sha256(MAIN)},
            "trial": {"path": str(TRIAL), "sha256": sha256(TRIAL), "version": trial_root.get("version")},
        },
        "native_definition_evidence": definition_capability,
        "wizard_evidence": {
            "help_path": str(WIZARD_HELP),
            "dll_path": str(WIZARD_DLL),
            "checks": wizard_capability,
            "gui_path": "Workspace -> trial project -> Definitions -> Component Wizard... -> Component tab -> Module",
            "definition_edit_path": "Workspace -> project -> Definitions -> definition -> right-click Edit, or instance -> right-click Edit Definition",
            "instance_path": "Workspace -> Definitions -> definition -> Copy, then Paste on target module canvas",
        },
        "baseline": {
            "definition_count": len(definitions),
            "output_channel_count": len(output_channels),
            "output_channel_titles": output_channels,
            "new_tokens_absent": new_tokens_absent,
            "forbidden_structures": forbidden,
        },
        "statuses": statuses,
    }
    print(json.dumps(result, indent=2))
    return 0 if passed else 2


if __name__ == "__main__":
    raise SystemExit(main())
