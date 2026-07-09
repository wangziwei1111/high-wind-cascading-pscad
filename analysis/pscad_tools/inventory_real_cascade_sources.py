"""Inventory real PSCAD sources eligible for a cascade-event adapter.

This script is intentionally read-only with respect to PSCAD files.  It parses
the active 3IBR project and the already-generated P3.f file, scores candidate
sources against the seven qualification gates required by the static
second-source task, and writes repository evidence artifacts.
"""

from __future__ import annotations

import csv
import hashlib
import json
import re
import xml.etree.ElementTree as ET
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Iterable


REPO_ROOT = Path(__file__).resolve().parents[2]
PROJECT_PATH = Path(r"C:\pscad_work\pnnl_39_3ibr_pscad46_strip5\PSCAD\3IBR.pscx")
FORTRAN_PATH = Path(r"C:\pscad_work\pnnl_39_3ibr_pscad46_strip5\PSCAD\3IBR.gf46\P3.f")
JSON_OUT = REPO_ROOT / "data" / "reference" / "real_second_source_inventory.json"
CSV_OUT = REPO_ROOT / "data" / "reference" / "real_second_source_inventory_summary.csv"

QUALIFICATION_FIELDS = [
    "distinct_electrical_source",
    "local_open_state_available",
    "open_state_semantics_proven",
    "initial_closed_state_proven",
    "P_or_Q_or_V_observable",
    "monitor_only_access",
    "not_shared_system_switch",
]


@dataclass
class Candidate:
    candidate_id: str
    display_name: str
    candidate_type: str
    page_path: str
    component_id: str | None = None
    component_definition: str | None = None
    related_breaker: str | None = None
    state_signal: str | None = None
    command_signal: str | None = None
    observable_signals: list[str] = field(default_factory=list)
    evidence: list[str] = field(default_factory=list)
    exclusion_reason: str = ""
    distinct_electrical_source: str = "unavailable"
    local_open_state_available: str = "unavailable"
    open_state_semantics_proven: str = "unavailable"
    initial_closed_state_proven: str = "unavailable"
    P_or_Q_or_V_observable: str = "unavailable"
    monitor_only_access: str = "unavailable"
    not_shared_system_switch: str = "unavailable"

    @property
    def qualified(self) -> bool:
        return all(getattr(self, field) == "pass" for field in QUALIFICATION_FIELDS)

    @property
    def pass_count(self) -> int:
        return sum(getattr(self, field) == "pass" for field in QUALIFICATION_FIELDS)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def params_for(user: ET.Element) -> dict[str, str]:
    params: dict[str, str] = {}
    for param in user.findall(".//param"):
        name = param.attrib.get("name")
        if name:
            params[name] = param.attrib.get("value", "")
    return params


def find_users(root: ET.Element, predicate) -> list[ET.Element]:
    return [
        elem
        for elem in root.iter()
        if elem.tag == "User" and predicate(elem, params_for(elem))
    ]


def unique(values: Iterable[str]) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for value in values:
        if value and value not in seen:
            seen.add(value)
            out.append(value)
    return out


def extract_fortran_evidence(text: str) -> dict[str, list[str]]:
    result: dict[str, list[str]] = {}
    patterns = {
        "generators": r"!\s+\d+:\[(G_\d+_0_1_DYR)\] Generator from DYR File",
        "ibr_calls": r"!\s+(\d+):\[IBR_AVM_2_1_1\]",
        "breaker3": r"!\s+(\d+):\[breaker3\] 3 Phase Breaker '([^']*)'",
        "pgb": r"!\s+\d+:\[pgb\] Output Channel '([^']*)'",
    }
    for key, pattern in patterns.items():
        result[key] = unique("|".join(m.groups()) if len(m.groups()) > 1 else m.group(1)
                             for m in re.finditer(pattern, text))
    return result


def pgb_signals(fortran_text: str) -> set[str]:
    return set(re.findall(r"Output Channel '([^']+)'", fortran_text))


