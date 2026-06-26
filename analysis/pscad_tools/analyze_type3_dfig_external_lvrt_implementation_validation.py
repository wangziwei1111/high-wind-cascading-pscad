"""Read-only checker for the Type-3 DFIG external LVRT scaffold state.

This script intentionally does not modify PSCAD files.  It inspects the
current 3IBR.pscx text for the external LVRT monitoring signal names that were
created before the safe fallback decision.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


SIGNALS = [
    "VIBR1_2",
    "DFIG_LVRT_LOWV",
    "DFIG_LVRT_IMMTRIP",
    "DFIG_LVRT_CLEAR",
    "DFIG_LVRT_TIMER_S",
    "DFIG_BRK_STATE",
    "BRK_DFIG",
]


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest().upper()


def line_numbers(text: str, token: str) -> list[int]:
    lines = []
    for index, line in enumerate(text.splitlines(), start=1):
        if token in line:
            lines.append(index)
    return lines


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--pscx",
        default=r"C:\pscad_work\pnnl_39_3ibr_pscad46_strip5\PSCAD\3IBR.pscx",
        help="Path to the active 3IBR.pscx file.",
    )
    args = parser.parse_args()

    pscx = Path(args.pscx)
    text = pscx.read_text(encoding="utf-8", errors="replace")
    report = {
        "pscx": str(pscx),
        "size_bytes": pscx.stat().st_size,
        "sha256": sha256(psx := pscx),
        "signal_occurrences": {
            signal: {
                "count": len(lines := line_numbers(text, signal)),
                "lines": lines[:25],
            }
            for signal in SIGNALS
        },
        "monitoring_only_safe_fallback": True,
        "breaker_connected_to_lvrt": False,
    }
    print(json.dumps(report, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
