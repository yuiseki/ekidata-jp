#!/usr/bin/env python3
"""Push the CSVs as served, their Parquet and the card to the Hugging Face Hub.

Each fetch's CSVs and MANIFEST.json go up unchanged after their sha256 is
checked against data/raw/<version>/MANIFEST.json. The card must declare
every Parquet file as a subset (table.YYYY-MM-DD, or pref), and the latest
edition of each table again under the table's own name; otherwise nothing
is sent.

    uv run python src/publish.py             # dry run
    uv run python src/publish.py --push
"""

import argparse
import hashlib
import importlib.util
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
REPO = "yuiseki/ekidata-jp"

_spec = importlib.util.spec_from_file_location("export", ROOT / "scripts" / "03_export_parquet.py")
export = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(export)


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def declared(card: str, name: str, rel: str) -> bool:
    return f"- config_name: '{name}'\n  data_files: {rel}\n" in card


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", default=REPO)
    ap.add_argument("--push", action="store_true")
    a = ap.parse_args()

    data = ROOT / "data"
    card = (data / "README.md").read_text(encoding="utf-8")
    files = ["README.md", "LICENSE", "provenance.yaml"]

    plan = export.outputs()
    on_disk = set((data / "parquet").rglob("*.parquet"))
    if on_disk != {p for _, _, p in plan}:
        raise SystemExit("data/parquet does not hold one Parquet per CSV; run the export")
    latest: dict[str, tuple[str, str]] = {}
    for subset, src, p in plan:
        rel = p.relative_to(data).as_posix()
        if not declared(card, subset, rel):
            raise SystemExit(f"the card does not declare the subset {subset} ({rel})")
        table, edition, _ = export.subset_of(src.name)
        if edition and (table not in latest or edition > latest[table][0]):
            latest[table] = (edition, rel)
        files.append(rel)
    for table, (_, rel) in latest.items():
        if not declared(card, table, rel):
            raise SystemExit(f"the card does not declare {table} as {rel}, its latest edition")

    for mpath in sorted((data / "raw").glob("*/MANIFEST.json")):
        d = mpath.parent
        for name, m in json.loads(mpath.read_text())["files"].items():
            if sha256(d / name) != m["sha256"]:
                raise SystemExit(f"raw/{d.name}/{name} is not the file in its manifest")
            files.append(f"raw/{d.name}/{name}")
        files.append(f"raw/{d.name}/MANIFEST.json")

    total = sum((data / f).stat().st_size for f in files)
    print(a.repo)
    for f in files:
        print(f"  {(data / f).stat().st_size:>10,}  {f}")
    print(f"  {len(files)} files, {total:,} bytes ({total / 1e6:.1f} MB)")
    if not a.push:
        print("\ndry run. pass --push to upload")
        return 0

    from huggingface_hub import HfApi

    api = HfApi()
    api.create_repo(a.repo, repo_type="dataset", exist_ok=True, private=False)
    api.upload_folder(
        folder_path=str(data), repo_id=a.repo, repo_type="dataset", allow_patterns=files
    )
    print(f"\npushed to https://huggingface.co/datasets/{a.repo}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
