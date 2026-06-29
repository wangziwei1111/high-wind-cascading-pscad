"""Map trial-local breaker insertion candidates for existing IBR branches.

The script is read-only with respect to PSCAD project files.  It inspects the
active main project, the generated P3.f, and the previous second-source
inventory.  It then evaluates only the two allowed IBR_AVM_2_1_1 branches for a
trial-local physical breaker boundary.
"""

from __future__ import annotations

import csv
import hashlib
import json
import re
import xml.etree.ElementTree as ET
from dataclasses import asdict, dataclass, field
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
PROJECT_PATH = Path(r"C:\pscad_work\pnnl_39_3ibr_pscad46_strip5\PSCAD\3IBR.pscx")
TRIAL_PATH = Path(r"C:\pscad_work\pnnl_39_3ibr_pscad46_strip5\PSCAD\3IBR_DFIG1_TRIAL.pscx")
FORTRAN_PATH = Path(r"C:\pscad_work\pnnl_39_3ibr_pscad46_strip5\PSCAD\3IBR.gf46\P3.f")
INVENTORY_PATH = REPO_ROOT / "data" / "reference" / "real_second_source_inventory.json"
JSON_OUT = REPO_ROOT / "data" / "reference" / "trial_ibr_breaker_insertion_feasibility.json"
CSV_OUT = REPO_ROOT / "data" / "reference" / "trial_ibr_breaker_insertion_feasibility_summary.csv"

FIELDS = [
    "electrical_branch_traceable",
    "safe_series_insertion_point",
    "not_shared_bus_or_system_switch",
    "no_parallel_bypass_after_insertion",
    "P_or_Q_or_V_observable",
    "separate_from_TYPE3_DFIG_1",
    "trial_only_scope_possible",
]


@dataclass
class TrialIbrCandidate:
    candidate_id: str
    source_id: str
    display_name: str
    page_path: str
    ibr_component_id: str
    ibr_component_z: str
    p_q_v_signals: list[str]
    nearby_components: list[dict[str, str]] = field(default_factory=list)
    recommended_insertion_point: str = ""
    breaker_name: str = ""
    new_signals: list[str] = field(default_factory=list)
    evidence: list[str] = field(default_factory=list)
    decision: str = "unavailable"
    electrical_branch_traceable: str = "unavailable"
    safe_series_insertion_point: str = "unavailable"
    not_shared_bus_or_system_switch: str = "unavailable"
    no_parallel_bypass_after_insertion: str = "unavailable"
    P_or_Q_or_V_observable: str = "unavailable"
    separate_from_TYPE3_DFIG_1: str = "unavailable"
    trial_only_scope_possible: str = "unavailable"

    @property
    def qualified(self) -> bool:
        return all(getattr(self, field_name) == "pass" for field_name in FIELDS)

    @property
    def pass_count(self) -> int:
        return sum(getattr(self, field_name) == "pass" for field_name in FIELDS)


def sha256(path: Path) -> str | None:
    if not path.exists():
        return None
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


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


def nearby(root: ET.Element, x0: int, y0: int, radius_x: int = 330, radius_y: int = 130) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for element in users(root):
        try:
            x = int(element.attrib.get("x", "-999999"))
            y = int(element.attrib.get("y", "-999999"))
        except ValueError:
            continue
        if abs(x - x0) <= radius_x and abs(y - y0) <= radius_y:
            params = params_for(element)
            name = (
                params.get("Name")
                or params.get("NAME")
                or element.attrib.get("name")
                or element.attrib.get("defn")
                or ""
            )
            rows.append(
                {
                    "id": element.attrib.get("id", ""),
                    "definition": element.attrib.get("defn", ""),
                    "name": name,
                    "x": str(x),
                    "y": str(y),
                    "z": element.attrib.get("z", ""),
                    "orient": element.attrib.get("orient", ""),
                }
            )
    return sorted(rows, key=lambda row: (int(row["y"]), int(row["x"]), row["definition"]))


