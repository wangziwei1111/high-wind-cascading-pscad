#!/usr/bin/env python3
"""Freeze the next paper-aligned mechanism path after Stage-13 diagnosis."""

from __future__ import annotations

import json
import sys
from datetime import datetime

from stage13_common import REPO, write_json


def choose_path(state: dict) -> tuple[str, str]:
    top = state["top_tline_risk_candidates"][0]
    if top["classification"] == "third_line_candidate_ready":
        return "third_line_protection_path", "high"
    if top["classification"] == "third_line_candidate_requires_longer_run":
        return "extend_runtime_before_third_line_path", "medium"
    if state["frequency_status"] == "frequency_observability_insufficient" and state["voltage_summary"]["overall"] in {"voltage_observability_insufficient", "local_voltage_response_only"}:
        return "ufls_uvls_observability_first_path", "medium"
    if state["topology_partition_status"] == "partitioned_after_second_trip":
        return "topology_partition_consequence_path", "medium"
    return "no_defensible_post_second_trip_escalation", "low"


def main() -> int:
    state = json.loads((REPO / "data/validation/stage13_post_second_trip_state_audit.json").read_text(encoding="utf-8"))
    path, confidence = choose_path(state)
    decision = {
        "decision_name": "stage13_next_paper_aligned_mechanism_decision",
        "generated_at_local": datetime.now().astimezone().isoformat(timespec="seconds"),
        "selected_next_path": path,
        "decision_confidence": confidence,
        "paper_evidence_ids": ["E003", "E010", "E011", "E012", "E013"],
        "runtime_evidence_ids": ["stage12_run_manifest", "stage13_post_second_trip_tline_risk_ranking"],
        "required_observables": ["existing TLine dual-end P/Q", "compiled topology", "actual breaker state chronology"],
        "missing_observables": ["real continuous thermal ratings", "real protection settings", "network-wide voltage coverage", "direct UFLS/load-shed state"],
        "model_change_needed_next_stage": path == "third_line_protection_path",
        "why_other_paths_rejected": {
            "third_line_protection_path": "Rejected as an immediate model change because the leading candidate is not yet third_line_candidate_ready." if path != "third_line_protection_path" else "Selected because the leading raw-stress candidate has a sustained W4 high-stress window.",
            "extend_runtime_before_third_line_path": "Rejected because the leading raw-stress candidate already has a separable sustained W4 window in the existing 20 s runtime." if path == "third_line_protection_path" else "Selected or retained when post-second-trip line stress rises but the existing window is not enough to justify a physical third relay.",
            "ufls_uvls_observability_first_path": "Rejected as immediate next path because a line-risk path is directly supported by current raw P/Q evidence; UFLS/UVLS still require observability before any shedding model.",
            "generator_protection_observability_first_path": "Rejected because no directly observed conventional-generator protection precursor is available.",
            "topology_partition_consequence_path": f"Rejected because topology status is {state['topology_partition_status']}.",
            "no_defensible_post_second_trip_escalation": "Rejected because the W4 raw P/Q-derived stress ranking shows separable post-second-trip line-risk candidates." if path != "no_defensible_post_second_trip_escalation" else "Selected because no defensible post-second-trip escalation evidence was found.",
        },
        "claim_boundary": "This freezes only the next mechanism direction. It does not add a third breaker, UFLS/UVLS, generator protection, islanding model, Build, or Run.",
    }
    write_json(REPO / "data/reference/stage13_next_paper_aligned_mechanism_decision.json", decision)
    audit = {
        "audit_name": "stage13_next_mechanism_decision_audit",
        "generated_at_local": decision["generated_at_local"],
        "execution_status": "stage13_next_mechanism_decision_frozen",
        "selected_next_path": path,
        "checks": {
            "paper_chain_waiver_accepted": state["paper_chain_waiver_accepted"],
            "one_path_selected": path in {
                "third_line_protection_path",
                "extend_runtime_before_third_line_path",
                "ufls_uvls_observability_first_path",
                "generator_protection_observability_first_path",
                "topology_partition_consequence_path",
                "no_defensible_post_second_trip_escalation",
            },
        },
    }
    write_json(REPO / "data/validation/stage13_next_mechanism_decision_audit.json", audit)
    (REPO / "docs/STAGE13_NEXT_PAPER_ALIGNED_MECHANISM_DECISION.md").write_text(
        f"""# Stage 13 next paper-aligned mechanism decision

Selected next path: `{path}`

Confidence: `{confidence}`

No PSCAD model change, Build, or Run was performed in Stage 13.

Boundary: this is a path freeze only, not a third-trip or UFLS/UVLS validation.

## Why this path is selected

The paper evidence supports later-stage overloaded-line protection, wind/source loss, UFLS/UVLS, generator protection and topology/islanding consequences as possible cascade mechanisms. In the current Stage-12 runtime, the only mechanism with a direct, model-consistent post-second-trip trace is the TLine raw P/Q-derived stress ranking.

`E_9_39_1` is the strongest candidate after `E_26_29_1` opens, but the existing 20 s runtime does not contain a defensible 5 s continuous high-stress interval after the second trip. Therefore the next paper-aligned step is not to add a third relay immediately; it is to extend/inspect runtime evidence before authorizing a third physical line-protection model.

## Why other paths are rejected now

- `third_line_protection_path`: rejected for immediate modeling because the candidate is not yet `third_line_candidate_ready`.
- `ufls_uvls_observability_first_path`: not selected as the next mechanism because current line-risk evidence is stronger; UFLS/UVLS still lacks direct system-frequency and network-wide voltage observability.
- `generator_protection_observability_first_path`: rejected because conventional-generator protection precursors are not directly observed.
- `topology_partition_consequence_path`: rejected because compiled topology plus breaker states indicate `connected_after_second_trip`.
- `no_defensible_post_second_trip_escalation`: rejected because W4 raw P/Q-derived stress does rise in a separable way for several candidate lines.

## Next-stage modeling implication

No new physical PSCAD model is justified by Stage 13 itself. The next stage should first obtain enough runtime evidence to decide whether a third line protection should be physically modeled. If that later evidence satisfies the sustained-window criterion, only then should a third relay/breaker be introduced.
""",
        encoding="utf-8",
    )
    print(json.dumps({"selected_next_path": path, "decision_confidence": confidence}, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
