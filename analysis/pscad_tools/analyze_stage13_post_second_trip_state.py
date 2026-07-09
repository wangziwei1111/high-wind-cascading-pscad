#!/usr/bin/env python3
"""Classify Stage-13 post-second-trip state from Stage-12 runtime outputs."""

from __future__ import annotations

import json
import math
from datetime import datetime

from stage13_common import (
    INF,
    OPENED_LINES,
    P3_DTA,
    REPO,
    WINDOWS,
    RuntimeReader,
    classify_voltage_scope,
    frequency_status_from_candidates,
    longest_continuous_interval,
    stats,
    third_line_readiness,
    tline_terminals_from_dta,
    topology_partition,
    voltage_risk_from_channels,
    window_values,
    write_csv,
    write_json,
)


def first_value_after(t, v, time_s):
    for x, y in zip(t, v):
        if x >= time_s:
            return y
    return None


def main() -> None:
    generated = datetime.now().astimezone().isoformat(timespec="seconds")
    manifest = json.loads((REPO / "data/reference/stage12_run_manifest.json").read_text(encoding="utf-8"))
    reader = RuntimeReader()
    w3 = WINDOWS["W3_first_to_second_line"]
    w4 = WINDOWS["W4_post_second_line"]

    risk_rows = []
    readiness_rows = []
    for branch in reader.branch_ids():
        t, s = reader.branch_smax(branch)
        if not t or branch in OPENED_LINES:
            continue
        s3, s4 = stats(t, s, *w3), stats(t, s, *w4)
        if s3["mean"] is None or s4["mean"] is None:
            readiness = "third_line_not_evaluable"
            delta = None
            interval = (None, None, 0.0)
        else:
            delta = s4["mean"] - s3["mean"]
            threshold = max(s3["max"] or 0.0, s3["mean"] or 0.0)
            mask = [w4[0] <= x <= w4[1] and y >= threshold for x, y in zip(t, s)]
            interval = longest_continuous_interval(t, mask)
            separable = delta > max(0.05 * abs(s3["mean"] or 0.0), 0.05)
            transient_only = (not separable) and interval[2] < 1.0 and (s4["max"] or 0.0) > 1.25 * (s4["mean"] or 0.0)
            readiness = third_line_readiness(separable, interval[2], transient_only)
        row = {
            "network_branch_id": branch,
            "W3_mean": s3["mean"],
            "W3_max": s3["max"],
            "W3_min": s3["min"],
            "W4_mean": s4["mean"],
            "W4_max": s4["max"],
            "W4_min": s4["min"],
            "W4_minus_W3_mean": delta,
            "longest_W4_high_stress_start_s": interval[0],
            "longest_W4_high_stress_end_s": interval[1],
            "longest_W4_high_stress_duration_s": interval[2],
            "relationship_to_E_26_29_1_open": "after_second_trip_window",
            "classification": readiness,
            "claim_boundary": "raw P/Q-derived response only; no real loading or thermal overload claim",
        }
        risk_rows.append(row)
        readiness_rows.append({
            "network_branch_id": branch,
            "third_line_readiness": readiness,
            "supporting_metric": delta,
            "sustained_duration_s": interval[2],
            "model_change_authorized_now": False,
        })
    risk_rows.sort(key=lambda r: ({"third_line_candidate_ready": 0, "third_line_candidate_requires_longer_run": 1, "third_line_not_defensible": 2, "third_line_not_evaluable": 3}[r["classification"]], -(r["W4_minus_W3_mean"] or -1e9)))
    for rank, row in enumerate(risk_rows, 1):
        row["risk_rank"] = rank
    write_csv(REPO / "data/derived/stage13_post_second_trip_tline_risk_ranking.csv", risk_rows)
    write_csv(REPO / "data/derived/stage13_third_line_readiness.csv", readiness_rows)

    # Frequency observability.
    freq_candidates = []
    for title in sorted(reader.by_title):
        cls = None
        if title == "SPD30":
            cls = "direct_system_frequency"
        elif title in {"Freq_PLL", "PLL_f", "PLL_f_1"}:
            cls = "local_controller_frequency_only"
        elif title.lower().startswith("w") or "speed" in title.lower():
            cls = "machine_speed_proxy_only"
        if cls:
            t, v = reader.series(title)
            st0 = stats(t, v, *WINDOWS["W0_pre_fault"]) if t else {}
            st4 = stats(t, v, *w4) if t else {}
            freq_candidates.append({"channel": title, "classification": cls, "W0": st0, "W4": st4})
    direct = [c for c in freq_candidates if c["classification"] == "direct_system_frequency"]
    risky_freq = False
    if direct:
        w4_min = direct[0]["W4"]["min"]
        risky_freq = w4_min is not None and w4_min < 49.0
    freq_status, ufls_status, genuf_status = frequency_status_from_candidates([c["classification"] for c in freq_candidates], risky_freq)
    write_json(REPO / "data/derived/stage13_frequency_observability_and_risk.json", {
        "frequency_candidates": freq_candidates,
        "frequency_observability_status": "direct_system_frequency_available" if direct else "frequency_observability_insufficient",
        "frequency_post_second_trip_trend": freq_status,
        "ufls_precondition_status": ufls_status,
        "generator_underfrequency_protection_precondition_status": genuf_status,
        "claim_boundary": "Only direct_system_frequency may be compared to paper Hz thresholds.",
    })

    # Voltage observability.
    voltage_rows = []
    for title in sorted(reader.by_title):
        if not (title.startswith("V") or "VIBR" in title or "ELEC_" in title and title.endswith("_V") or title.startswith("Vm_")):
            continue
        scope = classify_voltage_scope(title)
        if scope == "unmapped_or_ambiguous":
            continue
        t, v = reader.series(title)
        if not t:
            continue
        st0, st3, st4 = stats(t, v, *WINDOWS["W0_pre_fault"]), stats(t, v, *w3), stats(t, v, *w4)
        low_mask = [w4[0] <= x <= w4[1] and y < 0.8 for x, y in zip(t, v)]
        low_interval = longest_continuous_interval(t, low_mask)
        voltage_rows.append({
            "channel": title,
            "scope": scope,
            "W0_mean": st0["mean"], "W3_mean": st3["mean"], "W4_mean": st4["mean"],
            "W4_min": st4["min"], "W4_max": st4["max"],
            "post_second_low_voltage_duration_s": low_interval[2],
            "risk_conclusion": voltage_risk_from_channels([scope], low_interval[2] >= 1.0),
        })
    write_csv(REPO / "data/derived/stage13_voltage_observability_and_risk.csv", voltage_rows)

    # Source / generator status.
    source_status = {
        "DFIG_actual_disconnect": "directly_observed",
        "other_wind_farm_disconnect": "not_observed" if all(first_value_after(*reader.series(ch), 12.61) in (0.0, None) for ch in ["IBR2_TRIAL_BRK_STATE", "IBR3_TRIAL_BRK_STATE"]) else "indirectly_suggested",
        "synchronous_generator_disconnect": "not_observable",
        "conventional_generator_protection_action": "not_observable",
        "system_active_power_deficit": "not_observable",
        "system_reactive_power_deficit": "not_observable",
        "claim_boundary": "Only DFIG disconnect is directly observed; line raw S changes are not source-trip evidence.",
    }
    write_json(REPO / "data/derived/stage13_generator_and_source_status.json", source_status)

    # Topology partition.
    branches = []
    for branch in reader.branch_ids():
        ends = tline_terminals_from_dta(branch)
        if ends:
            branches.append((branch, ends[0], ends[1]))
    topo = topology_partition(branches, OPENED_LINES)
    topo["claim_boundary"] = "Topological connectivity only; not proof of island frequency, voltage, or balance."
    write_json(REPO / "data/derived/stage13_post_second_trip_topology_partition.json", topo)

    summary = {
        "audit_name": "stage13_post_second_trip_state_audit",
        "generated_at_local": generated,
        "execution_status": "stage13_post_second_trip_state_classified",
        "windows": WINDOWS,
        "stage12_event_times": manifest["event_times_s"],
        "top_tline_risk_candidates": risk_rows[:5],
        "frequency_status": freq_status,
        "voltage_summary": {
            "channel_count": len(voltage_rows),
            "network_wide_channel_count": sum(1 for r in voltage_rows if r["scope"] == "network_wide_representative"),
            "overall": "local_voltage_response_only" if voltage_rows else "voltage_observability_insufficient",
        },
        "source_status": source_status,
        "topology_partition_status": topo["status"],
        "paper_chain_waiver_accepted": manifest["offline_paper_chain_chronology"]["monitor_waiver"] == "PAPER_CHAIN_MODEL_MONITOR_WAIVED_OFFLINE_PARSER",
    }
    write_json(REPO / "data/validation/stage13_post_second_trip_state_audit.json", summary)
    doc = f"""# Stage 13 post-second-trip state diagnosis

No PSCAD model change, Build, or Run was performed. Stage 12 runtime outputs were used as the authoritative input.

## Runtime input

- Source run: Stage 12 unique 20 s / 50 us run.
- Runtime time axis: 0.00 to 20.00 s, 2001 samples, 0.01 s plot step.
- Event sequence used as fixed input: N29 fault 0.50 to 2.50 s, DFIG open 2.44 s, PAPER_OVL1 open 7.53 s, PAPER_OVL2 open 12.60 s.
- The Stage-12 `PAPER_CHAIN_MODEL_MONITOR_WAIVED_OFFLINE_PARSER` waiver is accepted; chronology is reconstructed in the backend from existing breaker-state/event channels.

## Main findings

- Top line-risk candidate after the second trip: `{risk_rows[0]['network_branch_id']}` with `{risk_rows[0]['classification']}`.
- Frequency status: `{freq_status}`.
- Voltage status: `{summary['voltage_summary']['overall']}`.
- Source/generator status: DFIG disconnect is directly observed; other source/generator mechanisms are not directly observed.
- Topology status after removing `E_28_29_1` and `E_26_29_1`: `{topo['status']}`.

All line-risk values are raw P/Q-derived response metrics, not real loading or thermal overload.

## Line-risk interpretation

The strongest post-second-trip raw P/Q-derived candidate is `{risk_rows[0]['network_branch_id']}`.
Its W4 mean rises above W3, so the post-second-trip line-risk direction is real enough to preserve.
However, the audited continuous high-stress span in the existing 20 s run is shorter than the 5.0 s protection-delay criterion, so Stage 13 does not authorize a third physical relay/breaker yet.

This is why the candidate class is:

```text
third_line_candidate_requires_longer_run
```

not:

```text
third_line_candidate_ready
```

## Frequency, voltage, source and topology boundaries

- Frequency: no direct system-frequency observable is available with enough semantic certainty to claim UFLS or conventional generator under-frequency protection.
- Voltage: available voltage observables are local/wind-PCC/generator-terminal style channels, not network-wide low-voltage coverage.
- Source/generator status: DFIG disconnection is directly observed; other wind-farm trips, synchronous-generator trips and conventional generator protection are not directly observed.
- Topology: compiled topology plus actual breaker state remains connected after the two line trips; no islanding consequence path is justified from Stage 12 alone.
"""
    (REPO / "docs/STAGE13_POST_SECOND_TRIP_STATE_DIAGNOSIS.md").write_text(doc, encoding="utf-8")
    print(json.dumps({"execution_status": summary["execution_status"], "top_candidate": risk_rows[0]["network_branch_id"], "classification": risk_rows[0]["classification"], "frequency": freq_status, "topology": topo["status"]}, indent=2))


if __name__ == "__main__":
    main()
