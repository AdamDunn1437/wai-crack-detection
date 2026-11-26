"""Score one model's crack predictions against the labels.

    python eval/evaluate.py --model yolo-seg-n --split eval/splits/public_test.csv \
        --images DATA/images --labels DATA/labels --preds PREDS

Appends one row to eval/results.csv and writes per-image scores and overlays
to eval/runs/<model>/<split>/. See eval/README.md for the formats.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import subprocess
import sys
from datetime import datetime
from pathlib import Path

import cv2
import numpy as np

EVAL_DIR = Path(__file__).resolve().parent
RESULT_FIELDS = [
    "date", "model", "split", "split_sha", "images", "missing_preds", "tolerance_px",
    "iou", "precision", "recall", "f1", "tol_precision", "tol_recall", "tol_f1",
    "code_commit", "notes",
]


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_split(split_csv: Path, images_dir: Path) -> list[str]:
    """Return image filenames in the split, failing if any image changed."""
    with open(split_csv, newline="") as f:
        rows = list(csv.DictReader(f))
    for row in rows:
        path = images_dir / row["image"]
        if not path.exists():
            sys.exit(f"{row['image']} is in the split but not in {images_dir}")
        if sha256(path) != row["sha256"]:
            sys.exit(f"{row['image']} does not match the frozen split (file changed)")
    return [row["image"] for row in rows]


def read_mask(path: Path, shape: tuple[int, int]) -> np.ndarray:
    """Binary mask PNG: 0 = background, anything else = crack."""
    mask = cv2.imread(str(path), cv2.IMREAD_GRAYSCALE)
    if mask is None:
        sys.exit(f"could not read {path}")
    if mask.shape != shape:
        sys.exit(f"{path} is {mask.shape[1]}x{mask.shape[0]}, image is {shape[1]}x{shape[0]}")
    return mask > 0


def read_yolo_polygons(path: Path, shape: tuple[int, int]) -> np.ndarray:
    """YOLO segmentation label: one 'class x1 y1 x2 y2 ...' line per crack, normalised."""
    h, w = shape
    mask = np.zeros(shape, np.uint8)
    for line in path.read_text().split("\n"):
        values = line.split()[1:]
        if len(values) < 4:
            continue
        xy = np.array(values, float).reshape(-1, 2) * [w, h]
        pts = [np.round(xy).astype(np.int32)]
        cv2.fillPoly(mask, pts, 255)
        cv2.polylines(mask, pts, True, 255, 1)  # keep very thin outlines visible
    return mask > 0


def read_label(labels_dir: Path, stem: str, shape: tuple[int, int]) -> np.ndarray:
    if (labels_dir / f"{stem}.txt").exists():
        return read_yolo_polygons(labels_dir / f"{stem}.txt", shape)
    if (labels_dir / f"{stem}.png").exists():
        return read_mask(labels_dir / f"{stem}.png", shape)
    sys.exit(f"no label for {stem} in {labels_dir} (expected {stem}.txt or {stem}.png)")


def grow(mask: np.ndarray, px: int) -> np.ndarray:
    """Every pixel within px of the mask."""
    if px == 0:
        return mask
    disk = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2 * px + 1, 2 * px + 1))
    return cv2.dilate(mask.astype(np.uint8), disk) > 0


def counts(label: np.ndarray, pred: np.ndarray, tol: int) -> dict[str, int]:
    """Pixel counts for strict scores and for scores where a near miss (within tol px) counts."""
    return {
        "tp": int((label & pred).sum()),
        "fp": int((~label & pred).sum()),
        "fn": int((label & ~pred).sum()),
        "pred_near_label": int((pred & grow(label, tol)).sum()),
        "label_near_pred": int((label & grow(pred, tol)).sum()),
        "pred": int(pred.sum()),
        "label": int(label.sum()),
    }


def div(a: int, b: int) -> float:
    return a / b if b else float("nan")


def scores(c: dict[str, int]) -> dict[str, float]:
    p, r = div(c["tp"], c["tp"] + c["fp"]), div(c["tp"], c["tp"] + c["fn"])
    tp_, tr_ = div(c["pred_near_label"], c["pred"]), div(c["label_near_pred"], c["label"])
    return {
        "iou": div(c["tp"], c["tp"] + c["fp"] + c["fn"]),
        "precision": p,
        "recall": r,
        "f1": 2 * p * r / (p + r) if p + r else float("nan"),
        "tol_precision": tp_,
        "tol_recall": tr_,
        "tol_f1": 2 * tp_ * tr_ / (tp_ + tr_) if tp_ + tr_ else float("nan"),
    }


def overlay(image: np.ndarray, label: np.ndarray, pred: np.ndarray, tol: int) -> np.ndarray:
    """Green = found, red = false alarm, blue = missed (near misses count as found)."""
    out = image.copy()
    out[pred & grow(label, tol)] = (0, 200, 0)
    out[pred & ~grow(label, tol)] = (0, 0, 255)
    out[label & ~grow(pred, tol)] = (255, 0, 0)
    return out


def code_commit() -> str:
    try:
        return subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"], cwd=EVAL_DIR,
            capture_output=True, text=True, check=True,
        ).stdout.strip()
    except (OSError, subprocess.CalledProcessError):
        return "unknown"


def fmt(x: float) -> str:
    return f"{x:.4f}"


def main(argv: list[str] | None = None) -> dict[str, float]:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--model", required=True, help="name for this run, e.g. yolo-seg-n")
    ap.add_argument("--split", required=True, type=Path, help="frozen split CSV (eval/freeze_split.py)")
    ap.add_argument("--images", required=True, type=Path)
    ap.add_argument("--labels", required=True, type=Path)
    ap.add_argument("--preds", required=True, type=Path, help="folder of <image stem>.png masks")
    ap.add_argument("--tolerance", type=int, default=2, help="near-miss distance in pixels (default 2)")
    ap.add_argument("--results", type=Path, default=EVAL_DIR / "results.csv")
    ap.add_argument("--out", type=Path, help="default eval/runs/<model>/<split>")
    ap.add_argument("--notes", default="", help="anything that explains this run")
    args = ap.parse_args(argv)

    out = args.out or EVAL_DIR / "runs" / args.model / args.split.stem
    (out / "overlays").mkdir(parents=True, exist_ok=True)

    total: dict[str, int] = {}
    missing = []
    per_image = []
    for name in read_split(args.split, args.images):
        stem = Path(name).stem
        image = cv2.imread(str(args.images / name))
        if image is None:
            sys.exit(f"could not read {args.images / name}")
        shape = image.shape[:2]
        label = read_label(args.labels, stem, shape)
        pred_path = args.preds / f"{stem}.png"
        if pred_path.exists():
            pred = read_mask(pred_path, shape)
        else:
            missing.append(name)  # a skipped image scores as "found nothing"
            pred = np.zeros(shape, bool)

        c = counts(label, pred, args.tolerance)
        for k, v in c.items():
            total[k] = total.get(k, 0) + v
        per_image.append({"image": name, **{k: fmt(v) for k, v in scores(c).items()}})
        cv2.imwrite(str(out / "overlays" / f"{stem}.jpg"), overlay(image, label, pred, args.tolerance))

    with open(out / "per_image.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(per_image[0]))
        w.writeheader()
        w.writerows(per_image)

    result = scores(total)
    row = {
        "date": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "model": args.model,
        "split": args.split.stem,
        "split_sha": sha256(args.split)[:8],
        "images": len(per_image),
        "missing_preds": len(missing),
        "tolerance_px": args.tolerance,
        **{k: fmt(v) for k, v in result.items()},
        "code_commit": code_commit(),
        "notes": args.notes,
    }
    new_file = not args.results.exists()
    with open(args.results, "a", newline="") as f:
        w = csv.DictWriter(f, fieldnames=RESULT_FIELDS)
        if new_file:
            w.writeheader()
        w.writerow(row)

    if missing:
        print(f"warning: {len(missing)} images had no prediction and were scored as empty: {missing[:5]}")
    print("  ".join(f"{k} {row[k]}" for k in ["iou", "precision", "recall", "f1", "tol_f1"]))
    print(f"row added to {args.results}, overlays in {out / 'overlays'}")
    return result


if __name__ == "__main__":
    main()