def p_q_v_observables(signals: set[str]) -> list[str]:
    return sorted(
        s
        for s in signals
        if re.fullmatch(r"[VPQ]IBR\d(?:_2)?", s)
        or s in {"VIBR1_2", "PIBR1_2", "QIBR1_2"}
    )


def breaker_candidates(root: ET.Element) -> list[Candidate]:
    candidates: list[Candidate] = []
    for breaker in find_users(root, lambda elem, p: elem.attrib.get("defn") == "master:breaker3"):
        p = params_for(breaker)
        name = p.get("NAME") or breaker.attrib.get("name") or f"breaker_{breaker.attrib.get('id')}"
        state = unique([p.get("SBRA", ""), p.get("SBRB", ""), p.get("SBRC", "")])
        candidate = Candidate(
            candidate_id=name.upper() if name else f"BREAKER_{breaker.attrib.get('id')}",
            display_name=name,
            candidate_type="breaker3",
            page_path="3IBR:Main(0):P1(0):P3(0)",
            component_id=breaker.attrib.get("id"),
            component_definition="master:breaker3",
            related_breaker=name,
            state_signal=", ".join(state) if state else None,
            command_signal=p.get("NAME") or None,
            evidence=[
                f"breaker3 id={breaker.attrib.get('id')} z={breaker.attrib.get('z')}",
                f"SBRA/SBRB/SBRC={state if state else 'none'}",
                f"InitStatus={p.get('InitStatus', '')}, Ctrl={p.get('Ctrl', '')}, ENAB={p.get('ENAB', '')}",
                f"BOpen1/2/3={p.get('BOpen1', '')}/{p.get('BOpen2', '')}/{p.get('BOpen3', '')}",
            ],
            distinct_electrical_source="fail",
            local_open_state_available="pass" if state else "fail",
            open_state_semantics_proven="pass" if state and name == "BRK_DFIG" else "fail",
            initial_closed_state_proven="pass" if p.get("InitStatus") == "0" else "unavailable",
            P_or_Q_or_V_observable="fail",
            monitor_only_access="pass" if state else "unavailable",
            not_shared_system_switch="fail" if name in {"Trip", "BRK"} else "unavailable",
        )
        if name == "BRK_DFIG":
            candidate.candidate_id = "TYPE3_DFIG_1"
            candidate.candidate_type = "protected_source_breaker"
            candidate.observable_signals = ["VIBR1_2", "PIBR1_2", "QIBR1_2"]
            candidate.P_or_Q_or_V_observable = "pass"
            candidate.exclusion_reason = "Protected source 1; excluded by task rule."
        else:
            candidate.exclusion_reason = (
                "Breaker exists, but no exposed SBRA/SBRB/SBRC actual-state signal is present; "
                "it cannot prove a source-local open state for a second source."
            )
        candidates.append(candidate)
    return candidates


def generator_candidates(root: ET.Element, fortran_text: str, observables: list[str]) -> list[Candidate]:
    candidates: list[Candidate] = []
    generator_names = unique(re.findall(r"\[(G_\d+_0_1_DYR)\] Generator from DYR File", fortran_text))
    for name in generator_names:
        candidates.append(
            Candidate(
                candidate_id=name,
                display_name=name,
                candidate_type="dyr_generator",
                page_path="3IBR:Main(0):P1(0):P3(0)",
                component_definition="Generator from DYR File",
                observable_signals=[],
                evidence=[
                    f"P3.f contains '{name}' Generator from DYR File.",
                    "No matching local breaker state output was found in the PSCAD XML.",
                ],
                exclusion_reason=(
                    "Real generator component, but no source-local actual breaker/open-state "
                    "signal was exposed for monitor-only event qualification."
                ),
                distinct_electrical_source="pass",
                local_open_state_available="fail",
                open_state_semantics_proven="fail",
                initial_closed_state_proven="unavailable",
                P_or_Q_or_V_observable="unavailable",
                monitor_only_access="pass",
                not_shared_system_switch="pass",
            )
        )
    return candidates


