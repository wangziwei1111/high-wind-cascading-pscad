#!/usr/bin/env python3
"""Resolve the real IBR2_TRIAL production path for corrected audits.

This tool is read-only with respect to PSCAD projects.  It distinguishes the
actual P3 production source-B path from MODULE_TEMPLATE_TEST_HARNESS instances.
"""

from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path
import re
import sys
import xml.etree.ElementTree as ET


PSCAD_ROOT = Path(r"C:\pscad_work\pnnl_39_3ibr_pscad46_strip5\PSCAD")
MAIN_PROJECT = PSCAD_ROOT / "3IBR.pscx"
TRIAL_PROJECT = PSCAD_ROOT / "3IBR_DFIG1_TRIAL.pscx"
P3_F = PSCAD_ROOT / "3IBR_DFIG1_TRIAL.gf46" / "P3.f"
P3_DTA = PSCAD_ROOT / "3IBR_DFIG1_TRIAL.gf46" / "P3.dta"

CORRECTION_JSON = Path("data/validation/three_source_controlled_chronology_production_target_correction.json")
TRACE_CSV = Path("data/validation/three_source_controlled_chronology_production_target_trace.csv")

EXPECTED_MAIN_SHA256 = "CBA120BB167CB7FA6C4A1AE4471268850AB61761EC1877EB7B87015627FE9DAB"
EXPECTED_OUTPUT_CHANNEL_COUNT = 253


def sha256(path: Path) -> str | None:
    if not path.exists():
        return None
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest().upper()


def params(elem: ET.Element | None) -> dict[str, str]:
    if elem is None:
        return {}
    return {p.get("name", ""): p.get("value", "") for p in elem.findall("./paramlist/param")}


def number(value: str | None) -> float | None:
    try:
        return float(value) if value is not None else None
    except ValueError:
        return None


def name_param(elem: ET.Element) -> str:
    p = params(elem)
    return p.get("Name") or p.get("NAME") or ""


def describe(elem: ET.Element | None) -> dict[str, object] | None:
    if elem is None:
        return None
    p = params(elem)
    return {
        "id": elem.get("id"),
        "defn": elem.get("defn") or elem.get("name"),
        "x": number(elem.get("x")),
        "y": number(elem.get("y")),
        "name": p.get("Name") or p.get("NAME") or "",
        "value": p.get("Value"),
        "open_time_s": p.get("OPEN_TIME_S"),
        "cause_code_value": p.get("CAUSE_CODE_VALUE"),
        "sbra": p.get("SBRA"),
    }


def collect(root: ET.Element, defn: str | None = None, name: str | None = None) -> list[ET.Element]:
    out: list[ET.Element] = []
    for elem in root.iter():
        if elem.tag != "User":
            continue
        if defn is not None and elem.get("defn") != defn:
            continue
        if name is not None and name_param(elem) != name:
            continue
        out.append(elem)
    return out


def first(root: ET.Element, defn: str | None = None, name: str | None = None) -> ET.Element | None:
    hits = collect(root, defn, name)
    return hits[0] if hits else None


def nearest_constant(root: ET.Element, x: float, y: float, value: str | None = None) -> ET.Element | None:
    best: tuple[float, ET.Element] | None = None
    for elem in collect(root, "master:const"):
        p = params(elem)
        if value is not None and p.get("Value") != value:
            continue
        ex = number(elem.get("x"))
        ey = number(elem.get("y"))
        if ex is None or ey is None:
            continue
        if abs(ex - x) <= 180 and abs(ey - y) <= 72:
            dist = abs(ex - x) + abs(ey - y)
            if best is None or dist < best[0]:
                best = (dist, elem)
    return best[1] if best else None


def colocated_pgb(root: ET.Element, signal_name: str, x: float, y: float) -> ET.Element | None:
    for elem in collect(root, "master:pgb", signal_name):
        ex = number(elem.get("x"))
        ey = number(elem.get("y"))
        if ex is not None and ey is not None and abs(ex - x) <= 36 and abs(ey - y) <= 36:
            return elem
    return None


def production_label_with_pgb(root: ET.Element, label_name: str, pgb_name: str) -> ET.Element | None:
    for label in collect(root, "master:datalabel", label_name):
        lx = number(label.get("x"))
        ly = number(label.get("y"))
        if lx is None or ly is None:
            continue
        if colocated_pgb(root, pgb_name, lx, ly) is not None:
            return label
    return None


def pgb_names(root: ET.Element) -> list[str]:
    return [name_param(e) for e in collect(root, "master:pgb") if name_param(e)]


def pgb_mapping(root: ET.Element) -> dict[str, int]:
    names = pgb_names(root)
    return {name: i + 1 for i, name in enumerate(names)}


