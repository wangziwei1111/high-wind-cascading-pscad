from pathlib import Path
import sys
import yaml

ok = True
for path in Path("config").glob("*.yaml"):
    try:
        yaml.safe_load(path.read_text(encoding="utf-8"))
        print(f"OK {path}")
    except Exception as exc:
        ok = False
        print(f"FAIL {path}: {exc}")
sys.exit(0 if ok else 1)

