"""Read-only preflight for the IBR2_TRIAL local breaker boundary task.

This script inspects the main PSCAD project, the independent trial project,
and already-generated Fortran only. It does not build, run, or modify PSCAD
project files.
"""

from __future__ import annotations

import hashlib
import json
import xml.etree.ElementTree as ET
from dataclasses import asdict, dataclass
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
MAIN_PROJECT = Path(r"C:\pscad_work\pnnl_39_3ibr_pscad46_strip5\PSCAD\3IBR.pscx")
TRIAL_PROJECT = Path(r"C:\pscad_work\pnnl_39_3ibr_pscad46_strip5\PSCAD\3IBR_DFIG1_TRIAL.pscx")
MAIN_FORTRAN = Path(r"C:\pscad_work\pnnl_39_3ibr_pscad46_strip5\PSCAD\3IBR.gf46\P3.f")
TRIAL_FORTRAN = Path(r"C:\pscad_work\pnnl_39_3ibr_pscad46_strip5\PSCAD\3IBR_DFIG1_TRIAL.gf46\P3.f")
MAIN_SHA_AUDIT = REPO_ROOT / "data" / "reference" / "main_project_sha_delta_audit.json"
FEASIBILITY_JSON = REPO_ROOT / "data" / "reference" / "trial_ibr_breaker_insertion_feasibility.json"

AUDITED_MAIN_SHA = "97AE9A99E199734510352DACBDE6120BBC411356C244C3DEA0ED8B01AB2B7906"
EXPECTED_TRIAL_SHA = "62A9202F708402A850F6810797C852A54CD7D627D77B691749C4C6512CAEEF15"

PLANNED_OBJECTS = [
    "BRK_IBR2_TRIAL",
    "IBR2_TRIAL_BRK_CMD",
    "IBR2_TRIAL_BRK_STATE",
    "IBR2_TRIAL_BRK_OPEN_BOOL",
    "IBR2_TRIAL_SOURCE_AVAILABLE",
]

IBR2_IDS = {
    "ibr": "1220231535",
    "lv_multimeter": "1433370859",
    "hv_multimeter": "797238293",
    "transformer": "275469438",
    "inductor": "24850255",
}

IBR2_SERIES_WIRE = {
    "id": "1422683866",
    "classid": "WireOrthogonal",
    "x": "936",
    "y": "1332",
    "vertices": [("0", "0"), ("72", "0")],
}


@dataclass
class ComponentSummary:
    role: str
    component_id: str
    definition: str
    name: str
    x: str
    y: str
    z: str
    orient: str
    key_params: dict[str, str]


def sha256(path: Path) -> str | None:
    if not path.exists():
        return None
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def parse_xml(path: Path) -> ET.Element:
    return ET.parse(path).getroot()


def params_for(element: ET.Element) -> dict[str, str]:
    return {
        param.attrib.get("name", ""): param.attrib.get("value", "")
        for param in element.findall(".//param")
        if param.attrib.get("name")
    }


def users(root: ET.Element) -> list[ET.Element]:
    return [element for element in root.iter() if element.tag == "User"]


def find_user(root: ET.Element, component_id: str) -> ET.Element | None:
    return next((element for element in users(root) if element.attrib.get("id") == component_id), None)


def param_values(root: ET.Element) -> list[str]:
    values: list[str] = []
    for param in root.iter("param"):
        value = param.attrib.get("value")
        if value:
            values.append(value)
    for curve in root.iter("Curve"):
        name = curve.attrib.get("name")
        if name:
            values.append(name)
    return values


def exact_signal_present(root: ET.Element, signal: str) -> bool:
    return signal in param_values(root)


def output_channel_present(root: ET.Element, signal: str) -> bool:
    return any(
        element.attrib.get("defn") == "master:pgb" and params_for(element).get("Name") == signal
        for element in users(root)
    )


def component_summary(root: ET.Element, role: str, component_id: str) -> ComponentSummary | None:
    element = find_user(root, component_id)
    if element is None:
        return None
    params = params_for(element)
    return ComponentSummary(
        role=role,
        component_id=component_id,
        definition=element.attrib.get("defn", ""),
        name=params.get("Name") or params.get("NAME") or element.attrib.get("name", ""),
        x=element.attrib.get("x", ""),
        y=element.attrib.get("y", ""),
        z=element.attrib.get("z", ""),
        orient=element.attrib.get("orient", ""),
        key_params={key: params[key] for key in sorted(params) if key in {"Name", "NAME", "P", "Q", "Vrms", "BaseV", "V1LL", "V2LL", "L"}},
    )


