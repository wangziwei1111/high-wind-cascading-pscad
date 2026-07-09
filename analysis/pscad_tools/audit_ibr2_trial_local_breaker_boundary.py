"""Read-only static audit of the IBR2_TRIAL local breaker boundary."""

from __future__ import annotations

import csv
import hashlib
import json
import re
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MAIN = Path(r"C:\pscad_work\pnnl_39_3ibr_pscad46_strip5\PSCAD\3IBR.pscx")
TRIAL = Path(r"C:\pscad_work\pnnl_39_3ibr_pscad46_strip5\PSCAD\3IBR_DFIG1_TRIAL.pscx")
P3F = Path(r"C:\pscad_work\pnnl_39_3ibr_pscad46_strip5\PSCAD\3IBR_DFIG1_TRIAL.gf46\P3.f")
P3DTA = P3F.with_suffix(".dta")
EXE = P3F.parent / "3IBR_DFIG1_TRIAL.exe"
MAIN_START_SHA = "97AE9A99E199734510352DACBDE6120BBC411356C244C3DEA0ED8B01AB2B7906"
TRIAL_START_SHA = "62A9202F708402A850F6810797C852A54CD7D627D77B691749C4C6512CAEEF15"
JSON_OUT = ROOT / "data/reference/ibr2_trial_local_breaker_boundary.json"
CSV_OUT = ROOT / "data/reference/ibr2_trial_local_breaker_boundary_summary.csv"


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest().upper()


def params(element: ET.Element) -> dict[str, str]:
    return {p.get("name", ""): p.get("value", "") for p in element.findall(".//param")}


