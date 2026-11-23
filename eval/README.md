# eval/ (Lucian, WAI-7)

One scoring script that every model goes through: the same test set and the same metrics, which makes the comparison fair.

**Goes here**

- `evaluate.py`: e.g. `python eval/evaluate.py --model <name> --preds <dir> --labels <dir>`
- Outputs: IoU and F1 (precision / recall), one row appended to the shared results table, and overlay images showing misses and false alarms
- A short design note: inputs, prediction format, metrics

Test set: held-out canoe photos, split by piece/zone **before** tiling. Until our labels exist, run it on Alan's public-data split.

Timeline: design + running on public data by Dec 8.
