"""Read-only preflight for the three-event chronology module task.

This gate intentionally performs no PSCAD automation, Build, Run, or .pscx
write.  It validates that the protected main project is unchanged and that the
trial project is still at the qualified post-IBR3 baseline before any manual
GUI construction of THREE_EVENT_CHRONOLOGY_MONITOR is authorized.
"""

from __future__ import annotations

import hashlib
import json
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path


PSCAD = Path(r"C:\pscad_work\pnnl_39_3ibr_pscad46_strip5\PSCAD")
MAIN = PSCAD / "3IBR.pscx"
TRIAL = PSCAD / "3IBR_DFIG1_TRIAL.pscx"
P3F = PSCAD / "3IBR_DFIG1_TRIAL.gf46" / "P3.f"
P3DTA = P3F.with_suffix(".dta")

EXPECTED_MAIN_SHA = "CBA120BB167CB7FA6C4A1AE4471268850AB61761EC1877EB7B87015627FE9DAB"
EXPECTED_TRIAL_SHA = "CDFBBAA3A987B67E3B3BC3294E9993AB06AA3F77BED90AF111B6B35A55B0C99E"
EXPECTED_OUTPUT_CHANNEL_COUNT = 245

EXISTING_MODULES = (
    "MONITORED_OBJECT_EVENT_PACKET",
    "ONE_SHOT_BREAKER_OPEN_STIMULUS",
    "TWO_EVENT_CHRONOLOGY_MONITOR",
    "BREAKER_STATE_ADAPTER",
    "THREE_SOURCE_EVENT_COLLECTOR",
)

FORBIDDEN_NEW_TESTS = (
    "MODTEST_THREE_EVENT_CHRONOLOGY_NONE",
    "MODTEST_THREE_EVENT_CHRONOLOGY_TWO_STRICT",
    "MODTEST_THREE_EVENT_CHRONOLOGY_THREE_TIE",
)

SOURCE_INTERFACE_CANDIDATES = {
    "A_event_valid": ("DFIG_LVRT_CASCADE_EVENT_VALID",),
    "A_first_time": ("DFIG_LVRT_CAS_FIRST_TIME_S",),
    "B_event_valid": ("IBR2_CAS_EVT_VALID",),
    "B_first_time": ("IBR2_CAS_FIRST_S",),
    "C_event_valid": ("IBR3_CAS_EVT_VALID", "IBR3_TRIAL_CASCADE_EVENT_VALID"),
    "C_first_time": ("IBR3_CAS_FIRST_S", "IBR3_TRIAL_CASCADE_FIRST_EVENT_TIME_S"),
}

