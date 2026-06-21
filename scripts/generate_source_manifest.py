from pathlib import Path
from hashlib import sha256

root = Path("external/pnnl-enhanced-ieee39/Enhanced IEEE 39-Bus System_3IBRs")
for rel in [
    "PSCAD/3IBR.pscx",
    "PSCAD/ETRAN46.pslx",
    "PSCAD/ETRAN_GF46.lib",
    "PSCAD/IEEE39bus_original_Modified5.dyr",
]:
    path = root / rel
    if path.exists():
        print(f"{rel},{path.stat().st_size},{sha256(path.read_bytes()).hexdigest()}")

