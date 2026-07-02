#!/usr/bin/env python3
"""Read-only audit for the first full-network TLine measurement cell.

This verifies the single GUI-added E_16_19_1 dual-end P/Q/I metering cell
before the same pattern is expanded to every P3 TLine.  It writes only a repo
audit artifact and never edits PSCAD project/build files.
"""

from __future__ import annotations

import csv
import hashlib
import json
import re
from pathlib import Path
import xml.etree.ElementTree as ET


ROOT = Path(__file__).resolve().parents[2]
PSCAD = Path(r"C:\pscad_work\pnnl_39_3ibr_pscad46_strip5\PSCAD")
MAIN = PSCAD / "3IBR.pscx"
TRIAL = PSCAD / "3IBR_DFIG1_TRIAL.pscx"
GF46 = PSCAD / "3IBR_DFIG1_TRIAL.gf46"
P3_FORTRAN = GF46 / "P3.f"
MAP_FILE = GF46 / "3IBR_DFIG1_TRIAL.map"
BASELINE = ROOT / "data" / "validation" / "full_network_tline_measurement_existing_channel_baseline.json"
INVENTORY = ROOT / "data" / "reference" / "full_network_tline_inventory.csv"
AUDIT_OUT = ROOT / "data" / "validation" / "single_tline_measurement_cell_audit.json"

