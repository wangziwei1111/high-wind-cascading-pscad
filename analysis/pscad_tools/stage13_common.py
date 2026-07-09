#!/usr/bin/env python3
"""Shared helpers for Stage-13 zero-model post-second-trip classification."""

from __future__ import annotations

import csv
import hashlib
import json
import math
import re
from collections import defaultdict, deque
from pathlib import Path
from statistics import fmean
from typing import Any


REPO = Path(__file__).resolve().parents[2]
PSCAD = Path(r"C:\pscad_work\pnnl_39_3ibr_pscad46_strip5\PSCAD")
MAIN = PSCAD / "3IBR.pscx"
TRIAL = PSCAD / "3IBR_DFIG1_TRIAL.pscx"
GF46 = PSCAD / "3IBR_DFIG1_TRIAL.gf46"
P3_DTA = GF46 / "P3.dta"
P3_MAP = GF46 / "3IBR_DFIG1_TRIAL.map"
INF = GF46 / "3IBR_DFIG1_TRIAL.inf"
PREFIX = "3IBR_DFIG1_TRIAL"
EXPECTED_MAIN_SHA = "CBA120BB167CB7FA6C4A1AE4471268850AB61761EC1877EB7B87015627FE9DAB"
STAGE12_TRIAL_SHA = "74EB2656E6F65106F519F1F1D85492CBF6960008588835F219D8F88B27C483CE"
OPENED_LINES = {"E_28_29_1", "E_26_29_1"}
WINDOWS = {
    "W0_pre_fault": (0.00, 0.49),
    "W1_fault": (0.50, 2.50),
    "W2_dfig_to_first_line": (2.51, 7.53),
    "W3_first_to_second_line": (7.54, 12.60),
    "W4_post_second_line": (12.61, 20.00),
}


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest().upper()


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


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


def parse_inf(path: Path = INF) -> list[dict[str, Any]]:
    pat = re.compile(r'^PGB\((\d+)\)\s+Output\s+Desc="([^"]*)"\s+Group="([^"]*)".*Units="([^"]*)"')
    rows = []
    for line in path.read_text(encoding="utf-8", errors="ignore").splitlines():
        if m := pat.search(line):
            rows.append({"pgb_index": int(m.group(1)), "title": m.group(2), "group": m.group(3), "units": m.group(4)})
    return rows


def load_out(path: Path) -> list[list[float]]:
    return [[float(x) for x in line.split()] for line in path.read_text(encoding="ascii", errors="ignore").splitlines() if line.split()]


class RuntimeReader:
    def __init__(self, gf46: Path = GF46) -> None:
        self.inf = parse_inf(gf46 / f"{PREFIX}.inf")
        self.by_title: dict[str, list[dict[str, Any]]] = {}
        for row in self.inf:
            self.by_title.setdefault(row["title"], []).append(row)
        self.outs = sorted(gf46.glob(f"{PREFIX}_*.out"))
        self.cache: dict[int, list[list[float]]] = {}
        first = load_out(self.outs[0]) if self.outs else []
        self.channels_per_file = len(first[0]) - 1 if first else 0
        if first:
            self.cache[1] = first
        self.time = [r[0] for r in first] if first else []

    def series(self, title: str) -> tuple[list[float], list[float]]:
        matches = self.by_title.get(title, [])
        if len(matches) != 1 or self.channels_per_file <= 0:
            return [], []
        idx = matches[0]["pgb_index"]
        file_no, col = (idx - 1) // self.channels_per_file + 1, (idx - 1) % self.channels_per_file + 1
        if file_no not in self.cache:
            self.cache[file_no] = load_out(GF46 / f"{PREFIX}_{file_no:02d}.out")
        rows = self.cache[file_no]
        return [r[0] for r in rows], [r[col] for r in rows]

    def branch_ids(self) -> list[str]:
        return sorted({m.group(1) for row in self.inf if (m := re.match(r"^(E_\d+_\d+_1)_[AB]_[PQI]$", row["title"]))})

    def branch_smax(self, branch: str) -> tuple[list[float], list[float]]:
        pa_t, pa = self.series(f"{branch}_A_P")
        qa_t, qa = self.series(f"{branch}_A_Q")
        pb_t, pb = self.series(f"{branch}_B_P")
        qb_t, qb = self.series(f"{branch}_B_Q")
        if not pa_t or not (pa_t == qa_t == pb_t == qb_t):
            return [], []
        return pa_t, [max(math.hypot(a, b), math.hypot(c, d)) for a, b, c, d in zip(pa, qa, pb, qb)]


