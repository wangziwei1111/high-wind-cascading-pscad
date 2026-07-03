#!/usr/bin/env python3
"""Pre-run gate for Stage 8 PAPER_OVL1 runtime output observability.

Read-only. Run this only after the user performs the single GUI repair and a
PSCAD Build. It verifies the rebuilt trial generated code has exactly one
Output Channel title for each Stage 8 canonical signal before any Run is
allowed.
"""

from __future__ import annotations

import csv
import hashlib
import json
import re
import subprocess
import xml.etree.ElementTree as ET
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any


REPO = Path(__file__).resolve().parents[2]
PSCAD = Path(r"C:\pscad_work\pnnl_39_3ibr_pscad46_strip5\PSCAD")
MAIN = PSCAD / "3IBR.pscx"
TRIAL = PSCAD / "3IBR_DFIG1_TRIAL.pscx"
GF46 = PSCAD / "3IBR_DFIG1_TRIAL.gf46"
P3_F = GF46 / "P3.f"
PROJECT_MAP = GF46 / "3IBR_DFIG1_TRIAL.map"
P3_DTA = GF46 / "P3.dta"

EXPECTED_MAIN_SHA = "CBA120BB167CB7FA6C4A1AE4471268850AB61761EC1877EB7B87015627FE9DAB"
EXPECTED_START_COMMIT = "31e886e715f59846019e86ff8ade5d7b7ebdf27d"
REPAIR_COMPONENT_ID = 518433536
REAL_RELAY_ENABLE_COMPONENT_ID = 865554842

CANONICAL = [
    "PAPER_OVL1_S_A_PU",
    "PAPER_OVL1_S_B_PU",
    "PAPER_OVL1_S_MAX_PU",
    "PAPER_OVL1_EFFECTIVE_CAPACITY_PU",
    "PAPER_OVL1_LOADING_INDEX_EQ",
    "PAPER_OVL1_ABOVE_THRESHOLD",
    "PAPER_OVL1_TIMER_OR_CURVE_STATE",
    "PAPER_OVL1_TRIP_REQUEST",
    "PAPER_OVL1_BRK_CMD",
    "PAPER_OVL1_BRK_STATE",
    "PAPER_OVL1_TRIP_EVENT_VALID",
    "PAPER_OVL1_FIRST_TRIP_TIME_S",
    "PAPER_OVL1_RELAY_ENABLE",
]


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest().upper()


def git(*args: str) -> str:
    return subprocess.check_output(["git", *args], cwd=REPO, text=True, encoding="utf-8").strip()


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fields: list[str] = []
    for row in rows:
        for key in row:
            if key not in fields:
                fields.append(key)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows(rows)


def param(user: ET.Element, name: str) -> str:
    for p in user.findall(".//param"):
        if p.attrib.get("name") == name:
            return p.attrib.get("value", "")
    return ""


def parse_users() -> list[dict[str, Any]]:
    root = ET.parse(TRIAL).getroot()
    rows: list[dict[str, Any]] = []
    for u in root.findall(".//User"):
        rows.append({
            "id": int(u.attrib["id"]),
            "name": u.attrib.get("name", ""),
            "defn": u.attrib.get("defn", ""),
            "x": int(float(u.attrib.get("x", "0"))),
            "y": int(float(u.attrib.get("y", "0"))),
            "z": int(float(u.attrib.get("z", "0"))),
            "title": param(u, "Name"),
            "scale": param(u, "Scale"),
            "use_signal_name": param(u, "UseSignalName"),
            "enabled": param(u, "enab"),
        })
    return rows


def nearest_label(pgb: dict[str, Any], labels: list[dict[str, Any]]) -> dict[str, Any] | None:
    candidates = [
        (abs(pgb["y"] - l["y"]) + max(0, pgb["x"] - l["x"]), l)
        for l in labels
        if abs(pgb["y"] - l["y"]) <= 12 and l["x"] <= pgb["x"]
    ]
    return sorted(candidates, key=lambda t: t[0])[0][1] if candidates else None


def parse_p3_pgb() -> list[dict[str, Any]]:
    if not P3_F.exists():
        return []
    lines = P3_F.read_text(encoding="utf-8", errors="ignore").splitlines()
    rows: list[dict[str, Any]] = []
    for i, line in enumerate(lines):
        m = re.search(r"\[pgb\] Output Channel '([^']+)'", line)
        if not m:
            continue
        assignment = ""
        for nxt in lines[i + 1 : i + 8]:
            if "PGB(" in nxt:
                assignment = nxt.strip()
                break
        m2 = re.search(r"PGB\(IPGB\+(\d+)\)\s*=\s*(.*)", assignment)
        rows.append({
            "title": m.group(1),
            "p3_f_line": i + 1,
            "pgb_offset": int(m2.group(1)) if m2 else None,
            "runtime_expression": m2.group(2).strip() if m2 else "",
        })
    return rows


