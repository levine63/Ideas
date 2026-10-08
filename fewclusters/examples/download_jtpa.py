#!/usr/bin/env python3
"""Download and inventory two publicly distributed National JTPA Study datasets.

This utility prepares source-preserving research inputs, *not* a causal analysis.

Sources
-------
1. Full public-use archive hosted by the W. E. Upjohn Institute:
   https://www.upjohn.org/sites/default/files/2019-02/jtpa_national_evaluation.zip
2. Women's extract distributed by Melody Huang in the senseweight R package:
   https://raw.githubusercontent.com/melodyyhuang/senseweight/main/data/jtpa_women.rda

The women's file is suitable for exploring site-level borrowing because it
contains a site identifier. The full archive is preferable for a publishable
application, but it requires a documented merge and review of original codebooks.

WARNING: Do not interpret the observed treatment fraction as the exact known
randomization probability. Verify the site's and any strata's assignment
protocol from the original design documentation before supplying m_known.

Usage
-----
    python -m pip install requests pandas pyreadr
    python download_jtpa.py --dataset women --output-dir jtpa_data
    python download_jtpa.py --dataset full --output-dir jtpa_data
    python download_jtpa.py --dataset both --output-dir jtpa_data

The script deliberately does NOT unpack the full archive, whose contents may
include nested ZIPs, old Stata/SAS datasets, and documentation. It saves a
manifest identifying the archive members so they can be screened before use.

Files are saved only under --output-dir. Existing data files are not replaced
unless --overwrite is set.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys
import zipfile

import pandas as pd
import requests

WOMEN_URL = (
    "https://raw.githubusercontent.com/melodyyhuang/senseweight/"
    "main/data/jtpa_women.rda"
)
FULL_URL = (
    "https://www.upjohn.org/sites/default/files/2019-02/"
    "jtpa_national_evaluation.zip"
)


def download(url: str, destination: Path, overwrite: bool = False) -> str:
    """Stream a public file to disk and compute its SHA-256 without buffering it.

    A temporary .part file prevents a failed download from masquerading as a
    completed dataset. The function does not attempt to bypass access controls.
    """
    if destination.exists() and not overwrite:
        print(f"Using existing: {destination}")
        return sha256(destination)
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = destination.with_suffix(destination.suffix + ".part")
    try:
        with requests.get(url, stream=True, timeout=(30, 180)) as response:
            response.raise_for_status()
            with temporary.open("wb") as fh:
                for chunk in response.iter_content(chunk_size=1024 * 1024):
                    if chunk:
                        fh.write(chunk)
        if temporary.stat().st_size == 0:
            raise RuntimeError(f"Empty download from {url}")
        temporary.replace(destination)
    finally:
        if temporary.exists():
            temporary.unlink()
    print(f"Saved {destination} ({destination.stat().st_size:,} bytes)")
    return sha256(destination)


def sha256(path: Path) -> str:
    """Return a reproducible content fingerprint for a local source file."""
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def women_extract(output_dir: Path, overwrite: bool = False) -> None:
    """Convert R's JTPA women's dataset to an auditable CSV and QA manifest."""
    try:
        import pyreadr
    except ImportError as exc:
        raise RuntimeError(
            "Conversion requires pyreadr. Install: python -m pip install pyreadr"
        ) from exc

    rda_file = output_dir / "jtpa_women_source.rda"
    source_hash = download(WOMEN_URL, rda_file, overwrite)
    objects = pyreadr.read_r(str(rda_file))
    if "jtpa_women" in objects:
        df = objects["jtpa_women"]
    elif len(objects) == 1:
        # R object capitalization sometimes varies between package versions.
        df = next(iter(objects.values()))
    else:
        raise RuntimeError(f"Cannot identify jtpa_women in objects: {list(objects)}")

    required = {"site", "T", "Y", "prevearn", "age"}
    missing_columns = required.difference(df.columns)
    if missing_columns:
        raise RuntimeError(f"Missing expected columns: {sorted(missing_columns)}")

    # CRAN documentation has said 6,109 rows while the package's web dataset
    # browser has displayed 6,102. Record what the actual file contains.
    # Do not delete observations or silently reconcile that discrepancy.
    site_table = (
        df.groupby("site", dropna=False)
        .agg(
            n=("T", "size"),
            n_treated=("T", lambda x: int((x == 1).sum())),
            n_control=("T", lambda x: int((x == 0).sum())),
            observed_assignment_share=("T", "mean"),
        )
        .reset_index()
        .sort_values("n")
    )
    values = sorted(df["T"].dropna().unique().tolist())
    if not set(values).issubset({0, 1}):
        raise RuntimeError(f"Nonbinary assignment values found: {values}")

    out_csv = output_dir / "jtpa_women.csv"
    out_sites = output_dir / "jtpa_women_site_counts.csv"
    out_manifest = output_dir / "jtpa_women_manifest.json"
    if not overwrite and any(p.exists() for p in (out_csv, out_sites, out_manifest)):
        raise FileExistsError("Output already exists. Use --overwrite to regenerate.")
    df.to_csv(out_csv, index=False)
    site_table.to_csv(out_sites, index=False)
    manifest = {
        "source_url": WOMEN_URL,
        "source_rda_sha256": source_hash,
        "csv_sha256": sha256(out_csv),
        "rows": int(len(df)),
        "columns": df.columns.tolist(),
        "number_of_sites": int(df["site"].nunique(dropna=True)),
        "site_sizes_min_max": [int(site_table["n"].min()), int(site_table["n"].max())],
        "missing_counts": {str(k): int(v) for k, v in df.isna().sum().items()},
        "assignment_values": values,
        "critical_warning": (
            "Assignment shares in this extract are not verified design probabilities. "
            "Check original documentation before using m_known."
        ),
    }
    out_manifest.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(f"Women's sample: {manifest['rows']:,} rows, {manifest['number_of_sites']} sites.")
    print(site_table.to_string(index=False))
    print(f"Manifest: {out_manifest}")


def full_archive(output_dir: Path, overwrite: bool = False) -> None:
    """Preserve and index the original Upjohn ZIP without guessing variable roles."""
    archive = output_dir / "jtpa_national_evaluation.zip"
    source_hash = download(FULL_URL, archive, overwrite)
    if not zipfile.is_zipfile(archive):
        raise RuntimeError(f"Downloaded file is not a valid ZIP: {archive}")
    with zipfile.ZipFile(archive) as src:
        members = [
            {
                "path": info.filename,
                "uncompressed_bytes": int(info.file_size),
                "compressed_bytes": int(info.compress_size),
                "is_directory": bool(info.is_dir()),
            }
            for info in src.infolist()
        ]
    manifest = {
        "source_url": FULL_URL,
        "source_zip_sha256": source_hash,
        "archive_members": len(members),
        "notes": (
            "This indexes the original distribution only. Select the analysis "
            "files and verify identifiers, assignment design, outcome timing, "
            "baseline status and codebook before merging or analysis."
        ),
    }
    manifest_path = output_dir / "jtpa_full_manifest.json"
    inventory_path = output_dir / "jtpa_full_inventory.csv"
    if not overwrite and (manifest_path.exists() or inventory_path.exists()):
        raise FileExistsError("Full archive manifest already exists. Use --overwrite.")
    pd.DataFrame(members).to_csv(inventory_path, index=False)
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(f"Full archive: {len(members)} ZIP members. Inventory: {inventory_path}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset", choices=("women", "full", "both"), default="women")
    parser.add_argument("--output-dir", type=Path, default=Path("jtpa_data"))
    parser.add_argument("--overwrite", action="store_true")
    args = parser.parse_args(argv)
    try:
        if args.dataset in {"women", "both"}:
            women_extract(args.output_dir, args.overwrite)
        if args.dataset in {"full", "both"}:
            full_archive(args.output_dir, args.overwrite)
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