def window_values(t: list[float], v: list[float], lo: float, hi: float) -> list[float]:
    return [y for x, y in zip(t, v) if lo <= x <= hi]


def stats(t: list[float], v: list[float], lo: float, hi: float) -> dict[str, float | None]:
    values = window_values(t, v, lo, hi)
    return {"mean": fmean(values) if values else None, "max": max(values) if values else None, "min": min(values) if values else None}


def classify_voltage_scope(channel_name: str) -> str:
    if channel_name in {"CASCADE3_ELEC_DFIG_V", "VIBR1_2", "VIBR2_2", "VIBR3_2"}:
        return "wind_pcc_only"
    if re.fullmatch(r"V\d+", channel_name) or channel_name.startswith("Vm_"):
        return "local_bus_only"
    if channel_name.startswith("V_Mach"):
        return "generator_terminal_only"
    return "unmapped_or_ambiguous"


def voltage_risk_from_channels(channel_scopes: list[str], sustained_low: bool) -> str:
    if not channel_scopes:
        return "voltage_observability_insufficient"
    if any(scope == "network_wide_representative" for scope in channel_scopes) and sustained_low:
        return "voltage_risk_observed"
    if sustained_low:
        return "local_voltage_response_only"
    return "local_voltage_response_only"


def frequency_status_from_candidates(classes: list[str], risky: bool) -> tuple[str, str, str]:
    if "direct_system_frequency" not in classes:
        return ("frequency_observability_insufficient", "ufls_precondition_not_evaluable", "generator_underfrequency_precondition_not_evaluable")
    return ("frequency_risk_observed" if risky else "frequency_risk_not_observed", "ufls_precondition_evaluable", "generator_underfrequency_precondition_evaluable")


def longest_continuous_interval(t: list[float], mask: list[bool]) -> tuple[float | None, float | None, float]:
    best = (None, None, 0.0)
    start = None
    last = None
    for x, ok in zip(t, mask):
        if ok:
            if start is None:
                start = x
            last = x
            if last - start > best[2]:
                best = (start, last, last - start)
        else:
            start = None
            last = None
    return best


def third_line_readiness(separable: bool, duration_s: float, transient_only: bool) -> str:
    if not separable:
        return "third_line_not_defensible"
    if duration_s >= 5.0 and not transient_only:
        return "third_line_candidate_ready"
    if duration_s > 0 and not transient_only:
        return "third_line_candidate_requires_longer_run"
    return "third_line_not_defensible"


def tline_terminals_from_dta(name: str, dta_path: Path = P3_DTA) -> tuple[int, int] | None:
    lines = dta_path.read_text(encoding="utf-8", errors="ignore").splitlines()
    for i, line in enumerate(lines):
        if line.strip().startswith(f"! {name}"):
            return int(lines[i + 2].split()[0]), int(lines[i + 3].split()[0])
    return None


def topology_partition(branches: list[tuple[str, int, int]], opened: set[str]) -> dict[str, Any]:
    active = [(name, a, b) for name, a, b in branches if name not in opened]
    buses = sorted({bus for _, a, b in active for bus in (a, b)})
    graph: dict[int, set[int]] = defaultdict(set)
    for _, a, b in active:
        graph[a].add(b)
        graph[b].add(a)
    seen: set[int] = set()
    comps = []
    for bus in buses:
        if bus in seen:
            continue
        q = deque([bus])
        seen.add(bus)
        comp = []
        while q:
            cur = q.popleft()
            comp.append(cur)
            for nxt in graph[cur]:
                if nxt not in seen:
                    seen.add(nxt)
                    q.append(nxt)
        comps.append(sorted(comp))
    return {
        "status": "connected_after_second_trip" if len(comps) == 1 else "partitioned_after_second_trip",
        "component_count": len(comps),
        "components": comps,
        "opened_lines_removed": sorted(opened),
    }
