# models/baselines/ (Alan, WAI-8)

**Goes here**

- Off-the-shelf model prompted with "crack", no training (e.g. Grounding DINO + SAM)
- YOLO segmentation trained on public crack datasets (e.g. CRACK500, DeepCrack)
- One training script + config, rerunnable by anyone
- Results on a held-out public split (IoU, F1), scored with `eval/` so they line up with every other approach
- A short note on what failed and why

Weights and `runs/` stay out of git.

Timeline: Dec 8.
