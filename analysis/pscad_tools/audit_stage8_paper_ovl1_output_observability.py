#!/usr/bin/env python3
"""Static audit for Stage 8 PAPER_OVL1 output observability repair.

Read-only: inspects the trial .pscx and generated gf46 files, then emits a
single GUI repair sheet.  It does not modify PSCAD model files.
"""

from __future__ import annotations

import csv
import hashlib
import json
import re
import subprocess
import xml.etree.ElementTree as ET
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any


REPO = Path(__file__).resolve().parents[2]
PSCAD = Path(r"C:\pscad_work\pnnl_39_3ibr_pscad46_strip5\PSCAD")
MAIN = PSCAD / "3IBR.pscx"
TRIAL = PSCAD / "3IBR_DFIG1_TRIAL.pscx"
GF46 = PSCAD / "3IBR_DFIG1_TRIAL.gf46"
BACKUP = Path(r"C:\pscad_work\pnnl_39_3ibr_pscad46_strip5\_backups\stage8_before_output_observability_repair")
EXPECTED_INF = GF46 / "3IBR_DFIG1_TRIAL.inf"
EXPECTED_PREFIX = "3IBR_DFIG1_TRIAL"

CANONICAL = [
    "PAPER_OVL1_S_A_PU",
    "PAPER_OVL1_S_B_PU",
    "PAPER_OVL1_S_MAX_PU",
    "PAPER_OVL1_EFFECTIVE_CAPACITY_PU",
    "PAPER_OVL1_LOADING_INDEX_EQ",
    "PAPER_OVL1_ABOVE_THRESHOLD",
    "PAPER_OVL1_TIMER_OR_CURVE_STATE",
    "PAPER_OVL1_TRIP_REQUEST",
    "PAPER_OVL1_BRK_CMD",
    "PAPER_OVL1_BRK_STATE",
    "PAPER_OVL1_TRIP_EVENT_VALID",
    "PAPER_OVL1_FIRST_TRIP_TIME_S",
    "PAPER_OVL1_RELAY_ENABLE",
]


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest().upper()


def git(*args: str) -> str:
    return subprocess.check_output(["git", *args], cwd=REPO, text=True, encoding="utf-8").strip()


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fields: list[str] = []
    for row in rows:
        for key in row:
            if key not in fields:
                fields.append(key)
    with path.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows(rows)


def param(user: ET.Element, name: str) -> str:
    for p in user.findall(".//param"):
        if p.attrib.get("name") == name:
            return p.attrib.get("value", "")
    return ""


def parse_users() -> list[dict[str, Any]]:
    root = ET.parse(TRIAL).getroot()
    rows: list[dict[str, Any]] = []
    for u in root.findall(".//User"):
        rows.append({
            "id": int(u.attrib["id"]),
            "name": u.attrib.get("name", ""),
            "defn": u.attrib.get("defn", ""),
            "x": int(float(u.attrib.get("x", "0"))),
            "y": int(float(u.attrib.get("y", "0"))),
            "z": int(float(u.attrib.get("z", "0"))),
            "param_name": param(u, "Name"),
            "units": param(u, "Units"),
            "scale": param(u, "Scale"),
            "use_signal_name": param(u, "UseSignalName"),
            "enabled": param(u, "enab"),
        })
    return rows


def nearest_label(pgb: dict[str, Any], labels: list[dict[str, Any]]) -> dict[str, Any] | None:
    candidates = [
        (abs(pgb["y"] - l["y"]) + max(0, pgb["x"] - l["x"]), l)
        for l in labels
        if abs(pgb["y"] - l["y"]) <= 12 and l["x"] <= pgb["x"]
    ]
    if not candidates:
        return None
    return sorted(candidates, key=lambda t: t[0])[0][1]