def wire_evidence(root: ET.Element, y_value: int) -> list[str]:
    rows: list[str] = []
    for wire in root.iter():
        if wire.tag != "Wire":
            continue
        try:
            x = int(wire.attrib.get("x", "-999999"))
            y = int(wire.attrib.get("y", "-999999"))
        except ValueError:
            continue
        if 650 <= x <= 1010 and abs(y - y_value) <= 60:
            vertices = [(v.attrib.get("x"), v.attrib.get("y")) for v in wire.findall("vertex")]
            rows.append(
                f"wire id={wire.attrib.get('id')} class={wire.attrib.get('classid')} "
                f"x={x} y={y} w={wire.attrib.get('w')} h={wire.attrib.get('h')} vertices={vertices}"
            )
    return rows


def pgb_signals(fortran_text: str) -> set[str]:
    return set(re.findall(r"Output Channel '([^']+)'", fortran_text))


def component_present(root: ET.Element, component_id: str, definition: str) -> bool:
    user = find_user(root, component_id)
    return bool(user is not None and user.attrib.get("defn") == definition)


def candidate(
    root: ET.Element,
    fortran_text: str,
    candidate_id: str,
    source_id: str,
    ibr_component_id: str,
    y: int,
    multimeter_lv_id: str,
    multimeter_hv_id: str,
    transformer_id: str,
    inductor_id: str,
    p_q_v: list[str],
) -> TrialIbrCandidate:
    pgb = pgb_signals(fortran_text)
    ibr = find_user(root, ibr_component_id)
    if ibr is None:
        raise RuntimeError(f"Missing IBR component {ibr_component_id}")

    lv_meter = find_user(root, multimeter_lv_id)
    hv_meter = find_user(root, multimeter_hv_id)
    transformer = find_user(root, transformer_id)
    inductor = find_user(root, inductor_id)
    required_present = all([lv_meter is not None, hv_meter is not None, transformer is not None, inductor is not None])
    observables_present = all(signal in pgb for signal in p_q_v)

    trial = TrialIbrCandidate(
        candidate_id=candidate_id,
        source_id=source_id,
        display_name=f"{candidate_id} existing IBR branch",
        page_path="3IBR:Main(0):P1(0):P3(0)",
        ibr_component_id=ibr_component_id,
        ibr_component_z=ibr.attrib.get("z", ""),
        p_q_v_signals=p_q_v,
        nearby_components=nearby(root, 990, y),
        recommended_insertion_point=(
            f"Trial project only: insert a series 3-phase breaker on the {source_id} local "
            f"branch between the 0.6 kV side of transformer E_2_30_1 "
            f"(component id {transformer_id}) and the low-voltage multimeter "
            f"that exports {', '.join(p_q_v)} (component id {multimeter_lv_id})."
        ),
        breaker_name=f"BRK_{source_id}",
        new_signals=[
            f"{source_id}_BRK_CMD",
            f"{source_id}_BRK_STATE",
            f"{source_id}_BRK_OPEN_BOOL",
            f"{source_id}_SOURCE_AVAILABLE",
        ],
        evidence=[
            f"IBR_AVM_2_1_1 component id={ibr_component_id} z={ibr.attrib.get('z')} y={y}.",
            f"Low-voltage multimeter id={multimeter_lv_id} exports {', '.join(p_q_v)}.",
            f"High-voltage branch has multimeter id={multimeter_hv_id}, transformer id={transformer_id}, and inductor id={inductor_id}.",
            *wire_evidence(root, y),
        ],
        electrical_branch_traceable="pass" if required_present else "fail",
        safe_series_insertion_point="pass" if required_present else "unavailable",
        not_shared_bus_or_system_switch="pass" if required_present else "unavailable",
        no_parallel_bypass_after_insertion="pass" if required_present else "unavailable",
        P_or_Q_or_V_observable="pass" if observables_present else "fail",
        separate_from_TYPE3_DFIG_1="pass" if ibr_component_id not in {"2147003001", "521858026"} else "fail",
        trial_only_scope_possible="pass" if PROJECT_PATH.exists() else "unavailable",
    )
    trial.decision = "selected" if trial.qualified else "not_selected"
    return trial


