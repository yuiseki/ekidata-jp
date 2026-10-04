#!/usr/bin/env python3
"""Fetch the free CSV files of ekidata.jp (駅データ.jp) into data/raw/<version>/.

The site needs a (free) member login before it lists its downloads. The
script logs in through the site's own form at https://ekidata.jp/dl/, reading
the form's action and field names from the page, then reads the download page
https://ekidata.jp/dl/?p=1 and takes every link in its free section
(無料データダウンロード): company, line, station and connecting-station
data, each offered as several dated files. Links the site has commented out
are not shown to users and are not taken; the paid section (有料データ) is
not taken. The prefecture master pref.csv, linked from the free section via
doc/pref.php, is taken too.

The site corrects its data in place and posts dated change notes, so the
version is the fetch date, in Japan time (YYYY-MM-DD).

Credentials come from the environment, never from a file:

    set -a; . ~/Workspaces/.env; set +a      # EKI_DATA_EMAIL, EKI_DATA_PASS
    uv run python scripts/01_download.py

data/raw/<version>/MANIFEST.json records, for each file, the URL, the
category and date the download page shows for it, size, sha256,
Last-Modified (the download handler sends none), fetch time, encoding and CSV
row count, plus the latest change note date on the page. A file already in
the manifest whose sha256 still matches is not fetched again.
"""

import csv
import hashlib
import http.cookiejar
import json
import os
import re
import sys
import time
import urllib.parse
import urllib.request
from datetime import UTC, datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RAW = ROOT / "data" / "raw"
LOGIN_URL = "https://ekidata.jp/dl/"
LIST_URL = "https://ekidata.jp/dl/?p=1"
UA = "ekidata-jp/1 (+https://github.com/yuiseki/ekidata-jp)"
JST = timezone(timedelta(hours=9))
DELAY = 1.5
LIMIT = 100 * 1000 * 1000

COMMENT = re.compile(r"<!--.*?-->", re.S)
DATE = r"(\d{4}-\d{2}-\d{2})"


def strip_comments(html: str) -> str:
    return COMMENT.sub("", html)


def attrs(tag: str) -> dict:
    return {k.lower(): v for k, v in re.findall(r'(\w+)\s*=\s*"([^"]*)"', tag)}


def parse_login_form(html: str) -> dict:
    """The login form's action, method, hidden fields and the user/password field names."""
    html = strip_comments(html)
    for m in re.finditer(r"<form\b([^>]*)>(.*?)</form>", html, re.S | re.I):
        inputs = [attrs(t) for t in re.findall(r"<input\b[^>]*>", m.group(2), re.I)]
        pw = [i["name"] for i in inputs if i.get("type", "").lower() == "password"]
        if not pw:
            continue
        text = [i["name"] for i in inputs if i.get("type", "text").lower() in ("text", "email")]
        hidden = {
            i["name"]: i.get("value", "") for i in inputs if i.get("type", "").lower() == "hidden"
        }
        fa = attrs(m.group(1))
        return {
            "action": fa.get("action", ""),
            "method": fa.get("method", "GET").upper(),
            "hidden": hidden,
            "user_field": text[0],
            "password_field": pw[0],
        }
    raise ValueError("no login form on the page")


def free_section(html: str) -> str:
    html = strip_comments(html)
    start = html.index("無料データダウンロード")
    end = html.find("有料データダウンロード", start)
    return html[start : end if end >= 0 else len(html)]


def parse_free_links(html: str, base: str) -> list[dict]:
    """Every dated download link in the free section, in page order, with its category."""
    links, category, encoding = [], None, None
    pat = re.compile(
        r"<th>(?P<th>.*?)</th>|<a\s+href=\"(?P<href>[^\"]*f\.php\?[^\"]*)\"[^>]*>.*?</a>\s*" + DATE,
        re.S | re.I,
    )
    for m in pat.finditer(free_section(html)):
        if m.group("th") is not None:
            th = m.group("th")
            category = re.sub(r"<[^>]*>.*", "", th, flags=re.S).strip()
            enc = re.search(r"文字コード[:：]\s*([\w-]+)", th)
            encoding = enc.group(1).lower() if enc else None
            continue
        if category is None or "有料" in category:
            continue
        links.append(
            {
                "category": category,
                "page_date": m.group(3),
                "url": urllib.parse.urljoin(base, m.group("href").replace("&amp;", "&")),
                "declared_encoding": encoding,
            }
        )
    return links


def parse_pref_page_link(html: str, base: str) -> str | None:
    m = re.search(r'<a\s+href="([^"]*pref\.php)"', free_section(html), re.I)
    return urllib.parse.urljoin(base, m.group(1)) if m else None


def parse_pref_csv_link(html: str, base: str) -> str | None:
    m = re.search(r'<a\s+href="([^"]*\.csv)"', strip_comments(html), re.I)
    return urllib.parse.urljoin(base, m.group(1)) if m else None


def latest_change_note(html: str) -> str | None:
    html = strip_comments(html)
    i = html.find("更新履歴")
    dates = re.findall(r"<td>\s*" + DATE, html[i:]) if i >= 0 else []
    return max(dates) if dates else None


def filename_from_disposition(value: str | None) -> str | None:
    if not value:
        return None
    m = re.search(r'filename="?([^";]+)"?', value)
    return Path(m.group(1)).name if m else None


def version_for(now: datetime) -> str:
    return now.astimezone(JST).strftime("%Y-%m-%d")


