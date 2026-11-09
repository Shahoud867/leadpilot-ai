import sys, argparse
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "services/api"))
from app.db import SessionLocal
from app.seed import seed, checksum

p = argparse.ArgumentParser()
p.add_argument("--seed", type=int, default=20261108)
p.add_argument("--reset", action="store_true")
p.add_argument("--count", type=int, default=3000)
p.add_argument("--scenario", default="all")
a = p.parse_args()
with SessionLocal() as db:
    seed(db, a.seed, a.count, a.reset)
    print("LP-1 seeded. Stable business-data SHA256:", checksum(db))
