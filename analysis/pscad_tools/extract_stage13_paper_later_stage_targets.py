#!/usr/bin/env python3
"""Extract Stage-13 paper later-stage evidence from existing direct-text registry."""

from __future__ import annotations

import csv
from datetime import datetime

from stage13_common import REPO, write_json


KEEP = {"E003", "E005", "E006", "E007", "E010", "E011", "E012", "E013", "E019", "E021"}


def main() -> None:
    rows = list(csv.DictReader((REPO / "data/reference/paper_reproduction_evidence_registry.csv").open(encoding="utf-8")))
    evidence = []
    for row in rows:
        if row["evidence_id"] not in KEEP:
            continue
        mech = row["modeling_category"]
        threshold = row["parameter_or_logic_name"] if row["evidence_id"] in {"E003", "E005", "E006", "E007", "E019"} else "paper_threshold_not_explicit"
        evidence.append({
            "paper_event_name": row["paper_statement_paraphrase"],
            "paper_page": row["paper_page"],
            "paper_section": row["paper_section"],
            "paper_figure_or_table": row["paper_figure_or_table"],
            "direct_text_excerpt_short": row["exact_short_quote_if_available"],
            "mechanism_type": mech,
            "trigger_condition_if_explicit": threshold,
            "time_information_if_explicit": row["notes"] if "delay" in row["notes"].lower() or "duration" in row["paper_statement_paraphrase"].lower() else "paper_time_not_explicit",
            "confidence": "high_registry_direct_text",
            "evidence_id": row["evidence_id"],
        })
    payload = {
        "generated_at_local": datetime.now().astimezone().isoformat(timespec="seconds"),
        "source": "data/reference/paper_reproduction_evidence_registry.csv",
        "ocr_used": False,
        "network_used": False,
        "evidence": evidence,
    }
    write_json(REPO / "data/reference/stage13_paper_later_stage_evidence.json", payload)
    lines = ["# Stage 13 paper later-stage evidence\n", "No OCR or network source was used; entries come from the existing direct-text evidence registry.\n"]
    for item in evidence:
        lines.append(f"- `{item['evidence_id']}` {item['mechanism_type']}: {item['paper_event_name']} ({item['paper_page']}, {item['paper_figure_or_table']})\n")
    (REPO / "docs/STAGE13_PAPER_LATER_STAGE_EVIDENCE.md").write_text("\n".join(lines), encoding="utf-8")
    print({"stage13_paper_evidence_count": len(evidence)})


if __name__ == "__main__":
    main()