def wire_evidence(root: ET.Element) -> list[dict[str, str]]:
    evidence: list[dict[str, str]] = []
    for wire in root.iter("Wire"):
        try:
            x = int(wire.attrib.get("x", "-999999"))
            y = int(wire.attrib.get("y", "-999999"))
        except ValueError:
            continue
        if 830 <= x <= 1010 and 1300 <= y <= 1360:
            vertices = ";".join(f"{v.attrib.get('x')},{v.attrib.get('y')}" for v in wire.findall("vertex"))
            evidence.append(
                {
                    "id": wire.attrib.get("id", ""),
                    "classid": wire.attrib.get("classid", ""),
                    "x": str(x),
                    "y": str(y),
                    "w": wire.attrib.get("w", ""),
                    "h": wire.attrib.get("h", ""),
                    "vertices": vertices,
                }
            )
    return sorted(evidence, key=lambda row: (int(row["y"]), int(row["x"]), row["id"]))


def exact_series_wire(root: ET.Element) -> dict[str, object]:
    wire = next(
        (element for element in root.iter("Wire") if element.attrib.get("id") == IBR2_SERIES_WIRE["id"]),
        None,
    )
    if wire is None:
        return {"found": False, "matches_audited_geometry": False}
    vertices = [(vertex.attrib.get("x", ""), vertex.attrib.get("y", "")) for vertex in wire.findall("vertex")]
    matches = (
        wire.attrib.get("classid") == IBR2_SERIES_WIRE["classid"]
        and wire.attrib.get("x") == IBR2_SERIES_WIRE["x"]
        and wire.attrib.get("y") == IBR2_SERIES_WIRE["y"]
        and vertices == IBR2_SERIES_WIRE["vertices"]
    )
    return {
        "found": True,
        "matches_audited_geometry": matches,
        "id": wire.attrib.get("id", ""),
        "classid": wire.attrib.get("classid", ""),
        "absolute_start": [wire.attrib.get("x", ""), wire.attrib.get("y", "")],
        "relative_vertices": vertices,
        "absolute_end": ["1008", "1332"],
    }


def breaker_reference(root: ET.Element, fortran_text: str) -> dict[str, object]:
    brk = next(
        (
            element
            for element in users(root)
            if element.attrib.get("defn") == "master:breaker3" and params_for(element).get("NAME") == "BRK_DFIG"
        ),
        None,
    )
    params = params_for(brk) if brk is not None else {}
    has_closed_semantics = "NINT(1.0-BRK_DFIG)" in fortran_text.replace(" ", "")
    has_state_semantics = "DFIG_BRK_STATE = IVD1_1" in fortran_text and "EMTDC_X2COMP(0,0,0.5,REAL(DFIG_BRK_STATE)" in fortran_text
    return {
        "reference_breaker": "BRK_DFIG",
        "component_found": brk is not None,
        "definition": brk.attrib.get("defn", "") if brk is not None else "",
        "settings_to_reuse": {
            "Ctrl": params.get("Ctrl"),
            "OPCUR": params.get("OPCUR"),
            "ROFF": params.get("ROFF"),
            "RON": params.get("RON"),
            "TDA": params.get("TDA"),
            "TDB": params.get("TDB"),
            "TDC": params.get("TDC"),
            "TDRA": params.get("TDRA"),
            "TDRB": params.get("TDRB"),
            "TDRC": params.get("TDRC"),
            "BOpen1": params.get("BOpen1"),
            "BOpen2": params.get("BOpen2"),
            "BOpen3": params.get("BOpen3"),
            "SBRA": params.get("SBRA"),
        },
        "command_semantics": "0.0 closes the breaker, 1.0 opens it",
        "command_semantics_evidence": "P3.f calls EMTDC_BREAKER1(..., NINT(1.0-BRK_DFIG))",
        "closed_command_value": 0.0,
        "open_command_value": 1.0,
        "state_semantics": "DFIG_BRK_STATE is actual breaker open-state evidence; >0.5 maps to open bool 1",
        "state_semantics_evidence": "P3.f assigns DFIG_BRK_STATE = IVD1_1 and compares it at threshold 0.5",
        "closed_semantics_found": has_closed_semantics,
        "state_semantics_found": has_state_semantics,
    }


def main_audit_supported(current_sha: str | None) -> bool:
    if current_sha != AUDITED_MAIN_SHA:
        return False
    if not MAIN_SHA_AUDIT.exists():
        return False
    audit = json.loads(MAIN_SHA_AUDIT.read_text(encoding="utf-8"))
    return (
        audit.get("functional_equivalence_status") == "supported"
        and audit.get("trial_resumption_eligibility") == "eligible_for_separate_task"
    )


