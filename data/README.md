---
license: other
license_name: ekidata-jp-terms
license_link: https://ekidata.jp/agreement.php
language:
- ja
tags:
- japan
- railway
- railway-stations
- transportation
- geospatial
- geoparquet
size_categories:
- 10K<n<100K
configs:
- config_name: 'station'
  data_files: parquet/2026-10-05/station.2026-07-31.parquet
  default: true
- config_name: 'line'
  data_files: parquet/2026-10-05/line.2026-06-18.parquet
- config_name: 'company'
  data_files: parquet/2026-10-05/company.2026-04-09.parquet
- config_name: 'join'
  data_files: parquet/2026-10-05/join.2026-09-14.parquet
- config_name: 'pref'
  data_files: parquet/2026-10-05/pref.parquet
- config_name: 'station.2026-07-31'
  data_files: parquet/2026-10-05/station.2026-07-31.parquet
- config_name: 'station.2026-07-13'
  data_files: parquet/2026-10-05/station.2026-07-13.parquet
- config_name: 'station.2026-06-18'
  data_files: parquet/2026-10-05/station.2026-06-18.parquet
- config_name: 'station.2026-05-28'
  data_files: parquet/2026-10-05/station.2026-05-28.parquet
- config_name: 'station.2026-04-30'
  data_files: parquet/2026-10-05/station.2026-04-30.parquet
- config_name: 'station.2026-04-09'
  data_files: parquet/2026-10-05/station.2026-04-09.parquet
- config_name: 'line.2026-06-18'
  data_files: parquet/2026-10-05/line.2026-06-18.parquet
- config_name: 'line.2026-04-09'
  data_files: parquet/2026-10-05/line.2026-04-09.parquet
- config_name: 'line.2026-03-23'
  data_files: parquet/2026-10-05/line.2026-03-23.parquet
- config_name: 'line.2025-06-04'
  data_files: parquet/2026-10-05/line.2025-06-04.parquet
- config_name: 'line.2025-05-29'
  data_files: parquet/2026-10-05/line.2025-05-29.parquet
- config_name: 'company.2026-04-09'
  data_files: parquet/2026-10-05/company.2026-04-09.parquet
- config_name: 'company.2025-10-15'
  data_files: parquet/2026-10-05/company.2025-10-15.parquet
- config_name: 'company.2025-06-04'
  data_files: parquet/2026-10-05/company.2025-06-04.parquet
- config_name: 'company.2025-05-29'
  data_files: parquet/2026-10-05/company.2025-05-29.parquet
- config_name: 'company.2025-05-23'
  data_files: parquet/2026-10-05/company.2025-05-23.parquet
- config_name: 'join.2026-09-14'
  data_files: parquet/2026-10-05/join.2026-09-14.parquet
- config_name: 'join.2026-06-18'
  data_files: parquet/2026-10-05/join.2026-06-18.parquet
- config_name: 'join.2026-04-09'
  data_files: parquet/2026-10-05/join.2026-04-09.parquet
- config_name: 'join.2026-02-26'
  data_files: parquet/2026-10-05/join.2026-02-26.parquet
- config_name: 'join.2025-09-16'
  data_files: parquet/2026-10-05/join.2025-09-16.parquet
- config_name: 'join.2025-09-03'
  data_files: parquet/2026-10-05/join.2025-09-03.parquet
---

# ekidata-jp

