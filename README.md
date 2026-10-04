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
uv run python scripts/03_export_parquet.py   # typed Parquet into data/parquet/<version>/
uv run python scripts/02_verify.py     # again: now also checks every Parquet against its CSV
uv run python -m pytest                # unit tests for the page parsing and the type rule
uv run python src/publish.py           # dry run: lists the files and their total size
uv run python src/publish.py --push    # upload to https://huggingface.co/datasets/yuiseki/ekidata-jp
```

The export writes one Parquet per CSV, named by its table and the date in its
file name (`station20260731free.csv` becomes
`data/parquet/<version>/station.2026-07-31.parquet`; `pref.csv` becomes
`pref.parquet`). Column types come from the column names (codes and small
integer fields INTEGER, `lon` and `lat` DOUBLE, the rest text); a value that
does not fit stops the export. Stations get a point geometry from `lon` and
`lat`. `publish.py` refuses to upload unless `data/README.md` declares every
Parquet as a subset, and the latest edition of each table under the table's
name, and every raw file still has the sha256 of its manifest. It uploads
`data/README.md` (the dataset card), `data/LICENSE`, `data/provenance.yaml`,
the Parquet and the raw files unchanged.

Requests are sequential and at least 1.5 seconds apart. Running the download
again on the same day fetches nothing that is already in the manifest.

## Layout

```
scripts/01_download.py    log in, read the download page, fetch the free files
scripts/02_verify.py      check files against MANIFEST.json, and the Parquet against the CSVs
scripts/03_export_parquet.py  typed Parquet (GeoParquet for stations)
src/publish.py            dry run, or --push to the Hugging Face Hub
tests/                    parsing and type-rule tests; tests/fixtures/ holds trimmed pages
data/README.md            the dataset card; data/LICENSE and data/provenance.yaml beside it
data/raw/<YYYY-MM-DD>/    the CSV files as served, and MANIFEST.json (not in git)
data/parquet/<YYYY-MM-DD>/  one Parquet per CSV (not in git)
```

`MANIFEST.json` holds the latest change note date on the page and, for each
file, its URL, the category and date the page shows for it, size, sha256,
Last-Modified (the download handler sends none), fetch time, detected
encoding and CSV row count (header excluded).
