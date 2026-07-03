#!/usr/bin/env python3
"""Read-only pre-run gate for the Stage-9 9.0-second validation."""

from __future__ import annotations

import csv
import hashlib
import json
import re
import xml.etree.ElementTree as ET
from datetime import datetime
from pathlib import Path
from typing import Any


REPO = Path(__file__).resolve().parents[2]
PSCAD = Path(r"C:\pscad_work\pnnl_39_3ibr_pscad46_strip5\PSCAD")
MAIN = PSCAD / "3IBR.pscx"
TRIAL = PSCAD / "3IBR_DFIG1_TRIAL.pscx"
GF46 = PSCAD / "3IBR_DFIG1_TRIAL.gf46"


def sha(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest().upper()


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, obj: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    fields = list(rows[0]) if rows else []
    with path.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields); w.writeheader(); w.writerows(rows)


def param(user: ET.Element, name: str) -> str | None:
    p = user.find(f"./paramlist/param[@name='{name}']")
    return p.get("value") if p is not None else None


def semantic_fingerprint(path: Path) -> str:
    root = ET.parse(path).getroot()
    for elem in root.iter():
        elem.attrib.pop("crc", None); elem.attrib.pop("date", None)
        if elem.tag == "param" and elem.get("name") == "revisor": elem.set("value", "<volatile>")
        if elem.tag == "param" and elem.get("name") == "time_duration": elem.set("value", "<stage9-authorized>")
    relay = root.find("./definitions/Definition[@name='PAPER_OVL1_RELAY']")
    if relay is None: return "missing"
    off = relay.find(".//User[@id='522397627']/paramlist/param[@name='Value']")
    if off is not None: off.set("value", "<stage9-authorized>")
    return hashlib.sha256(ET.tostring(root, encoding="utf-8")).hexdigest().upper()