def p3f_hits(pattern: str) -> list[dict[str, object]]:
    if not P3_F.exists():
        return []
    rx = re.compile(pattern)
    hits = []
    for idx, line in enumerate(P3_F.read_text(encoding="utf-8", errors="ignore").splitlines(), 1):
        if rx.search(line):
            hits.append({"file": str(P3_F), "line": idx, "text": line.strip()})
    return hits


def hierarchy_contains(raw: str, link: str, parent_name: str) -> bool:
    parent = raw.find(parent_name)
    child = raw.find(f'link="{link}"')
    return parent != -1 and child != -1 and parent < child


def status(ok: bool) -> str:
    return "pass" if ok else "fail"


def resolve(write_outputs: bool = True) -> dict[str, object]:
    root = ET.parse(TRIAL_PROJECT).getroot()
    raw_xml = TRIAL_PROJECT.read_text(encoding="utf-8", errors="ignore")
    names = pgb_names(root)
    pgb = {name: i + 1 for i, name in enumerate(names)}

    enable_label = production_label_with_pgb(root, "IBR2_TEST_ENABLE", "IBR2_TRIAL_TEST_ENABLE")
    enable_const = None
    if enable_label is not None:
        enable_const = nearest_constant(root, number(enable_label.get("x")) - 108, number(enable_label.get("y")))  # type: ignore[operator]

    open_time_label = production_label_with_pgb(root, "IBR2_TEST_OPEN_TIME_S", "IBR2_TRIAL_TEST_OPEN_TIME_S")
    open_time_const = None
    if open_time_label is not None:
        open_time_const = nearest_constant(root, number(open_time_label.get("x")) - 90, number(open_time_label.get("y")), "4")  # type: ignore[operator]

    open_request = production_label_with_pgb(root, "IBR2_TEST_OPEN_REQ", "IBR2_TRIAL_TEST_OPEN_REQUEST")
    brk_cmd_pgb = first(root, "master:pgb", "IBR2_TRIAL_BRK_CMD")
    brk_cmd_labels = collect(root, "master:datalabel", "IBR2_TRIAL_BRK_CMD")
    breaker = first(root, "master:breaker3", "BRK_IBR2_TRIAL")

    harness_stim = first(root, name="MODTEST_ONE_SHOT_STIMULUS")
    harness_packet = first(root, name="MODTEST_OBJECT_EVENT_PACKET")
    harness_stim_id = harness_stim.get("id") if harness_stim is not None else None
    harness_packet_id = harness_packet.get("id") if harness_packet is not None else None

    source_b_outputs = {
        "event_valid": first(root, "master:pgb", "IBR2_TRIAL_CASCADE_EVENT_VALID"),
        "cause": first(root, "master:pgb", "IBR2_TRIAL_CASCADE_EVENT_CAUSE_CODE"),
        "breaker_open": first(root, "master:pgb", "IBR2_TRIAL_CASCADE_EVENT_BRK_OPEN"),
        "source_available": first(root, "master:pgb", "IBR2_TRIAL_CASCADE_SOURCE_AVAILABLE"),
        "first_event_time": first(root, "master:pgb", "IBR2_TRIAL_CASCADE_FIRST_EVENT_TIME_S"),
    }

    production_trace = [
        {
            "step": "production_ibr2_test_enable_constant",
            "evidence": "P3 XML label IBR2_TEST_ENABLE is co-located with Output Channel IBR2_TRIAL_TEST_ENABLE; nearest Constant is the restored production enable value.",
            "xml": describe(enable_const),
            "p3f": p3f_hits(r"IBR2_TEST_ENABLE = 0\.0|PGB\(IPGB\+5\) = IBR2_TEST_ENABLE"),
        },
        {
            "step": "production_ibr2_open_time_source",
            "evidence": "P3 XML label IBR2_TEST_OPEN_TIME_S is co-located with Output Channel IBR2_TRIAL_TEST_OPEN_TIME_S and Constant 4.",
            "xml": describe(open_time_const),
            "p3f": p3f_hits(r"IBR2_TEST_OPEN_TIME_S = 4\.0|PGB\(IPGB\+3\) = IBR2_TEST_OPEN_TIME_S"),
        },
        {
            "step": "production_ibr2_open_request_signal",
            "evidence": "P3 XML Output Channel IBR2_TRIAL_TEST_OPEN_REQUEST records IBR2_TEST_OPEN_REQ; P3.f forms it from enable, armed, and time-reached logic.",
            "xml": describe(open_request),
            "p3f": p3f_hits(r"IBR2_TEST_ARMED = IBR2_TEST_ENABLE|IBR2_TRIAL_BRK_CMD = 1\.0 \* IBR2_TEST_CMD_LIMITED"),
        },
        {
            "step": "production_ibr2_breaker_command_signal",
            "evidence": "IBR2_TRIAL_BRK_CMD has a production PGB and is assigned from IBR2_TEST_CMD_LIMITED, then drives BRK_IBR2_TRIAL.",
            "xml": {"pgb": describe(brk_cmd_pgb), "labels": [describe(e) for e in brk_cmd_labels]},
            "p3f": p3f_hits(r"IBR2_TRIAL_BRK_CMD = 1\.0 \* IBR2_TEST_CMD_LIMITED|BRK_IBR2_TRIAL = 1\.0 \* IBR2_TRIAL_BRK_CMD"),
        },
        {
            "step": "production_ibr2_breaker_boundary",
            "evidence": "The real three-phase breaker is BRK_IBR2_TRIAL and returns state through IBR2_TRIAL_BRK_STATE.",
            "xml": describe(breaker),
            "p3f": p3f_hits(r"3 Phase Breaker 'BRK_IBR2_TRIAL'|IBR2_TRIAL_BRK_STATE = IVD1_1"),
        },
        {
            "step": "production_source_b_event_packet_logic",
            "evidence": "Production source-B event packet is implemented by P3 source-B labels/logic, not by MODTEST_OBJECT_EVENT_PACKET; cause is assigned as 4.0 * IBR2_CAS_EVT_VALID.",
            "xml": {
                "event_valid_labels": [describe(e) for e in collect(root, "master:datalabel", "IBR2_CAS_EVT_VALID")],
                "cause_labels": [describe(e) for e in collect(root, "master:datalabel", "IBR2_CAS_CAUSE")],
                "first_time_labels": [describe(e) for e in collect(root, "master:datalabel", "IBR2_CAS_FIRST_S")],
            },
            "p3f": p3f_hits(r"IBR2_CAS_EVT_VALID = 1\.0 \* IBR2_CAS_LATCH_MEM|IBR2_CAS_CAUSE = 4\.0 \* IBR2_CAS_EVT_VALID|IBR2_CAS_FIRST_S = 1\.0 \* IBR2_CAS_TIME_MEM"),
        },
        {
            "step": "production_source_b_output_interface",
            "evidence": "The production source-B labels feed the IBR2_TRIAL_CASCADE_* Output Channels used by the dynamic run parser.",
            "xml": {key: describe(value) for key, value in source_b_outputs.items()},
            "p3f": p3f_hits(r"PGB\(IPGB\+33\) = IBR2_CAS_CAUSE|PGB\(IPGB\+35\) = IBR2_CAS_EVT_VALID|PGB\(IPGB\+86\) = IBR2_CAS_FIRST_S"),
        },
    ]

    harness_exclusion = {
        "module_test_harness_path": "MODULE_TEMPLATE_TEST_HARNESS",
        "excluded_objects": {
            "MODTEST_ONE_SHOT_STIMULUS": describe(harness_stim),
            "MODTEST_OBJECT_EVENT_PACKET": describe(harness_packet),
        },
        "hierarchy_evidence": {
            "stimulus_under_module_template_test_harness": hierarchy_contains(raw_xml, str(harness_stim_id), "MODULE_TEMPLATE_TEST_HARNESS") if harness_stim_id else False,
            "packet_under_module_template_test_harness": hierarchy_contains(raw_xml, str(harness_packet_id), "MODULE_TEMPLATE_TEST_HARNESS") if harness_packet_id else False,
        },
    }

    checks = {
        "harness_target_exclusion_status": status(
            harness_exclusion["hierarchy_evidence"]["stimulus_under_module_template_test_harness"]
            and harness_exclusion["hierarchy_evidence"]["packet_under_module_template_test_harness"]
        ),
        "production_target_resolution_status": status(
            enable_const is not None
            and params(enable_const).get("Value") == "0"
            and open_time_const is not None
            and params(open_time_const).get("Value") == "4"
            and brk_cmd_pgb is not None
            and breaker is not None
            and params(breaker).get("SBRA") == "IBR2_TRIAL_BRK_STATE"
            and all(v is not None for v in source_b_outputs.values())
        ),
        "production_path_trace_status": status(
            bool(p3f_hits(r"IBR2_TEST_ENABLE = 0\.0"))
            and bool(p3f_hits(r"IBR2_TEST_OPEN_TIME_S = 4\.0"))
            and bool(p3f_hits(r"IBR2_TRIAL_BRK_CMD = 1\.0 \* IBR2_TEST_CMD_LIMITED"))
            and bool(p3f_hits(r"BRK_IBR2_TRIAL = 1\.0 \* IBR2_TRIAL_BRK_CMD"))
            and bool(p3f_hits(r"IBR2_CAS_CAUSE = 4\.0 \* IBR2_CAS_EVT_VALID"))
        ),
    }

    report = {
        "execution_status": "ibr2_trial_production_path_resolution",
        "main_project": str(MAIN_PROJECT),
        "trial_project": str(TRIAL_PROJECT),
        "p3_f": str(P3_F),
        "p3_dta": str(P3_DTA),
        "main_sha": sha256(MAIN_PROJECT),
        "trial_sha_read_only": sha256(TRIAL_PROJECT),
        "output_channel_count": len(names),
        "output_channel_count_status": status(len(names) == EXPECTED_OUTPUT_CHANNEL_COUNT),
        "main_project_integrity_status": status(sha256(MAIN_PROJECT) == EXPECTED_MAIN_SHA256),
        "prior_audit_targeting_status": "superseded_harness_target_error",
        "production_path": {
            "production_ibr2_test_enable_constant": describe(enable_const),
            "production_ibr2_test_enable_label": describe(enable_label),
            "production_ibr2_open_time_source": describe(open_time_const),
            "production_ibr2_open_request_signal": describe(open_request),
            "production_ibr2_breaker_command_signal": describe(brk_cmd_pgb),
            "production_ibr2_breaker_state_signal": "IBR2_TRIAL_BRK_STATE",
            "production_ibr2_open_bool_signal": "IBR2_CAS_BRK_OPEN / IBR2_TRIAL_CASCADE_EVENT_BRK_OPEN",
            "production_ibr2_source_available_signal": "IBR2_CAS_AVAIL / IBR2_TRIAL_CASCADE_SOURCE_AVAILABLE",
            "production_source_b_event_packet_object": "P3 inline production source-B event packet logic group (IBR2_CAS_* labels), not MODTEST_OBJECT_EVENT_PACKET",
            "production_source_b_cause_code_parameter": "IBR2_CAS_CAUSE = 4.0 * IBR2_CAS_EVT_VALID",
            "production_source_b_event_valid_signal": "IBR2_CAS_EVT_VALID / IBR2_TRIAL_CASCADE_EVENT_VALID",
            "production_source_b_first_event_time_signal": "IBR2_CAS_FIRST_S / IBR2_TRIAL_CASCADE_FIRST_EVENT_TIME_S",
            "production_source_b_cause_output_signal": "IBR2_CAS_CAUSE / IBR2_TRIAL_CASCADE_EVENT_CAUSE_CODE",
            "production_output_channel_mapping": {k: pgb.get(k) for k in [
                "IBR2_TRIAL_TEST_ENABLE",
                "IBR2_TRIAL_TEST_OPEN_TIME_S",
                "IBR2_TRIAL_TEST_OPEN_REQUEST",
                "IBR2_TRIAL_BRK_CMD",
                "IBR2_TRIAL_BRK_STATE",
                "IBR2_TRIAL_BRK_OPEN_BOOL",
                "IBR2_TRIAL_SOURCE_AVAILABLE",
                "IBR2_TRIAL_CASCADE_EVENT_VALID",
                "IBR2_TRIAL_CASCADE_EVENT_CAUSE_CODE",
                "IBR2_TRIAL_CASCADE_EVENT_BRK_OPEN",
                "IBR2_TRIAL_CASCADE_SOURCE_AVAILABLE",
                "IBR2_TRIAL_CASCADE_FIRST_EVENT_TIME_S",
            ]},
        },
        "module_test_harness_path": harness_exclusion,
        "production_trace": production_trace,
        "checks": checks,
    }
    report["execution_status"] = (
        "ibr2_trial_production_path_resolved_pass"
        if all(value == "pass" for value in checks.values())
        and report["main_project_integrity_status"] == "pass"
        and report["output_channel_count_status"] == "pass"
        else "ibr2_trial_production_path_resolution_fallback"
    )

    if write_outputs:
        CORRECTION_JSON.parent.mkdir(parents=True, exist_ok=True)
        CORRECTION_JSON.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        with TRACE_CSV.open("w", newline="", encoding="utf-8") as fh:
            writer = csv.writer(fh)
            writer.writerow(["step", "evidence", "xml_summary", "p3f_lines"])
            for step in production_trace:
                writer.writerow([
                    step["step"],
                    step["evidence"],
                    json.dumps(step["xml"], ensure_ascii=False),
                    json.dumps(step["p3f"], ensure_ascii=False),
                ])
    return report


def main() -> int:
    report = resolve(write_outputs=True)
    print(json.dumps(report, indent=2, ensure_ascii=False))
    return 0 if report["execution_status"] == "ibr2_trial_production_path_resolved_pass" else 2


if __name__ == "__main__":
    sys.exit(main())