def main() -> None:
    users = parse_users()
    labels = [u for u in users if u["name"] == "master:datalabel"]
    paper_pgbs = [u for u in users if u["name"] == "master:pgb" and str(u["title"]).startswith("PAPER_OVL1_")]
    title_counts = Counter(u["title"] for u in paper_pgbs)
    p3_rows = [r for r in parse_p3_pgb() if str(r["title"]).startswith("PAPER_OVL1_")]
    p3_by_title: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in p3_rows:
        p3_by_title[row["title"]].append(row)

    trace: list[dict[str, Any]] = []
    for pgb in sorted(paper_pgbs, key=lambda r: (r["y"], r["x"])):
        src = nearest_label(pgb, labels)
        matches = p3_by_title.get(pgb["title"], [])
        trace.append({
            "output_channel_component_id": pgb["id"],
            "output_channel_title": pgb["title"],
            "source_label_left_of_channel": src["title"] if src else "",
            "x": pgb["x"],
            "y": pgb["y"],
            "xml_title_count": title_counts[pgb["title"]],
            "p3_f_title_count": len(matches),
            "p3_f_runtime_expression": matches[0]["runtime_expression"] if matches else "",
            "p3_f_line": matches[0]["p3_f_line"] if matches else "",
            "pgb_offset": matches[0]["pgb_offset"] if matches else "",
        })

    canonical_rows: list[dict[str, Any]] = []
    for name in CANONICAL:
        xml_matches = [r for r in trace if r["output_channel_title"] == name]
        p3_matches = p3_by_title.get(name, [])
        generated_present = len(p3_matches) >= 1
        canonical_rows.append({
            "canonical_title": name,
            "xml_title_count": len(xml_matches),
            "p3_f_title_count": len(p3_matches),
            "source_labels": ";".join(sorted(set(r["source_label_left_of_channel"] for r in xml_matches))),
            "runtime_expressions": ";".join(r["runtime_expression"] for r in p3_matches),
            "status": "pass" if len(xml_matches) == 1 and generated_present else "fail",
        })

    repair_component = next((r for r in trace if r["output_channel_component_id"] == REPAIR_COMPONENT_ID), None)
    relay_enable_component = next((r for r in trace if r["output_channel_component_id"] == REAL_RELAY_ENABLE_COMPONENT_ID), None)
    main_sha = sha256(MAIN)
    trial_sha = sha256(TRIAL)
    head = git("rev-parse", "HEAD")

    gates = {
        "git_head_contains_stage7_start": subprocess.run(
            ["git", "merge-base", "--is-ancestor", EXPECTED_START_COMMIT, "HEAD"],
            cwd=REPO,
            text=True,
            capture_output=True,
            check=False,
        ).returncode == 0,
        "main_project_sha_unchanged": main_sha == EXPECTED_MAIN_SHA,
        "p3_f_exists_after_build": P3_F.exists(),
        "project_map_exists_after_build": PROJECT_MAP.exists(),
        "p3_dta_exists_after_build": P3_DTA.exists(),
        "all_13_xml_titles_unique": all(r["xml_title_count"] == 1 for r in canonical_rows),
        "all_13_generated_pgb_titles_present": all(r["p3_f_title_count"] >= 1 for r in canonical_rows),
        "above_threshold_component_repaired": bool(
            repair_component
            and repair_component["output_channel_title"] == "PAPER_OVL1_ABOVE_THRESHOLD"
            and repair_component["source_label_left_of_channel"] == "PAPER_OVL1_ABOVE_THRESHOLD"
        ),
        "relay_enable_component_preserved": bool(
            relay_enable_component
            and relay_enable_component["output_channel_title"] == "PAPER_OVL1_RELAY_ENABLE"
            and relay_enable_component["source_label_left_of_channel"] == "PAPER_OVL1_RELAY_ENABLE"
        ),
        "paper_ovl1_frozen_line_present": "E_28_29_1" in P3_F.read_text(encoding="utf-8", errors="ignore") if P3_F.exists() else False,
        "breaker_command_present": "PAPER_OVL1_BRK_CMD" in P3_F.read_text(encoding="utf-8", errors="ignore") if P3_F.exists() else False,
    }
    execution_status = "pre_run_gate_pass" if all(gates.values()) else "pre_run_gate_fail"

    payload = {
        "audit_name": "stage8_pre_run_output_gate",
        "generated_at_local": datetime.now().isoformat(timespec="seconds"),
        "execution_status": execution_status,
        "git_head": head,
        "main_sha": main_sha,
        "trial_sha_after_gui_repair_and_build": trial_sha,
        "frozen_selected_line": "E_28_29_1",
        "frozen_effective_capacity_pu": 7.872883989661206,
        "frozen_threshold_multiplier": 1.1,
        "frozen_delay_s": 5.0,
        "gates": gates,
        "canonical_output_gate": canonical_rows,
        "component_trace": trace,
        "run_authorization": "RUN_ALLOWED_ONCE" if execution_status == "pre_run_gate_pass" else "RUN_BLOCKED",
    }

    write_json(REPO / "data/validation/stage8_pre_run_output_gate.json", payload)
    write_csv(REPO / "data/validation/stage8_pre_run_output_gate_trace.csv", trace)

    doc = [
        "# STAGE8 pre-run output gate",
        "",
        f"Status: `{execution_status}`",
        "",
        "This read-only gate is run only after the single GUI repair and Build.",
        "",
        "Run is allowed only when all gates are true:",
        "",
    ]
    for key, value in gates.items():
        doc.append(f"- `{key}`: `{value}`")
    doc.extend([
        "",
        "If status is `pre_run_gate_pass`, perform exactly one PSCAD Run for Stage 8.",
        "If status is `pre_run_gate_fail`, do not Run; inspect the generated JSON and repair only the failing item.",
        "",
    ])
    (REPO / "docs/STAGE8_PRE_RUN_OUTPUT_GATE.md").write_text("\n".join(doc), encoding="utf-8")

    print(json.dumps({
        "execution_status": execution_status,
        "run_authorization": payload["run_authorization"],
        "failed_gates": [k for k, v in gates.items() if not v],
    }, ensure_ascii=False, indent=2))
    if execution_status != "pre_run_gate_pass":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
