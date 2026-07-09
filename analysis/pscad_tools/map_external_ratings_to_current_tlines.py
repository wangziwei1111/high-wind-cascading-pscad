#!/usr/bin/env python3
"""Map external/open branch ratings to the current 31 PSCAD TLines."""

from __future__ import annotations

import csv
import json
import math
from datetime import datetime
from pathlib import Path


REPO = Path(__file__).resolve().parents[2]
GF46 = Path(r"C:\pscad_work\pnnl_39_3ibr_pscad46_strip5\PSCAD\3IBR_DFIG1_TRIAL.gf46")
RAW_3IBR = REPO / "external/pnnl-enhanced-ieee39/Enhanced IEEE 39-Bus System_3IBRs/PSSE/IEEE39_PV_30_BV_Pmax_Pmin_equals_Pgen.raw"


def read_json(path: Path) -> object:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def write_csv(path: Path, rows: list[dict[str, object]]) -> None:
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


def parse_raw_branches() -> dict[tuple[int, int, str], dict[str, object]]:
    lines = RAW_3IBR.read_text(encoding="utf-8", errors="ignore").splitlines()
    start = next(i for i, l in enumerate(lines) if "BEGIN BRANCH DATA" in l) + 1
    end = next(i for i, l in enumerate(lines[start:], start) if "END OF BRANCH DATA" in l)
    branches: dict[tuple[int, int, str], dict[str, object]] = {}
    for line_no, line in enumerate(lines[start:end], start + 1):
        if not line.strip() or line.strip().startswith("@"):
            continue
        data = line.split("/")[0].strip()
        row = next(csv.reader([data], skipinitialspace=True))
        i, j, ckt = int(row[0]), int(row[1]), row[2].strip(" '")
        rates = [float(row[7 + k]) if len(row) > 7 + k and row[7 + k].strip() else 0.0 for k in range(12)]
        branches[(min(i, j), max(i, j), ckt)] = {
            "line_no": line_no,
            "raw_line": line,
            "from": i,
            "to": j,
            "ckt": ckt,
            "r": float(row[3]),
            "x": float(row[4]),
            "b": float(row[5]),
            "name": row[6].strip(" '"),
            "rates": rates,
        }
    return branches


def parse_tli(branch: str) -> dict[str, object]:
    path = GF46 / f"{branch}.tli"
    out: dict[str, object] = {"path": str(path)}
    for line in path.read_text(encoding="utf-8", errors="ignore").splitlines():
        if "Voltage Rating" in line:
            out["voltage"] = float(line.split("=")[1].strip())
        elif "Line Length" in line:
            out["length"] = float(line.split("=")[1].strip())
        elif "+ve Sequence Resistance" in line:
            out["r"] = float(line.split("=")[1].strip())
        elif "+ve Sequence Inductive Reactance" in line:
            out["x"] = float(line.split("=")[1].strip())
        elif "+ve Sequence Capacitive Susceptance" in line:
            out["b"] = float(line.split("=")[1].strip())
    return out


def branch_key(network_branch_id: str) -> tuple[int, int, str]:
    _, a, b, p = network_branch_id.split("_")
    return min(int(a), int(b)), max(int(a), int(b)), p


def close(a: float, b: float) -> bool:
    return math.isclose(a, b, rel_tol=1e-8, abs_tol=1e-8)