EXPECTED_MAIN_SHA = "CBA120BB167CB7FA6C4A1AE4471268850AB61761EC1877EB7B87015627FE9DAB"
BASELINE_TRIAL_SHA = "1F747F067339547ECCFD03AD41A1B56ABE3DDC6D627AD1F085B37BFA9532DD95"
TARGET = "E_16_19_1"
TARGET_CHANNELS = [
    "E_16_19_1_A_P",
    "E_16_19_1_A_Q",
    "E_16_19_1_A_I",
    "E_16_19_1_B_P",
    "E_16_19_1_B_Q",
    "E_16_19_1_B_I",
]
EXPECTED_CHANNEL_PARAMS = {
    "Group": "",
    "UseSignalName": "0",
    "enab": "1",
    "Display": "1",
    "Scale": "1.0",
    "Units": "",
    "mrun": "0",
    "Pol": "0",
    "Max": "2.0",
    "Min": "-2.0",
}
EXPECTED_METER_COMMON = {
    "MeasV": "0",
    "MeasI": "0",
    "MeasP": "1",
    "MeasQ": "1",
    "RMS": "0",
    "IRMS": "1",
    "MeasPh": "0",
    "S": "100.0 [MVA]",
    "BaseA": "1.0 [kA]",
    "TS": "0.02 [s]",
    "Freq": "60.0 [Hz]",
    "Dis": "0",
}
EXPECTED_METERS = {
    "M1619A": {
        "P": "E_16_19_1_A_P",
        "Q": "E_16_19_1_A_Q",
        "Crms": "E_16_19_1_A_I",
    },
    "M1619B": {
        "P": "E_16_19_1_B_P",
        "Q": "E_16_19_1_B_Q",
        "Crms": "E_16_19_1_B_I",
    },
}
EXPECTED_DEFAULTS = {
    "IBR2_TEST_ENABLE": "0",
    "IBR2_TEST_OPEN_TIME_S": "4",
    "IBR3_TEST_OPEN_TIME_S": "5",
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def params(element: ET.Element) -> dict[str, str]:
    result: dict[str, str] = {}
    for plist in element.findall("./paramlist"):
        for param in plist.findall("./param"):
            name = param.get("name", "")
            if name:
                result[name] = param.get("value", "")
    return result


def channel_record(user: ET.Element, order: int) -> dict[str, object]:
    return {
        "xml_order": order,
        "name": params(user).get("Name", ""),
        "component_id": user.get("id", ""),
        "definition": user.get("defn", ""),
        "x": user.get("x", ""),
        "y": user.get("y", ""),
        "xml_parameters": params(user),
    }


def fingerprint_channels(channels: list[dict[str, object]]) -> str:
    return hashlib.sha256(json.dumps(channels, sort_keys=True).encode()).hexdigest().upper()


def normalized_existing_channel_record(record: dict[str, object]) -> dict[str, object]:
    """Ignore XML order because adding channels naturally renumbers later rows."""
    normalized = dict(record)
    normalized.pop("xml_order", None)
    normalized.pop("fortran_mappings", None)
    return normalized


def nearby_constant_values_for_label(root: ET.Element, label: str) -> list[dict[str, object]]:
    users = list(root.iter("User"))
    constants = []
    labels = []
    for user in users:
        plist = params(user)
        if user.get("defn") == "master:const":
            constants.append(
                {
                    "id": user.get("id", ""),
                    "x": int(user.get("x", "0")),
                    "y": int(user.get("y", "0")),
                    "value": plist.get("Value", ""),
                }
            )
        elif user.get("defn") == "master:datalabel" and plist.get("Name") == label:
            labels.append(
                {
                    "id": user.get("id", ""),
                    "x": int(user.get("x", "0")),
                    "y": int(user.get("y", "0")),
                }
            )
    matches = []
    for label_row in labels:
        for const in constants:
            if abs(const["y"] - label_row["y"]) <= 5 and 0 <= label_row["x"] - const["x"] <= 180:
                matches.append({"label": label_row, "constant": const})
    return matches


def collect_fortran_output_bindings(text: str) -> dict[str, list[dict[str, object]]]:
    bindings: dict[str, list[dict[str, object]]] = {}
    current = None
    for line_number, line in enumerate(text.splitlines(), 1):
        comment = re.search(r"Output Channel '([^']+)'", line)
        if comment:
            current = comment.group(1)
            continue
        assignment = re.search(r"PGB\(IPGB\+(\d+)\)\s*=\s*(.+)", line)
        if current and assignment:
            bindings.setdefault(current, []).append(
                {
                    "line": line_number,
                    "pgb_offset": int(assignment.group(1)),
                    "rhs": assignment.group(2).strip(),
                }
            )
            current = None
    return bindings


def gate(name: str, passed: bool, detail: object) -> dict[str, object]:
    return {"gate": name, "passed": bool(passed), "detail": detail}


def main() -> int:
    missing = [str(p) for p in [MAIN, TRIAL, P3_FORTRAN, MAP_FILE, BASELINE, INVENTORY] if not p.exists()]
    if missing:
        raise FileNotFoundError("missing audit inputs: " + "; ".join(missing))

    root = ET.parse(TRIAL).getroot()
    baseline = json.loads(BASELINE.read_text(encoding="utf-8"))
    p3_text = P3_FORTRAN.read_text(encoding="utf-8", errors="replace")
    map_text = MAP_FILE.read_text(encoding="utf-8", errors="replace")

    pgb_users = [u for u in root.iter("User") if u.get("defn") == "master:pgb"]
    channels = [channel_record(u, i) for i, u in enumerate(pgb_users, 1)]
    inventory_lines = [row["network_branch_id"] for row in csv.DictReader(INVENTORY.open(encoding="utf-8"))]
    full_network_channel_names = {
        name
        for line in inventory_lines
        for name in [
            f"{line}_A_P",
            f"{line}_A_Q",
            f"{line}_A_I",
            f"{line}_B_P",
            f"{line}_B_Q",
            f"{line}_B_I",
        ]
    }
    target_channels = [c for c in channels if c["name"] in TARGET_CHANNELS]
    existing_channels = [c for c in channels if c["name"] not in full_network_channel_names]
    baseline_existing = [normalized_existing_channel_record(c) for c in baseline["channels"]]
    current_existing = [normalized_existing_channel_record(c) for c in existing_channels]

    gates: list[dict[str, object]] = []
    gates.append(gate("main_project_integrity", sha256(MAIN) == EXPECTED_MAIN_SHA, sha256(MAIN)))
    gates.append(
        gate(
            "trial_changed_from_preflight_baseline",
            sha256(TRIAL) != BASELINE_TRIAL_SHA,
            {"baseline": BASELINE_TRIAL_SHA, "current": sha256(TRIAL)},
        )
    )
    gates.append(
        gate(
            "xml_output_channel_count",
            len(channels)
            in {
                baseline["output_channel_count"] + len(TARGET_CHANNELS),
                baseline["output_channel_count"] + len(full_network_channel_names),
            },
            {
                "baseline": baseline["output_channel_count"],
                "current": len(channels),
                "expected_single_delta": len(TARGET_CHANNELS),
                "expected_full_network_delta": len(full_network_channel_names),
            },
        )
    )
    gates.append(
        gate(
            "existing_output_channels_preserved",
            fingerprint_channels(current_existing) == fingerprint_channels(baseline_existing),
            {
                "baseline_fingerprint": fingerprint_channels(baseline_existing),
                "current_existing_fingerprint": fingerprint_channels(current_existing),
                "current_existing_count": len(existing_channels),
            },
        )
    )

    channel_counts = {name: [c["xml_parameters"] for c in target_channels if c["name"] == name] for name in TARGET_CHANNELS}
    bad_channel_params: dict[str, object] = {}
    for name, plist in channel_counts.items():
        if len(plist) != 1:
            bad_channel_params[name] = {"occurrences": len(plist)}
            continue
        mismatches = {
            key: {"expected": expected, "actual": plist[0].get(key)}
            for key, expected in EXPECTED_CHANNEL_PARAMS.items()
            if plist[0].get(key) != expected
        }
        if mismatches:
            bad_channel_params[name] = mismatches
    gates.append(gate("six_new_output_channels_exact", not bad_channel_params, bad_channel_params or sorted(channel_counts)))

    datalabels = [params(u).get("Name", "") for u in root.iter("User") if u.get("defn") == "master:datalabel"]
    datalabel_counts = {name: datalabels.count(name) for name in TARGET_CHANNELS}
    gates.append(
        gate(
            "six_matching_data_labels_present",
            all(count == 1 for count in datalabel_counts.values()),
            datalabel_counts,
        )
    )

    meter_users = [u for u in root.iter("User") if u.get("defn") == "master:multimeter"]
    named_meters = {params(u).get("Name", ""): params(u) for u in meter_users if params(u).get("Name", "") in EXPECTED_METERS}
    meter_mismatches: dict[str, object] = {}
    for name, expected_signals in EXPECTED_METERS.items():
        plist = named_meters.get(name)
        if not plist:
            meter_mismatches[name] = "missing"
            continue
        expected = {**EXPECTED_METER_COMMON, **expected_signals}
        mismatches = {
            key: {"expected": value, "actual": plist.get(key)}
            for key, value in expected.items()
            if plist.get(key) != value
        }
        if mismatches:
            meter_mismatches[name] = mismatches
    gates.append(gate("two_native_multimeters_exact", not meter_mismatches, meter_mismatches or sorted(named_meters)))

    forbidden_new_target_channels = [
        c["name"]
        for c in channels
        if isinstance(c["name"], str)
        and c["name"].startswith(TARGET + "_")
        and c["name"] not in TARGET_CHANNELS
    ]
    gates.append(gate("no_extra_target_prefixed_channels", not forbidden_new_target_channels, forbidden_new_target_channels))

    fortran_bindings = collect_fortran_output_bindings(p3_text)
    binding_detail = {name: fortran_bindings.get(name, []) for name in TARGET_CHANNELS}
    gates.append(
        gate(
            "generated_fortran_pgb_bindings_present",
            all(any(b["rhs"] == name for b in binding_detail[name]) for name in TARGET_CHANNELS),
            binding_detail,
        )
    )

    meter_fortran_detail = {
        "M1619A": {
            "comment_present": "Multimeter 'M1619A'" in p3_text,
            "p_assignment": "E_16_19_1_A_P = RVD1_1" in p3_text,
            "q_assignment": "E_16_19_1_A_Q = RVD1_1" in p3_text,
            "i_assignment": "E_16_19_1_A_I = RVD1_1" in p3_text,
        },
        "M1619B": {
            "comment_present": "Multimeter 'M1619B'" in p3_text,
            "p_assignment": "E_16_19_1_B_P = RVD1_1" in p3_text,
            "q_assignment": "E_16_19_1_B_Q = RVD1_1" in p3_text,
            "i_assignment": "E_16_19_1_B_I = RVD1_1" in p3_text,
        },
        "uses_pqirms_functions": all(token in p3_text for token in ["P3PH3", "Q3PH3", "RMS3PH"]),
    }
    gates.append(
        gate(
            "generated_fortran_meter_semantics_present",
            all(
                all(v for v in detail.values()) if isinstance(detail, dict) else bool(detail)
                for detail in meter_fortran_detail.values()
            ),
            meter_fortran_detail,
        )
    )

    map_descs = {
        name: bool(re.search(rf'Desc="{re.escape(name)}"', map_text))
        for name in TARGET_CHANNELS
    }
    gates.append(gate("generated_map_contains_six_channel_descriptions", all(map_descs.values()), map_descs))

    defaults_found = {
        key: sorted({row["constant"]["value"] for row in nearby_constant_values_for_label(root, key)})
        for key in EXPECTED_DEFAULTS
    }
    default_mismatches = {
        key: {"expected": expected, "actual_values": defaults_found[key]}
        for key, expected in EXPECTED_DEFAULTS.items()
        if defaults_found[key] != [expected]
    }
    gates.append(gate("trial_test_defaults_still_disabled", not default_mismatches, default_mismatches or defaults_found))

    payload = {
        "audit_name": "single_tline_measurement_cell_audit",
        "target_tline": TARGET,
        "execution_status": "pass" if all(g["passed"] for g in gates) else "fail",
        "main_sha256": sha256(MAIN),
        "trial_sha256": sha256(TRIAL),
        "xml_output_channel_count": len(channels),
        "new_channel_count": len(target_channels),
        "generated_map_pgbs": re.search(r"PGBS\s*=\s*(\d+)", map_text).group(1) if re.search(r"PGBS\s*=\s*(\d+)", map_text) else None,
        "gates": gates,
        "notes": [
            "Generated map PGBS may exceed XML Output Channel component count because vector channels expand.",
            "M1619B unused Vrms/Ph parameter text is ignored because MeasV=0 and MeasPh=0; audit only requires P/Q/Crms.",
            "No PSCAD GUI, Build, Run, or model file writes were performed by this script.",
        ],
    }
    AUDIT_OUT.parent.mkdir(parents=True, exist_ok=True)
    AUDIT_OUT.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({"execution_status": payload["execution_status"], "failed_gates": [g for g in gates if not g["passed"]]}, indent=2))
    return 0 if payload["execution_status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
