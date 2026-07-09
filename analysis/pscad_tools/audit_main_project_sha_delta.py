"""Read-only audit for the active 3IBR.pscx SHA delta.

The audit locates the exact protected baseline by SHA-256, compares it with
the current main PSCAD project, classifies every XML attribute/text difference,
and records whether the current main project is functionally equivalent to the
protected baseline.  It never modifies PSCAD files and never invokes PSCAD.
"""

from __future__ import annotations

import csv
import hashlib
import json
import os
import re
import xml.etree.ElementTree as ET
from collections import Counter
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[2]
PROTECTED_SHA = "9A4D8B4594CDEAC3085E34BE64A6A52DA0CB626FE91E37240D0C8CE74F6D33DB"
PREVIOUS_OBSERVED_SHA = "97AE9A99E199734510352DACBDE6120BBC411356C244C3DEA0ED8B01AB2B7906"
CURRENT_MAIN = Path(r"C:\pscad_work\pnnl_39_3ibr_pscad46_strip5\PSCAD\3IBR.pscx")
TRIAL_PROJECT = Path(r"C:\pscad_work\pnnl_39_3ibr_pscad46_strip5\PSCAD\3IBR_DFIG1_TRIAL.pscx")
MAIN_P3F = Path(r"C:\pscad_work\pnnl_39_3ibr_pscad46_strip5\PSCAD\3IBR.gf46\P3.f")

JSON_OUT = REPO_ROOT / "data" / "reference" / "main_project_sha_delta_audit.json"
SUMMARY_CSV = REPO_ROOT / "data" / "reference" / "main_project_sha_delta_audit_summary.csv"
RAW_DIFF_CSV = REPO_ROOT / "data" / "reference" / "main_project_sha_delta_raw_differences.csv"

ALLOWED_ATTR_DIFFS = {"date", "z"}
ALLOWED_PARAM_NAMES = {"revisor"}
PROTECTED_TRIAL_SIGNALS = [
    "BRK_IBR2_TRIAL",
    "IBR2_TRIAL_BRK_CMD",
    "IBR2_TRIAL_BRK_STATE",
    "IBR2_TRIAL_BRK_OPEN_BOOL",
    "IBR2_TRIAL_SOURCE_AVAILABLE",
]
CRITICAL_PATTERNS = [
    "TYPE3_DFIG_1",
    "Type3WTG_Lib",
    "Dblk_DFIG",
    "XFMR_DFIG_22_33",
    "BRK_DFIG",
    "DFIG_BRK_STATE",
    "DFIG_LVRT_",
    "VIBR1_2",
    "PIBR1_2",
    "QIBR1_2",
    "IBR_AVM_2_1_1",
    "VIBR2",
    "PIBR2",
    "QIBR2",
    "VIBR3",
    "PIBR3",
    "QIBR3",
    "CASCADE_MONITOR_",
]


@dataclass
class FileInfo:
    path: str
    sha256: str | None
    size_bytes: int | None
    modified_time: str | None


def sha256(path: Path) -> str | None:
    if not path.exists():
        return None
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def file_info(path: Path) -> FileInfo:
    if not path.exists():
        return FileInfo(str(path), None, None, None)
    stat = path.stat()
    return FileInfo(
        path=str(path),
        sha256=sha256(path),
        size_bytes=stat.st_size,
        modified_time=datetime.fromtimestamp(stat.st_mtime).isoformat(),
    )


def candidate_paths() -> list[Path]:
    out: list[Path] = []
    external = REPO_ROOT / "external"
    if external.exists():
        out.extend(external.rglob("3IBR.pscx"))
    backups = Path(r"C:\pscad_work\backups")
    if backups.exists():
        out.extend(backups.rglob("3IBR.pscx"))
    return sorted(set(out), key=lambda p: str(p).lower())


def locate_baseline() -> tuple[Path | None, list[FileInfo]]:
    candidates: list[FileInfo] = []
    match: Path | None = None
    for path in candidate_paths():
        info = file_info(path)
        candidates.append(info)
        if info.sha256 == PROTECTED_SHA and match is None:
            match = path
    return match, candidates


