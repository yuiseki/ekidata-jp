import importlib.util
from pathlib import Path

import duckdb
import pytest

_spec = importlib.util.spec_from_file_location(
    "export", Path(__file__).parents[1] / "scripts" / "03_export_parquet.py"
)
m = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(m)


@pytest.mark.parametrize(
    ("name", "sql"),
    [
        ("station_cd", "INTEGER"),
        ("station_g_cd", "INTEGER"),
        ("line_cd", "INTEGER"),
        ("company_cd", "INTEGER"),
        ("rr_cd", "INTEGER"),
        ("pref_cd", "INTEGER"),
        ("station_cd1", "INTEGER"),
        ("station_cd2", "INTEGER"),
        ("company_type", "INTEGER"),
        ("line_type", "INTEGER"),
        ("e_status", "INTEGER"),
        ("e_sort", "INTEGER"),
        ("zoom", "INTEGER"),
        ("lon", "DOUBLE"),
        ("lat", "DOUBLE"),
        ("post", "VARCHAR"),
        ("line_color_c", "VARCHAR"),
        ("open_ymd", "VARCHAR"),
        ("close_ymd", "VARCHAR"),
        ("station_name", "VARCHAR"),
        ("a_column_the_rule_does_not_know", "VARCHAR"),
    ],
)
def test_column_type(name, sql):
    assert m.column_type(name) == sql


@pytest.mark.parametrize(
    ("file", "want"),
    [
        ("station20260731free.csv", ("station", "2026-07-31", "station.2026-07-31")),
        ("line20260618free.csv", ("line", "2026-06-18", "line.2026-06-18")),
        ("company20260409.csv", ("company", "2026-04-09", "company.2026-04-09")),
        ("join20260914.csv", ("join", "2026-09-14", "join.2026-09-14")),
        ("pref.csv", ("pref", None, "pref")),
    ],
)
def test_subset_from_file_name(file, want):
    assert m.subset_of(file) == want


@pytest.mark.parametrize(
    "file", ["station2026073free.csv", "stations20260731.csv", "MANIFEST.json"]
)
def test_an_unknown_file_name_stops_the_run(file):
    with pytest.raises(ValueError, match=file):
        m.subset_of(file)


STATION = (
    "station_cd,station_g_cd,station_name,station_name_k,station_name_r,line_cd,pref_cd,"
    "post,address,lon,lat,open_ymd,close_ymd,e_status,e_sort\n"
)
GOOD = (
    "1110101,1110101,函館,,,11101,1,040-0063,北海道函館市若松町１２-１３,"
    "140.726413,41.773709,1902-12-10,0000-00-00,0,1110101\n"
)


def _rel(tmp_path, name, text):
    f = tmp_path / name
    f.write_text(text, encoding="utf-8")
    con = duckdb.connect()
    con.execute("install spatial; load spatial")
    return con.sql(m.select_sql(f))


def test_station_values_are_typed_and_text_stays_text(tmp_path):
    rel = _rel(tmp_path, "station20260731free.csv", STATION + GOOD)
    row = dict(zip(rel.columns, rel.fetchone(), strict=True))
    assert row["station_cd"] == 1110101 and row["line_cd"] == 11101 and row["pref_cd"] == 1
    assert row["lon"] == 140.726413 and row["lat"] == 41.773709
    assert row["post"] == "040-0063"
    assert row["open_ymd"] == "1902-12-10" and row["close_ymd"] == "0000-00-00"
    assert row["station_name_k"] is None
    assert rel.select("st_astext(geometry)").fetchone() == ("POINT (140.726413 41.773709)",)


def test_an_integer_latitude_is_read(tmp_path):
    # 加木屋中ノ池 has lat 35 in every station edition.
    rel = _rel(tmp_path, "station20260731free.csv", STATION + GOOD.replace("41.773709", "35"))
    assert rel.select("lat").fetchone() == (35.0,)


def test_only_stations_get_a_geometry(tmp_path):
    line = (
        "line_cd,company_cd,line_name,line_name_k,line_name_h,line_color_c,line_color_t,"
        "line_type,lon,lat,zoom,e_status,e_sort\n"
        "11302,2,JR山手線,ヤマノテセン,JR山手線,000000,黒,,139.73522275686,35.693027021137,12,0,11302\n"
    )
    rel = _rel(tmp_path, "line20260618free.csv", line)
    assert "geometry" not in rel.columns
    row = dict(zip(rel.columns, rel.fetchone(), strict=True))
    assert row["line_color_c"] == "000000" and row["line_type"] is None and row["zoom"] == 12


@pytest.mark.parametrize(
    ("old", "new", "message"),
    [
        (
            "1110101,1110101,",
            "01110101,1110101,",
            "station_cd is not an integer without leading zeros: 01110101",
        ),
        (",11101,1,", ",11101.0,1,", "line_cd is not an integer without leading zeros: 11101.0"),
        ("140.726413", "140,726413", None),
        ("140.726413", "E140.7", "lon is not a decimal number: E140.7"),
        (",0,1110101\n", ",-1,1110101\n", "e_status is not an integer without leading zeros: -1"),
    ],
)
def test_a_value_that_does_not_fit_stops_the_run(tmp_path, old, new, message):
    with pytest.raises((duckdb.Error, ValueError), match=message):
        _rel(tmp_path, "station20260731free.csv", STATION + GOOD.replace(old, new)).fetchall()


def test_the_error_names_the_file(tmp_path):
    with pytest.raises(duckdb.Error, match="station20260731free.csv"):
        bad = GOOD.replace(",0,1110101\n", ",x,1110101\n")
        _rel(tmp_path, "station20260731free.csv", STATION + bad).fetchall()


def test_a_header_that_differs_stops_the_run(tmp_path):
    with pytest.raises(ValueError, match="columns"):
        _rel(tmp_path, "station20260731free.csv", STATION.replace("address", "add") + GOOD)
