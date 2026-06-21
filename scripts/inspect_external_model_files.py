from pathlib import Path
from hashlib import sha256

root = Path("external")
for path in sorted(root.rglob("*")):
    if path.is_file() and ".git" not in path.parts:
        print(f"{path},{path.stat().st_size},{sha256(path.read_bytes()).hexdigest()}")

