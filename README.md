# ekidata-jp

A reproducible collection of the free CSV files of 駅データ.jp (ekidata.jp), the
railway station database of Value and Vision Co., Ltd. (株式会社バリューアンドビジョン).

## What the data is

The free tier of the download page (https://ekidata.jp/dl/?p=1, members only)
offers four UTF-8 CSV tables, each as several dated files:

| Category (page label) | File names | Content |
| --- | --- | --- |
| 事業者データ | `companyYYYYMMDD.csv` | railway companies |
| 路線データ | `lineYYYYMMDDfree.csv` | lines |
| 駅データ | `stationYYYYMMDDfree.csv` | stations (name, address, coordinates, station group code) |
| 接続駅データ | `joinYYYYMMDD.csv` | adjacent station pairs on each line |

plus the prefecture master `pref.csv` (https://ekidata.jp/doc/pref.php), linked
from the same section. Field definitions are in the specification at
https://ekidata.jp/doc/. The paid tier (有料データ) is not collected.

The site corrects its data in place and posts dated change notes (更新履歴) on
the download page, so a collection is versioned by its fetch date (Japan time).

## Licence

Terms of use: https://ekidata.jp/agreement.php (revised 2025-06-04; read 2026-10-05).
In short:

- Article 4 (use): the data may be used for commercial and non-commercial
  purposes, without contacting the company, except for the uses prohibited in
  Article 7. The company accepts no liability for damage from its use.
  Attribution is not required, but credit or a link to the site is welcome.
- Article 5 (modification): the data may be modified, commercially or not.
- Article 6 (provision to third parties): modified or unmodified data may be
  provided to third parties, but unmodified data only free of charge. (The
  site notes this applies to the data on its own; it may be built into a paid
  system.)
- Article 7 (prohibited): uses that encourage crime; obscene or otherwise
  offensive uses; uses that mislead consumers; infringing third parties'
  property, privacy or reputation; defaming the company or hindering its
  business; spreading viruses or otherwise harming third parties.

## How to run

Downloading needs a free member account at https://ekidata.jp/dl/. The script
reads the credentials from the environment variables `EKI_DATA_EMAIL` and
`EKI_DATA_PASS` and logs in through the site's own form:

```sh
set -a; . ~/Workspaces/.env; set +a
uv run python scripts/01_download.py   # fetch into data/raw/<fetch date>/
uv run python scripts/02_verify.py     # re-hash and count CSV rows against the manifest
uv run python -m pytest                # unit tests for the page parsing
```

Requests are sequential and at least 1.5 seconds apart. Running the download
again on the same day fetches nothing that is already in the manifest.

## Layout

```
scripts/01_download.py    log in, read the download page, fetch the free files
scripts/02_verify.py      check files against MANIFEST.json
tests/                    parsing tests; tests/fixtures/ holds trimmed pages
data/raw/<YYYY-MM-DD>/    the CSV files as served, and MANIFEST.json (not in git)
```

`MANIFEST.json` holds the latest change note date on the page and, for each
file, its URL, the category and date the page shows for it, size, sha256,
Last-Modified (the download handler sends none), fetch time, detected
encoding and CSV row count (header excluded).
