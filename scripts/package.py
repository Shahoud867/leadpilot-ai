"""Package only source, documentation and verified build artifacts; never sessions."""

from pathlib import Path
import zipfile, hashlib

root = Path(__file__).resolve().parents[1]
output = root / "deliverables/LeadPilot_AI_MVP.zip"
output.parent.mkdir(exist_ok=True)
skip_dirs = {
    ".venv",
    "node_modules",
    "__pycache__",
    ".pytest_cache",
    "test-results",
    "playwright-report",
    "deliverables",
    ".git",
}
skip_names = {".env", "inspect.mjs", "debug-mobile.mjs"}
with zipfile.ZipFile(output, "w", zipfile.ZIP_DEFLATED, compresslevel=8) as archive:
    for p in sorted(root.rglob("*")):
        relative = p.relative_to(root)
        if (
            not p.is_file()
            or any(x in skip_dirs for x in relative.parts)
            or p.name in skip_names
        ):
            continue
        if p.name.endswith((".db", ".db-shm", ".db-wal", ".pyc", ".tsbuildinfo")):
            continue
        archive.write(p, "LeadPilot_AI/" + str(relative))
with zipfile.ZipFile(output) as archive:
    assert archive.testzip() is None
    required = [
        "README.md",
        "DEMO_GUIDE.md",
        "DEPLOYMENT.md",
        "FUTURE_INTEGRATIONS.md",
        "IMPLEMENTATION_STATUS.md",
        "TEST_REPORT.md",
        "apps/web/package-lock.json",
        "services/api/alembic/versions/0001_initial.py",
    ]
    for name in required:
        assert "LeadPilot_AI/" + name in archive.namelist(), name
print(output)
print("bytes:", output.stat().st_size)
print("SHA256:", hashlib.sha256(output.read_bytes()).hexdigest())
