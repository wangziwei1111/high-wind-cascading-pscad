#!/usr/bin/env python3
"""Audit Stage 15 minimal output-channel plan."""

from __future__ import annotations

import json

from stage15_common import OUTPUT_CHANNELS, REPO


def main() -> int:
    manifest = json.loads((REPO / "data/reference/stage15_output_minimum_manifest.json").read_text(encoding="utf-8"))
    channels = manifest["new_output_channels"]
    ok = channels == OUTPUT_CHANNELS and len(channels) == 15 and len(set(channels)) == 15
    audit = {
        "audit_name": "stage15_output_minimum_audit",
        "status": "pass" if ok else "blocked_output_mapping_unresolved",
        "new_output_channel_count": len(channels),
        "unique": len(set(channels)) == len(channels),
    }
    (REPO / "data/validation/stage15_output_minimum_audit.json").write_text(json.dumps(audit, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(audit, indent=2))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