def main() -> None:
    freeze = read_json(REPO / "data/reference/stage9_short_run_initialization_repair_freeze.json")
    root = ET.parse(TRIAL).getroot()
    relay = root.find("./definitions/Definition[@name='PAPER_OVL1_RELAY']")
    if relay is None: raise RuntimeError("PAPER_OVL1_RELAY missing")
    timer = relay.find(".//User[@id='2132554116']"); latch = relay.find(".//User[@id='897892378']")
    von = relay.find(".//User[@id='2118574082']"); voff = relay.find(".//User[@id='522397627']")
    reset = relay.find(".//User[@id='801784199']")
    settings = {p.get("name"): p.get("value") for p in root.findall("./paramlist[@name='Settings']/param")}
    f = (GF46 / "PAPER_OVL1_RELAY.f").read_text(encoding="utf-8", errors="ignore")
    p3 = (GF46 / "P3.f").read_text(encoding="utf-8", errors="ignore")
    build_files = [GF46 / "P3.f", GF46 / "P3.dta", GF46 / "3IBR_DFIG1_TRIAL.map"]
    artifact_times = {p.name: datetime.fromtimestamp(p.stat().st_mtime).isoformat(timespec="seconds") if p.exists() else None for p in build_files}
    trial_mtime = TRIAL.stat().st_mtime

    expected_map = freeze["required_generated_pgb_mapping"]
    channel_rows = []
    mapping_ok = True
    for title, expected in expected_map.items():
        m = re.search(r"Output Channel '" + re.escape(title) + r"'.{0,200}?PGB\(IPGB\+(\d+)\)\s*=\s*([^\r\n]+)", p3, re.S)
        actual_offset = int(m.group(1)) if m else None
        actual_expr = m.group(2).strip().rstrip(";") if m else None
        expected_expr = str(expected.get("runtime_expressions") or "").strip().rstrip(";")
        ok = actual_offset == expected.get("pgb_offset") and actual_expr == expected_expr
        mapping_ok &= ok
        channel_rows.append({"canonical_title": title, "expected_pgb_offset": expected.get("pgb_offset"),
                             "actual_pgb_offset": actual_offset, "expected_expression": expected_expr,
                             "actual_expression": actual_expr, "status": "pass" if ok else "fail"})

    gates = {
        "main_sha_unchanged": sha(MAIN) == freeze["main_sha"],
        "trial_semantic_changes_only_authorized": semantic_fingerprint(TRIAL) == freeze["trial_semantic_fingerprint_excluding_two_authorized_values"],
        "run_duration_exactly_9s": float(settings.get("time_duration", -1)) == 9.0,
        "emt_time_step_5us": float(settings.get("time_step", -1)) == 5.0,
        "plot_step_10000us": float(settings.get("sample_step", -1)) == 10000.0,
        "timer_trigger_threshold_0p5": param(timer, "FSet") == "0.5",
        "timer_delay_5s": str(param(timer, "TS")).startswith("5.0"),
        "timer_duration_on_100s": str(param(timer, "TD")).startswith("100"),
        "timer_von_is_1": param(von, "Value") == "1.0",
        "timer_voff_repaired_to_0": param(voff, "Value") in {"0", "0.0"},
        "latch_simple_rs_qinit0": param(latch, "F_GL_L") == "2" and param(latch, "Type") == "1" and param(latch, "QInit") == "0",
        "latch_reset_zero": param(reset, "Value") in {"0", "0.0"},
        "generated_timer_off_value_zero": bool(re.search(r"RT_17\s*=\s*0\.0", f)),
        "generated_timer_on_value_one": bool(re.search(r"RT_16\s*=\s*1\.0", f)),
        "generated_active_low_completion_logic": "RT_15 = + RT_14 - RT_13" in f and "RT_18 = TIMER3(5.0, 100.0, RT_15, 0.5, RT_17, RT_16)" in f,
        "generated_timer_output_to_latch_set": "RVD2_1(1) = RT_18" in f,
        "generated_latch_qinit0": "CALL E_XFLIP1_CFG(2,1,0,0)" in f,
        "generated_trip_only_from_latch_q": "TRIP_REQ = REAL(IT_4)" in f,
        "breaker_closed_when_command_zero": p3.count("NINT(1.0-PAPER_OVL1_BRK_CMD)") == 3,
        "no_time_fault_dfig_oneshot_bypass": not bool(re.search(r"PAPER_OVL1_BRK_CMD\s*=\s*.*(TIME|FAULT|DFIG|ONE_SHOT)", p3, re.I)),
        "stage8_13_channel_mapping_preserved": mapping_ok and len(channel_rows) == 13,
        "build_products_exist": all(p.exists() for p in build_files),
        "build_products_not_older_than_save": all(p.exists() and p.stat().st_mtime + 2 >= trial_mtime for p in build_files),
        "no_build_error_artifact": not any(GF46.glob("*.err")),
    }
    passed = all(gates.values())
    status = "pre_run_gate_pass" if passed else "pre_run_gate_blocked"
    audit = {"audit_name": "stage9_short_run_pre_run_gate", "generated_at_local": datetime.now().isoformat(timespec="seconds"),
             "execution_status": status, "run_authorization": "RUN_9S_ALLOWED_ONCE" if passed else "RUN_BLOCKED",
             "main_sha": sha(MAIN), "trial_sha_after_gui_repair_and_build": sha(TRIAL),
             "trial_mtime": datetime.fromtimestamp(trial_mtime).isoformat(timespec="seconds"),
             "build_artifact_times": artifact_times, "gates": gates, "canonical_output_gate": channel_rows,
             "failed_gates": [k for k, v in gates.items() if not v]}
    trace = [{"check": k, "status": "pass" if v else "fail"} for k, v in gates.items()]
    write_json(REPO / "data/validation/stage9_short_run_pre_run_gate.json", audit)
    write_csv(REPO / "data/validation/stage9_short_run_pre_run_gate_trace.csv", trace)
    doc = "# Stage 9 short-run pre-run gate\n\n" + f"Result: `{status}`\n\n" + "\n".join(f"- {k}: `{v}`" for k, v in gates.items()) + "\n"
    (REPO / "docs/STAGE9_SHORT_RUN_PRE_RUN_GATE.md").write_text(doc, encoding="utf-8")
    print("stage9_short_run_pre_run_gate = " + ("pass" if passed else "blocked"))


if __name__ == "__main__":
    main()
