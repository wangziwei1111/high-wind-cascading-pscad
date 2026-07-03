#!/usr/bin/env python3
"""Shared helpers for Stage-12 second-line trip preparation and auditing."""

from __future__ import annotations

import csv
import hashlib
import json
import math
import re
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from pathlib import Path
from statistics import fmean
from typing import Any


REPO = Path(__file__).resolve().parents[2]
PSCAD = Path(r"C:\pscad_work\pnnl_39_3ibr_pscad46_strip5\PSCAD")
MAIN = PSCAD / "3IBR.pscx"
TRIAL = PSCAD / "3IBR_DFIG1_TRIAL.pscx"
GF46 = PSCAD / "3IBR_DFIG1_TRIAL.gf46"
P3_DTA = GF46 / "P3.dta"
P3_F = GF46 / "P3.f"
P3_MAP = GF46 / "3IBR_DFIG1_TRIAL.map"
INF = GF46 / "3IBR_DFIG1_TRIAL.inf"
PREFIX = "3IBR_DFIG1_TRIAL"

EXPECTED_MAIN_SHA = "CBA120BB167CB7FA6C4A1AE4471268850AB61761EC1877EB7B87015627FE9DAB"
STAGE11_COMMIT = "0a53d1217ffde1f1ba101ef658d0c3c0bab7b17a"
STAGE11_DFIG_TRIP_S = 2.44
STAGE11_FIRST_LINE_OPEN_S = 7.53
STAGE12_RUN_DURATION_S = 20.0
STAGE12_PLOT_STEP_S = 0.01
STAGE12_SOLUTION_STEP_US = 50.0
THRESHOLD_MULTIPLIER = 1.1
DEFINITE_DELAY_S = 5.0
FIRST_LINE = "E_28_29_1"


@dataclass(frozen=True)
class CandidateResult:
    tline_id: str
    eligible: bool
    rejection_reason: str
    pre_first_trip_max_s: float | None
    post_first_trip_5s_floor_s: float | None
    threshold_t: float | None
    effective_capacity_c_eff: float | None
    selection_margin: float | None
    expected_pickup_time_s: float | None
    expected_second_open_time_s: float | None
    selected_5s_window_start_s: float | None
    selected_5s_window_end_s: float | None
    sustained_sample_count: int
    score: float


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
    rows: list[dict[str, Any]] = []
    pat = re.compile(r'^PGB\((\d+)\)\s+Output\s+Desc="([^"]*)"\s+Group="([^"]*)".*Units="([^"]*)"')
    for line in path.read_text(encoding="utf-8", errors="ignore").splitlines():
        if m := pat.search(line):
            rows.append({"pgb_index": int(m.group(1)), "title": m.group(2), "group": m.group(3), "units": m.group(4)})
    return rows


def load_out(path: Path) -> list[list[float]]:
    rows: list[list[float]] = []
    for line in path.read_text(encoding="ascii", errors="ignore").splitlines():
        if line.split():
            rows.append([float(x) for x in line.split()])
    return rows


class RuntimeReader:
    def __init__(self, gf46: Path = GF46, prefix: str = PREFIX) -> None:
        self.gf46 = gf46
        self.prefix = prefix
        self.inf = parse_inf(gf46 / f"{prefix}.inf")
        self.by_title: dict[str, list[dict[str, Any]]] = {}
        for row in self.inf:
            self.by_title.setdefault(row["title"], []).append(row)
        self.outs = sorted(gf46.glob(f"{prefix}_*.out"))
        self._cache: dict[int, list[list[float]]] = {}
        first = load_out(self.outs[0]) if self.outs else []
        self.channels_per_file = len(first[0]) - 1 if first else 0
        if first:
            self._cache[1] = first
        self.time = [row[0] for row in first] if first else []

    def series(self, title: str) -> tuple[list[float], list[float]]:
        matches = self.by_title.get(title, [])
        if len(matches) != 1 or self.channels_per_file <= 0:
            return [], []
        idx = matches[0]["pgb_index"]
        number, column = (idx - 1) // self.channels_per_file + 1, (idx - 1) % self.channels_per_file + 1
        if number not in self._cache:
            path = self.gf46 / f"{self.prefix}_{number:02d}.out"
            self._cache[number] = load_out(path) if path.exists() else []
        data = self._cache[number]
        return [row[0] for row in data], [row[column] for row in data]

    def branch_ids(self) -> list[str]:
        return sorted({m.group(1) for row in self.inf if (m := re.match(r"^(E_\d+_\d+_1)_[AB]_[PQI]$", row["title"]))})

    def branch_smax(self, branch_id: str) -> tuple[list[float], list[float]]:
        pa_t, pa = self.series(f"{branch_id}_A_P")
        qa_t, qa = self.series(f"{branch_id}_A_Q")
        pb_t, pb = self.series(f"{branch_id}_B_P")
        qb_t, qb = self.series(f"{branch_id}_B_Q")
        if not pa_t or not (pa_t == qa_t == pb_t == qb_t):
            return [], []
        return pa_t, [max(math.hypot(a, b), math.hypot(c, d)) for a, b, c, d in zip(pa, qa, pb, qb)]


