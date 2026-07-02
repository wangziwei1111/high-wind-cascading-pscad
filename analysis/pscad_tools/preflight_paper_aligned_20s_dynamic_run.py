#!/usr/bin/env python3
"""Read-only preflight for the one-shot paper-aligned 20 s dynamic Run.

This script does not invoke PSCAD, Build, EMTDC, or modify any PSCAD artifact.
It records the exact static scenario, channel baseline, and current generated
output inventory before the user performs the single permitted GUI Run.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
from datetime import datetime
from pathlib import Path
import xml.etree.ElementTree as ET


REPO = Path(__file__).resolve().parents[2]
DEFAULT_MAIN = Path(r"C:\pscad_work\pnnl_39_3ibr_pscad46_strip5\PSCAD\3IBR.pscx")
DEFAULT_TRIAL = Path(r"C:\pscad_work\pnnl_39_3ibr_pscad46_strip5\PSCAD\3IBR_DFIG1_TRIAL.pscx")
DEFAULT_GF46 = Path(r"C:\pscad_work\pnnl_39_3ibr_pscad46_strip5\PSCAD\3IBR_DFIG1_TRIAL.gf46")

EXPECTED_MAIN_SHA = "CBA120BB167CB7FA6C4A1AE4471268850AB61761EC1877EB7B87015627FE9DAB"
EXPECTED_TRIAL_SHA = "F81959EA62211FF9C1536C8481B67675AFE4DDCC3C56E804D048731A4B88A300"


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest().upper()


def load_xml(path: Path) -> ET.Element:
    return ET.fromstring(path.read_text(encoding="utf-8", errors="replace"))


def write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def read_json(path: Path) -> object:
    return json.loads(path.read_text(encoding="utf-8"))


def params_under(user: ET.Element) -> dict[str, str]:
    out: dict[str, str] = {}
    for param in user.findall(".//param"):
        name = param.attrib.get("name")
        if name:
            out[name] = param.attrib.get("value", "")
    return out


def as_float(value: str | None) -> float | None:
    try:
        return float(value) if value is not None else None
    except ValueError:
        return None


def project_settings(root: ET.Element) -> dict[str, str]:
    return {p.attrib.get("name", ""): p.attrib.get("value", "") for p in root.findall("./paramlist/param")}


def output_channels(root: ET.Element) -> tuple[dict[str, object], list[dict[str, object]]]:
    rows: list[dict[str, object]] = []
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
                }
            )
    return {"xml_output_channel_count": len(rows), "status": "pass" if len(rows) == 448 else "fail"}, rows


def fault_status(root: ET.Element, gf46: Path) -> dict[str, object]:
    faults = [u for u in root.iter("User") if "tfault" in u.attrib.get("defn", "").lower()]
    fault = faults[0] if faults else None
    params = params_under(fault) if fault is not None else {}
    p3_dta = gf46 / "P3.dta"
    p3_f = gf46 / "P3.f"
    dta_text = p3_dta.read_text(encoding="utf-8", errors="replace") if p3_dta.exists() else ""
    f_text = p3_f.read_text(encoding="utf-8", errors="replace") if p3_f.exists() else ""
    return {
        "fault_component_count": len(faults),
        "fault_component_id": fault.attrib.get("id") if fault is not None else None,
        "fault_defn": fault.attrib.get("defn") if fault is not None else None,
        "fault_x": fault.attrib.get("x") if fault is not None else None,
        "fault_y": fault.attrib.get("y") if fault is not None else None,
        "fault_start_s": as_float(params.get("TF")),
        "fault_duration_s": as_float(params.get("DF")),
        "fault_clear_s": (as_float(params.get("TF")) or 0.0) + (as_float(params.get("DF")) or 0.0),
        "n29_ground_branch_evidence_count": sum(1 for line in dta_text.splitlines() if "N29(" in line and "GND" in line),
        "three_phase_fault_code_present": "Three Phase Fault" in f_text and "E3PHFLT1_EXE" in f_text,
        "fault_timing_code_present": "TIME .GE. 0.5" in f_text and "TIME .GE. (0.5+2.0)" in f_text,
    }


def tline_measurement_status(root: ET.Element) -> dict[str, object]:
    inventory = read_json(REPO / "data/reference/full_network_tline_inventory.json")
    pgb_names = {
        (params_under(u).get("Name") or params_under(u).get("Title") or "")
        for u in root.iter("User")
        if u.attrib.get("defn") == "master:pgb"
    }
    missing: list[dict[str, object]] = []
    for item in inventory.get("tlines", []):
        branch = item["network_branch_id"]
        expected = [f"{branch}_{terminal}_{quantity}" for terminal in ("A", "B") for quantity in ("P", "Q", "I")]
        absent = [name for name in expected if name not in pgb_names]
        if absent:
            missing.append({"network_branch_id": branch, "missing": absent})
    return {
        "inventory_tline_count": len(inventory.get("tlines", [])),
        "expected_tline_raw_channel_count": len(inventory.get("tlines", [])) * 6,
        "missing_tline_channel_groups": missing,
        "status": "pass" if len(inventory.get("tlines", [])) == 31 and not missing else "fail",
    }


def default_trial_state(root: ET.Element) -> dict[str, object]:
    f_text_path = DEFAULT_GF46 / "P3.f"
    f_text = f_text_path.read_text(encoding="utf-8", errors="replace") if f_text_path.exists() else ""
    return {
        "IBR2_TEST_ENABLE_label_present": "IBR2_TEST_ENABLE" in ET.tostring(root, encoding="unicode"),
        "IBR3_TEST_ENABLE_label_present": "IBR3_TEST_ENABLE" in ET.tostring(root, encoding="unicode"),
        "IBR2_TEST_OPEN_TIME_S_4_in_build_code": "IBR2_TEST_OPEN_TIME_S = 4.0" in f_text,
        "IBR3_TEST_OPEN_TIME_S_5_in_build_code": "IBR3_TEST_OPEN_TIME_S = 5.0" in f_text,
        "status": "pass"
        if "IBR2_TEST_ENABLE" in ET.tostring(root, encoding="unicode")
        and "IBR3_TEST_ENABLE" in ET.tostring(root, encoding="unicode")
        and "IBR2_TEST_OPEN_TIME_S = 4.0" in f_text
        and "IBR3_TEST_OPEN_TIME_S = 5.0" in f_text
        else "fail",
    }


def file_inventory(directory: Path) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    if not directory.exists():
        return rows
    for p in sorted(directory.iterdir()):
        if p.is_file():
            rows.append(
                {
                    "name": p.name,
                    "path": str(p),
                    "suffix": p.suffix.lower(),
                    "length": p.stat().st_size,
                    "mtime_local": datetime.fromtimestamp(p.stat().st_mtime).isoformat(timespec="seconds"),
                    "sha256": sha256(p) if p.stat().st_size <= 25_000_000 else None,
                }
            )
    return rows


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--main-pscx", type=Path, default=DEFAULT_MAIN)
    parser.add_argument("--trial-pscx", type=Path, default=DEFAULT_TRIAL)
    parser.add_argument("--gf46-dir", type=Path, default=DEFAULT_GF46)
    args = parser.parse_args()

    main_sha = sha256(args.main_pscx)
    trial_sha = sha256(args.trial_pscx)
    root = load_xml(args.trial_pscx)
    settings = project_settings(root)
    channel_summary, channel_rows = output_channels(root)
    fault = fault_status(root, args.gf46_dir)
    tline = tline_measurement_status(root)
    defaults = default_trial_state(root)
    final_static_audit = read_json(REPO / "data/validation/paper_aligned_fault_scenario_final_audit.json")
    full_network_audit = read_json(REPO / "data/validation/full_network_tline_measurement_final_audit.json")
    generated_inventory = file_inventory(args.gf46_dir)

    gates = {
        "main_project_integrity_status": "pass" if main_sha == EXPECTED_MAIN_SHA else "fail",
        "trial_static_scenario_integrity_status": "pass" if trial_sha == EXPECTED_TRIAL_SHA else "fail",
        "fault_configuration_status": "pass"
        if fault["fault_component_count"] == 1
        and fault["fault_start_s"] == 0.5
        and fault["fault_duration_s"] == 2.0
        and fault["fault_clear_s"] == 2.5
        and fault["n29_ground_branch_evidence_count"] >= 3
        and fault["three_phase_fault_code_present"]
        and fault["fault_timing_code_present"]
        else "fail",
        "simulation_horizon_status": "pass"
        if as_float(settings.get("time_duration")) == 20.0
        and as_float(settings.get("time_step")) == 5.0
        and as_float(settings.get("sample_step")) == 10000.0
        else "fail",
        "existing_448_channel_preservation_status": channel_summary["status"],
        "full_network_tline_measurement_preservation_status": tline["status"],
        "default_trial_state_status": defaults["status"],
        "build_artifact_status": "pass"
        if (args.gf46_dir / "P3.f").exists()
        and (args.gf46_dir / "P3.dta").exists()
        and (args.gf46_dir / "3IBR_DFIG1_TRIAL.map").exists()
        and (args.gf46_dir / "3IBR_DFIG1_TRIAL.exe").exists()
        else "fail",
        "static_final_audit_status": "pass" if final_static_audit.get("execution_status") == "pass" else "fail",
        "full_network_tline_final_audit_status": "pass" if full_network_audit.get("execution_status") == "pass" else "fail",
    }
    execution_status = "pass" if all(v == "pass" for v in gates.values()) else "paper_aligned_20s_dynamic_run_static_fallback"

    input_manifest = {
        "manifest_name": "paper_aligned_20s_dynamic_run_input_manifest",
        "generated_at_local": datetime.now().isoformat(timespec="seconds"),
        "main_pscx": str(args.main_pscx),
        "trial_pscx": str(args.trial_pscx),
        "gf46_dir": str(args.gf46_dir),
        "main_sha_before_run": main_sha,
        "trial_sha_before_run": trial_sha,
        "run_output_directory": str(args.gf46_dir),
        "expected_output_filename_pattern": [
            "3IBR_DFIG1_TRIAL_*.out",
            "3IBR_DFIG1_TRIAL.inf",
            "3IBR_DFIG1_TRIAL.out",
            "*.out",
            "*.inf",
        ],
        "existing_output_file_inventory": [
            x for x in generated_inventory if x["suffix"] in {".out", ".inf"}
        ],
        "existing_generated_file_inventory": generated_inventory,
        "run_start_time_placeholder": None,
        "single_permitted_run_status": "pending_user_gui_run",
        "model_editing_allowed": False,
        "build_allowed": False,
    }

    channel_baseline = {
        "baseline_name": "paper_aligned_20s_dynamic_run_channel_baseline",
        "generated_at_local": datetime.now().isoformat(timespec="seconds"),
        "xml_output_channel_count": channel_summary["xml_output_channel_count"],
        "expected_original_existing_channel_count": 262,
        "expected_tline_raw_channel_count": 186,
        "tline_measurement_status": tline,
        "channels": channel_rows,
    }

    preflight = {
        "audit_name": "paper_aligned_20s_dynamic_run_preflight",
        "generated_at_local": datetime.now().isoformat(timespec="seconds"),
        "execution_status": execution_status,
        "gates": gates,
        "main_sha_before_run": main_sha,
        "trial_sha_before_run": trial_sha,
        "fault": fault,
        "project_settings": {
            "time_duration": settings.get("time_duration"),
            "time_step": settings.get("time_step"),
            "sample_step": settings.get("sample_step"),
        },
        "output_channel_summary": channel_summary,
        "tline_measurement_summary": tline,
        "default_trial_state": defaults,
        "run_input_manifest": "data/validation/paper_aligned_20s_dynamic_run_input_manifest.json",
        "next_action": "allow_single_user_gui_run" if execution_status == "pass" else "do_not_run_static_fallback",
    }

    write_json(REPO / "data/validation/paper_aligned_20s_dynamic_run_preflight.json", preflight)
    write_json(REPO / "data/validation/paper_aligned_20s_dynamic_run_channel_baseline.json", channel_baseline)
    write_json(REPO / "data/validation/paper_aligned_20s_dynamic_run_input_manifest.json", input_manifest)

    print(json.dumps(preflight, ensure_ascii=False, indent=2))
    return 0 if execution_status == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
