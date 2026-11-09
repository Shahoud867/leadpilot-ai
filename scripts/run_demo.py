"""One-process local presentation launcher after dependency installation."""

import os, subprocess, sys
from pathlib import Path

root = Path(__file__).resolve().parents[1]
os.chdir(root)
subprocess.run(
    [
        sys.executable,
        "-m",
        "alembic",
        "-c",
        "services/api/alembic.ini",
        "upgrade",
        "head",
    ],
    check=True,
)
if not (root / "apps/web/dist/index.html").exists():
    subprocess.run(["npm", "run", "build"], cwd=root / "apps/web", check=True)
print(
    "\nLeadPilot demo: http://127.0.0.1:8000\nOwner: owner@margalla.example / Demo@2026!\nAll data and communications are simulated.\n",
    flush=True,
)
subprocess.run(
    [
        sys.executable,
        "-m",
        "uvicorn",
        "app.main:app",
        "--app-dir",
        "services/api",
        "--host",
        "127.0.0.1",
        "--port",
        "8000",
    ],
    check=True,
)