def element_label(elem: ET.Element, index: int) -> str:
    bits = [elem.tag, str(index)]
    for key in ("id", "name", "defn", "classid"):
        if key in elem.attrib:
            bits.append(f"{key}={elem.attrib[key]}")
    if elem.tag == "param":
        bits.append(f"param={elem.attrib.get('name', '')}")
    return "[" + " ".join(bits) + "]"


def classify_diff(kind: str, path: str, attr: str, old: str, new: str) -> tuple[str, str]:
    if kind == "attr" and attr in ALLOWED_ATTR_DIFFS:
        return (
            "nonfunctional_metadata_or_display_change",
            f"`{attr}` is a PSCAD definition timestamp or visual stacking/display-order field.",
        )
    if kind == "attr" and attr == "value" and "param=revisor" in path:
        return (
            "nonfunctional_metadata_or_display_change",
            "`revisor` records PSCAD save/revision metadata.",
        )
    if kind == "attr" and attr in {"x", "y", "w", "h", "orient"}:
        return (
            "unclassified_difference",
            "Layout coordinate/display attribute changed; topology equivalence cannot be assumed by default.",
        )
    if "master:pgb" in path or "Output Channel" in path:
        return ("output_channel_change", "Output Channel related field changed.")
    if any(token in path or token in old or token in new for token in ("Fault", "Timed Fault", "Duration", "ON", "OFF")):
        return ("test_parameter_change", "Fault/test-parameter related field changed.")
    if kind in {"tag", "child_count", "missing_child", "text"}:
        return ("functional_control_or_network_change", "XML structure or text changed.")
    return ("functional_control_or_network_change", "Parameter, component, or connection field changed.")


def compare_xml(base: ET.Element, cur: ET.Element) -> list[dict[str, str]]:
    diffs: list[dict[str, str]] = []

    def walk(a: ET.Element, b: ET.Element, path: str) -> None:
        if a.tag != b.tag:
            cls, reason = classify_diff("tag", path, "tag", a.tag, b.tag)
            diffs.append({"path": path, "kind": "tag", "field": "tag", "baseline": a.tag, "current": b.tag, "classification": cls, "reason": reason})
            return

        for attr in sorted(set(a.attrib) | set(b.attrib)):
            old = a.attrib.get(attr, "")
            new = b.attrib.get(attr, "")
            if old != new:
                cls, reason = classify_diff("attr", path, attr, old, new)
                diffs.append({"path": path, "kind": "attr", "field": attr, "baseline": old, "current": new, "classification": cls, "reason": reason})

        old_text = (a.text or "").strip()
        new_text = (b.text or "").strip()
        if old_text != new_text:
            cls, reason = classify_diff("text", path, "text", old_text, new_text)
            diffs.append({"path": path, "kind": "text", "field": "text", "baseline": old_text, "current": new_text, "classification": cls, "reason": reason})

        if len(a) != len(b):
            cls, reason = classify_diff("child_count", path, "children", str(len(a)), str(len(b)))
            diffs.append({"path": path, "kind": "child_count", "field": "children", "baseline": str(len(a)), "current": str(len(b)), "classification": cls, "reason": reason})

        for index, (child_a, child_b) in enumerate(zip(list(a), list(b))):
            walk(child_a, child_b, f"{path}/{element_label(child_a, index)}")

    walk(base, cur, f"/{base.tag}")
    return diffs


def project_counts(root: ET.Element) -> dict[str, int]:
    users = [e for e in root.iter() if e.tag == "User"]
    return {
        "component_count": len(users),
        "wire_count": sum(1 for e in root.iter() if e.tag == "Wire"),
        "output_channel_count": sum(1 for e in users if e.attrib.get("defn") == "master:pgb"),
        "page_count": sum(1 for e in root.iter() if e.tag == "Definition" and e.attrib.get("classid") in {"StationDefn", "UserCmpDefn"}),
        "definition_count": sum(1 for e in root.iter() if e.tag == "Definition"),
        "critical_object_count": sum(1 for e in root.iter() if any(token in ET.tostring(e, encoding="unicode", method="xml") for token in CRITICAL_PATTERNS)),
    }