def first_true_run(t: list[float], mask: list[bool], required_duration_s: float) -> tuple[int | None, int | None]:
    """Return first continuous True run covering at least required_duration_s."""
    start: int | None = None
    last: int | None = None
    for idx, ok in enumerate(mask):
        if ok:
            if start is None:
                start = idx
            last = idx
            if t[last] - t[start] >= required_duration_s - 1e-12:
                return start, last
        else:
            start = None
            last = None
    return None, None


def best_5s_floor_window(
    t: list[float],
    s: list[float],
    search_start_s: float,
    latest_pickup_s: float,
    duration_s: float = DEFINITE_DELAY_S,
) -> tuple[float | None, float | None, float | None, int]:
    """Find the 5 s window with the largest minimum S floor."""
    best_floor: float | None = None
    best_start: float | None = None
    best_end: float | None = None
    best_count = 0
    for start_idx, start_t in enumerate(t):
        if start_t < search_start_s or start_t > latest_pickup_s:
            continue
        end_t = start_t + duration_s
        idxs = [i for i, x in enumerate(t) if start_t <= x <= end_t]
        if not idxs or t[idxs[-1]] < end_t - 1e-12:
            continue
        floor = min(s[i] for i in idxs)
        if best_floor is None or floor > best_floor + 1e-12:
            best_floor = floor
            best_start = start_t
            best_end = t[idxs[-1]]
            best_count = len(idxs)
    return best_floor, best_start, best_end, best_count


def evaluate_second_trip_candidate(
    tline_id: str,
    t: list[float],
    s: list[float],
    first_open_s: float = STAGE11_FIRST_LINE_OPEN_S,
    search_start_s: float = 7.54,
    latest_second_open_s: float = 15.00,
    delay_s: float = DEFINITE_DELAY_S,
) -> CandidateResult:
    if not t or not s or len(t) != len(s):
        return CandidateResult(tline_id, False, "missing_or_misaligned_runtime_series", None, None, None, None, None, None, None, None, None, 0, -1.0)
    pre_values = [value for x, value in zip(t, s) if 0.0 <= x <= first_open_s]
    if not pre_values:
        return CandidateResult(tline_id, False, "empty_pre_first_trip_window", None, None, None, None, None, None, None, None, None, 0, -1.0)
    pre_max = max(pre_values)
    latest_pickup = latest_second_open_s - delay_s
    floor, win_start, win_end, count = best_5s_floor_window(t, s, search_start_s, latest_pickup, delay_s)
    if floor is None or win_start is None or win_end is None:
        return CandidateResult(tline_id, False, "no_5s_post_first_trip_window_before_15s", pre_max, None, None, None, None, None, None, None, None, 0, -1.0)
    if floor <= pre_max:
        return CandidateResult(tline_id, False, "post_5s_floor_not_above_pre_first_trip_max", pre_max, floor, None, None, floor - pre_max, None, None, win_start, win_end, count, -1.0)
    threshold = (pre_max + floor) / 2.0
    c_eff = threshold / THRESHOLD_MULTIPLIER
    if any(value >= threshold for x, value in zip(t, s) if 0.0 <= x <= first_open_s):
        return CandidateResult(tline_id, False, "would_pickup_before_or_at_first_trip", pre_max, floor, threshold, c_eff, floor - pre_max, None, None, win_start, win_end, count, -1.0)
    post_mask = [x > first_open_s and x <= latest_second_open_s and value >= threshold for x, value in zip(t, s)]
    run_start, run_end = first_true_run(t, post_mask, delay_s)
    if run_start is None or run_end is None:
        return CandidateResult(tline_id, False, "threshold_not_sustained_5s_after_first_trip", pre_max, floor, threshold, c_eff, floor - pre_max, None, None, win_start, win_end, count, -1.0)
    pickup_t = t[run_start]
    open_t = pickup_t + delay_s
    if pickup_t <= first_open_s:
        return CandidateResult(tline_id, False, "pickup_not_after_first_trip", pre_max, floor, threshold, c_eff, floor - pre_max, pickup_t, open_t, win_start, win_end, count, -1.0)
    if open_t > latest_second_open_s + 1e-12:
        return CandidateResult(tline_id, False, "expected_open_after_15s", pre_max, floor, threshold, c_eff, floor - pre_max, pickup_t, open_t, win_start, win_end, count, -1.0)
    margin = floor - pre_max
    post_mean = fmean(value for x, value in zip(t, s) if win_start <= x <= win_end)
    persistence_score = post_mean - pre_max
    timing_score = max(0.0, latest_second_open_s - open_t)
    topology_bonus = 2.0 if tline_id in {"E_26_29_1", "E_17_27_1", "E_25_26_1", "E_26_27_1"} else 0.0
    score = margin * 100.0 + persistence_score * 10.0 + timing_score + topology_bonus
    return CandidateResult(tline_id, True, "", pre_max, floor, threshold, c_eff, margin, pickup_t, open_t, win_start, win_end, count, score)


