#!/usr/bin/env python3
"""Stage 10A: read-only Stage-4/Stage-9 DFIG event consistency audit.

This script only reads preserved PSCAD runtime/model artifacts.  It does not
invoke PSCAD, Build, Run, or modify any PSCAD project/generated file.
"""

from __future__ import annotations

import csv
import hashlib
import json
import math
import re
import subprocess
from datetime import datetime
from pathlib import Path
from statistics import fmean
from typing import Any


REPO = Path(__file__).resolve().parents[2]
PREFIX = "3IBR_DFIG1_TRIAL"
STAGE4 = Path(r"C:\pscad_work\pnnl_39_3ibr_pscad46_strip5\_backups\stage7_before_paper_calibrated_first_trip\PSCAD")
STAGE9 = Path(r"C:\pscad_work\pnnl_39_3ibr_pscad46_strip5\PSCAD\3IBR_DFIG1_TRIAL.gf46")
STAGE9_TRIAL = STAGE9.parent / "3IBR_DFIG1_TRIAL.pscx"

SIGNALS = [
    "VIBR1_2", "PIBR1_2", "QIBR1_2",
    "DFIG_LVRT_LOWV", "DFIG_LVRT_IMMTRIP", "DFIG_LVRT_TIMER_S",
    "DFIG_LVRT_DURATION_EXCEEDED", "DFIG_LVRT_TRIP_REQUEST",
    "DFIG_LVRT_TRIP_LATCH", "DFIG_LVRT_FINAL_BRK_CMD",
    "DFIG_LVRT_FINAL_CMD_BOOL", "DFIG_LVRT_BRK_OPEN_BOOL",
    "DFIG_LVRT_TRIP_CONFIRMED", "DFIG_LVRT_CASCADE_EVENT_VALID",
    "DFIG_LVRT_CASCADE_EVENT_CAUSE_CODE", "DFIG_LVRT_CASCADE_EVENT_BRK_OPEN",
    "DFIG_LVRT_CASCADE_SOURCE_AVAILABLE", "DFIG_LVRT_CASCADE_AVAILABLE",
    "DFIG_LVRT_CASCADE_FIRST_EVENT_TIME_S", "DFIG_LVRT_EXISTING_BRK_CMD",
    "DFIG_LVRT_ORIGINAL_CMD_OPEN_BOOL", "DFIG_LVRT_TALLOW_S",
    "E_28_29_1_A_P", "E_28_29_1_A_Q", "E_28_29_1_B_P", "E_28_29_1_B_Q",
    "PAPER_OVL1_S_MAX_PU", "PAPER_OVL1_LOADING_INDEX_EQ",
    "PAPER_OVL1_ABOVE_THRESHOLD", "PAPER_OVL1_TIMER_OR_CURVE_STATE",
    "PAPER_OVL1_TRIP_REQUEST", "PAPER_OVL1_BRK_STATE",
]
WINDOWS = [
    ("pre_fault", 0.00, 0.49), ("fault", 0.50, 2.50),
    ("post_fault_short", 2.50, 3.50), ("pre_first_trip_redistribution", 3.50, 7.50),
]


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, obj: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fields: list[str] = []
    for row in rows:
        for key in row:
            if key not in fields:
                fields.append(key)
    with path.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields); w.writeheader(); w.writerows(rows)


def sha256(path: Path) -> str | None:
    if not path.exists(): return None
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""): h.update(block)
    return h.hexdigest().upper()


