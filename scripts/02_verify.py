#!/usr/bin/env python3
"""Check every file under data/raw/<version>/ against its MANIFEST.json.

Re-hashes each file, tests zip and gzip files if there are any, and counts
CSV rows with the csv module in the encoding the manifest records, comparing
the count with the manifest. Prints ok/FAIL per file and exits non-zero on
any failure.

    uv run python scripts/02_verify.py
"""

import csv
import gzip
import hashlib
import json
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RAW = ROOT / "data" / "raw"


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def count_rows(path: Path, encoding: str) -> int:
    """Data rows (header excluded, blank lines ignored)."""
    with open(path, encoding=encoding, newline="") as f:
        return sum(1 for row in csv.reader(f) if row) - 1


def check(path: Path, entry: dict) -> str:
    if not path.exists():
        return "missing"
    if path.stat().st_size != entry["bytes"]:
        return f"size {path.stat().st_size} != {entry['bytes']}"
    if sha256(path) != entry["sha256"]:
        return "sha256 mismatch"
    if path.suffix == ".zip":
        with zipfile.ZipFile(path) as z:
            bad = z.testzip()
            if bad:
                return f"zip member {bad} is corrupt"
    if path.suffix == ".gz":
        with gzip.open(path) as g:
            while g.read(1 << 20):
                pass
    if path.suffix == ".csv":
        rows = count_rows(path, entry["encoding"])
        if rows != entry["rows"]:
            return f"rows {rows} != {entry['rows']}"
        return f"{rows} rows ({entry['encoding']})"
    return ""


def main() -> int:
    failures = 0
    manifests = sorted(RAW.glob("*/MANIFEST.json"))
    if not manifests:
        print("FAIL no MANIFEST.json under data/raw/")
        return 1
    for mpath in manifests:
        d = mpath.parent
        files = json.loads(mpath.read_text())["files"]
        for name, entry in files.items():
            try:
                note = check(d / name, entry)
                ok = not note.startswith(("missing", "size", "sha256", "zip", "rows "))
            except Exception as e:  # noqa: BLE001 - any failure is a FAIL line
                note, ok = f"{type(e).__name__}: {e}", False
            print(f"{'ok' if ok else 'FAIL'} {d.name}/{name} {note}")
            failures += not ok
        extra = {p.name for p in d.iterdir()} - set(files) - {"MANIFEST.json"}
        for name in sorted(extra):
            print(f"FAIL {d.name}/{name} not in manifest")
            failures += 1
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
