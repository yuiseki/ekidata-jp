import importlib.util
from datetime import UTC, datetime
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
FIX = Path(__file__).resolve().parent / "fixtures"


def load(name: str):
    spec = importlib.util.spec_from_file_location(name.replace(".py", ""), ROOT / "scripts" / name)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


dl = load("01_download.py")
verify = load("02_verify.py")


def text(name: str) -> str:
    return (FIX / name).read_text(encoding="utf-8")


def test_login_form_fields_are_read_from_the_page():
    form = dl.parse_login_form(text("dl_login_form.html"))
    assert form["action"] == "./"
    assert form["method"] == "POST"
    assert form["hidden"] == {"login": "1", "p": "0"}
    assert form["user_field"] == "ac"
    assert form["password_field"] == "ps"


def test_free_links_skip_commented_out_and_paid_sections():
    links = dl.parse_free_links(text("dl_p1.html"), "https://ekidata.jp/dl/?p=1")
    by_cat = {}
    for link in links:
        by_cat.setdefault(link["category"], []).append(link["page_date"])
    assert list(by_cat) == ["事業者データ", "路線データ", "駅データ", "接続駅データ"]
    assert by_cat["事業者データ"][0] == "2026-04-09"
    # 2026-09-14 for the station data is inside an HTML comment on the page
    assert "2026-09-14" not in by_cat["駅データ"]
    assert by_cat["駅データ"][0] == "2026-07-31"
    assert by_cat["接続駅データ"][0] == "2026-09-14"
    assert sum(len(v) for v in by_cat.values()) == 22
    first = links[0]
    assert first["url"] == "https://ekidata.jp/dl/f.php?t=1&d=20260409"
    assert first["declared_encoding"] == "utf-8"


def test_pref_link_is_discovered():
    assert dl.parse_pref_page_link(text("dl_p1.html"), "https://ekidata.jp/dl/?p=1") == (
        "https://ekidata.jp/doc/pref.php"
    )
    assert dl.parse_pref_csv_link(text("doc_pref.html"), "https://ekidata.jp/doc/pref.php") == (
        "https://ekidata.jp/doc/pref.csv"
    )


def test_latest_change_note():
    assert dl.latest_change_note(text("dl_p1.html")) == "2026-09-14"


def test_filename_from_content_disposition():
    assert dl.filename_from_disposition('attachment; filename="company20260409.csv"') == (
        "company20260409.csv"
    )
    assert dl.filename_from_disposition("inline") is None
    assert dl.filename_from_disposition(None) is None


def test_version_is_the_fetch_date_in_japan():
    assert dl.version_for(datetime(2026, 10, 4, 20, 3, tzinfo=UTC)) == "2026-10-05"
    assert dl.version_for(datetime(2026, 10, 4, 14, 59, tzinfo=UTC)) == "2026-10-04"


@pytest.mark.parametrize(
    ("name", "encoding", "rows"),
    [("company_head.csv", "utf-8", 2), ("sjis.csv", "cp932", 2)],
)
def test_encoding_and_row_count(name, encoding, rows):
    path = FIX / name
    assert dl.detect_encoding(path) == encoding
    assert verify.count_rows(path, encoding) == rows