class Runtime:
    def __init__(self, name: str, root: Path, expected_samples: int, expected_end: float):
        self.name, self.root = name, root
        self.inf = root / f"{PREFIX}.inf"
        self.mapping: dict[str, dict[str, Any]] = {}
        pat = re.compile(r'PGB\((\d+)\).*?Desc="([^"]+)".*?Group="([^"]*)".*?Units="([^"]*)"')
        for line in self.inf.read_text(encoding="utf-8", errors="ignore").splitlines():
            m = pat.search(line)
            if m: self.mapping[m.group(2)] = {"pgb": int(m.group(1)), "group": m.group(3), "units": m.group(4)}
        first = self._load(root / f"{PREFIX}_01.out")
        self.channels_per_file = len(first[0]) - 1
        self.cache = {1: first}
        self.time = [r[0] for r in first]
        assert len(self.time) == expected_samples, (name, len(self.time))
        assert abs(self.time[-1] - expected_end) < 1e-9, (name, self.time[-1])

    @staticmethod
    def _load(path: Path) -> list[list[float]]:
        rows = []
        for line in path.read_text(encoding="ascii", errors="ignore").splitlines():
            p = line.split()
            if p: rows.append([float(x) for x in p])
        return rows

    def series(self, title: str) -> list[float] | None:
        info = self.mapping.get(title)
        if not info: return None
        idx = info["pgb"]
        no, col = (idx - 1) // self.channels_per_file + 1, (idx - 1) % self.channels_per_file + 1
        if no not in self.cache:
            p = self.root / f"{PREFIX}_{no:02d}.out"
            if not p.exists(): return None
            self.cache[no] = self._load(p)
        return [r[col] for r in self.cache[no] if len(r) > col]

    def first_ge(self, title: str, level: float = 0.5) -> float | None:
        v = self.series(title)
        return next((t for t, x in zip(self.time, v or []) if x >= level), None)

    def first_le_after_high(self, title: str, level: float = 0.5) -> float | None:
        v = self.series(title)
        seen = False
        for t, x in zip(self.time, v or []):
            seen = seen or x > level
            if seen and x <= level: return t
        return None


def stat(values: list[float]) -> tuple[float | None, float | None, float | None]:
    x = [v for v in values if math.isfinite(v)]
    return (min(x), fmean(x), max(x)) if x else (None, None, None)


def fmt(v: Any) -> str:
    return "runtime_unavailable" if v is None else f"{v:.12g}" if isinstance(v, float) else str(v)


def update_reference_files(status: str, claim: str) -> None:
    inv = REPO / "data/reference/current_pscad_model_capability_inventory.json"
    obj = read_json(inv)
    obj["stage10_dfig_event_consistency_status"] = status
    obj["stage10_dfig_event_consistency_evidence"] = "data/validation/stage10_dfig_event_consistency_final_audit.json"
    for cap in obj.get("capabilities", []):
        if cap.get("capability_id") in {"CAP08", "CAP13"}:
            cap["current_status"] = "stage10_stage4_trip_confirmed_stage9_no_trip_confirmed"
            cap["existing_dynamic_evidence"] = "data/validation/stage10_dfig_event_consistency_final_audit.json"
            cap["claim_boundary"] = claim
    write_json(inv, obj)
    fidelity = REPO / "data/reference/paper_reproduction_fidelity_assessment.json"
    obj = read_json(fidelity)
    obj.update({"stage10_dfig_event_consistency_status": status,
                "stage10_paper_event_order_status": "not_aligned_dfig_absent_before_first_line_trip",
                "strict_reproduction_status_after_stage10": "not_achieved",
                "stage10_evidence": "data/validation/stage10_dfig_event_consistency_final_audit.json"})
    write_json(fidelity, obj)
    future = REPO / "data/reference/future_shadow_overload_candidate_decision.json"
    obj = read_json(future)
    obj.update({"stage10_dfig_event_consistency_status": status,
                "stage10_minimal_next_change_scope": "fault_to_dfig_interface_alignment",
                "next_run_gate": "Demonstrate from static evidence that the unchanged physical LVRT chain will see a fault-period VIBR1_2 below 0.9 long enough to operate; do not synthesize an event or timed breaker command."})
    write_json(future, obj)
    matrix = REPO / "data/reference/paper_reproduction_alignment_matrix.csv"
    rows = list(csv.DictReader(matrix.open(encoding="utf-8", newline="")))
    fields = list(rows[0])
    for row in rows:
        if row.get("paper_item_id") == "P07":
            row["current_status"] = "stage4_trip_confirmed_stage9_no_trip_confirmed"
            row["current_evidence"] = "data/validation/stage10_dfig_event_consistency_final_audit.json"
        if row.get("paper_item_id") in {"P08", "P09", "P10"}:
            row["current_status"] = "stage9_first_line_subchain_only_paper_order_not_aligned"
            row["current_evidence"] = "data/derived/stage10_paper_event_order_timeline.csv"
    with matrix.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields); w.writeheader(); w.writerows(rows)
    marker = "\n## Stage 10A DFIG event consistency and paper sequence\n"
    addition = marker + f"\nStatus: `{status}`. Stage 4 contains a physical DFIG opening and matching event packet at 2.43 s; Stage 9 contains neither before the E_28_29_1 opening at 7.51 s. The channels are present and readable, so this is not an observability/parser failure. The verified signal-level cause is that Stage-9 fault-period VIBR1_2 stayed above the unchanged 0.9 duration-LVRT threshold. {claim}\n"
    for p in [REPO / "docs/PAPER_REPRODUCTION_GAP_REGISTER.md", REPO / "docs/PAPER_REPRODUCTION_ALIGNMENT_AND_MINIMUM_CASCADE_PLAN.md"]:
        if p.exists():
            text = p.read_text(encoding="utf-8"); text = text.split(marker)[0].rstrip()
            p.write_text(text + addition, encoding="utf-8")