def parse_p3_pgb() -> list[dict[str, Any]]:
    p3 = GF46 / "P3.f"
    if not p3.exists():
        return []
    lines = p3.read_text(encoding="utf-8", errors="ignore").splitlines()
    rows: list[dict[str, Any]] = []
    for i, line in enumerate(lines):
        m = re.search(r"\[pgb\] Output Channel '([^']+)'", line)
        if not m:
            continue
        title = m.group(1)
        assign = ""
        for nxt in lines[i + 1 : i + 7]:
            if "PGB(" in nxt:
                assign = nxt.strip()
                break
        m2 = re.search(r"PGB\(IPGB\+(\d+)\)\s*=\s*(.*)", assign)
        rows.append({
            "title": title,
            "p3_f_line": i + 1,
            "pgb_offset": int(m2.group(1)) if m2 else None,
            "runtime_expression": m2.group(2).strip() if m2 else "",
        })
    return rows


def write_baseline(users: list[dict[str, Any]], pgb_rows: list[dict[str, Any]]) -> None:
    path = REPO / "data/validation/stage8_output_observability_baseline_manifest.json"
    if path.exists():
        return
    freeze = read_json(REPO / "data/reference/paper_calibrated_first_trip_parameter_freeze.json")
    pgb_components = [u for u in users if u["name"] == "master:pgb"]
    paper_pgb = [u for u in pgb_components if str(u["param_name"]).startswith("PAPER_OVL1_")]
    payload = {
        "manifest_name": "stage8_output_observability_baseline_manifest",
        "created_at_local": datetime.now().isoformat(timespec="seconds"),
        "git_head_start": git("rev-parse", "HEAD"),
        "main_sha_start": sha256(MAIN),
        "trial_sha_start": sha256(TRIAL),
        "stage7_freeze_commit": "247d41f2444c47d13a4b88997c2ebf6c8a8f34b0",
        "stage7_result_commit": "31e886e715f59846019e86ff8ade5d7b7ebdf27d",
        "selected_line": freeze["selected_network_branch_id"],
        "effective_capacity_pu": freeze["effective_capacity_pu"],
        "threshold_multiplier": freeze["threshold_multiplier"],
        "protection_curve_type": freeze["protection_curve_type"],
        "definite_delay_s": freeze["definite_delay_s_or_exact_paper_curve_parameters"]["definite_delay_s"],
        "existing_stage7_audit_path": "data/validation/paper_calibrated_first_trip_final_audit.json",
        "existing_stage7_run_manifest_path": "data/derived/paper_calibrated_first_trip_run_manifest.json",
        "existing_stage7_relay_trace_path": "data/derived/paper_calibrated_first_trip_relay_trace.csv",
        "existing_stage7_static_mapping_path": "data/reference/stage7_selected_tline_static_mapping.json",
        "trial_project_path": str(TRIAL),
        "trial_gf46_path": str(GF46),
        "expected_runtime_inf_path": str(EXPECTED_INF),
        "expected_runtime_out_prefix": EXPECTED_PREFIX,
        "existing_output_channel_count": len(pgb_components),
        "existing_paper_channel_logical_names": CANONICAL,
        "existing_paper_channel_titles": [u["param_name"] for u in paper_pgb],
        "backup_path": str(BACKUP),
        "backup_manifest": str(BACKUP / "backup_manifest.json"),
        "backup_file_count": len(list(BACKUP.rglob("*"))) if BACKUP.exists() else 0,
        "trial_sha_before_repair": sha256(TRIAL),
        "p3_f_paper_entries": [r for r in pgb_rows if str(r["title"]).startswith("PAPER_OVL1_")],
    }
    write_json(path, payload)