COLLECTOR_INTERFACE_CANDIDATES = {
    "evented_count": ("C3_EVENTED_COUNT", "CASCADE3_MONITOR_EVENTED_SOURCE_COUNT"),
    "first_time": ("C3_FIRST_TIME_S", "CASCADE3_MONITOR_FIRST_EVENT_TIME_S"),
    "first_source": ("C3_FIRST_SRC_CODE", "CASCADE3_MONITOR_FIRST_EVENT_SOURCE_CODE"),
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def params(element: ET.Element) -> dict[str, str]:
    return {
        item.get("name", ""): item.get("value", "")
        for item in element.findall("./paramlist/param")
    }


def all_project_text(root: ET.Element, p3f: str, p3dta: str) -> str:
    return "\n".join(
        [
            ET.tostring(root, encoding="unicode"),
            p3f,
            p3dta,
        ]
    )


def present_label(text: str, candidates: tuple[str, ...]) -> str | None:
    for candidate in candidates:
        if re.search(rf"(?<![A-Za-z0-9_]){re.escape(candidate)}(?![A-Za-z0-9_])", text):
            return candidate
    return None


def fail_result(reason: str, **details: object) -> int:
    print(
        json.dumps(
            {
                "execution_status": "three_event_chronology_static_fallback",
                "failure_reason": reason,
                **details,
            },
            indent=2,
            ensure_ascii=False,
        )
    )
    return 2


def main() -> int:
    missing = [str(path) for path in (MAIN, TRIAL, P3F, P3DTA) if not path.exists()]
    if missing:
        return fail_result("required_path_missing", missing=missing)

    if MAIN.resolve() == TRIAL.resolve():
        return fail_result("main_and_trial_paths_not_distinct")

    try:
        main_root = ET.parse(MAIN).getroot()
        trial_root = ET.parse(TRIAL).getroot()
    except ET.ParseError as exc:
        return fail_result("project_xml_parse_error", error=str(exc))

    p3f = P3F.read_text(encoding="utf-8", errors="replace")
    p3dta = P3DTA.read_text(encoding="utf-8", errors="replace")
    combined_text = all_project_text(trial_root, p3f, p3dta)

    main_sha = sha256(MAIN)
    trial_sha = sha256(TRIAL)

    definitions = {item.get("name", ""): item for item in trial_root.iter("Definition")}
    output_channel_count = sum(
        user.get("defn") == "master:pgb" for user in trial_root.iter("User")
    )

    statuses: dict[str, str] = {}
    statuses["main_project_integrity_status"] = (
        "pass"
        if main_sha == EXPECTED_MAIN_SHA and main_root.get("version") == "4.6.2"
        else "fail"
    )
    statuses["trial_project_status"] = (
        "pass"
        if trial_sha == EXPECTED_TRIAL_SHA
        and trial_root.get("version") == "4.6.2"
        and output_channel_count == EXPECTED_OUTPUT_CHANNEL_COUNT
        else "fail"
    )

    module_presence = {name: name in definitions for name in EXISTING_MODULES}
    pages = {
        "MODULE_TEMPLATE_TEST_HARNESS": "MODULE_TEMPLATE_TEST_HARNESS" in definitions,
        "CASCADE_CONTROL_MODULE_LIBRARY": "CASCADE_CONTROL_MODULE_LIBRARY" in definitions,
    }
    statuses["module_library_phase2_status"] = (
        "pass" if all(module_presence.values()) and all(pages.values()) else "fail"
    )

    chronology_absent = "THREE_EVENT_CHRONOLOGY_MONITOR" not in definitions
    tests_absent = all(test_name not in combined_text for test_name in FORBIDDEN_NEW_TESTS)
    statuses["chronology_module_clean_state_status"] = (
        "pass" if chronology_absent and tests_absent else "fail"
    )

    source_interfaces = {
        key: present_label(combined_text, candidates)
        for key, candidates in SOURCE_INTERFACE_CANDIDATES.items()
    }
    collector_interfaces = {
        key: present_label(combined_text, candidates)
        for key, candidates in COLLECTOR_INTERFACE_CANDIDATES.items()
    }
    collector_present = "CASCADE3_TRIAL__EVENT_COLLECTOR" in combined_text
    statuses["three_source_interface_status"] = (
        "pass"
        if collector_present
        and all(source_interfaces.values())
        and all(collector_interfaces.values())
        else "fail"
    )

    forbidden_structure_evidence = {
        "automatic_reclose": bool(re.search(r"AUTO[_ -]?RECLOSE|AUTORECLOSE", combined_text, re.I)),
        "matlab_component": any(
            "matlab" in (user.get("defn") or "").lower() for user in trial_root.iter("User")
        ),
        "fourth_source": bool(re.search(r"(?:SOURCE|SRC)[_ -]?D|FOURTH[_ -]?SOURCE|SOURCE[_ -]?4", combined_text, re.I)),
        "virtual_source": bool(re.search(r"VIRTUAL_(?:CAS|SOURCE)|CAS_VIRTUAL|VIRT[_ -]?SOURCE", combined_text, re.I)),
    }
    statuses["forbidden_structure_status"] = (
        "pass" if not any(forbidden_structure_evidence.values()) else "fail"
    )

    failed = [name for name, state in statuses.items() if state != "pass"]
    result = {
        "execution_status": (
            "three_event_chronology_gui_authorized"
            if not failed
            else "three_event_chronology_static_fallback"
        ),
        "statuses": statuses,
        "failed_statuses": failed,
        "paths": {
            "main": str(MAIN),
            "trial": str(TRIAL),
            "p3f": str(P3F),
            "p3dta": str(P3DTA),
        },
        "main_sha": main_sha,
        "expected_main_sha": EXPECTED_MAIN_SHA,
        "trial_sha": trial_sha,
        "expected_trial_sha": EXPECTED_TRIAL_SHA,
        "output_channel_count": output_channel_count,
        "module_presence": module_presence,
        "pages": pages,
        "chronology_clean_state": {
            "definition_absent": chronology_absent,
            "future_test_instances_absent": tests_absent,
            "future_test_instances": list(FORBIDDEN_NEW_TESTS),
        },
        "source_interfaces": source_interfaces,
        "collector_interfaces": collector_interfaces,
        "collector_present": collector_present,
        "forbidden_structure_evidence": forbidden_structure_evidence,
        "limitations": [
            "Read-only XML/generated-code preflight only; no PSCAD Build or Run was performed.",
            "GUI work is authorized only for the trial project after this gate passes.",
        ],
    }
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0 if not failed else 2


if __name__ == "__main__":
    sys.exit(main())
