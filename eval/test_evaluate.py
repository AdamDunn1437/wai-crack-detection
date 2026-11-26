"""Run with: python -m pytest eval"""
from __future__ import annotations

import csv
import sys
from pathlib import Path

import cv2
import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).parent))
import evaluate  # noqa: E402
import freeze_split  # noqa: E402

H, W = 40, 60


def crack(x: int) -> np.ndarray:
    """A 1 px wide vertical crack at column x, as a 0/255 mask."""
    m = np.zeros((H, W), np.uint8)
    m[5:35, x] = 255
    return m


def setup(tmp_path: Path, pred: np.ndarray | None) -> list[str]:
    for d in ["images", "labels", "preds"]:
        (tmp_path / d).mkdir()
    cv2.imwrite(str(tmp_path / "images/a.png"), np.full((H, W, 3), 128, np.uint8))
    cv2.imwrite(str(tmp_path / "labels/a.png"), crack(30))
    if pred is not None:
        cv2.imwrite(str(tmp_path / "preds/a.png"), pred)
    freeze_split.main(["--images", str(tmp_path / "images"), "--out", str(tmp_path / "split.csv")])
    return [
        "--model", "test", "--split", str(tmp_path / "split.csv"),
        "--images", str(tmp_path / "images"), "--labels", str(tmp_path / "labels"),
        "--preds", str(tmp_path / "preds"), "--results", str(tmp_path / "results.csv"),
        "--out", str(tmp_path / "out"),
    ]


def test_perfect_prediction(tmp_path):
    r = evaluate.main(setup(tmp_path, crack(30)))
    assert r["iou"] == r["f1"] == r["tol_f1"] == 1.0


def test_near_miss_counts_only_with_tolerance(tmp_path):
    r = evaluate.main(setup(tmp_path, crack(31)))  # one pixel off
    assert r["iou"] == 0.0
    assert r["tol_f1"] == 1.0


def test_far_miss_scores_zero(tmp_path):
    r = evaluate.main(setup(tmp_path, crack(50)))
    assert r["tol_precision"] == r["tol_recall"] == 0.0


def test_missing_prediction_scores_as_empty(tmp_path):
    r = evaluate.main(setup(tmp_path, None))
    assert r["recall"] == 0.0
    with open(tmp_path / "results.csv") as f:
        row = next(csv.DictReader(f))
    assert row["missing_preds"] == "1"
    assert (tmp_path / "out/overlays/a.jpg").exists()


def test_changed_image_is_rejected(tmp_path):
    args = setup(tmp_path, crack(30))
    cv2.imwrite(str(tmp_path / "images/a.png"), np.zeros((H, W, 3), np.uint8))
    with pytest.raises(SystemExit, match="does not match"):
        evaluate.main(args)


def test_yolo_polygon_label(tmp_path):
    label = tmp_path / "a.txt"
    label.write_text("0 0.5 0.1 0.52 0.1 0.52 0.9 0.5 0.9\n")
    mask = evaluate.read_yolo_polygons(label, (H, W))
    assert mask[20, 30] and not mask[20, 10]