def snapshot_user_params(root: ET.Element) -> dict[str, dict[str, Any]]:
    data: dict[str, dict[str, Any]] = {}
    for elem in root.iter():
        if elem.tag != "User":
            continue
        elem_id = elem.attrib.get("id", "")
        params = {p.attrib.get("name", ""): p.attrib.get("value", "") for p in elem.findall(".//param") if p.attrib.get("name")}
        data[elem_id] = {
            "defn": elem.attrib.get("defn", ""),
            "name": elem.attrib.get("name", ""),
            "params": params,
            "wire_vertices": [],
        }
    return data


def output_channels(root: ET.Element) -> dict[str, dict[str, str]]:
    channels: dict[str, dict[str, str]] = {}
    for elem in root.iter():
        if elem.tag == "User" and elem.attrib.get("defn") == "master:pgb":
            params = {p.attrib.get("name", ""): p.attrib.get("value", "") for p in elem.findall(".//param") if p.attrib.get("name")}
            title = params.get("Name") or params.get("Title") or elem.attrib.get("id", "")
            channels[title] = {
                "id": elem.attrib.get("id", ""),
                "title": title,
                "group": params.get("Group", ""),
                "transfer_data": params.get("Store", params.get("Transfer", "")),
                "multiple_run_save": params.get("Mruns", params.get("MSave", "")),
                "scale_factor": params.get("Scale", params.get("SF", "")),
                "unit": params.get("Unit", ""),
                "min": params.get("Min", params.get("ymin", "")),
                "max": params.get("Max", params.get("ymax", "")),
                "raw_params": json.dumps(params, sort_keys=True),
            }
    return channels


def dict_delta(a: dict[str, Any], b: dict[str, Any]) -> list[str]:
    out: list[str] = []
    for key in sorted(set(a) | set(b)):
        if a.get(key) != b.get(key):
            out.append(key)
    return out


def p3f_info(path: Path) -> dict[str, Any]:
    info = file_info(path)
    return {
        "path": info.path,
        "sha256": info.sha256,
        "size_bytes": info.size_bytes,
        "modified_time": info.modified_time,
        "use_boundary": "auxiliary evidence only; not regenerated and not proof of current main project equivalence",
    }


def trial_status(path: Path) -> dict[str, Any]:
    info = file_info(path)
    text = path.read_text(errors="replace") if path.exists() else ""
    parse_status = "pass"
    if path.exists():
        try:
            ET.parse(path)
        except ET.ParseError:
            parse_status = "fail"
    else:
        parse_status = "missing"
    presence = {signal: bool(re.search(rf"\b{re.escape(signal)}\b", text)) for signal in PROTECTED_TRIAL_SIGNALS}
    expected_absent = not any(presence.values())
    return {
        "trial_exists": path.exists(),
        "trial_sha256": info.sha256,
        "trial_size_bytes": info.size_bytes,
        "trial_modified_time": info.modified_time,
        "trial_xml_parse_status": parse_status,
        "trial_breaker_boundary_status": "not_constructed" if expected_absent else "unexpected_state_detected",
        "trial_has_BRK_IBR2_TRIAL": presence["BRK_IBR2_TRIAL"],
        "trial_has_IBR2_TRIAL_BRK_CMD": presence["IBR2_TRIAL_BRK_CMD"],
        "trial_has_IBR2_TRIAL_BRK_STATE": presence["IBR2_TRIAL_BRK_STATE"],
        "trial_has_IBR2_TRIAL_BRK_OPEN_BOOL": presence["IBR2_TRIAL_BRK_OPEN_BOOL"],
        "trial_has_IBR2_TRIAL_SOURCE_AVAILABLE": presence["IBR2_TRIAL_SOURCE_AVAILABLE"],
    }