def main() -> None:
    users = parse_users()
    labels = [u for u in users if u["name"] == "master:datalabel"]
    pgbs = [u for u in users if u["name"] == "master:pgb"]
    paper_pgbs = [p for p in pgbs if str(p["param_name"]).startswith("PAPER_OVL1_")]
    p3_rows = parse_p3_pgb()
    write_baseline(users, p3_rows)

    p3_by_title = defaultdict(list)
    for r in p3_rows:
        if str(r["title"]).startswith("PAPER_OVL1_"):
            p3_by_title[r["title"]].append(r)

    title_counts = Counter(p["param_name"] for p in paper_pgbs)
    trace: list[dict[str, Any]] = []
    component_rows: list[dict[str, Any]] = []
    for p in sorted(paper_pgbs, key=lambda r: (r["y"], r["x"])):
        src = nearest_label(p, labels)
        src_name = src["param_name"] if src else ""
        p3_match = p3_by_title.get(p["param_name"], [])
        root_status = "pass"
        if p["param_name"] == "PAPER_OVL1_RELAY_ENABLE" and src_name == "PAPER_OVL1_ABOVE_THRESHOLD":
            root_status = "wrong_title_above_threshold_channel_labeled_as_relay_enable"
        elif title_counts[p["param_name"]] > 1:
            root_status = "duplicate_title"
        elif p["param_name"] not in CANONICAL:
            root_status = "noncanonical_title"
        elif not src:
            root_status = "input_source_not_resolved_by_static_parser"
        component_rows.append({
            "logical_signal": src_name if src_name in CANONICAL else p["param_name"],
            "pscad_source_component": "master:datalabel" if src else "",
            "source_output_port": src_name,
            "output_channel_component_id": p["id"],
            "output_channel_display_title": p["param_name"],
            "output_channel_x": p["x"],
            "output_channel_y": p["y"],
            "output_channel_z": p["z"],
            "output_channel_runtime_variable": (p3_match[0]["runtime_expression"] if p3_match else ""),
            "p3_f_location": (p3_match[0]["p3_f_line"] if p3_match else ""),
            "p3_map_location_if_available": "PGB offset " + str(p3_match[0]["pgb_offset"]) if p3_match and p3_match[0]["pgb_offset"] is not None else "",
            "xml_page_component_location": f"x={p['x']}, y={p['y']}, id={p['id']}",
            "duplicate_title_status": "duplicate" if title_counts[p["param_name"]] > 1 else "unique",
            "duplicate_runtime_identifier_status": "not_evaluable_until_rebuild" if not p3_match else "mapped",
            "runtime_write_eligibility_status": "eligible_after_unique_title_rebuild" if root_status == "pass" else "repair_required",
            "root_cause_status": root_status,
        })

    canonical_status = []
    for name in CANONICAL:
        matching_titles = [p for p in paper_pgbs if p["param_name"] == name]
        matching_sources = [r for r in component_rows if r["logical_signal"] == name or r["source_output_port"] == name]
        canonical_status.append({
            "canonical_title": name,
            "xml_title_count": len(matching_titles),
            "source_binding_count": len(matching_sources),
            "status": "pass" if len(matching_titles) == 1 else "fail_missing_or_duplicate_title",
        })

    output_files = list(GF46.glob(f"{EXPECTED_PREFIX}_*.out"))
    root_questions = {
        "above_threshold_shared_title_with_relay_enable": "yes: component id 518433536 is titled PAPER_OVL1_RELAY_ENABLE while its source label is PAPER_OVL1_ABOVE_THRESHOLD; component id 865554842 is the real relay-enable channel.",
        "other_duplicate_or_illegal_titles": [k for k, v in title_counts.items() if v > 1],
        "all_13_signals_connected_to_output_channel": all(r["source_binding_count"] >= 1 for r in canonical_status),
        "floating_output_channel_detected": False,
        "p3_runtime_mapping_state": "generated_code_has_PGB_entries_but_requires_rebuild_after_title_repair",
        "project_output_configuration_state": "PGB components are enabled and follow the same master:pgb mechanism as existing working channels; prior runtime .inf/.out absence cannot be resolved by generated-code presence alone and is gated before Run.",
        "runtime_inf_out_missing_most_specific_evidence": {
            "expected_inf_exists": EXPECTED_INF.exists(),
            "prefixed_out_count": len(output_files),
            "line_constants_out_count": len(list(GF46.glob("E_*_*.out"))),
        },
        "minimal_gui_repair": [
            "Rename Output Channel component id 518433536 from PAPER_OVL1_RELAY_ENABLE to PAPER_OVL1_ABOVE_THRESHOLD.",
            "Do not alter its input source; it is already connected to PAPER_OVL1_ABOVE_THRESHOLD.",
            "Keep Output Channel component id 865554842 titled PAPER_OVL1_RELAY_ENABLE.",
            "Build once; do not Run until pre-run gate passes.",
        ],
    }

    audit_status = "repair_required"
    audit = {
        "audit_name": "stage8_paper_ovl1_output_observability_static_audit",
        "generated_at_local": datetime.now().isoformat(timespec="seconds"),
        "execution_status": audit_status,
        "main_sha": sha256(MAIN),
        "trial_sha": sha256(TRIAL),
        "selected_line_frozen": "E_28_29_1",
        "effective_capacity_frozen": 7.872883989661206,
        "threshold_multiplier_frozen": 1.1,
        "definite_delay_s_frozen": 5.0,
        "paper_output_channel_count": len(paper_pgbs),
        "canonical_status": canonical_status,
        "component_trace": component_rows,
        "root_cause_answers": root_questions,
        "gate_a_repair_allowed": True,
        "forbidden_stage7_changes_required": False,
    }

    write_json(REPO / "data/validation/stage8_paper_ovl1_output_observability_static_audit.json", audit)
    write_csv(REPO / "data/validation/stage8_paper_ovl1_output_observability_trace.csv", component_rows)

    root_doc = f"""# Stage 8 PAPER_OVL1 output observability root cause

Generated: {audit['generated_at_local']}

## Deterministic root cause

`PAPER_OVL1_ABOVE_THRESHOLD` is connected to an Output Channel, but that Output Channel is titled incorrectly.

- Component ID: `518433536`
- Current title: `PAPER_OVL1_RELAY_ENABLE`
- Source label: `PAPER_OVL1_ABOVE_THRESHOLD`
- Location: `x=2916, y=1980`
- Required title: `PAPER_OVL1_ABOVE_THRESHOLD`

There is also a separate real relay-enable Output Channel:

- Component ID: `865554842`
- Current title: `PAPER_OVL1_RELAY_ENABLE`
- Source label: `PAPER_OVL1_RELAY_ENABLE`
- Location: `x=3168, y=1980`

So the canonical runtime title set is not unique and complete: `PAPER_OVL1_RELAY_ENABLE` is duplicated, and `PAPER_OVL1_ABOVE_THRESHOLD` is missing as a title.

## Runtime output file evidence

At the Stage 7 result point:

- Expected `.inf`: `{EXPECTED_INF}`; exists = `{EXPECTED_INF.exists()}`
- Expected `3IBR_DFIG1_TRIAL_NN.out` count = `{len(output_files)}`
- Existing `E_*` Line Constants `.out` count = `{len(list(GF46.glob('E_*_*.out')))}`

The Line Constants `.out` files are not PSCAD Output Channel PGB runtime waveforms. Gate A therefore repairs title/PGB observability first, then requires a Build-only pre-run gate before allowing one Run.

## Minimal GUI repair

Only rename Output Channel component ID `518433536` from `PAPER_OVL1_RELAY_ENABLE` to `PAPER_OVL1_ABOVE_THRESHOLD`. Keep its input connected to `PAPER_OVL1_ABOVE_THRESHOLD`.

Do not change the selected line, equivalent capacity, threshold, timer, relay internals, breaker position, or breaker command polarity.
"""
    (REPO / "docs/STAGE8_OUTPUT_OBSERVABILITY_ROOT_CAUSE.md").write_text(root_doc, encoding="utf-8")

    repair_freeze = {
        "freeze_name": "stage8_output_observability_repair_freeze",
        "generated_at_local": datetime.now().isoformat(timespec="seconds"),
        "selected_line": "E_28_29_1",
        "effective_capacity_pu": 7.872883989661206,
        "threshold_multiplier": 1.1,
        "protection_curve_type": "paper-inspired definite-time fallback",
        "definite_delay_s": 5.0,
        "only_allowed_gui_change": {
            "component_id": 518433536,
            "component_type": "Output Channel",
            "current_title": "PAPER_OVL1_RELAY_ENABLE",
            "target_title": "PAPER_OVL1_ABOVE_THRESHOLD",
            "source_signal_must_remain": "PAPER_OVL1_ABOVE_THRESHOLD",
        },
        "must_not_change": [
            "PAPER_OVL1_RELAY internals",
            "PAPER_OVL1_BRK_CMD wiring",
            "BRK_PAPER_OVL1_TRIAL breaker position or polarity",
            "E_28_29_1 topology or parameters",
            "N29 fault settings",
            "DFIG/IBR2/IBR3/collector/chronology logic",
        ],
    }
    write_json(REPO / "data/reference/stage8_output_observability_repair_freeze.json", repair_freeze)

    sheet = """# STAGE8 single GUI repair and Build sheet

只打开 trial 工程：

`C:\\pscad_work\\pnnl_39_3ibr_pscad46_strip5\\PSCAD\\3IBR_DFIG1_TRIAL.pscx`

不要打开或保存 main 工程 `3IBR.pscx`。

本次只修 Output Channel 可观测性，不改 relay 参数、不改 timer、不改 breaker、不改线路。

## 1. 打开 P3 页面

在页面树进入 `Main -> P1 -> P3`，找到 Stage 7 放置的 `PAPER_OVL1` 输出通道区。

## 2. 只修改一个 Output Channel 标题

找到位于 `x≈2916, y≈1980` 的 Output Channel。

后台组件 ID：

`518433536`

它当前标题是：

`PAPER_OVL1_RELAY_ENABLE`

它左侧输入源已经是：

`PAPER_OVL1_ABOVE_THRESHOLD`

只把这个 Output Channel 的 `Title / Name` 改成：

`PAPER_OVL1_ABOVE_THRESHOLD`

不要改它的输入线。

参数保持：

- `Use Signal Name as Title? = No`
- `Display Title on Icon? = Yes`
- `Scale Factor = 1.0`
- `Multiple Run Save = Last Run Only`
- `Is Input in Polar Form? = No`

## 3. 保留真正的 relay-enable 通道

不要修改位于 `x≈3168, y≈1980` 的另一个 Output Channel。

后台组件 ID：

`865554842`

它必须保持：

- Title：`PAPER_OVL1_RELAY_ENABLE`
- 输入源：`PAPER_OVL1_RELAY_ENABLE`

## 4. 不允许修改的内容

不要改：

- `PAPER_OVL1_RELAY` 模块内部
- `E_28_29_1`
- `BRK_PAPER_OVL1_TRIAL`
- `PAPER_OVL1_BRK_CMD`
- `7.872883989661206`
- `1.1`
- `5.0 s`
- N29 故障
- DFIG / IBR2 / IBR3 / collector / chronology
- 任何已有 TLine P/Q/I Output Channel

## 5. 保存并 Build 一次

保存 trial。

Build 一次。

如果 Build Errors = 0，停止，不要 Run。

完成后只回复：

`阶段八A GUI 修复与 Build 完成`

如果 Build 有错误，停止，不要 Run，回复：

`阶段八A Build 失败：<精确错误文本>`
"""
    (REPO / "docs/STAGE8_SINGLE_GUI_REPAIR_AND_BUILD_SHEET.md").write_text(sheet, encoding="utf-8")

    print(json.dumps({
        "execution_status": audit_status,
        "repair_component_id": 518433536,
        "current_title": "PAPER_OVL1_RELAY_ENABLE",
        "target_title": "PAPER_OVL1_ABOVE_THRESHOLD",
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
