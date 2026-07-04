#!/usr/bin/env python3
"""Audit WF38-first LVRT result from parsed Stage 15 runtime."""

from __future__ import annotations

import json
from datetime import datetime

from stage15_common import REPO, write_json


def main() -> int:
    now = datetime.now().astimezone().isoformat(timespec="seconds")
    runtime = json.loads((REPO / "data/reference/stage15_runtime_manifest.json").read_text(encoding="utf-8")) if (REPO / "data/reference/stage15_runtime_manifest.json").exists() else {}
    status = "stage15_runtime_output_parser_fallback" if runtime.get("runtime_status") != "runtime_available_for_parse" else "stage15_runtime_available_needs_channel_parse"
    audit = {
        "audit_name": "stage15_wf38_first_lvrt_final_audit",
        "generated_at_local": now,
        "result_class": status,
        "reason": "Runtime parser is a guarded scaffold until the single Stage15 Run exists.",
    }
    write_json(REPO / "data/validation/stage15_wf38_first_lvrt_final_audit.json", audit)
    (REPO / "docs/STAGE15_WF38_FIRST_LVRT_RESULT.md").write_text(
        "# Stage 15 WF38-first LVRT result\n\nRuntime result is pending until the single authorized Stage15 Run is completed.\n",
        encoding="utf-8",
    )
    print(json.dumps(audit, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