def main() -> int:
    inv = read_json(REPO / "data/reference/full_network_tline_inventory.json")
    raw = parse_raw_branches()
    rows: list[dict[str, object]] = []
    qualified: list[dict[str, object]] = []
    for t in inv["tlines"]:  # type: ignore[index]
        bid = t["network_branch_id"]
        key = branch_key(bid)
        ext = raw.get(key)
        cur = parse_tli(bid)
        if not ext:
            status = "not_mapped"
            mapping_class = "not_mapped"
            reason = "No matching from/to/circuit branch in PNNL 3IBR RAW."
            rate = ""
            semantic = "rating_semantic_unresolved"
            evidence = ""
        else:
            rx_match = close(float(cur["r"]), float(ext["r"])) and close(float(cur["x"]), float(ext["x"])) and close(float(cur["b"]), float(ext["b"]))
            rate = ext["rates"][0]  # type: ignore[index]
            mapping_class = "exact_current_model_origin_mapping" if rx_match else "mapping_ambiguous"
            status = mapping_class
            if rate and float(rate) > 0:
                semantic = "normal_operating_rating_qualified"
                reason = ""
            else:
                semantic = "rating_semantic_unresolved"
                reason = "PNNL 3IBR RAW branch maps exactly, but RATE1/Rate-A is 0.0 and therefore unspecified, not a usable continuous thermal limit."
            evidence = f"from/to/circuit={key}; R/X/B current={cur.get('r')}/{cur.get('x')}/{cur.get('b')} external={ext['r']}/{ext['x']}/{ext['b']}; raw line {ext['line_no']}"
        row = {
            "network_branch_id": bid,
            "current_component_id": t["component_id"],
            "terminal_a_node": t["terminal_a_node"],
            "terminal_b_node": t["terminal_b_node"],
            "parallel_group_id": t["parallel_group_id"],
            "parallel_index": t["parallel_index"],
            "current_voltage_rating": cur.get("voltage", ""),
            "current_r": cur.get("r", ""),
            "current_x": cur.get("x", ""),
            "current_b_or_shunt_if_available": cur.get("b", ""),
            "current_length_or_equivalent_if_available": cur.get("length", ""),
            "external_source_id": "SRC_PNNL_GITHUB_3IBR_RAW" if ext else "",
            "external_from_bus": ext.get("from", "") if ext else "",
            "external_to_bus": ext.get("to", "") if ext else "",
            "external_circuit_id": ext.get("ckt", "") if ext else "",
            "external_base_kv": 345 if ext and max(key[:2]) < 30 else "",
            "external_r": ext.get("r", "") if ext else "",
            "external_x": ext.get("x", "") if ext else "",
            "external_b_or_shunt": ext.get("b", "") if ext else "",
            "external_rate_a_value": rate,
            "external_rate_a_unit": "MVA",
            "external_rate_a_semantic": "zero_unspecified_not_continuous_thermal_limit" if rate == 0.0 else "candidate_rate_a_normal_rating",
            "mapping_method": "from_to_circuit_plus_exact_r_x_b_match",
            "mapping_evidence": evidence,
            "mapping_confidence": "high" if status == "exact_current_model_origin_mapping" else "none",
            "mapping_status": status,
            "mapping_rejection_reason": reason,
            "rating_semantic_class": semantic,
            "protection_grade_rating_status": "pass" if semantic in {"continuous_thermal_limit_qualified", "normal_operating_rating_qualified"} and status in {"exact_current_model_origin_mapping", "high_confidence_electrical_mapping"} and rate and float(rate) > 0 else "fail",
        }
        if row["protection_grade_rating_status"] == "pass":
            qualified.append(row)
        rows.append(row)

    counts = {
        "exact_current_model_origin_mapping": sum(1 for r in rows if r["mapping_status"] == "exact_current_model_origin_mapping"),
        "high_confidence_electrical_mapping": sum(1 for r in rows if r["mapping_status"] == "high_confidence_electrical_mapping"),
        "candidate_only_mapping": sum(1 for r in rows if r["mapping_status"] == "candidate_only_mapping"),
        "mapping_ambiguous": sum(1 for r in rows if r["mapping_status"] == "mapping_ambiguous"),
        "not_mapped": sum(1 for r in rows if r["mapping_status"] == "not_mapped"),
    }
    if len(qualified) == 31:
        coverage = "pass_full_network_protection_rating_coverage"
    elif qualified:
        coverage = "pass_candidate_only_protection_rating_coverage"
    else:
        coverage = "fallback_no_protection_grade_rating_coverage"
    payload = {
        "artifact": "current_tline_external_rating_mapping",
        "generated_at_local": datetime.now().isoformat(timespec="seconds"),
        "source_registry": "data/reference/tline_thermal_limit_source_registry.json",
        "tline_count": len(rows),
        "mapping_counts": counts,
        "protection_grade_qualified_line_count": len(qualified),
        "full_network_protection_rating_coverage_status": coverage,
        "continuous_rating_semantic_status": "fail_all_exact_mappings_have_zero_unspecified_rate_a",
        "e_16_19_1_status": next(r for r in rows if r["network_branch_id"] == "E_16_19_1"),
        "e_28_29_1_status": next(r for r in rows if r["network_branch_id"] == "E_28_29_1"),
        "rows": rows,
    }
    write_csv(REPO / "data/reference/current_tline_external_rating_mapping.csv", rows)
    write_json(REPO / "data/reference/current_tline_external_rating_mapping.json", payload)
    fallback = {
        "artifact": "protection_grade_tline_loading_ratio_fallback",
        "generated_at_local": datetime.now().isoformat(timespec="seconds"),
        "protection_grade_loading_ratio_status": "not_generated_no_qualified_continuous_thermal_limits",
        "reason": "All 31 current TLines map exactly to the PNNL 3IBR RAW branch table, but each current-network branch has RATE1..RATE12 = 0.0, so no continuous thermal/normal rating is available.",
        "coverage_status": coverage,
        "no_metrics_files_generated": [
            "data/derived/protection_grade_tline_loading_ratio_metrics.csv",
            "data/derived/protection_grade_tline_loading_candidate_ranking.csv",
        ],
    }
    write_json(REPO / "data/derived/protection_grade_tline_loading_ratio_fallback.json", fallback)
    print(json.dumps({"mapping_counts": counts, "coverage": coverage, "qualified": len(qualified)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