def detect_encoding(path: Path) -> str:
    data = path.read_bytes()
    if data.startswith(b"\xef\xbb\xbf"):
        return "utf-8-sig"
    try:
        data.decode("utf-8")
        return "utf-8"
    except UnicodeDecodeError:
        data.decode("cp932")
        return "cp932"


def count_rows(path: Path, encoding: str) -> int:
    with open(path, encoding=encoding, newline="") as f:
        return sum(1 for row in csv.reader(f) if row) - 1


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


class Client:
    def __init__(self):
        self.opener = urllib.request.build_opener(
            urllib.request.HTTPCookieProcessor(http.cookiejar.CookieJar())
        )
        self.opener.addheaders = [("User-Agent", UA)]
        self.last = 0.0

    def open(self, url: str, data: bytes | None = None):
        wait = self.last + DELAY - time.monotonic()
        if wait > 0:
            time.sleep(wait)
        try:
            return self.opener.open(url, data, timeout=300)
        finally:
            self.last = time.monotonic()

    def page(self, url: str, data: bytes | None = None) -> str:
        with self.open(url, data) as r:
            return r.read().decode("utf-8")

    def login(self) -> None:
        user, password = os.environ.get("EKI_DATA_EMAIL"), os.environ.get("EKI_DATA_PASS")
        if not user or not password:
            raise SystemExit("set EKI_DATA_EMAIL and EKI_DATA_PASS (see README)")
        form = parse_login_form(self.page(LOGIN_URL))
        fields = dict(form["hidden"])
        fields[form["user_field"]] = user
        fields[form["password_field"]] = password
        body = urllib.parse.urlencode(fields).encode()
        html = self.page(urllib.parse.urljoin(LOGIN_URL, form["action"]), body)
        if "logout.php" not in html:
            raise SystemExit("login failed (no logout link after posting the form)")

    def download(self, url: str, dest_dir: Path, name: str | None = None) -> dict:
        with self.open(url) as r:
            name = filename_from_disposition(r.headers.get("Content-Disposition")) or name
            if not name:
                raise SystemExit(f"{url}: no file name in the response (session expired?)")
            ctype = r.headers.get("Content-Type", "")
            if ctype.startswith("text/html"):
                raise SystemExit(f"{url}: got an HTML page instead of a file")
            length = r.headers.get("Content-Length")
            lm = r.headers.get("Last-Modified", "")
            tmp = dest_dir / (name + ".part")
            with open(tmp, "wb") as f:
                for block in iter(lambda: r.read(1 << 20), b""):
                    f.write(block)
        got = tmp.stat().st_size
        if length is not None and got != int(length):
            tmp.unlink()
            raise SystemExit(f"{url}: got {got} bytes, the server stated {length}")
        dest = dest_dir / name
        tmp.replace(dest)
        enc = detect_encoding(dest)
        return {
            "name": name,
            "url": url,
            "bytes": got,
            "content_length_sent": length is not None,
            "sha256": sha256(dest),
            "last_modified": lm,
            "fetched_at": datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "encoding": enc,
            "rows": count_rows(dest, enc),
        }


def have(manifest: dict, d: Path, url: str) -> bool:
    for name, e in manifest["files"].items():
        if e["url"] == url and (d / name).exists() and sha256(d / name) == e["sha256"]:
            return True
    return False


def main() -> int:
    version = version_for(datetime.now(UTC))
    d = RAW / version
    d.mkdir(parents=True, exist_ok=True)
    mpath = d / "MANIFEST.json"
    manifest = json.loads(mpath.read_text()) if mpath.exists() else {"files": {}}

    c = Client()
    c.login()
    listing = c.page(LIST_URL)
    links = parse_free_links(listing, LIST_URL)
    if not links:
        raise SystemExit("no free download links found on the download page")
    pref_page = parse_pref_page_link(listing, LIST_URL)
    if pref_page:
        pref_csv = parse_pref_csv_link(c.page(pref_page), pref_page)
        if pref_csv:
            links.append(
                {
                    "category": "都道府県データ",
                    "page_date": None,
                    "url": pref_csv,
                    "declared_encoding": "utf-8",
                }
            )

    manifest.update(
        {
            "source": LIST_URL,
            "version": version,
            "version_is": "fetch date (Asia/Tokyo); the site updates its data in place",
            "latest_change_note": latest_change_note(listing),
        }
    )
    fetched = 0
    for link in links:
        if have(manifest, d, link["url"]):
            continue
        path_name = Path(urllib.parse.urlparse(link["url"]).path).name
        entry = c.download(link["url"], d, path_name if path_name.endswith(".csv") else None)
        entry.update({k: link[k] for k in ("category", "page_date", "declared_encoding")})
        manifest["files"][entry.pop("name")] = entry
        mpath.write_text(json.dumps(manifest, indent=1, ensure_ascii=False))
        fetched += 1
        if sum(e["bytes"] for e in manifest["files"].values()) > LIMIT:
            raise SystemExit(f"stopped: over the {LIMIT:,}-byte limit")
        print(f"{version}: {link['category']} {link['page_date']}: {entry['bytes']:,} bytes")
    mpath.write_text(json.dumps(manifest, indent=1, ensure_ascii=False))
    total = sum(e["bytes"] for e in manifest["files"].values())
    print(
        f"{version}: fetched {fetched}, manifest has {len(manifest['files'])} files, {total:,} bytes"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