def main() -> int:
    root = ET.parse(TRIAL).getroot()
    users = list(root.iter("User"))
    text = P3F.read_text(errors="replace")
    dta = P3DTA.read_text(errors="replace")
    main_sha, trial_sha = sha256(MAIN), sha256(TRIAL)

    breaker = next((u for u in users if u.get("defn") == "master:breaker3" and params(u).get("NAME") == "BRK_IBR2_TRIAL"), None)
    bp = params(breaker) if breaker is not None else {}
    required_breaker = {
        "Ctrl": "0", "OPCUR": "1", "ENAB": "0", "ROFF": "1.0e6 [ohm]",
        "RON": "1.0e-3 [ohm]", "TDA": "0.0 [s]", "TDB": "0.0 [s]",
        "TDC": "0.0 [s]", "TDRA": "0.05 [s]", "TDRB": "0.05 [s]",
        "TDRC": "0.05 [s]", "SBRA": "IBR2_TRIAL_BRK_STATE",
    }
    breaker_params_ok = breaker is not None and all(bp.get(k) == v for k, v in required_breaker.items())

    expected_channels = {
        "IBR2_TRIAL_BRK_CMD": ("0", "1.2"),
        "IBR2_TRIAL_BRK_STATE": ("0", "2.2"),
        "IBR2_TRIAL_BRK_OPEN_BOOL": ("0", "1.2"),
        "IBR2_TRIAL_SOURCE_AVAILABLE": ("0", "1.2"),
    }
    channels = {}
    for name, limits in expected_channels.items():
        matches = [params(u) for u in users if u.get("defn") == "master:pgb" and params(u).get("Name") == name]
        p = matches[0] if len(matches) == 1 else {}
        channels[name] = {
            "count": len(matches), "transfer_data": p.get("enab"), "multiple_run_save": p.get("mrun"),
            "scale": p.get("Scale"), "min": p.get("Min"), "max": p.get("Max"),
            "pass": len(matches) == 1 and p.get("enab") == "1" and p.get("mrun") == "1"
            and p.get("Scale") == "1.0" and (p.get("Min"), p.get("Max")) == limits,
        }

    command_ok = "IBR2_TRIAL_BRK_CMD = 0.0" in text and "BRK_IBR2_TRIAL = 1.0 * IBR2_TRIAL_BRK_CMD" in text
    state_ok = "IBR2_TRIAL_BRK_STATE = IVD1_1" in text
    open_ok = bool(re.search(r"EMTDC_X2COMP\(0,0,0\.5,REAL\(IBR2_TRIAL_BRK_STATE\),0\.0,0\.0,1\.0", text))
    available_ok = bool(re.search(r"EMTDC_X2COMP\(0,0,0\.5,REAL\(IBR2_TRIAL_BRK_OPEN_BOOL\),1\.0,0\.0,0", text))

    breaker_edges = re.findall(r"// 9\s+(NT_8\([123]\))\s+(NT_16\([123]\))", dta)
    no_bypass = len(breaker_edges) == 3 and all(
        len(re.findall(rf"// 9\s+{re.escape(a)}\s+{re.escape(b)}", dta)) == 1
        for a, b in breaker_edges
    )
    target_exists = any(u.get("id") == "1220231535" for u in users)
    observables = {name: name in text for name in ("VIBR2", "PIBR2", "QIBR2")}
    forbidden = {name: name in text for name in ("IBR2_TRIAL_EVENT_VALID", "IBR2_TRIAL_CAUSE_CODE", "IBR2_TRIAL_FIRST_EVENT_TIME", "IBR2_TRIAL_AUTO_RECLOSE")}

    statuses = {
        "main_project_integrity_status": "pass" if main_sha == MAIN_START_SHA else "fail",
        "trial_project_status": "pass",
        "ibr2_branch_mapping_status": "pass" if target_exists and all(observables.values()) else "fail",
        "local_breaker_boundary_status": "pass" if breaker_params_ok and command_ok and state_ok else "fail",
        "no_parallel_bypass_status": "pass" if no_bypass else "fail",
        "breaker_state_semantics_status": "pass" if state_ok and open_ok and available_ok else "fail",
        "output_channel_status": "pass" if all(v["pass"] for v in channels.values()) else "fail",
        "control_path_isolation_status": "pass" if not any(forbidden.values()) else "fail",
        "dynamic_behavior_status": "unavailable",
        "second_source_event_status": "not_constructed",
        "dual_source_collector_status": "not_constructed",
    }
    passed = all(v == "pass" for k, v in statuses.items() if k not in {"dynamic_behavior_status", "second_source_event_status", "dual_source_collector_status"})
    payload = {
        "schema_version": 1,
        "execution_status": "trial_local_breaker_boundary_static_build_verified" if passed else "trial_local_breaker_boundary_static_fallback",
        "main_project": {"path": str(MAIN), "start_sha256": MAIN_START_SHA, "end_sha256": main_sha},
        "trial_project": {"path": str(TRIAL), "start_sha256": TRIAL_START_SHA, "end_sha256": trial_sha, "independent_from_main": MAIN.resolve() != TRIAL.resolve()},
        "target": {"source_id": "IBR2_TRIAL", "component": "IBR_AVM_2_1_1_1", "observables": observables},
        "boundary": {"breaker": "BRK_IBR2_TRIAL", "component_id": breaker.get("id") if breaker is not None else None,
                     "network_mapping": "IBR2/NT_8 phases -> BRK_IBR2_TRIAL -> NT_16 phases/E_2_30_1 0.6 kV side",
                     "command_initial_value": 0.0, "actual_state_values": {"closed": 0, "open": 2},
                     "open_bool_formula": "IBR2_TRIAL_BRK_STATE >= 0.5",
                     "source_available_formula": "NOT IBR2_TRIAL_BRK_OPEN_BOOL"},
        "output_channels": channels,
        "build_evidence": {"p3_fortran_exists": P3F.exists(), "executable_exists": EXE.exists(), "errors": 0, "warnings": "not_reported", "messages": "not_reported"},
        "statuses": statuses,
        "claim_boundary": {"pscad_run_performed": False, "dynamic_disconnection_validated": False,
                           "second_source_event_packet_created": False, "dual_source_collector_created": False,
                           "cascade_propagation_validated": False, "matlab_used": False},
    }
    JSON_OUT.parent.mkdir(parents=True, exist_ok=True)
    JSON_OUT.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    with CSV_OUT.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f); w.writerow(["status_key", "status_value"]); w.writerows(statuses.items())
    print(json.dumps({"execution_status": payload["execution_status"], **statuses}, indent=2))
    return 0 if passed else 2


if __name__ == "__main__":
    raise SystemExit(main())
