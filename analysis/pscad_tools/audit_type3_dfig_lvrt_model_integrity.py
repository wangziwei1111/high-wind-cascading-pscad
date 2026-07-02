"""Read-only structural integrity audit for two PSCAD project files."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import os
import re
import xml.etree.ElementTree as ET
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Any


CATEGORIES = (
    "functional_control_or_network_change",
    "test_parameter_change",
    "nonfunctional_metadata_or_display_change",
    "unclassified_difference",
)

KEY_TERMS = (
    "DFIG_LVRT_",
    "BRK_DFIG",
    "Type3WTG_Lib",
    "Dblk_DFIG",
    "XFMR_DFIG_22_33",
    "VIBR1_2",
    "PIBR1_2",
    "QIBR1_2",
)

NONFUNCTIONAL_PARAMS = {
    "Pdisplay",
    "Qdisplay",
    "Vdisplay",
    "Idisplay",
    "description",
    "Description",
    "FortranComment",
}

NONFUNCTIONAL_ATTRS = {"date", "z", "view"}
LAYOUT_ATTRS = {"x", "y", "w", "h"}
TEST_PARAM_PATTERNS = (
    "fault",
    "resistance",
    "ron",
    "roff",
    "duration",
    "time to apply",
    "wind",
    "plotstep",
    "timestep",
    "delt",
    "time_duration",
)


@dataclass
class Component:
    key: str
    page: str
    tag: str
    component_id: str
    component_type: str
    name: str
    attrs: dict[str, str]
    params: dict[str, str]
    vertices: tuple[tuple[tuple[str, str], ...], ...]

    @property
    def searchable(self) -> str:
        return " ".join(
            [self.page, self.tag, self.component_type, self.name]
            + list(self.params.keys())
            + list(self.params.values())
        )


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def direct_params(element: ET.Element) -> dict[str, str]:
    result: dict[str, str] = {}
    for paramlist in element.findall("./paramlist"):
        for param in paramlist.findall("./param"):
            name = param.attrib.get("name", "")
            result[name] = param.attrib.get("value", "")
    return result


def vertex_signature(element: ET.Element) -> tuple[tuple[tuple[str, str], ...], ...]:
    return tuple(tuple(sorted(vertex.attrib.items())) for vertex in element.findall("./vertex"))


def parse_project(path: Path) -> dict[str, Any]:
    tree = ET.parse(path)
    root = tree.getroot()
    components: dict[str, Component] = {}
    definitions: dict[str, dict[str, str]] = {}
    duplicate_keys: list[str] = []

    for definition in root.findall(".//Definition"):
        definition_id = definition.attrib.get("id", "")
        page = definition.attrib.get("name", "") or definition_id or "unnamed_definition"
        def_key = f"{definition.attrib.get('classid', '')}:{page}:{definition_id}"
        definitions[def_key] = dict(definition.attrib)
        for element in definition.iter():
            if element is definition or "id" not in element.attrib:
                continue
            component_id = element.attrib["id"]
            key = f"{page}/{element.tag}/{component_id}"
            component = Component(
                key=key,
                page=page,
                tag=element.tag,
                component_id=component_id,
                component_type=element.attrib.get("defn", element.attrib.get("classid", element.tag)),
                name=element.attrib.get("name", ""),
                attrs=dict(element.attrib),
                params=direct_params(element),
                vertices=vertex_signature(element),
            )
            if key in components:
                duplicate_keys.append(key)
            components[key] = component

    output_channels = {
        key: {
            "page": component.page,
            "id": component.component_id,
            "title": component.params.get("Name"),
            "unit": component.params.get("Units"),
            "transfer": component.params.get("enab"),
            "multiple_run_save": component.params.get("mrun"),
            "display_min": component.params.get("Min"),
            "display_max": component.params.get("Max"),
            "params": component.params,
        }
        for key, component in components.items()
        if component.component_type.lower() == "master:pgb"
    }
    key_objects = {
        key: component.searchable
        for key, component in components.items()
        if any(term.lower() in component.searchable.lower() for term in KEY_TERMS)
    }
    wires = {
        key: {
            "page": component.page,
            "attrs": component.attrs,
            "vertices": component.vertices,
        }
        for key, component in components.items()
        if component.tag.lower() == "wire"
    }
    return {
        "root_tag": root.tag,
        "root_attrs": dict(root.attrib),
        "project_params": direct_params(root),
        "definitions": definitions,
        "components": components,
        "output_channels": output_channels,
        "key_objects": key_objects,
        "wires": wires,
        "duplicate_component_keys": duplicate_keys,
    }


def is_key_component(component: Component) -> bool:
    searchable = component.searchable.lower()
    return any(term.lower() in searchable for term in KEY_TERMS)


def is_output_channel(component: Component) -> bool:
    return component.component_type.lower() == "master:pgb"


def classify_component_difference(component: Component, field: str, kind: str) -> tuple[str, str]:
    lower_field = field.lower()
    if component.tag.lower() == "wire" or kind == "vertices":
        return CATEGORIES[0], "wire geometry/connection relationship changed"
    if field in NONFUNCTIONAL_ATTRS or field in LAYOUT_ATTRS:
        return CATEGORIES[2], "display stacking, layout, or revision metadata changed"
    if component.component_type.lower() == "master:breaker3" and field in {"P", "Q"}:
        return CATEGORIES[2], "saved breaker P/Q run-display value changed; circuit and command parameters are compared separately"
    if is_output_channel(component):
        return CATEGORIES[0], "Output Channel instance or parameter changed"
    if is_key_component(component):
        if field in NONFUNCTIONAL_ATTRS or field in LAYOUT_ATTRS or field in NONFUNCTIONAL_PARAMS:
            return CATEGORIES[2], "key-object layout/display metadata changed"
        return CATEGORIES[0], "critical LVRT/breaker-related object changed"
    if any(pattern in lower_field for pattern in TEST_PARAM_PATTERNS):
        return CATEGORIES[1], "test or runtime parameter changed"
    if field in NONFUNCTIONAL_PARAMS or field in NONFUNCTIONAL_ATTRS or field in LAYOUT_ATTRS:
        return CATEGORIES[2], "display, layout, description, or revision metadata changed"
    if kind in {"added", "removed", "type"}:
        return CATEGORIES[0], "component inventory/type changed"
    return CATEGORIES[3], "parameter/attribute difference has no proven harmless classification"


def semantically_equal_parameter(before: str | None, after: str | None) -> bool:
    if before == after:
        return True
    if before is None or after is None:
        return False
    number = r"[-+]?(?:\d+(?:\.\d*)?|\.\d+)(?:[Ee][-+]?\d+)?"
    before_match = re.fullmatch(rf"\s*({number})(?:\s*\[[^]]+\])?\s*", before)
    after_match = re.fullmatch(rf"\s*({number})(?:\s*\[[^]]+\])?\s*", after)
    if not before_match or not after_match:
        return False
    return math.isclose(float(before_match.group(1)), float(after_match.group(1)), rel_tol=0.0, abs_tol=1e-12)


def add_diff(
    differences: list[dict[str, Any]],
    category: str,
    reason: str,
    object_type: str,
    object_key: str,
    field: str,
    before: Any,
    after: Any,
) -> None:
    differences.append(
        {
            "category": category,
            "reason": reason,
            "object_type": object_type,
            "object_key": object_key,
            "field": field,
            "before": before,
            "after": after,
        }
    )


def compare_components(before: dict[str, Component], after: dict[str, Component]) -> list[dict[str, Any]]:
    differences: list[dict[str, Any]] = []
    for key in sorted(set(before) | set(after)):
        old = before.get(key)
        new = after.get(key)
        representative = old or new
        assert representative is not None
        if old is None or new is None:
            kind = "added" if old is None else "removed"
            category, reason = classify_component_difference(representative, "component", kind)
            add_diff(differences, category, reason, representative.tag, key, kind, old.searchable if old else None, new.searchable if new else None)
            continue
        if old.component_type != new.component_type:
            category, reason = classify_component_difference(new, "component_type", "type")
            add_diff(differences, category, reason, new.tag, key, "component_type", old.component_type, new.component_type)
        for field in sorted(set(old.attrs) | set(new.attrs)):
            if field in {"id", "classid", "defn", "name"}:
                continue
            if old.attrs.get(field) != new.attrs.get(field):
                category, reason = classify_component_difference(new, field, "attribute")
                add_diff(differences, category, reason, new.tag, key, f"attribute:{field}", old.attrs.get(field), new.attrs.get(field))
        for field in sorted(set(old.params) | set(new.params)):
            if not semantically_equal_parameter(old.params.get(field), new.params.get(field)):
                category, reason = classify_component_difference(new, field, "parameter")
                add_diff(differences, category, reason, new.tag, key, f"parameter:{field}", old.params.get(field), new.params.get(field))
        if old.vertices != new.vertices:
            category, reason = classify_component_difference(new, "vertices", "vertices")
            add_diff(differences, category, reason, new.tag, key, "vertices", old.vertices, new.vertices)
    return differences


def compare_metadata(before: dict[str, Any], after: dict[str, Any]) -> list[dict[str, Any]]:
    differences: list[dict[str, Any]] = []
    for field in sorted(set(before["project_params"]) | set(after["project_params"])):
        old = before["project_params"].get(field)
        new = after["project_params"].get(field)
        if old == new:
            continue
        if field == "revisor" or field in NONFUNCTIONAL_PARAMS:
            category, reason = CATEGORIES[2], "project revision/description metadata changed"
        elif any(pattern in field.lower() for pattern in TEST_PARAM_PATTERNS):
            category, reason = CATEGORIES[1], "project runtime/test parameter changed"
        else:
            category, reason = CATEGORIES[3], "project-level parameter difference is unclassified"
        add_diff(differences, category, reason, "project", "project", f"parameter:{field}", old, new)
    for key in sorted(set(before["definitions"]) | set(after["definitions"])):
        old = before["definitions"].get(key)
        new = after["definitions"].get(key)
        if old is None or new is None:
            add_diff(differences, CATEGORIES[0], "definition inventory changed", "definition", key, "presence", old, new)
            continue
        for field in sorted(set(old) | set(new)):
            if old.get(field) == new.get(field):
                continue
            if field in NONFUNCTIONAL_ATTRS:
                category, reason = CATEGORIES[2], "definition revision/view metadata changed"
            else:
                category, reason = CATEGORIES[3], "definition attribute difference is unclassified"
            add_diff(differences, category, reason, "definition", key, f"attribute:{field}", old.get(field), new.get(field))
    return differences


def file_info(path: Path) -> dict[str, Any]:
    stat = path.stat()
    return {
        "path": str(path),
        "sha256": sha256(path),
        "size_bytes": stat.st_size,
        "modified_time_ns": stat.st_mtime_ns,
    }


def audit(backup: Path, active: Path, expected_backup_sha: str, expected_active_sha: str) -> dict[str, Any]:
    backup_info = file_info(backup)
    active_info = file_info(active)
    backup_valid = backup_info["sha256"] == expected_backup_sha.upper()
    active_matches_expected = active_info["sha256"] == expected_active_sha.upper()
    if not backup_valid:
        return {
            "execution_status": "model_integrity_audit_unavailable",
            "model_integrity_status": "model_integrity_needs_explanation",
            "reason": "selected backup does not match the required task-start SHA-256",
            "backup": backup_info,
            "active": active_info,
        }

    try:
        before = parse_project(backup)
        after = parse_project(active)
        parse_status = "pass"
        parse_error = None
    except ET.ParseError as exc:
        return {
            "execution_status": "model_integrity_audit_partial",
            "model_integrity_status": "model_integrity_needs_explanation",
            "backup": backup_info,
            "active": active_info,
            "xml_parse_status": "fail",
            "xml_parse_error": str(exc),
        }

    differences = compare_metadata(before, after) + compare_components(before["components"], after["components"])
    counts = Counter(item["category"] for item in differences)
    count_map = {category: counts.get(category, 0) for category in CATEGORIES}
    if count_map[CATEGORIES[0]]:
        integrity_status = "model_integrity_functional_difference_detected"
    elif count_map[CATEGORIES[1]] or count_map[CATEGORIES[3]]:
        integrity_status = "model_integrity_needs_explanation"
    else:
        integrity_status = "model_integrity_nonfunctional_metadata_difference"

    gain_id = "65646757"
    gain_before = [component for component in before["components"].values() if component.component_id == gain_id]
    gain_after = [component for component in after["components"].values() if component.component_id == gain_id]
    if not gain_before and not gain_after:
        gain_conclusion = "absent_from_exact_task_start_backup_and_current_active_project"
    elif gain_before and gain_after:
        gain_conclusion = "present_in_both_projects"
    else:
        gain_conclusion = "presence_differs_between_projects"

    output_before = {item["title"]: item for item in before["output_channels"].values()}
    output_after = {item["title"]: item for item in after["output_channels"].values()}
    output_titles_added = sorted(set(output_after) - set(output_before))
    output_titles_removed = sorted(set(output_before) - set(output_after))
    output_titles_changed = sorted(
        title for title in set(output_before) & set(output_after) if output_before[title]["params"] != output_after[title]["params"]
    )

    functional_equivalence = (
        "proven_for_audited_structure_and_parameters"
        if integrity_status == "model_integrity_nonfunctional_metadata_difference"
        else "not_proven"
    )
    return {
        "execution_status": "type3_lvrt_model_integrity_audit_complete",
        "model_integrity_status": integrity_status,
        "backup": backup_info,
        "active": active_info,
        "expected_backup_sha256": expected_backup_sha.upper(),
        "expected_active_sha256": expected_active_sha.upper(),
        "backup_exact_match": backup_valid,
        "active_exact_match": active_matches_expected,
        "raw_files_equal": backup_info["sha256"] == active_info["sha256"],
        "xml_parse_status": parse_status,
        "xml_parse_error": parse_error,
        "inventory": {
            "backup_component_count": len(before["components"]),
            "active_component_count": len(after["components"]),
            "backup_wire_count": len(before["wires"]),
            "active_wire_count": len(after["wires"]),
            "backup_output_channel_count": len(before["output_channels"]),
            "active_output_channel_count": len(after["output_channels"]),
            "backup_duplicate_component_keys": before["duplicate_component_keys"],
            "active_duplicate_component_keys": after["duplicate_component_keys"],
        },
        "difference_count": len(differences),
        "difference_counts_by_category": count_map,
        "differences": differences,
        "output_channel_comparison": {
            "titles_added": output_titles_added,
            "titles_removed": output_titles_removed,
            "titles_with_parameter_changes": output_titles_changed,
        },
        "critical_object_scan": {
            "backup_matching_object_count": len(before["key_objects"]),
            "active_matching_object_count": len(after["key_objects"]),
            "matching_object_keys_added": sorted(set(after["key_objects"]) - set(before["key_objects"])),
            "matching_object_keys_removed": sorted(set(before["key_objects"]) - set(after["key_objects"])),
        },
        "master_gain_65646757": {
            "backup_presence_count": len(gain_before),
            "active_presence_count": len(gain_after),
            "conclusion": gain_conclusion,
        },
        "functional_equivalence": functional_equivalence,
        "audit_scope_note": "The audit compares raw bytes, parseable XML structure, component inventory/type/title/page, wire vertices, direct component parameters, Output Channels, critical objects, and metadata/display fields. Unknown differences remain unclassified by design.",
    }


def write_csv(result: dict[str, Any], path: Path) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=["category", "object_type", "object_key", "field", "before", "after", "reason"],
        )
        writer.writeheader()
        writer.writerows(result.get("differences", []))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--backup", required=True, type=Path)
    parser.add_argument("--active", required=True, type=Path)
    parser.add_argument("--expected-backup-sha", required=True)
    parser.add_argument("--expected-active-sha", required=True)
    parser.add_argument("--json-out", required=True, type=Path)
    parser.add_argument("--csv-out", required=True, type=Path)
    args = parser.parse_args()
    result = audit(args.backup, args.active, args.expected_backup_sha, args.expected_active_sha)
    args.json_out.parent.mkdir(parents=True, exist_ok=True)
    args.csv_out.parent.mkdir(parents=True, exist_ok=True)
    args.json_out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_csv(result, args.csv_out)
    print(json.dumps({"model_integrity_status": result["model_integrity_status"], "difference_counts": result.get("difference_counts_by_category")}, indent=2))


if __name__ == "__main__":
    main()