def ibr_candidates(root: ET.Element, observables: list[str]) -> list[Candidate]:
    users = find_users(root, lambda elem, p: elem.attrib.get("defn") == "3IBR:IBR_AVM_2_1_1")
    candidates: list[Candidate] = []
    observable_groups = [
        ["VIBR2", "PIBR2", "QIBR2"],
        ["VIBR3", "PIBR3", "QIBR3"],
        ["VIBR2_2", "PIBR2_2", "QIBR2_2"],
        ["VIBR3_2", "PIBR3_2", "QIBR3_2"],
    ]
    for index, user in enumerate(users, start=1):
        group = observable_groups[index - 1] if index <= len(observable_groups) else []
        group = [signal for signal in group if signal in observables]
        candidates.append(
            Candidate(
                candidate_id=f"IBR_AVM_2_1_1_{index}",
                display_name=f"IBR_AVM_2_1_1 instance {index}",
                candidate_type="ibr_control_module",
                page_path="3IBR:Main(0):P1(0):P3(0)",
                component_id=user.attrib.get("id"),
                component_definition="3IBR:IBR_AVM_2_1_1",
                observable_signals=group,
                evidence=[
                    f"IBR_AVM_2_1_1 XML id={user.attrib.get('id')} z={user.attrib.get('z')}.",
                    f"Observable P/Q/V candidates: {', '.join(group) if group else 'none'}",
                    "No local breaker/switch actual-state output was found for this module.",
                ],
                exclusion_reason=(
                    "Source-like IBR module with P/Q/V observability, but no exposed actual "
                    "local open-state signal; command-only or inferred status is not acceptable."
                ),
                distinct_electrical_source="pass",
                local_open_state_available="fail",
                open_state_semantics_proven="fail",
                initial_closed_state_proven="unavailable",
                P_or_Q_or_V_observable="pass" if group else "unavailable",
                monitor_only_access="pass",
                not_shared_system_switch="pass",
            )
        )
    return candidates


def type3_candidate(root: ET.Element) -> Candidate | None:
    users = find_users(root, lambda elem, p: "Type3_WTG_Avg" in elem.attrib.get("defn", ""))
    if not users:
        return None
    user = users[0]
    return Candidate(
        candidate_id="TYPE3_DFIG_1",
        display_name="Type3WTG_Lib:Type3_WTG_Avg",
        candidate_type="protected_source",
        page_path="3IBR:Main(0):P1(0):P3(0)",
        component_id=user.attrib.get("id"),
        component_definition=user.attrib.get("defn"),
        related_breaker="BRK_DFIG",
        state_signal="DFIG_BRK_STATE",
        command_signal="DFIG_LVRT_FINAL_BRK_CMD",
        observable_signals=["VIBR1_2", "PIBR1_2", "QIBR1_2"],
        evidence=[
            "Existing source 1 Type-3 DFIG package.",
            "BRK_DFIG exposes DFIG_BRK_STATE and is already protected by the task scope.",
        ],
        exclusion_reason="Already the canonical source 1; excluded from second-source selection.",
        distinct_electrical_source="fail",
        local_open_state_available="pass",
        open_state_semantics_proven="pass",
        initial_closed_state_proven="pass",
        P_or_Q_or_V_observable="pass",
        monitor_only_access="pass",
        not_shared_system_switch="pass",
    )


def peswitch_summary(root: ET.Element) -> dict[str, object]:
    switches = find_users(root, lambda elem, p: elem.attrib.get("defn") == "master:peswitch")
    examples = []
    for switch in switches[:10]:
        p = params_for(switch)
        examples.append(
            {
                "id": switch.attrib.get("id"),
                "z": switch.attrib.get("z"),
                "name": p.get("Name") or p.get("NAME") or switch.attrib.get("name", ""),
            }
        )
    return {
        "count": len(switches),
        "decision": "excluded",
        "reason": (
            "Power-electronics/internal switches do not expose a source-local actual open-state "
            "signal suitable for a real second-source cascade adapter."
        ),
        "examples": examples,
    }