The free CSV files of 駅データ.jp (https://ekidata.jp/), the railway station
database of Value and Vision Co., Ltd. (株式会社バリューアンドビジョン):
the railway companies of Japan, their lines, their stations with coordinates,
the pairs of adjacent stations on each line, and a prefecture master. Each
dated file the download page offers is its own subset, with a typed Parquet
beside the CSV as served; stations also carry a point geometry.

Use, modification and redistribution are allowed by the site's terms, with
one condition on redistribution: unmodified data only free of charge (see
Licence).

## What the data is

駅データ.jp offers its data in a free tier and a paid tier. This dataset holds
the free tier only, as listed on the members' download page
https://ekidata.jp/dl/?p=1. That page needs a login with a free member
account; the files here were downloaded with the account of the person who
built this dataset. No credential is part of this dataset or of the code that
built it, which reads them from the environment.

| table | file on the site | content | specification |
|---|---|---|---|
| `company` | `companyYYYYMMDD.csv` | railway companies (事業者) | https://ekidata.jp/doc/company.php |
| `line` | `lineYYYYMMDDfree.csv` | lines (路線) | https://ekidata.jp/doc/line.php |
| `station` | `stationYYYYMMDDfree.csv` | stations (駅) | https://ekidata.jp/doc/station.php |
| `join` | `joinYYYYMMDD.csv` | adjacent stations on a line (接続駅) | https://ekidata.jp/doc/join.php |
| `pref` | `pref.csv` | prefectures (都道府県マスタ) | https://ekidata.jp/doc/pref.php |

The site's specification (https://ekidata.jp/doc/) says the free data lacks,
compared with the paid data: part of `line_color_c` and `line_color_t`, all of
`line_type`, all of `station_name_k` and `station_name_r`, and every
Shinkansen station. Apart from these, the two are the same.

## Editions

The download page offers several dated files of each table. Each is a subset
named `<table>.<date>`, the date being the one in the file name. The latest
edition of each table is also the subset named after the table alone
(`station` is the default subset). `pref.csv` has no date and is the subset
`pref`.

| subset | rows | raw file |
|---|---:|---|
| `station.2026-07-31` (= `station`) | 10,962 | `raw/2026-10-05/station20260731free.csv` |
| `station.2026-07-13` | 10,962 | `raw/2026-10-05/station20260713free.csv` |
| `station.2026-06-18` | 10,962 | `raw/2026-10-05/station20260618free.csv` |
| `station.2026-05-28` | 10,941 | `raw/2026-10-05/station20260528free.csv` |
| `station.2026-04-30` | 10,943 | `raw/2026-10-05/station20260430free.csv` |
| `station.2026-04-09` | 10,943 | `raw/2026-10-05/station20260409free.csv` |
| `line.2026-06-18` (= `line`) | 624 | `raw/2026-10-05/line20260618free.csv` |
| `line.2026-04-09` | 623 | `raw/2026-10-05/line20260409free.csv` |
| `line.2026-03-23` | 622 | `raw/2026-10-05/line20260323free.csv` |
| `line.2025-06-04` | 622 | `raw/2026-10-05/line20250604free.csv` |
| `line.2025-05-29` | 622 | `raw/2026-10-05/line20250529free.csv` |
| `company.2026-04-09` (= `company`) | 175 | `raw/2026-10-05/company20260409.csv` |
| `company.2025-10-15` | 174 | `raw/2026-10-05/company20251015.csv` |
| `company.2025-06-04` | 174 | `raw/2026-10-05/company20250604.csv` |
| `company.2025-05-29` | 176 | `raw/2026-10-05/company20250529.csv` |
| `company.2025-05-23` | 174 | `raw/2026-10-05/company20250523.csv` |
| `join.2026-09-14` (= `join`) | 10,188 | `raw/2026-10-05/join20260914.csv` |
| `join.2026-06-18` | 10,189 | `raw/2026-10-05/join20260618.csv` |
| `join.2026-04-09` | 10,168 | `raw/2026-10-05/join20260409.csv` |
| `join.2026-02-26` | 10,168 | `raw/2026-10-05/join20260226.csv` |
| `join.2025-09-16` | 10,173 | `raw/2026-10-05/join20250916.csv` |
| `join.2025-09-03` | 10,172 | `raw/2026-10-05/join20250903.csv` |
| `pref` | 48 | `raw/2026-10-05/pref.csv` |

All files were fetched on 2026-10-05 (Japan time), which names the directory
`raw/2026-10-05/` and `parquet/2026-10-05/`. The site corrects its data and
posts dated change notes (更新履歴) on its pages; the latest note on the
download page that day was dated 2026-09-14. `raw/2026-10-05/MANIFEST.json`
gives each file's URL, the category and date the page shows for it, size,
sha256 and row count. The CSVs are the site's own files, byte for byte.

## Files and columns

`parquet/2026-10-05/<subset>.parquet` holds one subset each. Column names are
those of the CSV and keep its order. The type of a column comes from its name,
never from inference:

| columns | type |
|---|---|
| codes: `company_cd`, `rr_cd`, `line_cd`, `station_cd`, `station_g_cd`, `pref_cd`, `station_cd1`, `station_cd2` | INTEGER |
| `company_type`, `line_type`, `e_status`, `e_sort`, `zoom` | INTEGER |
| `lon`, `lat` | DOUBLE |
| everything else, including `post`, `line_color_c`, `open_ymd`, `close_ymd` | the text of the CSV |
| `geometry` (stations only) | added here: a point from `lon` and `lat` |

The codes are identifiers. They are kept as integers because every value in
every file is an integer without leading zeros, so no code loses anything; a
value with a leading zero, or any value that is not an integer, stops the
build instead of being changed. `line_color_c` stays text because it is a hex
colour (`000000` among them). `open_ymd` and `close_ymd` stay text because
they hold `0000-00-00`. An empty field is null.

| table | columns |
|---|---|
| `company` | `company_cd`, `rr_cd`, `company_name`, `company_name_k`, `company_name_h`, `company_name_r`, `company_url`, `company_type`, `e_status`, `e_sort` |
| `line` | `line_cd`, `company_cd`, `line_name`, `line_name_k`, `line_name_h`, `line_color_c`, `line_color_t`, `line_type`, `lon`, `lat`, `zoom`, `e_status`, `e_sort` |
| `station` | `station_cd`, `station_g_cd`, `station_name`, `station_name_k`, `station_name_r`, `line_cd`, `pref_cd`, `post`, `address`, `lon`, `lat`, `open_ymd`, `close_ymd`, `e_status`, `e_sort`, `geometry` |
| `join` | `line_cd`, `station_cd1`, `station_cd2` |
| `pref` | `pref_cd`, `pref_name` |

The meaning of every column is in the specification. In short: `e_status` is
0 in operation, 1 not yet open, 2 closed; `company_type` is 0 other, 1 JR,
2 major private, 3 semi-major private; `station_g_cd` groups stations of
different lines that count as one station; `rr_cd` is a two-digit railway
code; in `line`, `lon`, `lat` and `zoom` are the centre and Google Maps zoom
of a map that shows the whole line, not a location of the line.

The geometry is a GeoParquet 1.0.0 Point column without a `crs` key, which
the GeoParquet specification defines as OGC:CRS84 (WGS 84, longitude then
latitude). The station specification says of `lon` and `lat` only 世界測地系
(the world geodetic system) and refers to the FAQ for the datum; the FAQ
(https://ekidata.jp/faq.php, read 2026-10-05) has no entry on it. The
coordinates are therefore read as WGS 84; JGD2000 and JGD2011, Japan's
realisations of the world geodetic system, differ from it by much less than
the precision of a station's position. Rows keep the order of the CSV.

```sql
-- DuckDB, straight off the Hub: stations in operation per prefecture, latest edition
SELECT p.pref_name, count(*) AS stations
FROM 'hf://datasets/yuiseki/ekidata-jp/parquet/2026-10-05/station.2026-07-31.parquet' s
JOIN 'hf://datasets/yuiseki/ekidata-jp/parquet/2026-10-05/pref.parquet' p USING (pref_cd)
WHERE s.e_status = 0
GROUP BY ALL ORDER BY stations DESC;
```

## Things to know

- No Shinkansen stations. The free station files leave them out, as the
  specification says, but the free line and join files keep them: the 12
  Shinkansen lines (four-digit `line_cd`, 1001 to 1012) are in `line` with no
  station, and 154 rows of `join.2026-09-14` are on those lines, between
  six-digit station codes that are in no free station file. Two more lines of
  `line.2026-06-18` have no station: 11405 JR北陸本線(富山～直江津) and
  99207 三陸鉄道北リアス線, both closed (`e_status` 2).
- `station_name_k`, `station_name_r` and `line_type` are empty in every row
  (paid fields). `line_color_c` and `line_color_t` are filled for 48 of the 624
  lines of `line.2026-06-18`.
- `open_ymd` is `0000-00-00` for 10,584 of the 10,962 stations of
  `station.2026-07-31`, and `close_ymd` is `0000-00-00` for 295 of its 497
  closed stations; `0000-00-00` means no date is given.
- 加木屋中ノ池 (station_cd 3000922) has `lat` 35 in every station edition, a
  whole degree where every other station has at least three decimals (most
  have six), so its point is
  unlikely to be where the station is; it is kept as served.
- The specification names the address column `add`; the CSVs call it
  `address`. Addresses mix full-width and half-width digits.
- `station_g_cd` is not always a `station_cd`: 23 group codes of
  `station.2026-07-31` are not the code of any station, which the
  specification allows. `e_sort` repeats (143 values of `station.2026-07-31`
  occur more than once); the specification orders by `e_sort` and then the
  code.
- Editions differ in a few rows each. For example `station.2026-07-31` differs
  from `station.2026-07-13` in one row, the postcode of 島高松, as the change
  note of 2026-07-31 says; `join.2026-09-14` drops two rows of 京阪本線 and
  adds one of あいの風とやま鉄道線, as the notes of 2026-09-14 say.
- The download page also carries links to editions that are commented out in
  its HTML and so are not shown to users. Among them are 2026-09-14 editions
  of the line and station files (`f.php?t=3&d=20260914`,
  `f.php?t=5&d=20260914`), and older editions. None of these was taken. The
  change notes of 2026-09-14 on the site's pages describe changes to station
  and line data that the shown station and line files therefore may not
  have yet.
- The paid tier (有料データ) is not here.

## Checked before upload

`scripts/02_verify.py` in the source repository checks:

- every raw file has the size and sha256 in `MANIFEST.json`, and its row count
  by Python's csv module equals the manifest's
- there is one Parquet per CSV and no other
- each Parquet has as many rows as the CSV
- every value of every row equals the value read from the CSV with the csv
  module and typed by the same rule (empty is null), row by row in CSV order
- every column has the type of the rule, in CSV order
- stations: GeoParquet 1.0.0 metadata naming a Point and no `crs`; every row
  has a point whose x and y are its `lon` and `lat`
- a DuckDB without extensions opens every file; no row group has a bloom
  filter

## Licence

The data is under the terms of use of 駅データ.jp, not under an open licence.
The terms (利用規約, https://ekidata.jp/agreement.php, last revised
2025-06-04 (改定日：2025年6月4日), read on 2026-10-05) say, in Articles 4 to
7:

> 第4条 (利用)
> 商用、非商用にかかわらず、第7条（禁止事項）に該当する内容を除き、本件データを弊社に連絡する必要なく利用することができる。また、本件データを利用する際に、弊社のデータであることを明記する必要はない。
> 但し、本件データを利用することにより生じたいかなる損害についても弊社は責任を負わない。
> 会員登録した法人は、駅データおよび弊社のサイトまたは案内資料（紙またはPDFデータ）で利用者実績や事例として、社名や利用目的が公開される場合がある。
> また、公開時には利用者の法人ロゴの使用を弊社に認めるものとする。
> 【お願い】
> 弊社のデータであることを明記する必要はありませんが、弊社のデータであることの明記や、弊社サイトへのリンクを歓迎します。
>
> 第5条 (加工)
> 商用、非商用にかかわらず、本件データを加工して利用することができる。
> 但し、本件データを加工することにより生じたいかなる損害についても弊社は責任を負わない。
>
> 第6条 (第三者提供)
> 加工、非加工にかかわらず、本件データを第三者へ提供することができる。
> 但し、非加工で提供する場合は無償でなくてはならない。 ※
> また、本件データを第三者提供することにより生じたいかなる損害についても弊社は責任を負わない。
>
> 第7条 (禁止事項)
> 本件データを利用するにあたり以下に該当することをしてはならない。
> (1) 犯罪を勧誘又は助長するおそれのある利用
> (2) わいせつ、裸体、死体、その他公序良俗に反する情報に関係する利用
> (3) 消費者の判断に錯誤を与える恐れのある利用
> (4) 第三者の財産権(知的所有権を含む)の侵害、プライバシーの侵害、誹謗中傷その他の不利益を与える利用
> (5) 弊社または本件サービスへの誹謗中傷、弊社業務の運営・維持を妨げる利用
> (6) ウイルスその他第三者に害悪を加えるおそれのある利用

and, for the mark in Article 6:

> ※「無償」とは、データのみで第三者へ提供する場合です。
> 非加工のデータを有償のシステムに組み込み、有償で販売しても問題ありません。但し、データは無償としてください。

In English, in short: the data may be used for any purpose, commercial or
not, without contacting the company, except the uses Article 7 prohibits;
the company is not liable for any damage. Attribution is not required, but
credit or a link is welcome. The data may be modified. Modified or unmodified,
it may be provided to third parties, but unmodified data only free of charge
(free of charge refers to the data on its own; it may be built into a paid
system). Article 7 prohibits uses that encourage crime; obscene or otherwise
offensive uses; uses that may mislead consumers; uses that infringe third
parties' property, privacy or reputation; defaming the company or its service
or hindering its business; and uses that may spread viruses or otherwise harm
third parties. The terms may be revised on the site, and use after a revision
means agreement to it.

The raw CSVs here are unmodified data, provided free of charge on the Hub,
which Article 6 allows. The Parquet files are modified data (Article 5):
`LICENSE` beside this file says what was done. Whoever passes the unmodified
CSVs on must not charge for them, and every use is subject to Article 7.

## Citation

駅データ.jp, 株式会社バリューアンドビジョン (Value and Vision Co., Ltd.),
https://ekidata.jp/, free data, editions as listed above, downloaded
2026-10-05.
