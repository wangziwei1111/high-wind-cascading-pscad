#!/usr/bin/env python3
"""Parse Stage 15 runtime after the single authorized Run.

This parser intentionally blocks until the new trial runtime exists.
"""

from __future__ import annotations

import json
from datetime import datetime

from stage15_common import NEW_GF46, NEW_TRIAL, REPO, write_json


def main() -> int:
    now = datetime.now().astimezone().isoformat(timespec="seconds")
    runtime_exists = NEW_GF46.exists() and list(NEW_GF46.glob("3IBR_PAPER_WF33_35_38_TRIAL_*.out"))
    manifest = {
        "audit_name": "stage15_runtime_manifest",
        "generated_at_local": now,
        "new_trial_path": str(NEW_TRIAL),
        "new_gf46_path": str(NEW_GF46),
        "status": "runtime_available_for_parse" if runtime_exists else "runtime_missing",
        "runtime_status": "runtime_available_for_parse" if runtime_exists else "runtime_missing",
        "claim_boundary": "Raw runtime files are not committed to Git.",
    }
    write_json(REPO / "data/reference/stage15_runtime_manifest.json", manifest)
    write_json(REPO / "data/validation/stage15_runtime_input_audit.json", manifest)
    print(json.dumps(manifest, indent=2))
    return 0 if runtime_exists else 2


if __name__ == "__main__":
    raise SystemExit(main())