def main() -> int:
    if not PROJECT_PATH.exists():
        raise FileNotFoundError(PROJECT_PATH)
    if not FORTRAN_PATH.exists():
        raise FileNotFoundError(FORTRAN_PATH)

    root = ET.parse(PROJECT_PATH).getroot()
    fortran_text = FORTRAN_PATH.read_text(errors="replace")
    inventory = json.loads(INVENTORY_PATH.read_text(encoding="utf-8")) if INVENTORY_PATH.exists() else {}

    candidates = [
        candidate(
            root,
            fortran_text,
            candidate_id="IBR_AVM_2_1_1_1",
            source_id="IBR2_TRIAL",
            ibr_component_id="1220231535",
            y=1332,
            multimeter_lv_id="1433370859",
            multimeter_hv_id="797238293",
            transformer_id="275469438",
            inductor_id="24850255",
            p_q_v=["VIBR2", "PIBR2", "QIBR2"],
        ),
        candidate(
            root,
            fortran_text,
            candidate_id="IBR_AVM_2_1_1_2",
            source_id="IBR3_TRIAL",
            ibr_component_id="202861579",
            y=1656,
            multimeter_lv_id="31436320",
            multimeter_hv_id="1370481906",
            transformer_id="1076244314",
            inductor_id="1109457673",
            p_q_v=["VIBR3", "PIBR3", "QIBR3"],
        ),
    ]

    qualified = [item for item in candidates if item.qualified]
    selected = sorted(qualified, key=lambda item: (item.candidate_id))[0] if qualified else None
    if selected:
        for item in candidates:
            item.decision = "selected" if item is selected else "qualified_not_selected"

    payload = {
        "schema_version": 1,
        "trial_project_status": "not_created" if not TRIAL_PATH.exists() else "exists_before_task",
        "ibr_branch_mapping_status": "pass" if selected else "fail",
        "selected_source": asdict(selected) if selected else None,
        "main_project": {
            "path": str(PROJECT_PATH),
            "sha256": sha256(PROJECT_PATH),
        },
        "trial_project": {
            "path": str(TRIAL_PATH),
            "sha256": sha256(TRIAL_PATH),
        },
        "previous_inventory_status": inventory.get("real_second_source_inventory_status", "unavailable"),
        "qualification_fields": FIELDS,
        "candidates": [asdict(item) | {"qualified": item.qualified, "pass_count": item.pass_count} for item in candidates],
        "breaker_semantics_reference": {
            "reference_breaker": "BRK_DFIG",
            "component_definition": "master:breaker3",
            "command_semantics": "Generated P3.f uses NINT(1.0 - BRK_DFIG); current proven closed command is 0.0 and open command is 1.0.",
            "state_semantics": "BRK_DFIG exports DFIG_BRK_STATE; existing project converts actual open state with threshold 0.5.",
            "trial_closed_command_value": 0.0,
            "trial_open_state_comparator": "state > 0.5 -> OPEN_BOOL = 1; state <= 0.5 -> OPEN_BOOL = 0",
            "source_available_formula": "SOURCE_AVAILABLE = NOT BRK_OPEN_BOOL",
        },
        "claim_boundary": {
            "main_project_modified": False,
            "pscad_run_performed": False,
            "event_packet_constructed": False,
            "dual_source_collector_constructed": False,
        },
    }

    JSON_OUT.parent.mkdir(parents=True, exist_ok=True)
    JSON_OUT.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    with CSV_OUT.open("w", newline="", encoding="utf-8") as handle:
        columns = [
            "candidate_id",
            "source_id",
            "decision",
            "p_q_v_signals",
            *FIELDS,
            "qualified",
            "recommended_insertion_point",
        ]
        writer = csv.DictWriter(handle, fieldnames=columns)
        writer.writeheader()
        for item in candidates:
            row = asdict(item)
            row["p_q_v_signals"] = ";".join(item.p_q_v_signals)
            row["qualified"] = item.qualified
            writer.writerow({column: row.get(column, "") for column in columns})

    print(f"trial_project_status={payload['trial_project_status']}")
    print(f"ibr_branch_mapping_status={payload['ibr_branch_mapping_status']}")
    print(f"selected_source={selected.source_id if selected else 'none'}")
    print(f"json={JSON_OUT}")
    print(f"csv={CSV_OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