def project_settings(path: Path = TRIAL) -> dict[str, str]:
    root = ET.parse(path).getroot()
    return {p.get("name", ""): p.get("value", "") for p in root.findall("./paramlist/param")}


def user_params(user: ET.Element) -> dict[str, str]:
    return {p.get("name", ""): p.get("value", "") for p in user.findall("./paramlist/param")}


def tline_terminals_from_dta(name: str, dta_path: Path = P3_DTA) -> list[dict[str, Any]]:
    lines = dta_path.read_text(encoding="utf-8", errors="ignore").splitlines()
    marker = next(i for i, line in enumerate(lines) if line.strip().startswith(f"! {name}"))
    result = []
    for side, line in zip(("A", "B"), lines[marker + 2 : marker + 4]):
        values = [int(value) for value in line.split()[:4]]
        result.append({"side": side, "compiled_bus": values[0], "phase_nodes": values[1:]})
    return result


def detect_bypass_or_isolated(
    selected_endpoints_before: list[dict[str, Any]],
    selected_endpoints_after: list[dict[str, Any]],
    breaker_present: bool,
    breaker_command_ok: bool,
    forbidden_driver_hits: list[str],
) -> dict[str, Any]:
    """Small testable decision helper for the compiled pre-run gate."""
    before_buses = [row["compiled_bus"] for row in selected_endpoints_before]
    after_buses = [row["compiled_bus"] for row in selected_endpoints_after]
    isolated = any(bus <= 0 for bus in after_buses)
    unchanged = before_buses == after_buses
    return {
        "compiled_endpoint_buses_preserved": unchanged,
        "no_isolated_bus": not isolated,
        "breaker_present": breaker_present,
        "breaker_command_only": breaker_command_ok and not forbidden_driver_hits,
        "forbidden_driver_hits": forbidden_driver_hits,
        "passed": unchanged and (not isolated) and breaker_present and breaker_command_ok and not forbidden_driver_hits,
    }


def stage12_forbidden_parameter_changes() -> list[str]:
    return [
        "N29 fault parameters and timing",
        "DFIG LVRT thresholds, delay, controls, BRK_DFIG, and event packet",
        "PAPER_OVL1 relay, capacity, threshold, delay, breaker, and outputs",
        "E_26_29_1 N29 endpoint repair",
        "E_28_29_1 endpoint and PAPER_OVL1 series boundary",
        "all TLine R/X/B and existing Output Channels",
        "solution time step, plot step, and single-run target",
    ]


def json_default(value: Any) -> Any:
    if hasattr(value, "__dict__"):
        return value.__dict__
    raise TypeError(type(value).__name__)
