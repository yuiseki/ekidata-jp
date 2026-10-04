#!/usr/bin/env python3
"""Check every file under data/raw/<version>/ against its MANIFEST.json.

Re-hashes each file, tests zip and gzip files if there are any, and counts
CSV rows with the csv module in the encoding the manifest records, comparing
the count with the manifest.

Then checks the Parquet that scripts/03_export_parquet.py made of each CSV:
  - there is one Parquet for every CSV, and no other
  - its row count equals the count from the csv module and the manifest
  - every value equals the value of the CSV read with the csv module and
    typed by the same rule (empty is null, codes int, lon and lat float),
    row by row in the order of the CSV; a sha256 of the rows is printed
  - every column has the type column_type gives its name, in CSV order
  - stations: the GeoParquet metadata names a Point geometry with no crs key
    (OGC:CRS84), every row has a point, and its x and y are lon and lat
  - a plain DuckDB without extensions opens the file
  - no row group carries a bloom filter

Prints ok/FAIL per check and exits non-zero on any failure.

    uv run python scripts/02_verify.py
"""

import csv
import gzip
import hashlib
import importlib.util
import json
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RAW = ROOT / "data" / "raw"
PQ = ROOT / "data" / "parquet"

_spec = importlib.util.spec_from_file_location("export", ROOT / "scripts" / "03_export_parquet.py")
export = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(export)


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


def typed_rows(path: Path) -> list[tuple]:
    """The CSV read with the csv module and typed by the export's rule."""
    conv = []
    with open(path, encoding="utf-8", newline="") as f:
        reader = csv.reader(f)
        names = next(reader)
        for n in names:
            t = export.column_type(n)
            conv.append(int if t == "INTEGER" else float if t == "DOUBLE" else str)
        return [
            tuple(None if v == "" else c(v) for c, v in zip(conv, row, strict=True))
            for row in reader
            if row
        ]


def rows_digest(rows: list[tuple]) -> str:
    h = hashlib.sha256()
    for r in rows:
        h.update(repr(r).encode())
        h.update(b"\n")
    return h.hexdigest()


def check_parquet() -> int:
    import duckdb

    failures = 0

    def check(ok: bool, what: str) -> None:
        nonlocal failures
        print(f"{'ok' if ok else 'FAIL'} {what}")
        failures += not ok

    con = duckdb.connect()
    con.execute("set memory_limit = '8GB'")
    con.execute("install spatial; load spatial")
    plain = duckdb.connect(
        config={"autoload_known_extensions": False, "autoinstall_known_extensions": False}
    )
    plain.execute("set memory_limit = '8GB'")
    loaded = plain.sql(
        "select count(*) from duckdb_extensions() where loaded and extension_name = 'spatial'"
    ).fetchone()[0]
    check(loaded == 0, "the plain DuckDB has no spatial extension loaded")
    plan = export.outputs()
    want = {p for _, _, p in plan}
    have = set(PQ.rglob("*.parquet")) if PQ.exists() else set()
    check(have == want, f"parquet: {len(have)} files, one for each of the {len(want)} CSVs")
    for _subset, src, p in plan:
        name = f"{p.parent.name}/{p.name}"
        if not p.exists():
            check(False, f"{name} missing")
            continue
        table = export.subset_of(src.name)[0]
        rows = typed_rows(src)
        manifest = json.loads((src.parent / "MANIFEST.json").read_text())["files"][src.name]
        n = plain.sql(f"select count(*) from '{p}'").fetchone()[0]
        check(
            n == len(rows) == manifest["rows"],
            f"{name}: {n:,} rows, as the csv module and the manifest count",
        )

        cols = export.COLUMNS[table]
        got = plain.sql(
            f"select {', '.join(chr(34) + c + chr(34) for c in cols)} from '{p}'"
        ).fetchall()
        check(
            got == rows, f"{name}: every value as in the CSV (rows sha256 {rows_digest(rows)[:16]})"
        )

        types = plain.sql(
            f"select column_name, column_type from (describe select * from '{p}')"
        ).fetchall()
        expected = [(c, export.column_type(c)) for c in cols]
        geometric = table in export.GEOMETRY_TABLES
        body = types[:-1] if geometric else types
        check(body == expected, f"{name}: every column has the type of the rule, in CSV order")

        if geometric:
            check(types[-1][0] == "geometry", f"{name}: a geometry column last")
            geo = json.loads(
                con.sql(
                    f"select decode(value) from parquet_kv_metadata('{p}') where decode(key) = 'geo'"
                ).fetchone()[0]
            )
            g = geo["columns"]["geometry"]
            check(
                g["geometry_types"] == ["Point"] and "crs" not in g,
                f"{name}: GeoParquet {geo['version']}, Point, no crs key (OGC:CRS84)",
            )
            bad = con.sql(
                f"select count(*) filter (where geometry is null or st_x(geometry) <> lon "
                f"or st_y(geometry) <> lat) from '{p}'"
            ).fetchone()[0]
            check(bad == 0, f"{name}: every row has a point at its lon and lat")

        bloom = plain.sql(
            f"select count(*) filter (where bloom_filter_offset is not null) from parquet_metadata('{p}')"
        ).fetchone()[0]
        check(bloom == 0, f"{name}: no bloom filters, opened by a DuckDB without extensions")
    return failures


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
    failures += check_parquet()
    print("\nall checks passed" if not failures else f"\n{failures} checks failed")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
