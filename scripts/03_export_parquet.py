#!/usr/bin/env python3
"""Turn every CSV of every fetch into a typed Parquet, for the Hub viewer and DuckDB.

Each file is one subset, named by its table and the date in its file name
(station20260731free.csv is station.2026-07-31; pref.csv is pref), and is
written to data/parquet/<fetch version>/<subset>.parquet.

The type of a column comes from its name, never from inference. The codes
(company_cd, rr_cd, line_cd, station_cd, station_g_cd, pref_cd,
station_cd1, station_cd2) and the small integer fields (company_type,
line_type, e_status, e_sort, zoom) are INTEGER, and every value must be an
integer without leading zeros, so that nothing a code could carry in a
leading zero is lost; lon and lat are DOUBLE; everything else stays the text
of the CSV, including post, line_color_c (hex colours such as 000000) and
open_ymd and close_ymd (which hold 0000-00-00). An empty field is null. A
value that does not fit stops the run with the file, column and value.

The columns of each table are pinned; a file whose header differs stops the
run. Stations get a point geometry from lon and lat (the specification says
世界測地系, read here as WGS 84). The lon and lat of lines are the centre of
a map view, so lines get none. Rows keep the order of the CSV. Files are
written without bloom filters.

    uv run python scripts/03_export_parquet.py
"""

import csv
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RAW = ROOT / "data" / "raw"
OUT = ROOT / "data" / "parquet"

COLUMNS = {
    "company": [
        "company_cd", "rr_cd", "company_name", "company_name_k", "company_name_h",
        "company_name_r", "company_url", "company_type", "e_status", "e_sort",
    ],
    "line": [
        "line_cd", "company_cd", "line_name", "line_name_k", "line_name_h", "line_color_c",
        "line_color_t", "line_type", "lon", "lat", "zoom", "e_status", "e_sort",
    ],
    "station": [
        "station_cd", "station_g_cd", "station_name", "station_name_k", "station_name_r",
        "line_cd", "pref_cd", "post", "address", "lon", "lat", "open_ymd", "close_ymd",
        "e_status", "e_sort",
    ],
    "join": ["line_cd", "station_cd1", "station_cd2"],
    "pref": ["pref_cd", "pref_name"],
}  # fmt: skip
CODES = {
    "company_cd", "rr_cd", "line_cd", "station_cd", "station_g_cd", "pref_cd",
    "station_cd1", "station_cd2",
}  # fmt: skip
INTEGERS = CODES | {"company_type", "line_type", "e_status", "e_sort", "zoom"}
DOUBLES = {"lon", "lat"}
INTEGER_RE = "0|[1-9][0-9]*"
DOUBLE_RE = "-?[0-9]+(\\.[0-9]+)?"
FILE_RE = re.compile(r"(company|line|station|join)(\d{4})(\d{2})(\d{2})(free)?\.csv")
GEOMETRY_TABLES = {"station"}


def column_type(name: str) -> str:
    if name in INTEGERS:
        return "INTEGER"
    if name in DOUBLES:
        return "DOUBLE"
    return "VARCHAR"


def subset_of(file: str) -> tuple[str, str | None, str]:
    """(table, edition date, subset name) of a raw file name."""
    if file == "pref.csv":
        return "pref", None, "pref"
    m = FILE_RE.fullmatch(file)
    if not m:
        raise ValueError(f"{file}: not a file name this script knows")
    table, edition = m.group(1), f"{m.group(2)}-{m.group(3)}-{m.group(4)}"
    return table, edition, f"{table}.{edition}"


def _expr(path: Path, name: str) -> str:
    c, t = f'"{name}"', column_type(name)
    if t == "VARCHAR":
        return c
    if t == "INTEGER":
        ok, what = f"regexp_full_match({c}, '{INTEGER_RE}')", "an integer without leading zeros"
    else:
        ok, what = f"regexp_full_match({c}, '{DOUBLE_RE}')", "a decimal number"
    return (
        f"case when {c} is null then null when {ok} then cast({c} as {t}) "
        f"else error('{path.name}: {name} is not {what}: ' || {c}) end"
    )


def source(path: Path) -> str:
    return (
        f"read_csv('{path}', header = true, all_varchar = true, strict_mode = true, "
        "delim = ',', quote = '\"', escape = '\"', encoding = 'utf-8')"
    )


def header(path: Path) -> list[str]:
    with open(path, encoding="utf-8", newline="") as f:
        return next(csv.reader(f))


def select_sql(path: Path) -> str:
    table = subset_of(path.name)[0]
    names = header(path)
    if names != COLUMNS[table]:
        raise ValueError(f"{path.name}: columns {names} are not those of {table}")
    cols = [f'{_expr(path, n)} as "{n}"' for n in names]
    if table in GEOMETRY_TABLES:
        cols.append(
            "case when lon is null or lat is null then null "
            "else st_point(cast(lon as double), cast(lat as double)) end as geometry"
        )
    return f"select {', '.join(cols)} from {source(path)}"


def csv_rows(path: Path) -> int:
    """Records counted by the csv module, header excluded."""
    with open(path, encoding="utf-8", newline="") as f:
        return sum(1 for row in csv.reader(f) if row) - 1


def outputs() -> list[tuple[str, Path, Path]]:
    """(subset, raw CSV, Parquet) for every CSV in every fetch's manifest."""
    out = []
    for mpath in sorted(RAW.glob("*/MANIFEST.json")):
        version = mpath.parent.name
        for name in sorted(json.loads(mpath.read_text())["files"]):
            if name.endswith(".csv"):
                subset = subset_of(name)[2]
                out.append((subset, mpath.parent / name, OUT / version / f"{subset}.parquet"))
    return out


def main() -> int:
    import duckdb

    con = duckdb.connect()
    con.execute("set memory_limit = '8GB'")
    con.execute("install spatial; load spatial")
    for subset, src, p in outputs():
        p.parent.mkdir(parents=True, exist_ok=True)
        con.execute(
            f"copy ({select_sql(src)}) to '{p}' "
            "(format parquet, compression zstd, write_bloom_filter false)"
        )
        got = con.sql(f"select count(*) from '{p}'").fetchone()[0]
        want = csv_rows(src)
        if got != want:
            raise SystemExit(f"{src.name}: {got} rows written, the CSV has {want}")
        print(f"{subset}: {got:,} rows, {p.stat().st_size:,} bytes", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
