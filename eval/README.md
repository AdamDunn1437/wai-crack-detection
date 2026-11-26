# Eval (WAI-7)

One scoring script for every model, so the four approaches in the paper are graded on the same test images in the same way.

```bash
pip install -r eval/requirements.txt

# once per test set: freeze the split and commit the CSV
python eval/freeze_split.py --images DATA/cast3/images --out eval/splits/cast3_test.csv

# every run
python eval/evaluate.py --model yolo-seg-n --split eval/splits/cast3_test.csv \
    --images DATA/cast3/images --labels DATA/cast3/labels --preds PREDS/yolo-seg-n \
    --notes "trained on CRACK500 only"
```

Each run adds one row to `eval/results.csv` and writes `per_image.csv` plus overlay images to `eval/runs/<model>/<split>/` (ignored by git, since the overlays contain WECCA's photos).

## Inputs

| What | Format |
|---|---|
| Images | `.jpg` / `.png` in one folder |
| Labels | `<image stem>.txt` YOLO segmentation polygons (what Ben's tool exports), or `<image stem>.png` binary mask (what CRACK500 and DeepCrack ship with) |
| Split | CSV from `freeze_split.py`: `image,sha256` |
| Predictions | one `<image stem>.png` per test image (see below) |

## Prediction format

Every model writes **one PNG mask per test image**: same width and height as the original photo, 0 = background, any other value = crack. Each model applies its own threshold before saving.

A mask is the one output all four approaches can produce (YOLO-seg, Grounding DINO + SAM, the classical baseline, and the fine-tuned YOLO). If a model skips an image, the script scores it as "found nothing" and prints a warning, so no model gets credit for skipping hard photos.

YOLO-seg example (Ultralytics):

```python
from pathlib import Path
import cv2, numpy as np
from ultralytics import YOLO

model = YOLO("best.pt")
for r in model.predict("DATA/test/images", stream=True):
    mask = np.zeros(r.orig_shape, np.uint8)
    if r.masks is not None:
        for poly in r.masks.xy:  # polygons in original-image pixels
            cv2.fillPoly(mask, [poly.astype(np.int32)], 255)
    cv2.imwrite(f"PREDS/yolo-seg-n/{Path(r.path).stem}.png", mask)
```

## Metrics

Pixel counts are summed over the whole test set, then turned into scores (so a photo with a lot of crack counts for more than one with a hairline).

- **Strict**: IoU, precision, recall, F1. A predicted pixel only counts if it lands exactly on a labelled crack pixel.
- **Tolerant**: precision, recall, F1 where a predicted pixel counts if it's within `--tolerance` pixels of a labelled crack (default 2). Cracks are a few pixels wide, so a prediction that traces the crack one pixel to the side gets 0 strict IoU even though it found the crack. The tolerant scores answer "did it find the crack", the strict ones answer "did it outline it exactly". The tolerance is saved in every row, and rows are only comparable at the same tolerance.

Overlays: green = found, red = false alarm, blue = missed (near misses count as found).

## Test split

- **Public data**: use each dataset's official test split, frozen as its own CSV (e.g. `crack500_test.csv`, `deepcrack_test.csv`). That keeps our numbers comparable to published ones.
- **Our photos**: hold out a whole piece, not random photos. Cast 3 is the plan (WAI-27). If it isn't sanded until January, hold out one zone of cast 2 instead. Photos of the same spot look nearly identical, so a random split would leak training images into the test set.
- **Keeping it fixed**: the split CSV is committed and stores each image's SHA-256. The script refuses to run if an image is missing or has changed. Nobody trains or tunes thresholds on these images.

## Open questions (Alan, Adam)

1. OK with one PNG mask per image as the prediction format?
2. Which public test split(s) are you using for the Dec 8 baselines? I'll freeze them as soon as I know.
3. Our photos are high resolution. Should we score at full resolution (tiles stitched back together) or at a fixed downscaled size? This also decides what tolerance makes sense on canoe photos.

## Tests

```bash
python -m pytest eval
```