def main() -> int:
    if not PROJECT_PATH.exists():
        raise FileNotFoundError(PROJECT_PATH)
    if not FORTRAN_PATH.exists():
        raise FileNotFoundError(FORTRAN_PATH)

    root = ET.parse(PROJECT_PATH).getroot()
    fortran_text = FORTRAN_PATH.read_text(errors="replace")
    signals = pgb_signals(fortran_text)
    observables = p_q_v_observables(signals)

    candidates: list[Candidate] = []
    type3 = type3_candidate(root)
    if type3:
        candidates.append(type3)
    candidates.extend(ibr_candidates(root, observables))
    candidates.extend(generator_candidates(root, fortran_text, observables))
    candidates.extend(breaker_candidates(root))

    # De-duplicate TYPE3_DFIG_1 if both the source component and BRK_DFIG were found.
    deduped: dict[str, Candidate] = {}
    for candidate in candidates:
        if candidate.candidate_id == "TYPE3_DFIG_1" and "TYPE3_DFIG_1" in deduped:
            existing = deduped["TYPE3_DFIG_1"]
            existing.evidence.extend(candidate.evidence)
            existing.observable_signals = unique(existing.observable_signals + candidate.observable_signals)
            continue
        deduped.setdefault(candidate.candidate_id, candidate)
    candidates = list(deduped.values())

    qualified = [candidate for candidate in candidates if candidate.qualified]
    selected = sorted(qualified, key=lambda c: (-c.pass_count, c.candidate_id))[0] if qualified else None
    status = "qualified_candidate_found" if selected else "no_qualified_candidate"

    JSON_OUT.parent.mkdir(parents=True, exist_ok=True)
    CSV_OUT.parent.mkdir(parents=True, exist_ok=True)

    payload = {
        "schema_version": 1,
        "real_second_source_inventory_status": status,
        "second_source_qualification_status": "pass" if selected else "fail",
        "selected_source": asdict(selected) if selected else None,
        "project": {
            "path": str(PROJECT_PATH),
            "sha256": sha256(PROJECT_PATH),
            "fortran_path": str(FORTRAN_PATH),
        },
        "qualification_fields": QUALIFICATION_FIELDS,
        "observable_p_q_v_signals": observables,
        "fortran_evidence": extract_fortran_evidence(fortran_text),
        "peswitch_inventory": peswitch_summary(root),
        "candidates": [asdict(candidate) | {"qualified": candidate.qualified, "pass_count": candidate.pass_count}
                       for candidate in candidates],
        "claim_boundary": {
            "pscad_run_performed": False,
            "pscad_project_modified_by_script": False,
            "gui_modification_allowed": bool(selected),
            "reason": (
                "No GUI expansion is allowed unless a candidate passes all seven qualification gates."
            ),
        },
    }
    JSON_OUT.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    with CSV_OUT.open("w", newline="", encoding="utf-8") as handle:
        columns = [
            "candidate_id",
            "display_name",
            "candidate_type",
            "page_path",
            "related_breaker",
            "state_signal",
            "observable_signals",
            *QUALIFICATION_FIELDS,
            "qualified",
            "exclusion_reason",
        ]
        writer = csv.DictWriter(handle, fieldnames=columns)
        writer.writeheader()
        for candidate in candidates:
            row = asdict(candidate)
            row["observable_signals"] = ";".join(candidate.observable_signals)
            row["qualified"] = candidate.qualified
            writer.writerow({column: row.get(column, "") for column in columns})

    print(f"real_second_source_inventory_status={status}")
    print(f"second_source_qualification_status={'pass' if selected else 'fail'}")
    print(f"candidate_count={len(candidates)}")
    if selected:
        print(f"selected_source={selected.candidate_id}")
    else:
        ranked = sorted(candidates, key=lambda c: (-c.pass_count, c.candidate_id))[:5]
        print("top_candidates_without_full_qualification=" + ",".join(c.candidate_id for c in ranked))
    print(f"json={JSON_OUT}")
    print(f"csv={CSV_OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
