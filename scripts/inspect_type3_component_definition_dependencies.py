#!/usr/bin/env python3
"""Read-only dependency inspection for the official Type-3 Average PSCAD model.

This script does not modify PSCAD files. It parses the Type3_Ave_Nov_2018 case
as XML and reports which project-local definitions are reachable from the
Type3_WTG_Avg core module, plus which top-level standalone test objects should
not be part of a reusable library import.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import xml.etree.ElementTree as ET
from collections import defaultdict, deque
from pathlib import Path
from typing import Any


DEFAULT_TYPE3 = Path(r"C:\pscad_work\type3_wtg_v46_trial\Type3_Ave_Nov_2018.pscx")
DEFAULT_OUT = Path("data/reference/pscad_case_library_evidence.json")

CORE_DEFINITION_CANDIDATES = ["Type3_WTG_Avg", "Type_3_WTG_Avg", "Type3_Average", "Type 3 Average"]
STANDALONE_TERMS = [
    "V_source",
    "Vsource",
    "BusPOC",
    "POC Fault",
    "Terminal Fault",
    "Cable_1",
    "Cable_3",
    "source3",
    "xfmr-3p2w",
    "OverlayGraph",
    "GraphFrame",
]


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def local_name(defn: str) -> str:
    return defn.split(":")[-1] if defn else ""


def params_of(user: ET.Element) -> dict[str, str]:
    return {
        p.attrib.get("name", ""): p.attrib.get("value", "")
        for p in user.findall("./paramlist/param")
        if p.attrib.get("name")
    }


def ports_of(definition: ET.Element) -> list[dict[str, str]]:
    return [
        {
            "name": p.attrib.get("name", ""),
            "model": p.attrib.get("model", ""),
            "mode": p.attrib.get("mode", ""),
            "type": p.attrib.get("type", ""),
            "dim": p.attrib.get("dim", ""),
            "internal": p.attrib.get("internal", ""),
        }
        for p in definition.findall(".//port")
    ]


def parameters_of(definition: ET.Element) -> list[dict[str, str]]:
    out = []
    for p in definition.findall(".//parameter"):
        out.append(
            {
                "name": p.attrib.get("name", ""),
                "desc": p.attrib.get("desc", ""),
                "unit": p.attrib.get("unit", ""),
                "intent": p.attrib.get("intent", ""),
                "type": p.attrib.get("type", ""),
                "value_recorded": "omitted_restricted_model_detail",
            }
        )
    return out


def script_summary(definition: ET.Element) -> dict[str, Any]:
    tags = ["script", "fortran", "data"]
    result: dict[str, Any] = {}
    for tag in tags:
        elems = definition.findall(f".//{tag}")
        result[tag] = {
            "count": len(elems),
            "nonempty_count": sum(1 for e in elems if (e.text or "").strip()),
        }
    return result


def find_core_definition(definitions: dict[str, ET.Element]) -> str:
    for candidate in CORE_DEFINITION_CANDIDATES:
        if candidate in definitions:
            return candidate
    for name in definitions:
        if re.search(r"type\s*3.*(wtg|avg|average)|type3.*(wtg|avg|average)", name, re.I):
            return name
    raise SystemExit("Could not find a Type-3 Average core definition")


def build_uses(definitions: dict[str, ET.Element]) -> dict[str, set[str]]:
    uses: dict[str, set[str]] = defaultdict(set)
    names = set(definitions)
    for dname, definition in definitions.items():
        for user in definition.findall(".//User"):
            target = local_name(user.attrib.get("defn", ""))
            if target in names and target != dname:
                uses[dname].add(target)
    return uses


def transitive_closure(start: str, uses: dict[str, set[str]]) -> list[str]:
    seen = {start}
    order = []
    queue: deque[str] = deque([start])
    while queue:
        cur = queue.popleft()
        order.append(cur)
        for nxt in sorted(uses.get(cur, [])):
            if nxt not in seen:
                seen.add(nxt)
                queue.append(nxt)
    return order


def top_level_instances(root: ET.Element, project_name: str) -> list[dict[str, Any]]:
    main = None
    for definition in root.findall(".//Definition"):
        if definition.attrib.get("name") == "Main":
            main = definition
            break
    if main is None:
        return []
    rows = []
    for user in main.findall(".//User"):
        p = params_of(user)
        searchable = " ".join([user.attrib.get("name", ""), user.attrib.get("defn", "")] + list(p.values()))
        rows.append(
            {
                "id": user.attrib.get("id", ""),
                "name": user.attrib.get("name", ""),
                "defn": user.attrib.get("defn", ""),
                "local_defn": local_name(user.attrib.get("defn", "")),
                "x": user.attrib.get("x", ""),
                "y": user.attrib.get("y", ""),
                "is_core_instance": local_name(user.attrib.get("defn", "")) in CORE_DEFINITION_CANDIDATES
                or local_name(user.attrib.get("defn", "")) == "Type3_WTG_Avg",
                "standalone_term_hits": [term for term in STANDALONE_TERMS if term.lower() in searchable.lower()],
                "selected_param_names": sorted(
                    k for k in p if k in {"Name", "Vm", "Vbase", "freq", "VLL_Gr", "V1", "V2", "Tmva", "Length", "P", "Q"}
                ),
            }
        )
    return rows


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--type3", type=Path, default=DEFAULT_TYPE3)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    args = parser.parse_args()

    root = ET.parse(args.type3).getroot()
    project_name = root.attrib.get("name", "")
    definitions = {d.attrib.get("name", ""): d for d in root.findall(".//Definition") if d.attrib.get("name")}
    core = find_core_definition(definitions)
    uses = build_uses(definitions)
    closure = transitive_closure(core, uses)

    definition_records = []
    for name in closure:
        definition = definitions[name]
        definition_records.append(
            {
                "name": name,
                "classid": definition.attrib.get("classid", ""),
                "id": definition.attrib.get("id", ""),
                "instances": definition.attrib.get("instances", ""),
                "direct_local_dependencies": sorted(uses.get(name, [])),
                "ports": ports_of(definition),
                "parameters": parameters_of(definition),
                "script_summary": script_summary(definition),
                "runtime_object_counts": {
                    "controls": len(definition.findall(".//Control")),
                    "graphs": len(definition.findall(".//Graph")),
                    "frames": len(definition.findall(".//Frame")),
                    "wires": len(definition.findall(".//Wire")),
                    "users": len(definition.findall(".//User")),
                },
            }
        )

    top_instances = top_level_instances(root, project_name)
    evidence = {
        "generated_by": "scripts/inspect_type3_component_definition_dependencies.py",
        "mode": "read_only",
        "source_model": {
            "path": str(args.type3),
            "sha256": sha256(args.type3),
            "project_name": project_name,
            "project_version": root.attrib.get("version", ""),
        },
        "core_definition": core,
        "core_transitive_definition_count": len(closure),
        "core_transitive_definitions": definition_records,
        "definition_dependency_edges": [
            {"source": src, "target": dst, "relation": "uses_project_local_definition"}
            for src, targets in sorted(uses.items())
            for dst in sorted(targets)
        ],
        "top_level_main_instances": top_instances,
        "standalone_candidates_to_exclude": [
            row for row in top_instances if row["standalone_term_hits"] and not row["is_core_instance"]
        ],
        "library_migration_interpretation": {
            "copy_core_definition_only_excludes_main_page_test_network": True,
            "export_with_dependents_should_cover_project_local_module_hierarchy": True,
            "manual_gui_confirmation_required": [
                "Confirm the Definitions tree shows Type3_WTG_Avg as a Module Definition.",
                "Confirm Export with Dependents is available on that definition.",
                "Confirm imported Type3WTG_Lib definitions include every transitive child definition listed here.",
            ],
        },
        "official_documentation_evidence": {
            "local_pscad_v46_manual": {
                "path": r"C:\Program Files (x86)\PSCAD46\help\UserGuides\PSCAD Users Guide (V4.6).pdf",
                "extracted_hits": "data/reference/local_pscad_v46_pdf_keyword_hits.json",
                "findings": [
                    "Definitions may be exchanged by saving PSCAD Definition (*.psdx) files.",
                    "Definitions are imported from the workspace primary window Definitions branch using Import Definition(s)....",
                    "A single definition can be exported using Export As....",
                    "A module hierarchy can be exported using Export with Dependents.",
                    "Copy as Meta-File or Bitmap is documented as a visual/image export path, not a definition migration path.",
                ],
            },
            "official_web_help": [
                {
                    "url": "https://www.pscad.com/webhelp/PSCAD/The_Application_Environment/The_Workspace/The_Projects_Section.htm",
                    "finding": "Definitions branch supports Import Definition(s)..., Paste, Export As..., Copy with Dependents, and Export with Dependents; user definitions should reside in library projects.",
                },
                {
                    "url": "https://www.pscad.com/webhelp/PSCAD/Features_and_Operations/Components_and_Modules/Importing_Exporting_Definitions.htm",
                    "finding": "Definitions are imported/exported as PSCAD Definition (*.psdx) files; Export with Dependents includes dependent module definitions.",
                },
                {
                    "url": "https://www.pscad.com/webhelp/PSCAD/Features_and_Operations/Copying_and_Transferring_Module_Hierarchies.htm",
                    "finding": "Copy with Dependents and Copy Transfer are supported module hierarchy transfer mechanisms.",
                },
                {
                    "url": "https://www.pscad.com/webhelp/PSCAD/Features_and_Operations/Components_and_Modules/Linking_and_Re-linking_Definitions.htm",
                    "finding": "Switch Reference... and Edit Reference... are supported for re-linking an instance to loaded definitions.",
                },
            ],
            "decision": "Copy as Meta-File is not suitable for Type-3 case-to-library definition migration; use Export with Dependents to *.psdx and Import Definition(s)... into Type3WTG_Lib.",
        },
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(evidence, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps({"core_definition": core, "dependency_count": len(closure), "out": str(args.out)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
