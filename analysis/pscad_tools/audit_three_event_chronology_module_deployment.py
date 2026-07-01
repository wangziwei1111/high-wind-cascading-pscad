"""Static audit for THREE_EVENT_CHRONOLOGY_MONITOR deployment.

Read-only: parses PSCAD XML and generated source artifacts only.  It does not
launch PSCAD, Build, Run, or modify any project file.
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
EXPECTED_START_TRIAL_SHA = "CDFBBAA3A987B67E3B3BC3294E9993AB06AA3F77BED90AF111B6B35A55B0C99E"
EXPECTED_FINAL_OUTPUT_CHANNEL_COUNT = 253

EXISTING_MODULES = (
    "MONITORED_OBJECT_EVENT_PACKET",
    "ONE_SHOT_BREAKER_OPEN_STIMULUS",
    "TWO_EVENT_CHRONOLOGY_MONITOR",
    "BREAKER_STATE_ADAPTER",
    "THREE_SOURCE_EVENT_COLLECTOR",
)

MODULE_NAME = "THREE_EVENT_CHRONOLOGY_MONITOR"
HARNESS_INSTANCES = (
    "MODTEST_THREE_EVENT_CHRONOLOGY_NONE",
    "MODTEST_THREE_EVENT_CHRONOLOGY_TWO_STRICT",
    "MODTEST_THREE_EVENT_CHRONOLOGY_THREE_TIE",
)
PRODUCTION_INSTANCE = "CASCADE3_TRIAL__CHRONOLOGY_MONITOR"

INPUT_PORTS = (
    "IN_EVENT_VALID_A",
    "IN_FIRST_EVENT_TIME_A_S",
    "IN_EVENT_VALID_B",
    "IN_FIRST_EVENT_TIME_B_S",
    "IN_EVENT_VALID_C",
    "IN_FIRST_EVENT_TIME_C_S",
)
OUTPUT_PORTS = (
    "OUT_EVENTED_OBJECT_COUNT",
    "OUT_TIMED_EVENT_OBJECT_COUNT",
    "OUT_FIRST_EVENT_TIME_S",
    "OUT_SECOND_EVENT_TIME_S",
    "OUT_THIRD_EVENT_TIME_S",
    "OUT_FIRST_TO_SECOND_GAP_S",
    "OUT_SECOND_TO_THIRD_GAP_S",
    "OUT_FIRST_EVENT_SOURCE_CODE",
    "OUT_EVENT_ORDER_CLASS_CODE",
    "OUT_CHRONOLOGY_CONSISTENT",
)
FORBIDDEN_MODULE_LABELS = ("DFIG", "IBR2", "IBR3", "LINE_", "BRK_", "CASCADE3", "CAS_CHR")

SOURCE_INPUTS = (
    "DFIG_LVRT_CASCADE_EVENT_VALID",
    "DFIG_LVRT_CAS_FIRST_TIME_S",
    "IBR2_CAS_EVT_VALID",
    "IBR2_CAS_FIRST_S",
    "IBR3_CAS_EVT_VALID",
    "IBR3_CAS_FIRST_S",
)
CHR_OUTPUTS = (
    "CASCADE3_CHR_EVENTED_COUNT",
    "CASCADE3_CHR_TIMED_COUNT",
    "CASCADE3_CHR_FIRST_TIME_S",
    "CASCADE3_CHR_SECOND_TIME_S",
    "CASCADE3_CHR_THIRD_TIME_S",
    "CASCADE3_CHR_GAP_12_S",
    "CASCADE3_CHR_GAP_23_S",
    "CASCADE3_CHR_FIRST_SRC_CODE",
    "CASCADE3_CHR_ORDER_CLASS",
    "CASCADE3_CHR_CONSISTENT",
)
NEW_OUTPUT_CHANNELS = {
    "CASCADE3_MONITOR_TIMED_EVENT_SOURCE_COUNT": {"Min": "0", "Max": "3.2"},
    "CASCADE3_MONITOR_SECOND_EVENT_TIME_S": {"Min": "-1.2", "Max": "10.2"},
    "CASCADE3_MONITOR_THIRD_EVENT_TIME_S": {"Min": "-1.2", "Max": "10.2"},
    "CASCADE3_MONITOR_FIRST_TO_SECOND_GAP_S": {"Min": "-1.2", "Max": "10.2"},
    "CASCADE3_MONITOR_SECOND_TO_THIRD_GAP_S": {"Min": "-1.2", "Max": "10.2"},
    "CASCADE3_MONITOR_CHRONOLOGY_FIRST_SOURCE_CODE": {"Min": "0", "Max": "4.2"},
    "CASCADE3_MONITOR_EVENT_ORDER_CLASS_CODE": {"Min": "0", "Max": "6.2"},
    "CASCADE3_MONITOR_CHRONOLOGY_CONSISTENT": {"Min": "0", "Max": "1.2"},
}
FORBIDDEN_OUTPUT_CHANNELS = (
    "CASCADE3_MONITOR_GLOBAL_CAUSE_CODE",
    "CASCADE3_MONITOR_CAUSE_SUM",
    "CASCADE3_MONITOR_TOTAL_CAUSE",
)


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


def page_users(definition: ET.Element, name: str) -> list[ET.Element]:
    result: list[ET.Element] = []
    for user in definition.findall(".//User"):
        values = params(user)
        user_name = values.get("Name") or values.get("NAME") or ""
        if user_name == name:
            result.append(user)
    return result


def main() -> int:
    missing = [str(path) for path in (MAIN, TRIAL, P3F, P3DTA) if not path.exists()]
    if missing:
        print(json.dumps({"execution_status": "three_event_chronology_static_fallback", "missing": missing}, indent=2))
        return 2

    main_sha = sha256(MAIN)
    trial_sha = sha256(TRIAL)
    main_root = ET.parse(MAIN).getroot()
    trial_root = ET.parse(TRIAL).getroot()
    definitions = {item.get("name", ""): item for item in trial_root.iter("Definition")}
    module = definitions.get(MODULE_NAME)
    p3 = definitions.get("P3")
    harness = definitions.get("MODULE_TEMPLATE_TEST_HARNESS")
    all_text = TRIAL.read_text(encoding="utf-8-sig")
    p3f_text = P3F.read_text(encoding="utf-8", errors="replace")

    statuses: dict[str, str] = {}
    statuses["main_project_integrity_status"] = (
        "pass" if main_sha == EXPECTED_MAIN_SHA and main_root.get("version") == "4.6.2" else "fail"
    )
    statuses["trial_project_status"] = (
        "pass" if trial_root.get("version") == "4.6.2" and trial_sha != EXPECTED_START_TRIAL_SHA else "fail"
    )
    statuses["protected_module_library_status"] = (
        "pass" if all(name in definitions for name in EXISTING_MODULES) else "fail"
    )

    if module is None or p3 is None or harness is None:
        statuses.update({
            "three_event_chronology_template_status": "fail",
            "three_event_chronology_scope_isolation_status": "fail",
            "three_event_chronology_harness_status": "fail",
            "three_event_chronology_production_instance_status": "fail",
        })
    else:
        port_attrs = [dict(port.attrib) for port in module.findall("./svg/port")]
        port_names_by_mode = {
            "Input": {port.get("name") for port in port_attrs if port.get("mode") == "Input"},
            "Output": {port.get("name") for port in port_attrs if port.get("mode") == "Output"},
        }
        module_text = ET.tostring(module, encoding="unicode")
        # Namespace references to 3IBR_DFIG1_TRIAL are PSCAD mechanics; inspect user-visible labels.
        module_label_values = [
            (params(user).get("Name") or params(user).get("NAME") or "")
            for user in module.findall(".//User")
        ]
        forbidden_in_labels = {
            token: any(token in value for value in module_label_values)
            for token in FORBIDDEN_MODULE_LABELS
        }
        statuses["three_event_chronology_template_status"] = (
            "pass"
            if set(INPUT_PORTS).issubset(port_names_by_mode["Input"])
            and set(OUTPUT_PORTS).issubset(port_names_by_mode["Output"])
            else "fail"
        )
        statuses["three_event_chronology_scope_isolation_status"] = (
            "pass" if not any(forbidden_in_labels.values()) else "fail"
        )
        statuses["three_event_chronology_harness_status"] = (
            "pass"
            if all(page_users(harness, instance) for instance in HARNESS_INSTANCES)
            else "fail"
        )

        prod = page_users(p3, PRODUCTION_INSTANCE)
        main_page = definitions.get("Main")
        main_prod = page_users(main_page, PRODUCTION_INSTANCE) if main_page is not None else []
        p3_labels = [
            (params(user).get("Name") or params(user).get("NAME") or "")
            for user in p3.findall(".//User")
        ]
        statuses["three_event_chronology_production_instance_status"] = (
            "pass"
            if len(prod) == 1
            and not main_prod
            and all(label in p3_labels for label in SOURCE_INPUTS)
            and all(label in p3_labels for label in CHR_OUTPUTS)
            else "fail"
        )

        logic_tokens = {
            "time_logic": ("A_MIN", "B_MIN", "C_MIN", "A_MAX", "B_MAX", "C_MAX", "T_MIN", "T_MAX", "T_MID3"),
            "gap_logic": ("GAP12", "GAP23", "CNT_GE2", "CNT_GE3"),
            "first_source_logic": ("A_FIRST", "B_FIRST", "C_FIRST", "FM_CNT", "SRC1"),
            "order_class_logic": ("CLS2", "CLS3", "CLS_NORM", "ORDCLS", "CNT_BAD"),
            "consistency_logic": ("CONS", "CNT_BAD"),
        }
        statuses["three_event_time_logic_status"] = (
            "pass" if all(token in module_text for token in logic_tokens["time_logic"]) else "fail"
        )
        statuses["three_event_gap_logic_status"] = (
            "pass" if all(token in module_text for token in logic_tokens["gap_logic"]) else "fail"
        )
        statuses["three_event_first_source_logic_status"] = (
            "pass" if all(token in module_text for token in logic_tokens["first_source_logic"]) else "fail"
        )
        statuses["three_event_order_class_logic_status"] = (
            "pass" if all(token in module_text for token in logic_tokens["order_class_logic"]) else "fail"
        )
        statuses["three_event_consistency_logic_status"] = (
            "pass" if all(token in module_text for token in logic_tokens["consistency_logic"]) else "fail"
        )

    output_channels: dict[str, dict[str, str]] = {}
    for user in trial_root.iter("User"):
        if user.get("defn") != "master:pgb":
            continue
        values = params(user)
        channel_name = values.get("Name") or values.get("NAME") or ""
        output_channels[channel_name] = values

    output_channel_checks = {}
    for name, expected in NEW_OUTPUT_CHANNELS.items():
        actual = output_channels.get(name)
        output_channel_checks[name] = bool(
            actual
            and actual.get("UseSignalName") == "0"
            and actual.get("enab") == "1"
            and actual.get("Scale") == "1.0"
            and actual.get("mrun") == "1"
            and actual.get("Min") == expected["Min"]
            and actual.get("Max") == expected["Max"]
        )
    statuses["output_channel_status"] = (
        "pass"
        if sum(user.get("defn") == "master:pgb" for user in trial_root.iter("User"))
        == EXPECTED_FINAL_OUTPUT_CHANNEL_COUNT
        and all(output_channel_checks.values())
        and not any(name in output_channels for name in FORBIDDEN_OUTPUT_CHANNELS)
        else "fail"
    )

    control_forbidden = (
        "IBR2_TRIAL_BRK_CMD",
        "IBR3_TRIAL_BRK_CMD",
        "DFIG_LVRT_FINAL_BRK_CMD",
        "BRK_IBR2_TRIAL",
        "BRK_IBR3_TRIAL",
    )
    chr_control_intersection = {
        token: bool(re.search(rf"CASCADE3_CHR_.*{re.escape(token)}|{re.escape(token)}.*CASCADE3_CHR_", p3f_text))
        for token in control_forbidden
    }
    statuses["control_path_isolation_status"] = (
        "pass" if not any(chr_control_intersection.values()) else "fail"
    )

    forbidden_structure = {
        "fourth_source": bool(re.search(r"(?:SOURCE|SRC)[_ -]?D|FOURTH[_ -]?SOURCE|SOURCE[_ -]?4", all_text, re.I)),
        "virtual_source": bool(re.search(r"VIRTUAL_(?:CAS|SOURCE)|CAS_VIRTUAL|VIRT[_ -]?SOURCE", all_text, re.I)),
        "automatic_reclose": bool(re.search(r"AUTO[_ -]?RECLOSE|AUTORECLOSE", all_text, re.I)),
        "matlab": any("matlab" in (user.get("defn") or "").lower() for user in trial_root.iter("User")),
    }

    failed = [name for name, state in statuses.items() if state != "pass"]
    result = {
        "execution_status": "three_event_chronology_static_pass" if not failed else "three_event_chronology_static_fallback",
        "statuses": statuses,
        "failed_statuses": failed,
        "main_sha": main_sha,
        "trial_start_sha": EXPECTED_START_TRIAL_SHA,
        "trial_final_sha": trial_sha,
        "output_channel_count": sum(user.get("defn") == "master:pgb" for user in trial_root.iter("User")),
        "new_output_channel_checks": output_channel_checks,
        "production_instance": PRODUCTION_INSTANCE,
        "production_page": "P3",
        "source_mapping": {
            "A": ["DFIG_LVRT_CASCADE_EVENT_VALID", "DFIG_LVRT_CAS_FIRST_TIME_S"],
            "B": ["IBR2_CAS_EVT_VALID", "IBR2_CAS_FIRST_S"],
            "C": ["IBR3_CAS_EVT_VALID", "IBR3_CAS_FIRST_S"],
        },
        "harness_instances": list(HARNESS_INSTANCES),
        "forbidden_structure": forbidden_structure,
        "control_path_intersection": chr_control_intersection,
        "dynamic_behavior_status": "unavailable",
        "three_source_dynamic_behavior_status": "unavailable",
        "cascade_propagation_status": "unavailable",
        "matlab_status": "not_added",
        "run_performed": False,
        "build_status": "user_confirmed_zero_errors",
    }
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0 if not failed else 2


if __name__ == "__main__":
    sys.exit(main())
