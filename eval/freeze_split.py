"""Freeze a test split: list every image in a folder with its SHA-256.

    python eval/freeze_split.py --images DATA/cast3/images --out eval/splits/cast3_test.csv

Commit the CSV. evaluate.py refuses to score if any listed image is missing or
has changed, so every model is graded on exactly the same files.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
from pathlib import Path

IMAGE_TYPES = {".jpg", ".jpeg", ".png", ".tif", ".tiff", ".bmp"}


def main(argv: list[str] | None = None) -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--images", required=True, type=Path)
    ap.add_argument("--out", required=True, type=Path)
    args = ap.parse_args(argv)

    images = sorted(p for p in args.images.iterdir() if p.suffix.lower() in IMAGE_TYPES)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    with open(args.out, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["image", "sha256"])
        for p in images:
            w.writerow([p.name, hashlib.sha256(p.read_bytes()).hexdigest()])
    print(f"{len(images)} images written to {args.out}")


if __name__ == "__main__":
    main()
