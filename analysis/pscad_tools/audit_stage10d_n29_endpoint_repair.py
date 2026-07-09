#!/usr/bin/env python3
"""Audit the E_26_29_1 N29 endpoint repair and the confirming 3 s DFIG trip run."""

from __future__ import annotations

import csv
import hashlib
import json
import re
from datetime import datetime
from pathlib import Path
from statistics import fmean

REPO = Path(__file__).resolve().parents[2]
ROOT = Path(r"C:\pscad_work\pnnl_39_3ibr_pscad46_strip5")
MODEL = ROOT / "PSCAD/3IBR_DFIG1_TRIAL.pscx"
BUILD = ROOT / "PSCAD/3IBR_DFIG1_TRIAL.gf46"
PRE_REPAIR_DTA = ROOT / "_backups/stage9_before_short_run_initialization_repair/3IBR_DFIG1_TRIAL.gf46/P3.dta"
CURRENT_DTA = BUILD / "P3.dta"
PREFIX = "3IBR_DFIG1_TRIAL"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest().upper()


def tline_terminals(path: Path, name: str) -> list[dict[str, object]]:
    lines = path.read_text(errors="ignore").splitlines()
    marker = next(i for i, line in enumerate(lines) if line.strip().startswith(f"! {name}"))
    terminals = []
    for side, line in zip(("A", "B"), lines[marker + 2 : marker + 4]):
        values = [int(value) for value in line.split()[:4]]
        terminals.append({"side": side, "compiled_bus": values[0], "phase_nodes": values[1:]})
    return terminals


class Runtime:
    def __init__(self, root: Path):
        self.root = root
        self.channels: dict[str, int] = {}
        pattern = re.compile(r'PGB\((\d+)\).*?Desc="([^"]+)"')
        for line in (root / f"{PREFIX}.inf").read_text(errors="ignore").splitlines():
            match = pattern.search(line)
            if match:
                self.channels[match.group(2)] = int(match.group(1))
        self.cache: dict[int, list[list[float]]] = {}
        first = self._load(1)
        self.columns_per_file = len(first[0]) - 1
        self.time = [row[0] for row in first]

    def _load(self, file_number: int) -> list[list[float]]:
        if file_number not in self.cache:
            path = self.root / f"{PREFIX}_{file_number:02d}.out"
            self.cache[file_number] = [
                [float(value) for value in line.split()]
                for line in path.read_text(errors="ignore").splitlines()
                if line.split()
            ]
        return self.cache[file_number]

    def series(self, name: str) -> list[float]:
        channel = self.channels[name]
        file_number = (channel - 1) // self.columns_per_file + 1
        column = (channel - 1) % self.columns_per_file + 1
        return [row[column] for row in self._load(file_number)]


def first_transition(time: list[float], values: list[float], level: float = 0.5, after: float = 1.5) -> float | None:
    return next((t for t, value in zip(time, values) if t >= after and value > level), None)


