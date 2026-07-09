"""Audit the trial IBR local breaker boundary task state.

This script is read-only with respect to PSCAD files.  It records whether the
trial project exists, whether the main project still matches the protected
baseline, and whether the task may proceed beyond trial creation.
"""

from __future__ import annotations

import csv
import hashlib
import json
import re
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
MAIN_PROJECT = Path(r"C:\pscad_work\pnnl_39_3ibr_pscad46_strip5\PSCAD\3IBR.pscx")
TRIAL_PROJECT = Path(r"C:\pscad_work\pnnl_39_3ibr_pscad46_strip5\PSCAD\3IBR_DFIG1_TRIAL.pscx")
TRIAL_FORTRAN = Path(r"C:\pscad_work\pnnl_39_3ibr_pscad46_strip5\PSCAD\3IBR_DFIG1_TRIAL.gf46\P3.f")
FEASIBILITY_JSON = REPO_ROOT / "data" / "reference" / "trial_ibr_breaker_insertion_feasibility.json"
JSON_OUT = REPO_ROOT / "data" / "reference" / "ibr_trial_local_breaker_boundary.json"
CSV_OUT = REPO_ROOT / "data" / "reference" / "ibr_trial_local_breaker_boundary_summary.csv"

PROTECTED_MAIN_SHA = "9A4D8B4594CDEAC3085E34BE64A6A52DA0CB626FE91E37240D0C8CE74F6D33DB"


def sha256(path: Path) -> str | None:
    if not path.exists():
        return None
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def signal_exists(text: str, signal: str) -> bool:
    return bool(re.search(rf"\b{re.escape(signal)}\b", text))


def main() -> int:
    feasibility = json.loads(FEASIBILITY_JSON.read_text(encoding="utf-8")) if FEASIBILITY_JSON.exists() else {}
    selected = feasibility.get("selected_source") or {}

    main_sha = sha256(MAIN_PROJECT)
    trial_sha = sha256(TRIAL_PROJECT)
    trial_text = TRIAL_FORTRAN.read_text(errors="replace") if TRIAL_FORTRAN.exists() else ""

    source_id = selected.get("source_id", "IBR2_TRIAL")
    breaker_name = f"BRK_{source_id}"
    new_signals = [
        f"{source_id}_BRK_CMD",
        f"{source_id}_BRK_STATE",
        f"{source_id}_BRK_OPEN_BOOL",
        f"{source_id}_SOURCE_AVAILABLE",
    ]
    signal_presence = {signal: signal_exists(trial_text, signal) for signal in new_signals}
    breaker_present = signal_exists(trial_text, breaker_name)

    main_integrity = "pass" if main_sha == PROTECTED_MAIN_SHA else "fail"
    phase_b_constructed = breaker_present and all(signal_presence.values())

    payload = {
        "schema_version": 1,
        "execution_status": "trial_ibr_breaker_boundary_static_fallback",
        "selected_source_id": source_id,
        "selected_candidate": selected.get("candidate_id", "IBR_AVM_2_1_1_1"),
        "main_project": {
            "path": str(MAIN_PROJECT),
            "protected_sha256": PROTECTED_MAIN_SHA,
            "current_sha256": main_sha,
            "integrity_status": main_integrity,
        },
        "trial_project": {
            "path": str(TRIAL_PROJECT),
            "sha256": trial_sha,
            "exists": TRIAL_PROJECT.exists(),
            "fortran_path": str(TRIAL_FORTRAN),
            "fortran_exists": TRIAL_FORTRAN.exists(),
        },
        "planned_boundary": {
            "source_id": source_id,
            "target_ibr": selected.get("candidate_id", "IBR_AVM_2_1_1_1"),
            "p_q_v_signals": selected.get("p_q_v_signals", ["VIBR2", "PIBR2", "QIBR2"]),
            "breaker_name": breaker_name,
            "recommended_insertion_point": selected.get("recommended_insertion_point", ""),
            "new_signals": new_signals,
        },
        "static_presence": {
            "breaker_present_in_trial_fortran": breaker_present,
            "new_signal_presence_in_trial_fortran": signal_presence,
        },
        "statuses": {
            "trial_project_status": "created" if TRIAL_PROJECT.exists() else "missing",
            "ibr_branch_mapping_status": feasibility.get("ibr_branch_mapping_status", "unavailable"),
            "local_breaker_boundary_status": "pass" if phase_b_constructed else "not_constructed",
            "breaker_state_semantics_status": "pass" if phase_b_constructed else "not_constructed",
            "output_channel_status": "pass" if phase_b_constructed else "not_constructed",
            "control_path_isolation_status": "unavailable_after_main_integrity_failure",
            "main_project_integrity_status": main_integrity,
            "dynamic_behavior_status": "unavailable",
            "second_source_event_status": "not_constructed",
            "dual_source_collector_status": "not_constructed",
        },
        "build_evidence": {
            "trial_build_user_report": "completed",
            "trial_p3_fortran_exists": TRIAL_FORTRAN.exists(),
            "build_error_count": "unavailable",
            "build_warning_count": "unavailable",
            "build_message_count": "unavailable",
        },
        "stop_reason": (
            "Main project SHA changed from the protected baseline after trial stage A. "
            "Per task rules, no further GUI construction is allowed in this turn."
        ),
        "claim_boundary": {
            "pscad_run_performed": False,
            "main_project_modification_by_codex": False,
            "trial_breaker_inserted": bool(phase_b_constructed),
            "second_source_event_packet_created": False,
            "dual_source_collector_created": False,
        },
    }

    JSON_OUT.parent.mkdir(parents=True, exist_ok=True)
    JSON_OUT.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    with CSV_OUT.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=["status_key", "status_value"])
        writer.writeheader()
        for key, value in payload["statuses"].items():
            writer.writerow({"status_key": key, "status_value": value})

    print(f"execution_status={payload['execution_status']}")
    print(f"main_project_integrity_status={main_integrity}")
    print(f"trial_project_status={payload['statuses']['trial_project_status']}")
    print(f"local_breaker_boundary_status={payload['statuses']['local_breaker_boundary_status']}")
    print(f"json={JSON_OUT}")
    print(f"csv={CSV_OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
