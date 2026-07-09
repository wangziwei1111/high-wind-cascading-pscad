#!/usr/bin/env python3
"""Shared helpers and frozen constants for Stage 15 paper WF33/35/38 refactor."""

from __future__ import annotations

import csv
import hashlib
import json
import re
import xml.etree.ElementTree as ET
from collections import deque
from pathlib import Path
from typing import Any


REPO = Path(__file__).resolve().parents[2]
PSCAD_ROOT = Path(r"C:\pscad_work\pnnl_39_3ibr_pscad46_strip5\PSCAD")
MAIN = PSCAD_ROOT / "3IBR.pscx"
LEGACY_TRIAL = PSCAD_ROOT / "3IBR_DFIG1_TRIAL.pscx"
NEW_TRIAL = PSCAD_ROOT / "3IBR_PAPER_WF33_35_38_TRIAL.pscx"
NEW_GF46 = PSCAD_ROOT / "3IBR_PAPER_WF33_35_38_TRIAL.gf46"
BACKUP = Path(r"C:\pscad_work\pnnl_39_3ibr_pscad46_strip5\_backups\stage15_before_paper_wf33_35_38_refactor")
STAGE7_BASELINE = Path(r"C:\pscad_work\pnnl_39_3ibr_pscad46_strip5\_backups\stage7_before_paper_calibrated_first_trip\PSCAD\3IBR_DFIG1_TRIAL.pscx")
EXPECTED_MAIN_SHA = "CBA120BB167CB7FA6C4A1AE4471268850AB61761EC1877EB7B87015627FE9DAB"
START_COMMIT = "0a277d4d5577bb84d5d1ac9b3623cd7d00f5e0a2"
LEGACY_TRIAL_SHA = "74EB2656E6F65106F519F1F1D85492CBF6960008588835F219D8F88B27C483CE"

OUTPUT_CHANNELS = [
    "WF33_PCC_V", "WF33_PCC_P", "WF33_PCC_Q", "WF33_LVRT_TRIP_REQUEST", "WF33_BRK_STATE",
    "WF35_PCC_V", "WF35_PCC_P", "WF35_PCC_Q", "WF35_LVRT_TRIP_REQUEST", "WF35_BRK_STATE",
    "WF38_PCC_V", "WF38_PCC_P", "WF38_PCC_Q", "WF38_LVRT_TRIP_REQUEST", "WF38_BRK_STATE",
]

GENERATOR_TARGETS = {
    "bus30": {"definition": "G_30_0_1_DYR", "P": 250.0, "Q": 146.456, "V": 1.0475, "name": "Wang_30"},
    "WF33": {"target_bus": 33, "definition": "G_33_0_1_DYR", "P": 632.0, "Q": 123.3861, "V": 0.9972, "name": "Wang_33"},
    "WF35": {"target_bus": 35, "definition": "G_35_0_1_DYR", "P": 650.0, "Q": 225.0912, "V": 1.0493, "name": "Wang_35"},
    "WF38": {"target_bus": 38, "definition": "G_38_0_1_DYR", "P": 830.0, "Q": 41.0678, "V": 1.0265, "name": "Wang_38"},
}

PAPER_WIND_POWER = {"WF33": 632.0, "WF35": 650.0, "WF38": 850.0}


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest().upper()


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore")


def load_xml(path: Path) -> ET.Element:
    return ET.fromstring(read_text(path))


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def write_csv(path: Path, rows: list[dict[str, Any]], fields: list[str] | None = None) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if fields is None:
        fields = []
        for row in rows:
            for key in row:
                if key not in fields:
                    fields.append(key)
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def count_user_refs(path: Path, token: str) -> int:
    root = load_xml(path)
    return sum(token in ((u.get("name") or "") + " " + (u.get("defn") or "")) for u in root.findall(".//User"))


def count_defs(path: Path, token: str) -> int:
    root = load_xml(path)
    return sum(token in (d.get("name") or "") for d in root.findall(".//Definition"))


def definition_params(path: Path, definition: str) -> dict[str, str]:
    root = load_xml(path)
    found = next((d for d in root.findall(".//Definition") if d.get("name") == definition), None)
    params: dict[str, str] = {}
    if found is None:
        return params
    for param in found.findall(".//param"):
        name, value = param.get("name"), param.get("value")
        if name and value is not None:
            params[name] = value
    return params


def p3_tline_edges(p3_dta: Path) -> list[tuple[str, int, int]]:
    if not p3_dta.exists():
        return []
    lines = read_text(p3_dta).splitlines()
    edges = []
    for i, line in enumerate(lines):
        m = re.match(r"!\s+(E_\d+_\d+_1)\s+", line.strip())
        if not m or i + 3 >= len(lines):
            continue
        try:
            a = int(lines[i + 2].split()[0])
            b = int(lines[i + 3].split()[0])
        except Exception:
            continue
        edges.append((m.group(1), a, b))
    return edges


def shortest_path(edges: list[tuple[str, int, int]], src: int, dst: int) -> tuple[int | None, str]:
    graph: dict[int, list[tuple[int, str]]] = {}
    for name, a, b in edges:
        graph.setdefault(a, []).append((b, name))
        graph.setdefault(b, []).append((a, name))
    q = deque([(src, [])])
    seen = {src}
    while q:
        node, path = q.popleft()
        if node == dst:
            return len(path), " -> ".join(path)
        for nxt, edge_name in graph.get(node, []):
            if nxt not in seen:
                seen.add(nxt)
                q.append((nxt, path + [edge_name]))
    return None, ""


def stage7_gf46() -> Path:
    return STAGE7_BASELINE.parent / "3IBR_DFIG1_TRIAL.gf46"


def static_status_ready() -> str:
    return "stage15_static_ready_for_gui_refactor"