def write_csvs(diffs: list[dict[str, str]], summary: dict[str, Any]) -> None:
    JSON_OUT.parent.mkdir(parents=True, exist_ok=True)
    with RAW_DIFF_CSV.open("w", newline="", encoding="utf-8") as handle:
        columns = ["path", "kind", "field", "baseline", "current", "classification", "reason"]
        writer = csv.DictWriter(handle, fieldnames=columns)
        writer.writeheader()
        writer.writerows(diffs)
    with SUMMARY_CSV.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=["key", "value"])
        writer.writeheader()
        for key, value in summary.items():
            writer.writerow({"key": key, "value": json.dumps(value, ensure_ascii=False) if isinstance(value, (dict, list)) else value})


def main() -> int:
    current_start_sha = sha256(CURRENT_MAIN)
    trial_start_sha = sha256(TRIAL_PROJECT)
    baseline_path, candidates = locate_baseline()

    baseline_status = "pass" if baseline_path else "unavailable"
    execution_status = "main_project_sha_delta_audit_complete"

    if baseline_path is None:
        payload = {
            "execution_status": execution_status,
            "baseline_status": "unavailable",
            "functional_equivalence_status": "unavailable",
            "main_project_integrity_status": "baseline_unavailable",
            "trial_resumption_eligibility": "unavailable",
            "baseline_candidates": [info.__dict__ for info in candidates],
        }
        JSON_OUT.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        write_csvs([], payload)
        print("baseline_status=unavailable")
        return 0

    xml_parse_status = "pass"
    try:
        baseline_root = ET.parse(baseline_path).getroot()
        current_root = ET.parse(CURRENT_MAIN).getroot()
    except ET.ParseError:
        xml_parse_status = "fail"
        baseline_root = current_root = ET.Element("parse_failed")

    diffs = compare_xml(baseline_root, current_root) if xml_parse_status == "pass" else []
    classification_counts = Counter(diff["classification"] for diff in diffs)

    baseline_counts = project_counts(baseline_root) if xml_parse_status == "pass" else {}
    current_counts = project_counts(current_root) if xml_parse_status == "pass" else {}
    count_deltas = dict_delta(baseline_counts, current_counts)

    base_components = snapshot_user_params(baseline_root) if xml_parse_status == "pass" else {}
    current_components = snapshot_user_params(current_root) if xml_parse_status == "pass" else {}
    component_inventory_status = "pass" if not dict_delta(base_components, current_components) else "fail"

    base_channels = output_channels(baseline_root) if xml_parse_status == "pass" else {}
    current_channels = output_channels(current_root) if xml_parse_status == "pass" else {}
    output_channel_deltas = dict_delta(base_channels, current_channels)
    output_channel_integrity_status = "pass" if not output_channel_deltas else "fail"

    functional_count = classification_counts.get("functional_control_or_network_change", 0)
    test_count = classification_counts.get("test_parameter_change", 0)
    output_count = classification_counts.get("output_channel_change", 0)
    unclassified_count = classification_counts.get("unclassified_difference", 0)
    connectivity_equivalence_status = "pass" if functional_count == 0 and unclassified_count == 0 and not count_deltas else "fail"
    critical_scope_status = "pass" if functional_count == 0 and test_count == 0 and output_count == 0 and unclassified_count == 0 else "fail"

    raw_byte_identity_status = "pass" if current_start_sha == PROTECTED_SHA else "fail"
    equivalence_supported = all(
        [
            baseline_status == "pass",
            xml_parse_status == "pass",
            connectivity_equivalence_status == "pass",
            critical_scope_status == "pass",
            output_channel_integrity_status == "pass",
            functional_count == 0,
            test_count == 0,
            output_count == 0,
            unclassified_count == 0,
        ]
    )
    functional_equivalence_status = "supported" if equivalence_supported else "not_supported"
    main_project_integrity_status = (
        "main_project_nonfunctional_metadata_difference"
        if equivalence_supported and raw_byte_identity_status == "fail"
        else ("main_project_functional_difference_detected" if functional_count or test_count or output_count else "main_project_unclassified_difference_detected")
    )
    trial = trial_status(TRIAL_PROJECT)
    trial_resumption_eligibility = (
        "eligible_for_separate_task"
        if equivalence_supported and trial["trial_breaker_boundary_status"] == "not_constructed"
        else "not_eligible"
    )

    current_end_sha = sha256(CURRENT_MAIN)
    trial_end_sha = sha256(TRIAL_PROJECT)
    if current_end_sha != current_start_sha or trial_end_sha != trial_start_sha:
        execution_status = "main_project_sha_delta_audit_interrupted"
        functional_equivalence_status = "unavailable"
        trial_resumption_eligibility = "unavailable"

    payload = {
        "schema_version": 1,
        "execution_status": execution_status,
        "baseline_status": baseline_status,
        "raw_byte_identity_status": raw_byte_identity_status,
        "xml_parse_status": xml_parse_status,
        "component_inventory_status": component_inventory_status,
        "connectivity_equivalence_status": connectivity_equivalence_status,
        "critical_scope_status": critical_scope_status,
        "output_channel_integrity_status": output_channel_integrity_status,
        "functional_equivalence_status": functional_equivalence_status,
        "main_project_integrity_status": main_project_integrity_status,
        "trial_resumption_eligibility": trial_resumption_eligibility,
        "baseline": file_info(baseline_path).__dict__,
        "current_main": file_info(CURRENT_MAIN).__dict__,
        "previous_observed_sha": PREVIOUS_OBSERVED_SHA,
        "current_sha_matches_previous_observation": current_start_sha == PREVIOUS_OBSERVED_SHA,
        "trial": trial,
        "p3f_auxiliary_evidence": p3f_info(MAIN_P3F),
        "inventory_counts": {
            "baseline": baseline_counts,
            "current": current_counts,
            "count_delta_keys": count_deltas,
        },
        "difference_counts": {
            "raw_xml_difference_count": len(diffs),
            "nonfunctional_metadata_or_display_change": classification_counts.get("nonfunctional_metadata_or_display_change", 0),
            "functional_control_or_network_change": functional_count,
            "test_parameter_change": test_count,
            "output_channel_change": output_count,
            "unclassified_difference": unclassified_count,
        },
        "output_channel_delta_keys": output_channel_deltas,
        "functional_or_unclassified_differences": [
            diff for diff in diffs if diff["classification"] != "nonfunctional_metadata_or_display_change"
        ],
        "nonfunctional_difference_examples": [
            diff for diff in diffs if diff["classification"] == "nonfunctional_metadata_or_display_change"
        ][:50],
        "baseline_candidates": [info.__dict__ for info in candidates],
        "claim_boundary": {
            "pscad_started": False,
            "build_performed": False,
            "run_performed": False,
            "main_project_modified": False,
            "trial_project_modified": False,
            "breaker_construction_resumed": False,
            "second_source_event_packet_created": False,
            "dual_source_collector_created": False,
        },
        "audit_file_sha_stability": {
            "current_main_start_sha": current_start_sha,
            "current_main_end_sha": current_end_sha,
            "trial_start_sha": trial_start_sha,
            "trial_end_sha": trial_end_sha,
        },
    }

    JSON_OUT.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    write_csvs(diffs, {
        "execution_status": execution_status,
        "baseline_status": baseline_status,
        "raw_byte_identity_status": raw_byte_identity_status,
        "xml_parse_status": xml_parse_status,
        "component_inventory_status": component_inventory_status,
        "connectivity_equivalence_status": connectivity_equivalence_status,
        "critical_scope_status": critical_scope_status,
        "output_channel_integrity_status": output_channel_integrity_status,
        "functional_equivalence_status": functional_equivalence_status,
        "main_project_integrity_status": main_project_integrity_status,
        "trial_resumption_eligibility": trial_resumption_eligibility,
        **payload["difference_counts"],
    })

    print(f"execution_status={execution_status}")
    print(f"baseline_status={baseline_status}")
    print(f"raw_byte_identity_status={raw_byte_identity_status}")
    print(f"functional_equivalence_status={functional_equivalence_status}")
    print(f"main_project_integrity_status={main_project_integrity_status}")
    print(f"trial_resumption_eligibility={trial_resumption_eligibility}")
    print(f"raw_xml_difference_count={len(diffs)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