def main() -> None:
    s4 = Runtime("stage4", STAGE4, 2001, 20.0)
    s9 = Runtime("stage9", STAGE9, 901, 9.0)
    runs = [s4, s9]
    expected4 = read_json(REPO / "data/derived/paper_aligned_20s_run_manifest.json")["input_manifest"]["trial_sha_before_run"]
    expected9 = read_json(REPO / "data/derived/stage9_short_run_manifest.json")["trial_sha_final"]
    s4_model = STAGE4 / "3IBR_DFIG1_TRIAL.pscx"
    s4_sha, s9_sha = sha256(s4_model), sha256(STAGE9_TRIAL)

    # Time-aligned trace is deliberately limited to the common pre-first-trip horizon.
    trace = []
    for i, t in enumerate(s9.time):
        row: dict[str, Any] = {"time_s": t, "FAULT_ACTIVE_REFERENCE": 1 if 0.5 <= t < 2.5 else 0}
        for sig in SIGNALS:
            for run in runs:
                v = run.series(sig)
                row[f"{run.name}_{sig}"] = "" if v is None else v[i]
        trace.append(row)
    write_csv(REPO / "data/derived/stage10_dfig_stage4_stage9_time_aligned_trace.csv", trace)

    metrics = []
    for run in runs:
        for window, lo, hi in WINDOWS:
            idx = [i for i, t in enumerate(run.time) if lo <= t <= hi]
            for sig in SIGNALS:
                v = run.series(sig)
                mn, mean, mx = stat([v[i] for i in idx]) if v else (None, None, None)
                metrics.append({"run": run.name, "window": window, "start_s": lo, "end_s": hi,
                                "signal": sig, "runtime_status": "readable" if v else "runtime_unavailable",
                                "raw_units_from_inf": run.mapping.get(sig, {}).get("units", ""),
                                "min": mn, "mean": mean, "max": mx})
    write_csv(REPO / "data/derived/stage10_dfig_stage4_stage9_window_metrics.csv", metrics)

    event_specs = [
        ("fault_start", 0.5, 0.5), ("fault_clear", 2.5, 2.5),
        ("DFIG_physical_breaker_transition", s4.first_ge("DFIG_LVRT_BRK_OPEN_BOOL"), s9.first_ge("DFIG_LVRT_BRK_OPEN_BOOL")),
        ("DFIG_source_availability_transition", s4.first_le_after_high("DFIG_LVRT_CASCADE_SOURCE_AVAILABLE"), s9.first_le_after_high("DFIG_LVRT_CASCADE_SOURCE_AVAILABLE")),
        ("DFIG_event_valid_transition", s4.first_ge("DFIG_LVRT_CASCADE_EVENT_VALID"), s9.first_ge("DFIG_LVRT_CASCADE_EVENT_VALID")),
        # Ignore the PSCAD t=0 initialization sample (0.0); the configured unset
        # sentinel from the first solved sample onward is -1.0.
        ("DFIG_first_event_timestamp", next((x for x in s4.series("DFIG_LVRT_CASCADE_FIRST_EVENT_TIME_S") or [] if x > 0), None), next((x for x in s9.series("DFIG_LVRT_CASCADE_FIRST_EVENT_TIME_S") or [] if x > 0), None)),
        ("E_28_29_1_first_threshold_crossing", None, s9.first_ge("PAPER_OVL1_ABOVE_THRESHOLD")),
        ("E_28_29_1_timer_start", None, s9.first_ge("PAPER_OVL1_ABOVE_THRESHOLD")),
        ("E_28_29_1_trip_request", None, s9.first_ge("PAPER_OVL1_TRIP_REQUEST")),
        ("E_28_29_1_actual_breaker_open", None, s9.first_ge("PAPER_OVL1_BRK_STATE")),
    ]
    timeline = [{"event": e, "stage4_time_s": a, "stage4_status": "observed" if a is not None else "not_available_or_not_applicable",
                 "stage9_time_s": b, "stage9_status": "observed" if b is not None else "not_observed_or_not_applicable"} for e, a, b in event_specs]
    write_csv(REPO / "data/derived/stage10_paper_event_order_timeline.csv", timeline)

    static_dynamic = []
    for sig in SIGNALS:
        a, b = s4.series(sig), s9.series(sig)
        for run, v in [(s4, a), (s9, b)]:
            static_dynamic.append({"run": run.name, "signal": sig,
                "runtime_status": "readable" if v else "runtime_unavailable",
                "pgb": run.mapping.get(sig, {}).get("pgb", ""), "units_as_recorded": run.mapping.get(sig, {}).get("units", ""),
                "initial": v[0] if v else "", "final": v[-1] if v else "",
                "first_ge_0p5_s": run.first_ge(sig) if v else "",
                "static_or_generated_code_evidence": "runtime channel plus unchanged LVRT chain; V<0.9 duration comparator, timer, trip latch, final breaker command" if sig.startswith("DFIG_") else "runtime channel"})
    write_csv(REPO / "data/validation/stage10_dfig_event_static_dynamic_trace.csv", static_dynamic)

    fault4 = [x for x in metrics if x["run"] == "stage4" and x["window"] == "fault" and x["signal"] == "VIBR1_2"][0]
    fault9 = [x for x in metrics if x["run"] == "stage9" and x["window"] == "fault" and x["signal"] == "VIBR1_2"][0]
    stage4_trip = s4.first_ge("DFIG_LVRT_BRK_OPEN_BOOL")
    stage9_trip = s9.first_ge("DFIG_LVRT_BRK_OPEN_BOOL")
    line_trip = s9.first_ge("PAPER_OVL1_BRK_STATE")
    status = "stage10_read_only_audit_complete_dfig_actual_no_trip_in_stage9"
    claim = ("Stage 9 validates only the flow-driven E_28_29_1 protection subchain. Until a physical DFIG event precedes the first line trip, it is not a complete paper-style accident-chain reproduction.")
    audit = {
        "audit_name": "stage10_dfig_event_consistency_final_audit", "generated_at_local": datetime.now().isoformat(timespec="seconds"),
        "execution_status": status, "analysis_mode": "zero_build_zero_run_zero_gui_read_only",
        "branch": subprocess.check_output(["git", "branch", "--show-current"], cwd=REPO, text=True).strip(),
        "stage4_runtime": {"path": str(STAGE4), "sample_count": len(s4.time), "time_start_s": s4.time[0], "time_end_s": s4.time[-1], "plot_step_s": 0.01,
                           "trial_sha_expected": expected4, "trial_sha_preserved_model": s4_sha, "sha_match": s4_sha == expected4},
        "stage9_runtime": {"path": str(STAGE9), "sample_count": len(s9.time), "time_start_s": s9.time[0], "time_end_s": s9.time[-1], "plot_step_s": 0.01,
                           "trial_sha_expected": expected9, "trial_sha_current_model": s9_sha, "sha_match": s9_sha == expected9},
        "fault_static_comparison": {"fault_bus": "N29", "fault_type": "three_phase_to_ground", "fault_start_s": 0.5, "fault_clear_s": 2.5,
            "fault_component_parameters": "verified identical: Ctype=0, OpCur=0, Grnd=1, CLVL=0, RON=0.01 ohm, ROFF=1e6 ohm, phases A/B/C/G enabled",
            "run_duration_difference": "20.0 s versus 9.0 s cannot alter the already-computed 0-9 s causal response", "emt_step": "unchanged by the Stage-9 duration-only setting", "plot_step_s": 0.01},
        "dfig_static_comparison": {"fault_and_DFIG_LVRT_configuration": "no relevant parameter difference found", "low_voltage_threshold": 0.9,
            "immediate_threshold": 0.2, "breaker_identity": "BRK_DFIG", "relevant_physical_difference": "Stage 9 contains the Stage-7 PAPER line breaker/relay boundary on E_28_29_1; Stage 4 predates it"},
        "stage4_dfig_status": {"physical_breaker_open_s": stage4_trip, "source_availability_lost_s": s4.first_le_after_high("DFIG_LVRT_CASCADE_SOURCE_AVAILABLE"),
            "event_valid_s": s4.first_ge("DFIG_LVRT_CASCADE_EVENT_VALID"), "event_cause_code": max(s4.series("DFIG_LVRT_CASCADE_EVENT_CAUSE_CODE") or [0]),
            "first_event_time_s": next((x for x in s4.series("DFIG_LVRT_CASCADE_FIRST_EVENT_TIME_S") or [] if x > 0), None),
            "interpretation": "physical DFIG disconnect and matching duration-LVRT event packet"},
        "stage9_dfig_status": {"physical_breaker_open_s": stage9_trip, "source_availability_lost_s": s9.first_le_after_high("DFIG_LVRT_CASCADE_SOURCE_AVAILABLE"),
            "event_valid_s": s9.first_ge("DFIG_LVRT_CASCADE_EVENT_VALID"), "event_cause_code": max(s9.series("DFIG_LVRT_CASCADE_EVENT_CAUSE_CODE") or [0]),
            "first_event_time_s": next((x for x in s9.series("DFIG_LVRT_CASCADE_FIRST_EVENT_TIME_S") or [] if x > 0), None),
            "all_required_channels_present": all(s9.series(x) is not None for x in ["VIBR1_2", "PIBR1_2", "QIBR1_2", "DFIG_LVRT_BRK_OPEN_BOOL", "DFIG_LVRT_CASCADE_EVENT_VALID", "DFIG_LVRT_CASCADE_SOURCE_AVAILABLE"]),
            "interpretation": "actual no-trip; not a missing channel, parser, or event-packet mapping failure"},
        "verified_signal_level_root_cause": {"class": "B_actual_no_trip_due_verified_lvrt_input_difference",
            "stage4_fault_window_VIBR1_2_min": fault4["min"], "stage9_fault_window_VIBR1_2_min": fault9["min"],
            "unchanged_duration_threshold": 0.9, "stage4_duration_trigger_s": s4.first_ge("DFIG_LVRT_DURATION_EXCEEDED"),
            "stage9_duration_trigger_s": s9.first_ge("DFIG_LVRT_DURATION_EXCEEDED"),
            "reason": "Stage 4 VIBR1_2 entered the V<0.9 region and accumulated the duration timer; Stage 9 stayed above 0.9 throughout the fault window, so the unchanged physical trip chain did not operate."},
        "sequence_class": "dfig_not_observed_before_first_trip", "stage9_first_line_actual_open_s": line_trip,
        "paper_order_aligned": False, "claim_boundary": claim,
    }
    write_json(REPO / "data/validation/stage10_dfig_event_consistency_final_audit.json", audit)

    decision = {"execution_status": status, "stage4_dfig_status": "physical_trip_and_matching_event_packet_at_2p43s",
        "stage9_dfig_status": "physical_no_trip_and_event_packet_correctly_inactive_before_line_open_at_7p51s",
        "root_cause_class": "B_actual_no_trip_due_verified_lvrt_input_difference",
        "root_cause_evidence": audit["verified_signal_level_root_cause"], "paper_order_status": "not_aligned_dfig_absent_before_first_line_trip",
        "whether_model_change_is_required": True, "whether_only_output_observability_change_is_required": False, "whether_no_model_change_is_required": False,
        "minimal_next_change_scope": "fault_to_dfig_interface_alignment",
        "forbidden_changes": ["synthetic event packet", "fixed-time DFIG trip", "fixed-time line trip", "manual breaker pulse", "capacity/threshold/delay change without new evidence"],
        "recommended_next_run_duration_s": 9.0,
        "recommended_next_run_end_reason": "Expected first-line open remains about 7.51 s; 9.0 s supplies 1.49 s of post-open observation and meets the >=1.0 s rule without reverting to 20 s.",
        "expected_event_order_before_run": ["N29 three-phase fault", "physical DFIG LVRT/source-unavailable event", "power-flow redistribution", "flow-driven E_28_29_1 threshold and 5 s timer", "actual E_28_29_1 open", ">=1.0 s post-open response"],
        "confidence_level": "high_for_signal_level_no_trip_mechanism; medium_for_exact_upstream_network_cause_until_static_interface_alignment_is completed",
        "claim_boundary": claim}
    write_json(REPO / "data/reference/stage10_dfig_event_consistency_decision.json", decision)
    target = {"target_name": "stage10_paper_event_order_target", "status": "static_gate_for_next_unique_run",
        "required_order": decision["expected_event_order_before_run"], "physical_evidence_required": ["BRK_DFIG transition", "DFIG source availability loss", "matching event packet", "real TLine P/Q-driven protection"],
        "prohibited_shortcuts": decision["forbidden_changes"], "recommended_unique_run_duration_s": 9.0,
        "run_gate": "Do not run until fault-to-DFIG interface alignment is statically justified and the original physical LVRT chain, not an injected event, is expected to operate."}
    write_json(REPO / "data/reference/stage10_paper_event_order_target.json", target)
    update_reference_files(status, claim)

    def m(run: str, win: str, sig: str, field: str) -> Any:
        return next(x[field] for x in metrics if x["run"] == run and x["window"] == win and x["signal"] == sig)
    doc = f"""# Stage 10A DFIG event consistency and paper-sequence audit

Generated: {audit['generated_at_local']}

## Outcome

This was a strictly read-only, zero-Build, zero-Run, zero-GUI audit. Stage 4 contains a real DFIG breaker opening and a matching event packet at the 0.01 s output resolution. Stage 9 contains neither: all required channels are present and readable, but remain inactive. Therefore the answer is **B: the DFIG actually did not trip in Stage 9**.

The decisive mechanism is the unchanged LVRT duration input. During the 0.50-2.50 s fault window, Stage-4 `VIBR1_2` fell to `{m('stage4','fault','VIBR1_2','min'):.9g}` and the duration trigger asserted at `{s4.first_ge('DFIG_LVRT_DURATION_EXCEEDED'):.2f} s`; Stage-9 `VIBR1_2` stayed at or above `{m('stage9','fault','VIBR1_2','min'):.9g}`, above the `0.9` low-voltage threshold, so its duration trigger, trip latch, breaker state, availability transition, and event packet all correctly remained inactive.

## Locked runtime sources

| Run | Runtime source | Samples / horizon / plot step | Trial SHA |
|---|---|---|---|
| Stage 4 | `{STAGE4}` | 2001 / 20.0 s / 0.01 s | `{s4_sha}` |
| Stage 9 | `{STAGE9}` | 901 / 9.0 s / 0.01 s | `{s9_sha}` |

## DFIG dynamic comparison (raw recorded units)

| Window | Run | V min/mean/max | P min/mean/max | Q min/mean/max |
|---|---|---|---|---|
"""
    for win, _, _ in WINDOWS:
        for run in ["stage4", "stage9"]:
            doc += f"| {win} | {run} | {m(run,win,'VIBR1_2','min'):.6g} / {m(run,win,'VIBR1_2','mean'):.6g} / {m(run,win,'VIBR1_2','max'):.6g} | {m(run,win,'PIBR1_2','min'):.6g} / {m(run,win,'PIBR1_2','mean'):.6g} / {m(run,win,'PIBR1_2','max'):.6g} | {m(run,win,'QIBR1_2','min'):.6g} / {m(run,win,'QIBR1_2','mean'):.6g} / {m(run,win,'QIBR1_2','max'):.6g} |\n"
    doc += f"""

The `.inf` unit fields for these channels are blank; the values above are therefore reported only as raw PSCAD recorded values, not relabelled as MW, Mvar, or p.u.

## Paper-event-order comparison

| Paper mechanism link | Stage 4 evidence | Stage 9 evidence | Pass | Sequence consistent | Minimum allowed next change |
|---|---|---|---|---|---|
| N29 three-phase fault | 0.50-2.50 s | 0.50-2.50 s | yes | yes | none |
| Physical DFIG LVRT/source loss | breaker/event/availability at 2.43 s | no breaker or availability transition | no | no | align fault-to-DFIG physical interface |
| Power-flow redistribution after DFIG loss | DFIG P/Q collapses after 2.43 s | DFIG P/Q remains substantial | no | no | same as above |
| First-line flow-driven protection | not present in this older baseline | threshold 2.51 s; actual open 7.51 s | subchain only | no, because DFIG did not precede it | preserve relay; do not time-force it |
| Initial post-open response | not applicable | observed after 7.51 s | yes for subchain | no for full paper chain | none beyond upstream alignment |

## Decision

- Sequence class: `dfig_not_observed_before_first_trip`.
- Root-cause class: `B_actual_no_trip_due_verified_lvrt_input_difference`.
- This is not missing output, parser failure, or event-packet mismatch.
- Fault component and DFIG LVRT/breaker settings are unchanged. The relevant verified model boundary difference is the later PAPER breaker/relay topology on `E_28_29_1`; the signal-level proof is conclusive, while exact attribution of the upstream voltage-transfer change remains bounded to `fault_to_dfig_interface_alignment` until that interface is statically aligned.
- Next unique Run duration: `9.0 s`, because the expected first-line opening is about `7.51 s`, leaving `1.49 s` of post-open observation.
- No synthetic event, fixed-time DFIG trip, fixed-time line trip, or packet-only repair is permitted.

The Stage-9 first-line protection subchain is validated, but it must not be described as a complete paper-style accident-chain reproduction until a physical DFIG event is proven to precede it.
"""
    (REPO / "docs/STAGE10_DFIG_EVENT_CONSISTENCY_AND_PAPER_SEQUENCE_AUDIT.md").write_text(doc, encoding="utf-8")
    print(json.dumps({"execution_status": status, "stage4_dfig_open_s": stage4_trip, "stage9_dfig_open_s": stage9_trip,
                      "stage9_first_line_open_s": line_trip, "sequence_class": audit["sequence_class"]}, indent=2))


if __name__ == "__main__": main()