def write_json(path: Path, value: object) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    runtime = Runtime(BUILD)
    old_e2629 = tline_terminals(PRE_REPAIR_DTA, "E_26_29_1")
    new_e2629 = tline_terminals(CURRENT_DTA, "E_26_29_1")
    new_e2829 = tline_terminals(CURRENT_DTA, "E_28_29_1")
    dta_text = CURRENT_DTA.read_text(errors="ignore")
    model_text = MODEL.read_text(errors="ignore")

    voltage = runtime.series("CASCADE3_ELEC_DFIG_V")
    pre_fault = [value for t, value in zip(runtime.time, voltage) if 1.0 <= t < 2.0]
    fault_window = [(t, value) for t, value in zip(runtime.time, voltage) if 2.0 <= t <= 2.5]
    trip_signals = [
        "DFIG_LVRT_TRIP_CAUSE_DURATION_LATCH",
        "DFIG_LVRT_FINAL_BRK_CMD",
        "DFIG_LVRT_TRIP_CONFIRMED",
        "DFIG_BRK_STATE",
    ]
    timeline = []
    for name in trip_signals:
        values = runtime.series(name)
        timeline.append(
            {
                "signal": name,
                "first_assertion_after_1p5_s": first_transition(runtime.time, values),
                "value_at_3_s": values[-1],
            }
        )

    checks = [
        {"check": "pre_repair_E_26_29_1_B_terminal_was_bus_19", "status": "pass" if old_e2629[1]["compiled_bus"] == 19 else "fail"},
        {"check": "repaired_E_26_29_1_B_terminal_is_N29_bus_1", "status": "pass" if new_e2629[1]["compiled_bus"] == 1 else "fail"},
        {"check": "E_28_29_1_B_terminal_remains_bus_1", "status": "pass" if new_e2829[1]["compiled_bus"] == 1 else "fail"},
        {"check": "E_26_29_1_meter_nodes_connect_to_N29", "status": "pass" if re.search(r"NT_80\(1\)\s+N29\(1\)", dta_text) else "fail"},
        {"check": "PAPER_breaker_remains_series_between_N29_and_internal_node", "status": "pass" if re.search(r"N29\(1\)\s+NT_83\(1\)", dta_text) else "fail"},
        {"check": "model_contains_at_least_two_N29_node_labels", "status": "pass" if model_text.count('<param name="Name" value="N29"') >= 2 else "fail"},
        {"check": "3_s_runtime_complete", "status": "pass" if abs(runtime.time[-1] - 3.0) < 1e-9 else "fail"},
        {"check": "DFIG_final_breaker_command_asserted", "status": "pass" if timeline[1]["first_assertion_after_1p5_s"] == 2.44 else "fail"},
        {"check": "DFIG_trip_confirmed", "status": "pass" if timeline[2]["first_assertion_after_1p5_s"] == 2.44 else "fail"},
        {"check": "DFIG_breaker_open_state_observed", "status": "pass" if timeline[3]["value_at_3_s"] == 2.0 else "fail"},
    ]
    fault_min_time, fault_min = min(fault_window, key=lambda item: item[1])
    audit = {
        "audit_name": "stage10d_n29_endpoint_repair_and_dfig_trip_validation",
        "generated_at_local": datetime.now().astimezone().isoformat(timespec="seconds"),
        "execution_status": "pass" if all(row["status"] == "pass" for row in checks) else "fail",
        "root_cause": "E_26_29_1 B terminal compiled to isolated bus 19 instead of the N29 bus after the PAPER breaker insertion/layout change.",
        "repair": "Placed an electrical Node Label named N29 on the E_26_29_1 B-side conductor; this is not a control Data Label.",
        "compiled_topology": {
            "pre_repair_E_26_29_1": old_e2629,
            "post_repair_E_26_29_1": new_e2629,
            "post_repair_E_28_29_1": new_e2829,
            "paper_breaker_bypassed": False,
        },
        "runtime": {
            "duration_s": runtime.time[-1],
            "sample_interval_s": runtime.time[1] - runtime.time[0],
            "DFIG_voltage_pre_fault_mean_1_to_2_s": fmean(pre_fault),
            "DFIG_voltage_fault_window_min_2_to_2p5_s": fault_min,
            "DFIG_voltage_fault_window_min_time_s": fault_min_time,
            "event_timeline": timeline,
            "stage4_reference_trip_time_s": 2.43,
            "alignment_delta_s": 0.01,
        },
        "claim_boundary": "The repair restores the compiled N29 endpoint and DFIG disconnection. The LVRT timer was already accumulating before 2.0 s, so this run does not prove that the 2.0 s fault alone caused the trip.",
        "future_build_gate": "After any breaker insertion, endpoint move, or node-label edit, inspect generated P3.dta and require every affected TLine terminal to retain its intended compiled bus before authorizing a Run.",
        "artifact_hashes": {
            "trial_pscx_sha256": sha256(MODEL),
            "P3_dta_sha256": sha256(CURRENT_DTA),
            "runtime_inf_sha256": sha256(BUILD / f"{PREFIX}.inf"),
            "pre_repair_P3_dta_sha256": sha256(PRE_REPAIR_DTA),
        },
        "raw_model_and_runtime_files_committed": False,
        "raw_artifact_policy": "Third-party PSCAD model and generated runtime files remain outside Git under the repository ignore policy; hashes, topology evidence, and derived validation are committed.",
    }
    write_json(REPO / "data/validation/stage10d_n29_endpoint_repair_final_audit.json", audit)
    write_csv(REPO / "data/validation/stage10d_n29_endpoint_repair_trace.csv", checks)
    write_csv(REPO / "data/derived/stage10d_dfig_trip_event_timeline.csv", timeline)
    if audit["execution_status"] != "pass":
        raise SystemExit("Stage 10D audit failed")
    print(json.dumps({"status": "pass", "trip_time_s": 2.44, "model_sha256": audit["artifact_hashes"]["trial_pscx_sha256"]}, indent=2))


if __name__ == "__main__":
    main()
