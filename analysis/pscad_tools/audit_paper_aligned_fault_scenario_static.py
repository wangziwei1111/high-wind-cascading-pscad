#!/usr/bin/env python3
"""Final static audit for the paper-aligned 20 s bus-29 fault scenario.

The audit is read-only.  It verifies PSCAD XML configuration and Build-generated
artifacts after the manual GUI Build.  It does not run the case.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
from datetime import datetime
from pathlib import Path
import xml.etree.ElementTree as ET


REPO = Path(__file__).resolve().parents[2]
DEFAULT_MAIN = Path(r"C:\pscad_work\pnnl_39_3ibr_pscad46_strip5\PSCAD\3IBR.pscx")
DEFAULT_TRIAL = Path(r"C:\pscad_work\pnnl_39_3ibr_pscad46_strip5\PSCAD\3IBR_DFIG1_TRIAL.pscx")
DEFAULT_GF46 = Path(r"C:\pscad_work\pnnl_39_3ibr_pscad46_strip5\PSCAD\3IBR_DFIG1_TRIAL.gf46")

EXPECTED_MAIN_SHA = "CBA120BB167CB7FA6C4A1AE4471268850AB61761EC1877EB7B87015627FE9DAB"
BASELINE_TRIAL_SHA = "A9DC610D20C61022CDE2F2D73612C12499FB7E5D29C43562BA08D9D89EADF360"


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest().upper()


def load_xml(path: Path) -> ET.Element:
    return ET.fromstring(path.read_text(encoding="utf-8", errors="replace"))


def params_under(user: ET.Element) -> dict[str, str]:
    out: dict[str, str] = {}
    for param in user.findall(".//param"):
        name = param.attrib.get("name")
        if name:
            out[name] = param.attrib.get("value", "")
    return out


def as_float(value: str | None) -> float | None:
    if value is None:
        return None
    try:
        return float(value)
    except ValueError:
        return None


def write_json(path: Path, data: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames: list[str] = []
    for row in rows:
        for key in row:
            if key not in fieldnames:
                fieldnames.append(key)
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def project_settings(root: ET.Element) -> dict[str, str]:
    return {p.attrib.get("name", ""): p.attrib.get("value", "") for p in root.findall("./paramlist/param")}


def fault_trace(root: ET.Element, gf46: Path) -> tuple[dict[str, object], list[dict[str, object]]]:
    rows: list[dict[str, object]] = []
    users = [u for u in root.iter("User") if "tfault" in u.attrib.get("defn", "").lower()]
    for u in users:
        p = params_under(u)
        rows.append(
            {
                "source": "pscx",
                "component_id": u.attrib.get("id"),
                "defn": u.attrib.get("defn"),
                "x": u.attrib.get("x"),
                "y": u.attrib.get("y"),
                "TF": p.get("TF"),
                "DF": p.get("DF"),
                "fault_start_s": as_float(p.get("TF")),
                "fault_duration_s": as_float(p.get("DF")),
                "fault_clear_s": (as_float(p.get("TF")) or 0) + (as_float(p.get("DF")) or 0),
                "status": "observed",
            }
        )

    p3_dta = gf46 / "P3.dta"
    dta_text = p3_dta.read_text(encoding="utf-8", errors="replace") if p3_dta.exists() else ""
    n29_ground_lines = [
        (idx, line)
        for idx, line in enumerate(dta_text.splitlines(), 1)
        if re.search(r"N29\([123]\)\s+GND", line)
    ]
    for idx, line in n29_ground_lines:
        rows.append(
            {
                "source": "gf46/P3.dta",
                "line": idx,
                "evidence": line.strip(),
                "status": "N29_to_GND_branch_observed",
            }
        )

    p3_f = gf46 / "P3.f"
    f_text = p3_f.read_text(encoding="utf-8", errors="replace") if p3_f.exists() else ""
    timing_lines = [
        (idx, line)
        for idx, line in enumerate(f_text.splitlines(), 1)
        if "TIME .GE. 0.5" in line or "TIME .GE. (0.5+2.0)" in line or "E3PHFLT1_EXE" in line
    ]
    for idx, line in timing_lines:
        rows.append(
            {
                "source": "gf46/P3.f",
                "line": idx,
                "evidence": line.strip(),
                "status": "fault_timing_or_execution_observed",
            }
        )

    summary = {
        "fault_component_count": len(users),
        "xml_fault_start_s": rows[0]["fault_start_s"] if users else None,
        "xml_fault_duration_s": rows[0]["fault_duration_s"] if users else None,
        "xml_fault_clear_s": rows[0]["fault_clear_s"] if users else None,
        "n29_ground_branch_evidence_count": len(n29_ground_lines),
        "timing_code_evidence_count": len(timing_lines),
        "three_phase_fault_code_present": "Three Phase Fault" in f_text and "E3PHFLT1_EXE" in f_text,
        "status": "pass"
        if len(users) == 1
        and rows[0]["fault_start_s"] == 0.5
        and rows[0]["fault_duration_s"] == 2.0
        and rows[0]["fault_clear_s"] == 2.5
        and len(n29_ground_lines) >= 3
        and "TIME .GE. (0.5+2.0)" in f_text
        and "E3PHFLT1_EXE" in f_text
        else "fail",
    }
    return summary, rows


def channel_trace(root: ET.Element) -> tuple[dict[str, object], list[dict[str, object]]]:
    rows = []
    for u in root.iter("User"):
        if u.attrib.get("defn") == "master:pgb":
            p = params_under(u)
            rows.append(
                {
                    "component_id": u.attrib.get("id"),
                    "name": p.get("Name") or p.get("Title") or u.attrib.get("name"),
                    "group": p.get("Group"),
                    "x": u.attrib.get("x"),
                    "y": u.attrib.get("y"),
                    "status": "preserved_after_fault_static_config",
                }
            )
    return {"xml_output_channel_count": len(rows), "status": "pass" if len(rows) == 448 else "fail"}, rows


def tline_trace(root: ET.Element) -> tuple[dict[str, object], list[dict[str, object]]]:
    inv = json.loads((REPO / "data/reference/full_network_tline_inventory.json").read_text(encoding="utf-8"))
    expected = {x["network_branch_id"]: x for x in inv.get("tlines", [])}
    rows = []
    for branch, item in sorted(expected.items()):
        pgb_names = [f"{branch}_A_P", f"{branch}_A_Q", f"{branch}_A_I", f"{branch}_B_P", f"{branch}_B_Q", f"{branch}_B_I"]
        found = {name: False for name in pgb_names}
        for u in root.iter("User"):
            if u.attrib.get("defn") == "master:pgb":
                p = params_under(u)
                name = p.get("Name") or p.get("Title")
                if name in found:
                    found[name] = True
        rows.append(
            {
                "network_branch_id": branch,
                "terminal_a_node": item.get("terminal_a_node"),
                "terminal_b_node": item.get("terminal_b_node"),
                "component_id": item.get("component_id"),
                "expected_output_count": 6,
                "observed_output_count": sum(1 for ok in found.values() if ok),
                "status": "pass" if all(found.values()) else "fail",
            }
        )
    return {
        "inventory_tline_count": len(rows),
        "all_tline_measurements_preserved": all(r["status"] == "pass" for r in rows),
        "status": "pass" if len(rows) == 31 and all(r["status"] == "pass" for r in rows) else "fail",
    }, rows


def build_trace(gf46: Path) -> dict[str, object]:
    p3_f = gf46 / "P3.f"
    p3_dta = gf46 / "P3.dta"
    exe = gf46 / "3IBR_DFIG1_TRIAL.exe"
    map_file = gf46 / "3IBR_DFIG1_TRIAL.map"
    log_errors = []
    for log in gf46.glob("*.log"):
        text = log.read_text(encoding="utf-8", errors="replace")
        if re.search(r"\berror\b", text, flags=re.I):
            log_errors.append(str(log))
    return {
        "gf46_dir_exists": gf46.exists(),
        "p3_f_exists": p3_f.exists(),
        "p3_dta_exists": p3_dta.exists(),
        "map_exists": map_file.exists(),
        "exe_exists": exe.exists(),
        "build_generated_latest_files_local": {
            "P3.f": datetime.fromtimestamp(p3_f.stat().st_mtime).isoformat(timespec="seconds") if p3_f.exists() else None,
            "P3.dta": datetime.fromtimestamp(p3_dta.stat().st_mtime).isoformat(timespec="seconds") if p3_dta.exists() else None,
            "map": datetime.fromtimestamp(map_file.stat().st_mtime).isoformat(timespec="seconds") if map_file.exists() else None,
            "exe": datetime.fromtimestamp(exe.stat().st_mtime).isoformat(timespec="seconds") if exe.exists() else None,
        },
        "log_files_with_error_text": log_errors,
        "status": "pass" if gf46.exists() and p3_f.exists() and p3_dta.exists() and map_file.exists() and not log_errors else "fail",
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--main-pscx", type=Path, default=DEFAULT_MAIN)
    ap.add_argument("--trial-pscx", type=Path, default=DEFAULT_TRIAL)
    ap.add_argument("--gf46-dir", type=Path, default=DEFAULT_GF46)
    args = ap.parse_args()

    root = load_xml(args.trial_pscx)
    settings = project_settings(root)
    main_sha = sha256(args.main_pscx)
    trial_sha = sha256(args.trial_pscx)

    fault_summary, fault_rows = fault_trace(root, args.gf46_dir)
    channel_summary, channel_rows = channel_trace(root)
    tline_summary, tline_rows = tline_trace(root)
    build_summary = build_trace(args.gf46_dir)

    preflight = json.loads((REPO / "data/validation/paper_aligned_fault_scenario_preflight.json").read_text(encoding="utf-8"))
    evidence_extract = json.loads((REPO / "data/reference/paper_fault_scenario_evidence_extract.json").read_text(encoding="utf-8"))

    gates = {
        "main_project_unchanged": main_sha == EXPECTED_MAIN_SHA,
        "trial_changed_from_full_network_baseline": trial_sha != BASELINE_TRIAL_SHA,
        "duration_20s": as_float(settings.get("time_duration")) == 20.0,
        "time_step_preserved_5us": as_float(settings.get("time_step")) == 5.0,
        "plot_step_preserved_10000us": as_float(settings.get("sample_step")) == 10000.0,
        "fault_static_configuration": fault_summary["status"] == "pass",
        "output_channels_preserved": channel_summary["status"] == "pass",
        "tline_measurements_preserved": tline_summary["status"] == "pass",
        "build_artifacts_present": build_summary["status"] == "pass",
        "preflight_was_pass": preflight.get("execution_status") == "pass",
    }

    audit = {
        "audit_name": "paper_aligned_fault_scenario_final_static_audit",
        "generated_at_local": datetime.now().isoformat(timespec="seconds"),
        "execution_status": "pass" if all(gates.values()) else "fail",
        "run_status": "not_performed_by_task_design",
        "build_status": "user_build_completed_static_audit_passed" if build_summary["status"] == "pass" else "build_artifact_check_failed",
        "main_pscx": str(args.main_pscx),
        "trial_pscx": str(args.trial_pscx),
        "main_sha256": main_sha,
        "trial_sha256": trial_sha,
        "baseline_trial_sha256_before_fault_static_config": BASELINE_TRIAL_SHA,
        "project_settings": settings,
        "gates": gates,
        "paper_evidence_extract": evidence_extract,
        "fault_summary": fault_summary,
        "channel_summary": channel_summary,
        "tline_summary": tline_summary,
        "build_summary": build_summary,
        "claim_boundary": "paper-aligned static baseline fault configuration; no dynamic reproduction claim until a later Run and parsed results",
    }

    write_json(REPO / "data/validation/paper_aligned_fault_scenario_final_audit.json", audit)
    write_csv(REPO / "data/validation/paper_aligned_fault_scenario_channel_trace.csv", channel_rows)
    write_csv(REPO / "data/validation/paper_aligned_fault_scenario_fault_trace.csv", fault_rows)
    write_csv(REPO / "data/validation/paper_aligned_fault_scenario_tline_measurement_trace.csv", tline_rows)

    print(json.dumps(audit, ensure_ascii=False, indent=2))
    return 0 if audit["execution_status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