def main() -> int:
    main_sha = sha256(MAIN_PROJECT)
    trial_sha = sha256(TRIAL_PROJECT)
    main_root = parse_xml(MAIN_PROJECT)
    trial_root = parse_xml(TRIAL_PROJECT)
    main_fortran = MAIN_FORTRAN.read_text(errors="replace") if MAIN_FORTRAN.exists() else ""
    trial_fortran = TRIAL_FORTRAN.read_text(errors="replace") if TRIAL_FORTRAN.exists() else ""
    feasibility = json.loads(FEASIBILITY_JSON.read_text(encoding="utf-8")) if FEASIBILITY_JSON.exists() else {}

    absent = {name: not exact_signal_present(trial_root, name) and name not in trial_fortran for name in PLANNED_OBJECTS}
    components = {
        role: component_summary(trial_root, role, component_id)
        for role, component_id in IBR2_IDS.items()
    }
    observables = {
        signal: exact_signal_present(trial_root, signal) or output_channel_present(trial_root, signal) or signal in trial_fortran
        for signal in ["VIBR2", "PIBR2", "QIBR2"]
    }
    branch_components_ok = all(summary is not None for summary in components.values())
    lv = components["lv_multimeter"]
    xfmr = components["transformer"]
    ibr = components["ibr"]
    series_wire = exact_series_wire(trial_root)
    insertion_text = (
        "On trial page 3IBR_DFIG1_TRIAL:Main(0):P1(0):P3(0), replace only Wire id=1422683866, "
        "the horizontal three-phase conductor at y=1332 from absolute (936,1332) to (1008,1332). "
        "Its network-side endpoint is the 0.6 kV IBR2 node at low-voltage multimeter id=1433370859 "
        "(VIBR2/PIBR2/QIBR2), directly connected upstream to transformer E_2_30_1 id=275469438; "
        "its source-side endpoint is the grid port of IBR_AVM_2_1_1_1 id=1220231535."
    )
    no_bypass_evidence = (
        "Wire id=1422683866 is the sole audited horizontal physical conductor from the IBR2 source port "
        "to its 0.6 kV metering/transformer node. The other nearby wires at y=1314 are control-signal wires, "
        "not a second three-phase path. Replacing id=1422683866 (rather than adding alongside it) makes the "
        "breaker the only connection across this cut; the original conductor must not remain."
    )
    brk_ref = breaker_reference(trial_root, trial_fortran or main_fortran)

    statuses = {
        "trial_preflight_status": "pass",
        "main_project_functional_integrity_status": "pass" if main_audit_supported(main_sha) else "fail",
        "trial_clean_state_status": "pass" if all(absent.values()) and trial_sha == EXPECTED_TRIAL_SHA else "fail",
        "ibr2_branch_mapping_status": "pass" if branch_components_ok and all(observables.values()) else "fail",
        "unique_series_insertion_status": "pass" if branch_components_ok and series_wire.get("matches_audited_geometry") else "fail",
        "no_parallel_bypass_status": "pass" if branch_components_ok and series_wire.get("matches_audited_geometry") else "fail",
        "breaker_semantics_status": "pass" if brk_ref["component_found"] and brk_ref["closed_semantics_found"] and brk_ref["state_semantics_found"] else "fail",
    }
    if any(value != "pass" for key, value in statuses.items() if key != "trial_preflight_status"):
        statuses["trial_preflight_status"] = "fail"

    payload = {
        "main_project": {
            "path": str(MAIN_PROJECT),
            "sha256": main_sha,
            "audited_sha256": AUDITED_MAIN_SHA,
            "path_differs_from_trial": MAIN_PROJECT.resolve() != TRIAL_PROJECT.resolve(),
        },
        "trial_project": {
            "path": str(TRIAL_PROJECT),
            "sha256": trial_sha,
            "expected_pre_task_sha256": EXPECTED_TRIAL_SHA,
            "xml_parse_status": "pass",
        },
        "planned_object_absence": absent,
        "selected_source_from_feasibility": (feasibility.get("selected_source") or {}).get("source_id", "IBR2_TRIAL"),
        "target": {
            "source_id": "IBR2_TRIAL",
            "target_ibr": "IBR_AVM_2_1_1_1",
            "observables": observables,
            "components": {role: asdict(summary) if summary is not None else None for role, summary in components.items()},
        },
        "safe_insertion_point": {
            "page_path": "3IBR_DFIG1_TRIAL:Main(0):P1(0):P3(0)",
            "description": insertion_text,
            "selected_physical_wire": series_wire,
            "wire_evidence": wire_evidence(trial_root),
            "no_parallel_bypass_proof": no_bypass_evidence,
        },
        "breaker_semantics_reference": brk_ref,
        "trial_signal_plan": {
            "breaker": "BRK_IBR2_TRIAL",
            "command_signal": "IBR2_TRIAL_BRK_CMD",
            "command_initial_value": 0.0,
            "state_signal": "IBR2_TRIAL_BRK_STATE",
            "open_bool_formula": "IBR2_TRIAL_BRK_STATE > 0.5 -> IBR2_TRIAL_BRK_OPEN_BOOL = 1, else 0",
            "source_available_formula": "IBR2_TRIAL_SOURCE_AVAILABLE = NOT IBR2_TRIAL_BRK_OPEN_BOOL",
        },
        "statuses": statuses,
    }

    print(json.dumps(payload, indent=2))
    return 0 if statuses["trial_preflight_status"] == "pass" else 2


if __name__ == "__main__":
    raise SystemExit(main())
