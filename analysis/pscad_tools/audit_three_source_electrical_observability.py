"""Final static audit for three-source electrical observability outputs.

Read-only: validates PSCAD XML and generated Fortran after the user performed
manual Output Channel additions and Build Modified.  No PSCAD Run is invoked.
"""

from __future__ import annotations

import csv
import hashlib
import json
import re
import shutil
import xml.etree.ElementTree as ET
from datetime import datetime, timezone, timedelta
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
PSCAD = Path(r"C:\pscad_work\pnnl_39_3ibr_pscad46_strip5\PSCAD")
MAIN = PSCAD / "3IBR.pscx"
TRIAL = PSCAD / "3IBR_DFIG1_TRIAL.pscx"
P3F = PSCAD / "3IBR_DFIG1_TRIAL.gf46" / "P3.f"
EXE = PSCAD / "3IBR_DFIG1_TRIAL.gf46" / "3IBR_DFIG1_TRIAL.exe"

EXPECTED_MAIN_SHA = "CBA120BB167CB7FA6C4A1AE4471268850AB61761EC1877EB7B87015627FE9DAB"
EXPECTED_FINAL_OUTPUT_CHANNELS = 262
EXPECTED_NPGB = 115

EXPECTED = {
    "CASCADE3_ELEC_DFIG_V": "VIBR1_2",
    "CASCADE3_ELEC_DFIG_P": "PIBR1_2",
    "CASCADE3_ELEC_DFIG_Q": "QIBR1_2",
    "CASCADE3_ELEC_IBR2_V": "VIBR2",
    "CASCADE3_ELEC_IBR2_P": "PIBR2",
    "CASCADE3_ELEC_IBR2_Q": "QIBR2",
    "CASCADE3_ELEC_IBR3_V": "VIBR3",
    "CASCADE3_ELEC_IBR3_P": "PIBR3",
    "CASCADE3_ELEC_IBR3_Q": "QIBR3",
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def params(element: ET.Element) -> dict[str, str]:
    return {p.get("name", ""): p.get("value", "") for p in element.findall("./paramlist/param")}


def output_channels(root: ET.Element) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for user in root.iter("User"):
        if user.get("defn") != "master:pgb":
            continue
        p = params(user)
        rows.append(
            {
                "id": user.get("id", ""),
                "x": user.get("x", ""),
                "y": user.get("y", ""),
                "name": p.get("Name", ""),
                "scale": p.get("Scale", ""),
                "units": p.get("Units", ""),
                "min": p.get("Min", ""),
                "max": p.get("Max", ""),
                "transfer_data": p.get("enab", ""),
                "display": p.get("Display", ""),
                "multiple_run_save": p.get("mrun", ""),
                "use_signal_name": p.get("UseSignalName", ""),
                "gaddress": p.get("gaddress", ""),
            }
        )
    return rows


def parse_pgb_assignments(p3f: str) -> dict[str, str]:
    mapping: dict[str, str] = {}
    current: str | None = None
    for line in p3f.splitlines():
        comment = re.search(r"Output Channel '([^']+)'", line)
        if comment:
            current = comment.group(1)
            continue
        assign = re.search(r"PGB\(IPGB\+\d+\)\s*=\s*(.+)", line)
        if assign and current:
            mapping[current] = assign.group(1).strip()
            current = None
    return mapping


def main() -> int:
    out_dir = ROOT / "data" / "validation"
    out_dir.mkdir(parents=True, exist_ok=True)
    docs_dir = ROOT / "docs"
    docs_dir.mkdir(parents=True, exist_ok=True)

    root = ET.parse(TRIAL).getroot()
    channels = output_channels(root)
    by_name = {row["name"]: row for row in channels}
    p3f = P3F.read_text(encoding="utf-8", errors="replace")
    pgb = parse_pgb_assignments(p3f)
    npgb_values = [int(m.group(1)) for m in re.finditer(r"NPGB\s*=\s*NPGB\s*\+\s*(\d+)", p3f)]

    new_channel_details: dict[str, object] = {}
    csv_rows: list[dict[str, str]] = []
    for name, signal in EXPECTED.items():
        row = by_name.get(name)
        fortran_signal = pgb.get(name)
        param_ok = bool(
            row
            and row["scale"] == "1.0"
            and row["units"] == ""
            and row["min"] == "-2.0"
            and row["max"] == "2.0"
            and row["transfer_data"] == "1"
            and row["multiple_run_save"] == "0"
            and row["use_signal_name"] == "0"
        )
        mapping_ok = fortran_signal == signal
        new_channel_details[name] = {
            "expected_signal": signal,
            "xml": row,
            "fortran_assignment": fortran_signal,
            "parameter_status": "pass" if param_ok else "fail",
            "mapping_status": "pass" if mapping_ok else "fail",
        }
        csv_rows.append(
            {
                "new_output_channel": name,
                "expected_signal": signal,
                "fortran_assignment": fortran_signal or "",
                "mapping_status": "pass" if mapping_ok else "fail",
                "parameter_status": "pass" if param_ok else "fail",
            }
        )

    main_sha = sha256(MAIN)
    trial_sha = sha256(TRIAL)
    forbidden_dynamic = {
        "run_output_detection": bool(re.search(r"\.out\b|EMTDC Run|runtime result", p3f, re.I)),
        "matlab_coupling_token": "matlab" in TRIAL.read_text(encoding="utf-8-sig", errors="replace").lower(),
    }

    statuses = {
        "main_project_integrity_status": "pass" if main_sha == EXPECTED_MAIN_SHA else "fail",
        "trial_xml_parse_status": "pass",
        "final_output_channel_count_status": "pass" if len(channels) == EXPECTED_FINAL_OUTPUT_CHANNELS else "fail",
        "new_output_channel_presence_status": "pass" if all(name in by_name for name in EXPECTED) else "fail",
        "new_output_channel_parameter_status": "pass" if all(d["parameter_status"] == "pass" for d in new_channel_details.values()) else "fail",
        "new_output_channel_fortran_mapping_status": "pass" if all(d["mapping_status"] == "pass" for d in new_channel_details.values()) else "fail",
        "generated_fortran_npgb_status": "pass" if npgb_values and all(v == EXPECTED_NPGB for v in npgb_values) else "fail",
        "build_artifact_refresh_status": "pass" if P3F.exists() and EXE.exists() and P3F.stat().st_mtime >= TRIAL.stat().st_mtime else "fail",
        "monitor_only_scope_status": "pass" if not any(forbidden_dynamic.values()) else "fail",
        "pscad_run_status": "not_performed",
    }
    statuses["three_source_electrical_observability_static_build_status"] = (
        "pass" if all(v in ("pass", "not_performed") for v in statuses.values()) else "fail"
    )

    snapshot_dir = ROOT / "external" / "pscad_snapshot_20260702_three_source_electrical_observability_static"
    snapshot_dir.mkdir(parents=True, exist_ok=True)
    snapshot_path = snapshot_dir / "3IBR_DFIG1_TRIAL.pscx"
    shutil.copy2(TRIAL, snapshot_path)

    result = {
        "schema_version": 1,
        "audit_time": datetime.now(timezone(timedelta(hours=8))).isoformat(timespec="seconds"),
        "operation": "three_source_electrical_observability_final_static_audit",
        "main_project": {"path": str(MAIN), "sha256": main_sha, "expected_sha256": EXPECTED_MAIN_SHA},
        "trial_project": {"path": str(TRIAL), "sha256": trial_sha},
        "output_channels": {
            "expected_before": 253,
            "added": len(EXPECTED),
            "expected_final": EXPECTED_FINAL_OUTPUT_CHANNELS,
            "actual_final": len(channels),
        },
        "generated_fortran": {
            "path": str(P3F),
            "npgb_values": npgb_values,
            "expected_npgb": EXPECTED_NPGB,
            "exe_path": str(EXE),
            "p3f_last_write_time": datetime.fromtimestamp(P3F.stat().st_mtime).isoformat(timespec="seconds"),
            "exe_last_write_time": datetime.fromtimestamp(EXE.stat().st_mtime).isoformat(timespec="seconds"),
        },
        "new_channel_details": new_channel_details,
        "snapshot": str(snapshot_path),
        "statuses": statuses,
        "claim_boundary": {
            "pscad_build_verified": statuses["three_source_electrical_observability_static_build_status"] == "pass",
            "pscad_run_performed": False,
            "dynamic_electrical_response_validated": False,
            "event_logic_added": False,
            "control_feedback_added": False,
            "monitor_only_vpq_outputs_added": True,
        },
    }

    json_path = out_dir / "three_source_electrical_observability_final_audit.json"
    csv_path = out_dir / "three_source_electrical_observability_final_channel_trace.csv"
    json_path.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
    with csv_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(csv_rows[0]))
        writer.writeheader()
        writer.writerows(csv_rows)

    doc = f"""# Three-source electrical observability static Build audit

## Result

Static Build audit status: `{statuses["three_source_electrical_observability_static_build_status"]}`.

Nine monitor-only Output Channels were added in the trial project for existing
three-source V/P/Q observables. No PSCAD Run was performed, and no dynamic
electrical response is claimed.

## Signal map

| New Output Channel | Existing signal |
| --- | --- |
"""
    for name, signal in EXPECTED.items():
        doc += f"| `{name}` | `{signal}` |\n"
    doc += f"""
## Build evidence

- Output Channel count: {len(channels)} / expected {EXPECTED_FINAL_OUTPUT_CHANNELS}
- Generated Fortran NPGB values: {npgb_values}
- Main project SHA-256: `{main_sha}`
- Trial project SHA-256: `{trial_sha}`

## Boundary

This change adds observability only. It does not add sources, breakers,
event modules, time-ordering logic, protection logic, control feedback,
MATLAB coupling, or runtime validation.
"""
    (docs_dir / "THREE_SOURCE_ELECTRICAL_OBSERVABILITY_STATIC_AUDIT.md").write_text(doc, encoding="utf-8")

    print(json.dumps({"status": statuses["three_source_electrical_observability_static_build_status"], "json": str(json_path), "csv": str(csv_path)}, indent=2))
    return 0 if statuses["three_source_electrical_observability_static_build_status"] == "pass" else 2


if __name__ == "__main__":
    raise SystemExit(main())
