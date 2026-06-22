#!/usr/bin/env python3
"""Read-only PSCAD static audit for the PNNL 3IBR -> Type-3 WTG trial.

The script parses PSCAD XML-like project files without modifying them and writes
metadata-only CSV/JSON summaries. It deliberately avoids copying model source
content into the repository.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
import xml.etree.ElementTree as ET
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any


DEFAULT_PNNL = Path(r"C:\pscad_work\pnnl_39_3ibr_pscad46_strip5\PSCAD\3IBR.pscx")
DEFAULT_TYPE3 = Path(
    r"C:\Users\24186\Documents\动态模型\external\type3-wtg-v46\WORKING_COPY"
    r"\Type3WindTurbine_TRIAL\Type3_Ave_Nov_2018.pscx"
)

PNNL_KEYWORDS = [
    "IBR_AVM_2_1_1",
    "GBUS30",
    "N30",
    "Inputs1",
    "Flags1",
    "Sbase",
    "Pini",
    "Pord",
    "Qord",
    "Pfcmd",
    "DB",
    "DBLK",
    "QIBR",
    "INV_Vbase",
    "REGC_A",
    "REEC_A",
    "PLL",
    "Grid-Following",
    "GFM",
    "fPLL",
    "fGFM",
    "345",
    "22",
    "0.6",
]

TYPE3_KEYWORDS = [
    "Type 3",
    "Type3",
    "WTG",
    "DFIG",
    "Dblk",
    "Dblk_Rsc",
    "freq",
    "Vbase",
    "UN",
    "Rated_MW",
    "Vwind",
    "Machine_MVA",
    "RSC",
    "GSC",
    "DC-link",
    "DC Link",
    "crowbar",
    "chopper",
    "synchronizer",
    "BusPOC",
    "V_source",
    "Equivalent",
    "Cable",
    "POC Fault",
    "Terminal Fault",
    "Pout",
    "Qout",
]

INTERFACE_TERMS = [
    "Sbase",
    "Pini",
    "Pord",
    "Qord",
    "Pfcmd",
    "DB",
    "DBLK",
    "QIBR",
    "INV_Vbase",
    "Dblk",
    "freq",
    "Vbase",
    "UN",
    "Rated_MW",
    "Vwind",
    "Machine_MVA",
]


@dataclass
class ProjectAudit:
    path: Path
    label: str
    keywords: list[str]
    root: ET.Element | None = None
    parse_error: str | None = None


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def file_record(path: Path, repo_root: Path) -> dict[str, Any]:
    stat = path.stat()
    try:
        in_repo = path.resolve().is_relative_to(repo_root.resolve())
    except ValueError:
        in_repo = False
    return {
        "path": str(path),
        "name": path.name,
        "extension": path.suffix.lower(),
        "size_bytes": stat.st_size,
        "modified_time": stat.st_mtime,
        "sha256": sha256(path),
        "inside_git_repo": in_repo,
        "classification": classify_file(path),
    }


def classify_file(path: Path) -> str:
    suffix = path.suffix.lower()
    if suffix in {".pscx", ".pslx", ".pswx", ".psl", ".lib"}:
        return "restricted_pscad_source_or_library"
    if suffix in {".gf42", ".gf46", ".out", ".snp", ".obj", ".dll", ".exe"}:
        return "restricted_generated_or_binary"
    if suffix in {".dyr", ".raw"}:
        return "restricted_external_power_system_data"
    return "metadata_or_auxiliary"


def parse_xml(path: Path) -> tuple[ET.Element | None, str | None]:
    try:
        parser = ET.XMLParser(target=ET.TreeBuilder(insert_comments=True))
        return ET.parse(path, parser=parser).getroot(), None
    except Exception as exc:  # PSCAD files are XML-like; keep fallback scans.
        return None, str(exc)


def element_path_map(root: ET.Element | None) -> dict[int, str]:
    paths: dict[int, str] = {}
    if root is None:
        return paths

    def walk(node: ET.Element, prefix: str) -> None:
        label = node.tag
        name = node.attrib.get("name") or node.attrib.get("id") or node.attrib.get("classid")
        here = f"{prefix}/{label}"
        if name:
            here += f"[@name='{name}']"
        paths[id(node)] = here
        for child in list(node):
            walk(child, here)

    walk(root, "")
    return paths


def parent_map(root: ET.Element | None) -> dict[int, ET.Element]:
    if root is None:
        return {}
    return {id(child): parent for parent in root.iter() for child in list(parent)}


def nearest_definition(node: ET.Element, parents: dict[int, ET.Element]) -> str:
    cur: ET.Element | None = node
    while cur is not None:
        if cur.tag == "Definition":
            return cur.attrib.get("name", "")
        cur = parents.get(id(cur))
    return ""


def collect_definitions(root: ET.Element | None) -> list[dict[str, Any]]:
    if root is None:
        return []
    out = []
    for definition in root.findall(".//Definition"):
        ports = [
            {
                "name": p.attrib.get("name", ""),
                "model": p.attrib.get("model", ""),
                "mode": p.attrib.get("mode", ""),
                "type": p.attrib.get("type", ""),
                "dim": p.attrib.get("dim", ""),
            }
            for p in definition.findall(".//port")
        ]
        params = [
            {
                "name": p.attrib.get("name", ""),
                "unit": p.attrib.get("unit", ""),
                "intent": p.attrib.get("intent", ""),
                "type": p.attrib.get("type", ""),
                "desc": p.attrib.get("desc", ""),
                "value": (p.findtext("value") or "").strip(),
            }
            for p in definition.findall(".//parameter")
        ]
        out.append(
            {
                "name": definition.attrib.get("name", ""),
                "classid": definition.attrib.get("classid", ""),
                "id": definition.attrib.get("id", ""),
                "instances": definition.attrib.get("instances", ""),
                "ports": ports[:80],
                "parameter_count": len(params),
                "parameters": params[:120],
            }
        )
    return out


def collect_components(root: ET.Element | None) -> list[dict[str, Any]]:
    if root is None:
        return []
    parents = parent_map(root)
    components = []
    for user in root.findall(".//User"):
        params = {
            p.attrib.get("name", ""): p.attrib.get("value", "")
            for p in user.findall("./paramlist/param")
            if p.attrib.get("name")
        }
        components.append(
            {
                "id": user.attrib.get("id", ""),
                "name": user.attrib.get("name", ""),
                "defn": user.attrib.get("defn", ""),
                "classid": user.attrib.get("classid", ""),
                "definition_scope": nearest_definition(user, parents),
                "x": user.attrib.get("x", ""),
                "y": user.attrib.get("y", ""),
                "params": params,
            }
        )
    return components


def find_keyword_hits(path: Path, keywords: list[str], limit_per_keyword: int = 25) -> list[dict[str, Any]]:
    text = path.read_text(encoding="utf-8", errors="replace").splitlines()
    hits = []
    counts: Counter[str] = Counter()
    for idx, line in enumerate(text, 1):
        low = line.lower()
        for keyword in keywords:
            if keyword.lower() in low and counts[keyword] < limit_per_keyword:
                counts[keyword] += 1
                hits.append(
                    {
                        "keyword": keyword,
                        "line": idx,
                        "snippet": sanitize_snippet(line),
                    }
                )
    return hits


def sanitize_snippet(line: str) -> str:
    clean = re.sub(r"\s+", " ", line.strip())
    return clean[:240]


def trace_terms(root: ET.Element | None, terms: list[str], source: str) -> list[dict[str, Any]]:
    if root is None:
        return []
    parents = parent_map(root)
    paths = element_path_map(root)
    records = []
    for elem in root.iter():
        for term in terms:
            if element_has_term(elem, term):
                records.append(
                    {
                        "source_project": source,
                        "term": term,
                        "element": elem.tag,
                        "id": elem.attrib.get("id", ""),
                        "name": elem.attrib.get("name", ""),
                        "defn": elem.attrib.get("defn", ""),
                        "value": elem.attrib.get("value", ""),
                        "definition_scope": nearest_definition(elem, parents),
                        "xml_path": paths.get(id(elem), ""),
                        "evidence_class": "verified_from_model_file",
                    }
                )
    return records


def element_has_term(elem: ET.Element, term: str) -> bool:
    """Match PSCAD signal names exactly where possible, with word fallback."""
    term_l = term.lower()
    exact_fields = ["name", "Name", "defn", "value", "unit", "desc"]
    for field in exact_fields:
        value = elem.attrib.get(field, "")
        if value.lower() == term_l:
            return True
        # Component definitions often carry namespace prefixes.
        if field == "defn" and value.split(":")[-1].lower() == term_l:
            return True
    if elem.text and re.search(rf"(?<![A-Za-z0-9_]){re.escape(term)}(?![A-Za-z0-9_])", elem.text, re.I):
        return True
    for key, value in elem.attrib.items():
        if key in exact_fields:
            continue
        if re.search(rf"(?<![A-Za-z0-9_]){re.escape(term)}(?![A-Za-z0-9_])", value, re.I):
            return True
    return False


def build_dependency_graph(projects: list[ProjectAudit]) -> dict[str, Any]:
    nodes: dict[str, dict[str, Any]] = {}
    edges = []
    for project in projects:
        if project.root is None:
            continue
        definitions = collect_definitions(project.root)
        local_defs = {d["name"] for d in definitions}
        for d in definitions:
            key = f"{project.label}:def:{d['name']}"
            nodes[key] = {
                "id": key,
                "label": d["name"],
                "type": "definition",
                "project": project.label,
                "classid": d["classid"],
            }
        for comp in collect_components(project.root):
            ckey = f"{project.label}:cmp:{comp['id']}"
            nodes[ckey] = {
                "id": ckey,
                "label": comp["name"] or comp["defn"],
                "type": "component",
                "project": project.label,
                "definition_scope": comp["definition_scope"],
                "defn": comp["defn"],
            }
            scope = comp["definition_scope"]
            if scope:
                skey = f"{project.label}:def:{scope}"
                if skey in nodes:
                    edges.append({"source": skey, "target": ckey, "relation": "contains"})
            defn_name = comp["defn"].split(":")[-1] if comp["defn"] else ""
            if defn_name in local_defs:
                edges.append(
                    {
                        "source": ckey,
                        "target": f"{project.label}:def:{defn_name}",
                        "relation": "uses_project_local_definition",
                    }
                )
            elif comp["defn"]:
                dep_key = f"external:{comp['defn']}"
                nodes.setdefault(
                    dep_key,
                    {
                        "id": dep_key,
                        "label": comp["defn"],
                        "type": "external_or_master_definition",
                        "project": project.label,
                    },
                )
                edges.append({"source": ckey, "target": dep_key, "relation": "uses_definition"})
    return {"nodes": list(nodes.values()), "edges": edges}


def write_csv(path: Path, rows: list[dict[str, Any]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({k: row.get(k, "") for k in fieldnames})


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--pnnl", type=Path, default=DEFAULT_PNNL)
    parser.add_argument("--type3", type=Path, default=DEFAULT_TYPE3)
    parser.add_argument("--repo-root", type=Path, default=Path.cwd())
    parser.add_argument("--out-data", type=Path, default=Path("data/reference"))
    args = parser.parse_args()

    projects = [
        ProjectAudit(args.pnnl, "pnnl_3ibr", PNNL_KEYWORDS),
        ProjectAudit(args.type3, "type3_average", TYPE3_KEYWORDS),
    ]
    for project in projects:
        project.root, project.parse_error = parse_xml(project.path)

    file_inventory = []
    for root in {p.path.parent for p in projects}:
        for child in sorted(root.iterdir()):
            if child.is_file():
                file_inventory.append(file_record(child, args.repo_root))

    project_summaries = []
    term_rows_by_project: dict[str, list[dict[str, Any]]] = {}
    for project in projects:
        root_attrib = dict(project.root.attrib) if project.root is not None else {}
        defs = collect_definitions(project.root)
        comps = collect_components(project.root)
        project_summaries.append(
            {
                "label": project.label,
                "path": str(project.path),
                "exists": project.path.exists(),
                "sha256": sha256(project.path) if project.path.exists() else "",
                "parse_status": "xml_parsed" if project.root is not None else "fallback_keyword_scan_only",
                "parse_error": project.parse_error,
                "project_attributes": root_attrib,
                "definition_count": len(defs),
                "component_count": len(comps),
                "top_definitions": defs[:80],
                "keyword_hits": find_keyword_hits(project.path, project.keywords),
            }
        )
        term_rows_by_project[project.label] = trace_terms(project.root, INTERFACE_TERMS, project.label)

    graph = build_dependency_graph(projects)
    args.out_data.mkdir(parents=True, exist_ok=True)
    (args.out_data / "pscad_source_file_inventory.json").write_text(
        json.dumps(
            {
                "generated_by": "scripts/analyze_pscad_ibr_type3_mapping.py",
                "mode": "read_only_metadata",
                "files": file_inventory,
                "projects": project_summaries,
            },
            indent=2,
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    (args.out_data / "pscad_component_dependency_graph.json").write_text(
        json.dumps(graph, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    write_csv(
        args.out_data / "ibr_avm_inputs_trace.csv",
        term_rows_by_project["pnnl_3ibr"],
        ["source_project", "term", "element", "id", "name", "defn", "value", "definition_scope", "xml_path", "evidence_class"],
    )
    write_csv(
        args.out_data / "type3_external_interface_trace.csv",
        term_rows_by_project["type3_average"],
        ["source_project", "term", "element", "id", "name", "defn", "value", "definition_scope", "xml_path", "evidence_class"],
    )
    print(json.dumps({"projects": project_summaries, "graph_nodes": len(graph["nodes"]), "graph_edges": len(graph["edges"])}, ensure_ascii=False)[:4000])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
